"""Database Loader - Upload and execute SQL files"""
import os, json, logging, hashlib, time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
from database import get_pool
from auth import require_permission, UserInfo

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = '/tmp/pmo_uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

_load_status = {"status": "idle", "progress": 0, "message": "", "started": None, "finished": None, "statements_ok": 0, "statements_error": 0}

@router.post("/dev/upload-database-file")
async def upload_database_file(file: UploadFile = File(...), user: UserInfo = Depends(require_permission('devtools.sql'))):
    """Upload a SQL file for database loading"""
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(413, f"File too large. Max {MAX_FILE_SIZE // (1024*1024)}MB")

    content = await file.read()
    size = len(content)
    if size > MAX_FILE_SIZE:
        raise HTTPException(413, f"File too large: {size // (1024*1024)}MB")

    filepath = os.path.join(UPLOAD_DIR, 'uploaded_db.sql')
    with open(filepath, 'wb') as f:
        f.write(content)

    # Quick stats
    text = content.decode('utf-8', errors='replace')
    lines = text.count('\n')
    inserts = text.upper().count('INSERT')
    creates = text.upper().count('CREATE')

    return {
        "filename": file.filename,
        "size_bytes": size,
        "size_mb": round(size / (1024*1024), 2),
        "lines": lines,
        "insert_statements": inserts,
        "create_statements": creates,
        "uploaded_at": datetime.now().isoformat(),
        "filepath": filepath,
    }


@router.get("/dev/preview-database-file")
async def preview_database_file(user: UserInfo = Depends(require_permission('devtools.sql'))):
    """Preview the uploaded SQL file"""
    filepath = os.path.join(UPLOAD_DIR, 'uploaded_db.sql')
    if not os.path.exists(filepath):
        raise HTTPException(404, "No file uploaded")

    with open(filepath, 'r', errors='replace') as f:
        # Read first 100 lines
        preview_lines = []
        for i, line in enumerate(f):
            if i >= 100:
                break
            preview_lines.append(line.rstrip())

    size = os.path.getsize(filepath)
    return {
        "preview": preview_lines,
        "total_size_mb": round(size / (1024*1024), 2),
    }


@router.post("/dev/load-database-content")
async def load_database_content(request: Request, user: UserInfo = Depends(require_permission('devtools.sql'))):
    """Execute the uploaded SQL file against the database"""
    global _load_status
    filepath = os.path.join(UPLOAD_DIR, 'uploaded_db.sql')
    if not os.path.exists(filepath):
        raise HTTPException(404, "No file uploaded. Upload first.")

    pool = get_pool()
    if not pool:
        raise HTTPException(503, "Database not available")

    _load_status = {
        "status": "running", "progress": 0, "message": "Starting...",
        "started": datetime.now().isoformat(), "finished": None,
        "statements_ok": 0, "statements_error": 0, "errors": []
    }

    try:
        with open(filepath, 'r', errors='replace') as f:
            sql = f.read()

        # Split by semicolons
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        total = len(statements)
        ok = 0
        errors = 0
        error_list = []

        async with pool.acquire() as conn:
            for i, stmt in enumerate(statements):
                try:
                    await conn.execute(stmt)
                    ok += 1
                except Exception as e:
                    err = str(e)
                    if 'already exists' in err.lower() or 'duplicate' in err.lower() or 'unique' in err.lower():
                        ok += 1  # Count as OK (idempotent)
                    else:
                        errors += 1
                        if len(error_list) < 20:
                            error_list.append({"stmt": stmt[:100], "error": err[:200]})

                if i % 50 == 0:
                    _load_status["progress"] = int((i / max(total, 1)) * 100)
                    _load_status["message"] = f"Executing {i}/{total}..."
                    _load_status["statements_ok"] = ok
                    _load_status["statements_error"] = errors

            # Ensure admin user survives
            admin_hash = '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'
            await conn.execute("""
                INSERT INTO rbac_roles (code, nombre, descripcion, nivel_jerarquico, color, icono, activo)
                VALUES ('SUPERADMIN', 'Super Administrador', 'Acceso total al sistema', 0, '#EF4444', 'crown', TRUE)
                ON CONFLICT (code) DO NOTHING
            """)
            await conn.execute("""
                INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, departamento, cargo, activo, requiere_cambio_password)
                SELECT 'admin', $1, 'Administrador del Sistema', r.id_role, 'IT - Plataforma', 'System Administrator', TRUE, FALSE
                FROM rbac_roles r WHERE r.code = 'SUPERADMIN'
                ON CONFLICT (email) DO UPDATE SET password_hash = $1, activo = TRUE, requiere_cambio_password = FALSE
            """, admin_hash)
            await conn.execute("""
                INSERT INTO rbac_role_permisos (id_role, id_permiso)
                SELECT r.id_role, p.id_permiso FROM rbac_roles r, rbac_permisos p WHERE r.code = 'SUPERADMIN'
                ON CONFLICT DO NOTHING
            """)

        # Log audit
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO rbac_audit_log (id_usuario, email, accion, modulo, detalle, resultado)
                    VALUES ($1, $2, 'DATABASE_LOAD', 'devtools', $3, 'OK')
                """, user.id_usuario, user.email,
                    json.dumps({"ok": ok, "errors": errors, "total": total}))
        except:
            pass

        _load_status = {
            "status": "completed", "progress": 100,
            "message": f"Done! {ok} OK, {errors} errors out of {total} statements",
            "started": _load_status["started"],
            "finished": datetime.now().isoformat(),
            "statements_ok": ok, "statements_error": errors,
            "errors": error_list
        }

        return _load_status

    except Exception as e:
        _load_status["status"] = "error"
        _load_status["message"] = str(e)
        raise HTTPException(500, str(e))


@router.get("/dev/database-load-status")
async def database_load_status(user: UserInfo = Depends(require_permission('devtools.sql'))):
    return _load_status
