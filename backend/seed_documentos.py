"""
Seed script: registra todos los archivos de /app/data/documentos/ en la BD.
Ejecutar: docker exec cognitive-pmo-api-1 python seed_documentos.py
"""
import os
import hashlib
import asyncio
import asyncpg

STORAGE_ROOT = "/app/data/documentos"
DB_DSN = "postgresql://jose_admin:REDACTED-old-password@postgres:5432/cognitive_pmo"

MIME_MAP = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "md": "text/markdown",
    "html": "text/html",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "png": "image/png",
    "jpg": "image/jpeg",
}

TIPO_MAP = {
    "pdf": "pdf", "txt": "texto", "md": "texto", "html": "texto",
    "docx": "docx", "xlsx": "xlsx", "csv": "csv",
    "png": "imagen", "jpg": "imagen",
}


def extraer_texto_simple(path, mime):
    """Extrae texto sin dependencias pesadas para el seed."""
    try:
        if "text/" in mime:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()[:50000]
        if "pdf" in mime:
            from PyPDF2 import PdfReader
            reader = PdfReader(path)
            return "\n".join(p.extract_text() or "" for p in reader.pages)[:50000]
    except Exception as e:
        print(f"  ⚠ Text extraction failed for {path}: {e}")
    return ""


async def main():
    conn = await asyncpg.connect(DB_DSN)
    await conn.execute("SET search_path TO primitiva, compartido, public")

    # Get existing hashes to skip duplicates
    existing = set()
    rows = await conn.fetch("SELECT hash_sha256 FROM documentacion_repositorio WHERE hash_sha256 IS NOT NULL")
    for r in rows:
        existing.add(r["hash_sha256"])
    print(f"Existing docs in DB: {len(existing)}")

    inserted = 0
    skipped = 0
    errors = 0

    for root, dirs, files in os.walk(STORAGE_ROOT):
        for fname in sorted(files):
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, STORAGE_ROOT)

            # Determine silo from directory structure
            parts = rel_path.split(os.sep)
            silo = parts[0] if len(parts) > 1 else "transversal"
            if silo not in ("build", "run", "transversal", "confidencial", "cmdb"):
                silo = "transversal"

            # File info
            ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
            mime = MIME_MAP.get(ext, "application/octet-stream")
            tipo = TIPO_MAP.get(ext, "otro")
            size = os.path.getsize(full_path)

            # SHA256
            with open(full_path, "rb") as f:
                content = f.read()
            sha256 = hashlib.sha256(content).hexdigest()

            if sha256 in existing:
                skipped += 1
                continue

            # Title from filename
            titulo = fname.replace("_", " ").rsplit(".", 1)[0]

            # Extract text
            texto = extraer_texto_simple(full_path, mime)

            try:
                await conn.execute("""
                    INSERT INTO documentacion_repositorio
                    (titulo, tipo, silo, categoria, autor, mime_type, nombre_archivo,
                     tamanio_bytes, hash_sha256, ruta_fisica, texto_extraido,
                     estado_procesamiento, confidencialidad)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,'pendiente',$12)
                """,
                    titulo, tipo, silo, "organizacion", "seed",
                    mime, fname, size, sha256, rel_path, texto,
                    "confidencial" if silo == "confidencial" else "interna",
                )
                existing.add(sha256)
                inserted += 1
                if inserted % 20 == 0:
                    print(f"  ... {inserted} insertados")
            except Exception as e:
                errors += 1
                print(f"  ✗ Error inserting {fname}: {e}")

    await conn.close()
    print(f"\n{'='*50}")
    print(f"Seed completado:")
    print(f"  Insertados: {inserted}")
    print(f"  Duplicados: {skipped}")
    print(f"  Errores: {errors}")
    print(f"  Total en BD: {len(existing)}")
    print(f"\nEl worker AG-DOC procesará automáticamente los {inserted} docs pendientes.")
    print(f"Tiempo estimado: ~{inserted * 90 // 60} minutos (90s/doc con gemma3:1b)")


if __name__ == "__main__":
    asyncio.run(main())
