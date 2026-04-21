"""
AG-DOC: Agente de clasificación documental con Ollama.
Clasifica y resume documentos automáticamente usando gemma3:1b.
"""
import json
import logging
import asyncio
from datetime import datetime

from database import get_pool
from ollama_client import ollama_generate, ollama_health

logger = logging.getLogger("agent_doc")

PROMPT_CLASIFICACION = """Analiza este documento y devuelve SOLO un JSON válido sin explicaciones ni texto adicional:
{{"tipo":"procedimiento|normativa|acta|informe|contrato|manual|plantilla|politica|otro","subtipo":"descripcion breve 3-5 palabras","confidencialidad":"publica|interna|confidencial|restringida","departamento":"infraestructura|desarrollo|seguridad|operaciones|direccion|rrhh|legal|otro","palabras_clave":["max","5","keywords"]}}

DOCUMENTO:
{texto}"""

PROMPT_RESUMEN = """Resume este documento en máximo 3 frases en español.
Incluye: propósito principal, alcance y conclusión o acción requerida.
NO uses más de 150 palabras. Responde SOLO con el resumen.

DOCUMENTO:
{texto}"""

PROMPT_QA = """Basándote ÚNICAMENTE en estos documentos del repositorio, responde la pregunta.
Si no hay información suficiente, di "No he encontrado documentos relevantes sobre esto."
Cita el nombre del documento entre [corchetes] cuando hagas referencia a él.
Responde en español, máximo 200 palabras.

PREGUNTA: {query}

DOCUMENTOS ENCONTRADOS:
{contexto}

RESPUESTA:"""


async def procesar_documento(doc_id: int):
    """Clasifica y resume un documento con Ollama."""
    pool = get_pool()
    if not pool:
        logger.error(f"[AG-DOC] Pool no disponible para doc {doc_id}")
        return

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, titulo, texto_extraido FROM primitiva.documentacion_repositorio WHERE id=$1", doc_id
        )
    if not row:
        logger.warning(f"[AG-DOC] Doc {doc_id} no encontrado")
        return

    texto = row["texto_extraido"] or ""
    if len(texto.strip()) < 20:
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE primitiva.documentacion_repositorio SET estado_procesamiento='error', procesado_por='gemma3:1b' WHERE id=$1", doc_id
            )
        logger.warning(f"[AG-DOC] Doc {doc_id} sin texto suficiente ({len(texto)} chars)")
        return

    logger.info(f"[AG-DOC] Procesando doc {doc_id}: '{row['titulo']}' ({len(texto)} chars)")

    # 1. Clasificación
    clasificacion = None
    palabras_clave = None
    confianza = 0.0
    try:
        resp = await ollama_generate(PROMPT_CLASIFICACION.format(texto=texto[:2000]), max_tokens=300)
        # Extraer JSON de la respuesta (gemma3:1b a veces mete texto extra)
        start = resp.find("{")
        end = resp.rfind("}") + 1
        if start >= 0 and end > start:
            clasificacion = json.loads(resp[start:end])
            palabras_clave = clasificacion.get("palabras_clave", [])
            confianza = 0.7  # gemma3:1b base confidence
            logger.info(f"[AG-DOC] Doc {doc_id} clasificado: {clasificacion.get('tipo', '?')}")
        else:
            logger.warning(f"[AG-DOC] Doc {doc_id} clasificación sin JSON: {resp[:100]}")
    except json.JSONDecodeError as e:
        logger.warning(f"[AG-DOC] Doc {doc_id} JSON parse error: {e}")
    except Exception as e:
        logger.error(f"[AG-DOC] Doc {doc_id} clasificación falló: {e}")

    # 2. Resumen
    resumen = None
    try:
        resumen = await ollama_generate(PROMPT_RESUMEN.format(texto=texto[:3000]), max_tokens=200)
        resumen = resumen.strip()
        if len(resumen) < 10:
            resumen = None
        else:
            logger.info(f"[AG-DOC] Doc {doc_id} resumen: {resumen[:60]}...")
    except Exception as e:
        logger.error(f"[AG-DOC] Doc {doc_id} resumen falló: {e}")

    # 3. Actualizar BD
    estado = "completado" if (clasificacion or resumen) else "error"
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE primitiva.documentacion_repositorio SET
                resumen_ia=$1, clasificacion_ia=$2, palabras_clave_ia=$3,
                confianza_ia=$4, estado_procesamiento=$5, procesado_por='gemma3:1b',
                fecha_procesamiento=NOW()
            WHERE id=$6
        """,
            resumen,
            json.dumps(clasificacion) if clasificacion else None,
            palabras_clave,
            confianza, estado, doc_id
        )
        await conn.execute(
            "INSERT INTO primitiva.doc_actividad_log (doc_id, accion, usuario, detalle) VALUES ($1, 'classify', 'AG-DOC', $2)",
            doc_id, json.dumps({"estado": estado, "confianza": confianza})
        )
    logger.info(f"[AG-DOC] Doc {doc_id} → {estado}")


async def doc_worker_loop():
    """Worker que poll cada 10s buscando documentos pendientes."""
    logger.info("[AG-DOC] Worker iniciado")
    while True:
        try:
            pool = get_pool()
            if pool:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT id FROM primitiva.documentacion_repositorio WHERE estado_procesamiento='pendiente' ORDER BY id LIMIT 1"
                    )
                if row:
                    # Mark as processing
                    async with pool.acquire() as conn:
                        await conn.execute(
                            "UPDATE primitiva.documentacion_repositorio SET estado_procesamiento='procesando' WHERE id=$1", row["id"]
                        )
                    await procesar_documento(row["id"])
        except Exception as e:
            logger.error(f"[AG-DOC] Worker error: {e}")
        await asyncio.sleep(10)


async def responder_pregunta(query: str, scope: str = "all") -> dict:
    """Q&A sobre documentos usando full-text search + Ollama."""
    pool = get_pool()
    if not pool:
        return {"respuesta": "BD no disponible", "fuentes": []}

    # Full-text search
    where = "eliminado=false AND tsv @@ plainto_tsquery('spanish', $1)"
    params = [query]
    if scope != "all":
        where += " AND silo=$2"
        params.append(scope)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT id, titulo, resumen_ia, texto_extraido FROM primitiva.documentacion_repositorio WHERE {where} ORDER BY ts_rank(tsv, plainto_tsquery('spanish', $1)) DESC LIMIT 5",
            *params
        )

    if not rows:
        return {"respuesta": "No he encontrado documentos relevantes sobre esto.", "fuentes": [], "tiempo_ms": 0}

    # Build context
    contexto_parts = []
    fuentes = []
    for r in rows:
        titulo = r["titulo"]
        texto = r["resumen_ia"] or (r["texto_extraido"] or "")[:500]
        contexto_parts.append(f"[{titulo}]: {texto}")
        fuentes.append({"id": r["id"], "titulo": titulo})

    contexto = "\n\n".join(contexto_parts)

    import time
    t0 = time.time()
    respuesta = await ollama_generate(PROMPT_QA.format(query=query, contexto=contexto), max_tokens=300)
    tiempo_ms = int((time.time() - t0) * 1000)

    return {"respuesta": respuesta.strip(), "fuentes": fuentes, "tiempo_ms": tiempo_ms}
