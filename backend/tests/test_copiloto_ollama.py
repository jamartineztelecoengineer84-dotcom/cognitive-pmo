"""
ARQ-04 F7 — Test Tech Copiloto con Ollama (gemma3:1b, zero data exposure)
Ejecutar: docker exec cognitive-pmo-api-1 python /app/tests/test_copiloto_ollama.py
"""
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SYSTEM_PROMPT = """Eres el copiloto IA de Cognitive PMO. Ayudas a técnicos de BCC Bank con información de la CMDB, CAB, incidencias y proyectos.

Reglas:
- Responde de forma concisa y técnica
- Si tienes datos de la BD, úsalos y cítalos
- Si no tienes datos suficientes, dilo claramente
- Formato: usa markdown ligero (negritas, listas, código inline)
- Máximo 250 palabras
- Incluye recomendaciones accionables cuando sea posible
- No inventes datos que no estén en el contexto proporcionado"""


async def main():
    print("=" * 60)
    print("ARQ-04 F7 — Tech Copiloto via Ollama (gemma3:1b)")
    print("Zero data exposure: datos nunca salen del servidor")
    print("=" * 60)

    # 1. Test simple chat
    from llm_provider import get_provider
    provider = get_provider("ollama")
    print(f"\n1. Provider: OllamaProvider (base_url={provider.base_url})")

    t0 = time.monotonic()
    resp = await provider.create_message(
        model="gemma3:1b",
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": "¿Qué dependencias tiene un servidor de base de datos Oracle en producción?"}],
    )
    elapsed = int((time.monotonic() - t0) * 1000)
    print(f"\n2. Respuesta copiloto ({elapsed}ms):")
    print(f"   {resp.text[:500]}")
    print(f"   Tokens: in={resp.input_tokens} out={resp.output_tokens}")

    # 2. Test with CMDB context (simulating what tech_copiloto does)
    contexto = {
        "cmdb_activos": [{
            "codigo": "SRV-PRO-001",
            "nombre": "Servidor Core Banking Principal",
            "tipo": "Servidor",
            "estado_ciclo": "Operativo",
            "direccion_ip": "10.1.1.10",
            "hostname": "corebk-prod-01",
        }],
        "dependencias": [
            {"tipo_relacion": "ejecuta_en", "criticidad": "CRITICA",
             "codigo": "DB-PRO-001", "nombre": "Oracle Core Banking", "tipo": "Base de Datos"},
            {"tipo_relacion": "monitorizado_por", "criticidad": "ALTA",
             "codigo": "MON-PRO-002", "nombre": "Zabbix Infraestructura", "tipo": "Monitorización"},
        ]
    }
    contexto_json = json.dumps(contexto, indent=2, ensure_ascii=False)

    t0 = time.monotonic()
    resp2 = await provider.create_message(
        model="gemma3:1b",
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"""Pregunta del técnico Rafael García (REC-015):
¿Qué dependencias tiene SRV-PRO-001?

Datos de la BD de Cognitive PMO:
{contexto_json}"""}],
    )
    elapsed2 = int((time.monotonic() - t0) * 1000)
    print(f"\n3. Copiloto con contexto CMDB ({elapsed2}ms):")
    print(f"   {resp2.text[:500]}")
    print(f"   Tokens: in={resp2.input_tokens} out={resp2.output_tokens}")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"RESUMEN:")
    print(f"  Chat simple:       {elapsed}ms, {resp.output_tokens} tokens")
    print(f"  Copiloto con CMDB: {elapsed2}ms, {resp2.output_tokens} tokens")
    print(f"  Modelo: gemma3:1b (815MB, Q4_K_M)")
    print(f"  Coste: $0.00 (local)")
    print(f"  Data exposure: ZERO (todo en localhost)")
    has_context = "SRV-PRO-001" in resp2.text or "Oracle" in resp2.text or "DB-PRO" in resp2.text
    print(f"  Usa contexto CMDB: {'YES' if has_context else 'NO'}")


if __name__ == "__main__":
    asyncio.run(main())
