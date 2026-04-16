"""
COGNITIVE PMO - RBAC API Endpoints
Gestión de usuarios, roles, permisos, auditoría y directorio corporativo.
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Request, Depends, Query
from pydantic import BaseModel

from database import get_pool
from auth import (
    LoginRequest, authenticate_user, get_current_user,
    require_permission, hash_password, UserInfo,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Auth Endpoints ────────────────────────────────────────────────────────

@router.post("/auth/login")
async def login(body: LoginRequest, request: Request):
    """Authenticate user and return JWT token with permissions."""
    return await authenticate_user(body.email, body.password, request)


@router.get("/auth/me")
async def get_me(user: UserInfo = Depends(get_current_user)):
    """Get current authenticated user info."""
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return {
        "usuario": {
            "id_usuario": user.id_usuario,
            "email": user.email,
            "nombre_completo": user.nombre_completo,
            "departamento": user.departamento,
            "cargo": user.cargo,
        },
        "role": {
            "code": user.role_code,
            "nombre": user.role_nombre,
        },
        "permisos": user.permisos,
        "total_permisos": len(user.permisos),
    }


@router.post("/auth/logout")
async def logout(request: Request, user: UserInfo = Depends(get_current_user)):
    """Invalidate current session."""
    if not user:
        return {"ok": True}
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE rbac_sesiones SET activa = FALSE
                    WHERE id_usuario = $1 AND activa = TRUE
                """, user.id_usuario)
                await conn.execute("""
                    INSERT INTO rbac_audit_log (id_usuario, email, accion, modulo, ip_address, resultado)
                    VALUES ($1, $2, 'LOGOUT', 'auth', $3, 'OK')
                """, user.id_usuario, user.email,
                    request.client.host if request.client else None)
        except Exception:
            pass
    return {"ok": True}


class ChangePasswordRequest(BaseModel):
    password_actual: str
    password_nueva: str


@router.post("/auth/cambiar-password")
async def cambiar_password(body: ChangePasswordRequest, user: UserInfo = Depends(get_current_user)):
    """Change own password."""
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        current = await conn.fetchval(
            "SELECT password_hash FROM rbac_usuarios WHERE id_usuario=$1",
            user.id_usuario)
        if current != hash_password(body.password_actual):
            raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
        await conn.execute("""
            UPDATE rbac_usuarios
            SET password_hash=$1, requiere_cambio_password=FALSE, updated_at=NOW()
            WHERE id_usuario=$2
        """, hash_password(body.password_nueva), user.id_usuario)
    return {"ok": True, "message": "Contraseña actualizada"}


# ── Roles ─────────────────────────────────────────────────────────────────

@router.get("/rbac/roles")
async def get_roles(user: UserInfo = Depends(require_permission('rbac.ver'))):
    pool = get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT r.*, COUNT(rp.id_permiso) as total_permisos,
                   COUNT(DISTINCT u.id_usuario) as total_usuarios
            FROM rbac_roles r
            LEFT JOIN rbac_role_permisos rp ON r.id_role = rp.id_role
            LEFT JOIN rbac_usuarios u ON u.id_role = r.id_role AND u.activo = TRUE
            GROUP BY r.id_role
            ORDER BY r.nivel_jerarquico, r.nombre
        """)
        return [dict(r) for r in rows]


@router.get("/rbac/roles/{role_id}/permisos")
async def get_role_permisos(role_id: int, user: UserInfo = Depends(require_permission('rbac.ver'))):
    pool = get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT p.*
            FROM rbac_role_permisos rp
            JOIN rbac_permisos p ON rp.id_permiso = p.id_permiso
            WHERE rp.id_role = $1
            ORDER BY p.modulo, p.accion
        """, role_id)
        return [dict(r) for r in rows]


class RoleCreate(BaseModel):
    code: str
    nombre: str
    descripcion: Optional[str] = None
    nivel_jerarquico: int = 5
    color: str = "#6B7280"
    icono: str = "shield"


class RoleUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    nivel_jerarquico: Optional[int] = None
    color: Optional[str] = None
    icono: Optional[str] = None
    activo: Optional[bool] = None


@router.post("/rbac/roles")
async def create_role(body: RoleCreate, user: UserInfo = Depends(require_permission('rbac.roles'))):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO rbac_roles (code, nombre, descripcion, nivel_jerarquico, color, icono)
                VALUES ($1,$2,$3,$4,$5,$6) RETURNING *
            """, body.code.upper().replace(' ', '_'), body.nombre, body.descripcion,
                body.nivel_jerarquico, body.color, body.icono)
            return dict(row)
    except Exception as e:
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            raise HTTPException(status_code=409, detail=f"Rol '{body.code}' ya existe")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rbac/roles/{role_id}")
async def update_role(role_id: int, body: RoleUpdate, user: UserInfo = Depends(require_permission('rbac.roles'))):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        sets, params = ["updated_at = NOW()"], []
        if body.nombre is not None:
            params.append(body.nombre); sets.append(f"nombre = ${len(params)}")
        if body.descripcion is not None:
            params.append(body.descripcion); sets.append(f"descripcion = ${len(params)}")
        if body.nivel_jerarquico is not None:
            params.append(body.nivel_jerarquico); sets.append(f"nivel_jerarquico = ${len(params)}")
        if body.color is not None:
            params.append(body.color); sets.append(f"color = ${len(params)}")
        if body.icono is not None:
            params.append(body.icono); sets.append(f"icono = ${len(params)}")
        if body.activo is not None:
            params.append(body.activo); sets.append(f"activo = ${len(params)}")
        params.append(role_id)
        row = await conn.fetchrow(
            f"UPDATE rbac_roles SET {', '.join(sets)} WHERE id_role = ${len(params)} RETURNING *", *params)
        if not row:
            raise HTTPException(status_code=404)
        return dict(row)


@router.put("/rbac/roles/{role_id}/permisos")
async def set_role_permisos(role_id: int, body: dict, user: UserInfo = Depends(require_permission('rbac.roles'))):
    """Replace all permissions for a role. Body: {"permisos": [1,2,3,...]} (list of id_permiso)"""
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    permiso_ids = body.get("permisos", [])
    async with pool.acquire() as conn:
        # Verify role exists
        role = await conn.fetchrow("SELECT id_role, code FROM rbac_roles WHERE id_role=$1", role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Rol no encontrado")
        # Replace permisos
        await conn.execute("DELETE FROM rbac_role_permisos WHERE id_role=$1", role_id)
        if permiso_ids:
            values = ", ".join([f"({role_id}, {int(pid)})" for pid in permiso_ids])
            await conn.execute(f"INSERT INTO rbac_role_permisos (id_role, id_permiso) VALUES {values} ON CONFLICT DO NOTHING")
        count = await conn.fetchval("SELECT COUNT(*) FROM rbac_role_permisos WHERE id_role=$1", role_id)
        # Log
        await conn.execute("""
            INSERT INTO rbac_audit_log (id_usuario, email, accion, modulo, recurso, detalle, resultado)
            VALUES ($1, $2, 'CAMBIO_PERMISOS_ROL', 'rbac', $3, $4, 'OK')
        """, user.id_usuario, user.email, role['code'],
            json.dumps({"role_id": role_id, "permisos_count": count}))
        return {"ok": True, "role_id": role_id, "permisos_count": count}


@router.delete("/rbac/roles/{role_id}")
async def delete_role(role_id: int, user: UserInfo = Depends(require_permission('rbac.roles'))):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        # Check no users assigned
        count = await conn.fetchval("SELECT COUNT(*) FROM rbac_usuarios WHERE id_role=$1 AND activo=TRUE", role_id)
        if count and count > 0:
            raise HTTPException(status_code=400, detail=f"No se puede eliminar: {count} usuarios activos tienen este rol")
        result = await conn.execute("DELETE FROM rbac_roles WHERE id_role=$1", role_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404)
        return {"ok": True}


# ── Permisos ──────────────────────────────────────────────────────────────

@router.get("/rbac/permisos")
async def get_all_permisos(user: UserInfo = Depends(require_permission('rbac.ver'))):
    pool = get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM rbac_permisos ORDER BY modulo, accion")
        return [dict(r) for r in rows]


# ── Usuarios ──────────────────────────────────────────────────────────────

@router.get("/rbac/usuarios")
async def get_usuarios(
    role: Optional[str] = None,
    departamento: Optional[str] = None,
    search: Optional[str] = None,
    activo: Optional[bool] = True,
    limit: int = 200,
    offset: int = 0,
    user: UserInfo = Depends(require_permission('rbac.ver')),
):
    pool = get_pool()
    if not pool:
        return {"usuarios": [], "total": 0}
    clauses = []
    params = []
    if activo is not None:
        params.append(activo)
        clauses.append(f"u.activo = ${len(params)}")
    if role:
        params.append(role)
        clauses.append(f"r.code = ${len(params)}")
    if departamento:
        params.append(f"%{departamento}%")
        clauses.append(f"u.departamento ILIKE ${len(params)}")
    if search:
        params.append(f"%{search}%")
        clauses.append(f"(u.nombre_completo ILIKE ${len(params)} OR u.email ILIKE ${len(params)})")
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM rbac_usuarios u JOIN rbac_roles r ON u.id_role=r.id_role {where}", *params)
        params.extend([limit, offset])
        rows = await conn.fetch(f"""
            SELECT u.id_usuario, u.email, u.nombre_completo, u.departamento, u.cargo,
                   u.id_recurso, u.id_directivo, u.ultimo_login, u.login_count,
                   u.activo, u.requiere_cambio_password, u.created_at,
                   r.code as role_code, r.nombre as role_nombre, r.color as role_color,
                   r.icono as role_icono, r.nivel_jerarquico
            FROM rbac_usuarios u
            JOIN rbac_roles r ON u.id_role = r.id_role
            {where}
            ORDER BY r.nivel_jerarquico, u.nombre_completo
            LIMIT ${len(params)-1} OFFSET ${len(params)}
        """, *params)
        result = []
        for r in rows:
            d = dict(r)
            if d.get('ultimo_login'):
                d['ultimo_login'] = d['ultimo_login'].isoformat()
            if d.get('created_at'):
                d['created_at'] = d['created_at'].isoformat()
            result.append(d)
        return {"usuarios": result, "total": total}


class UsuarioCreate(BaseModel):
    email: str
    password: str = "12345"
    nombre_completo: str
    role_code: str
    departamento: Optional[str] = None
    cargo: Optional[str] = None
    id_recurso: Optional[str] = None
    id_directivo: Optional[str] = None


@router.post("/rbac/usuarios")
async def create_usuario(body: UsuarioCreate, user: UserInfo = Depends(require_permission('rbac.usuarios'))):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        role = await conn.fetchrow("SELECT id_role FROM rbac_roles WHERE code=$1", body.role_code)
        if not role:
            raise HTTPException(status_code=400, detail=f"Rol '{body.role_code}' no existe")
        try:
            row = await conn.fetchrow("""
                INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role,
                    departamento, cargo, id_recurso, id_directivo)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id_usuario, email, nombre_completo
            """, body.email, hash_password(body.password), body.nombre_completo,
                role['id_role'], body.departamento, body.cargo,
                body.id_recurso, body.id_directivo)
            return dict(row)
        except Exception as e:
            if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                raise HTTPException(status_code=409, detail=f"Email '{body.email}' ya existe")
            raise HTTPException(status_code=500, detail=str(e))


class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    role_code: Optional[str] = None
    departamento: Optional[str] = None
    cargo: Optional[str] = None
    activo: Optional[bool] = None


@router.put("/rbac/usuarios/{user_id}")
async def update_usuario(user_id: int, body: UsuarioUpdate, user: UserInfo = Depends(require_permission('rbac.usuarios'))):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        sets = ["updated_at = NOW()"]
        params = []
        if body.nombre_completo is not None:
            params.append(body.nombre_completo)
            sets.append(f"nombre_completo = ${len(params)}")
        if body.role_code is not None:
            role = await conn.fetchrow("SELECT id_role FROM rbac_roles WHERE code=$1", body.role_code)
            if not role:
                raise HTTPException(status_code=400, detail=f"Rol '{body.role_code}' no existe")
            params.append(role['id_role'])
            sets.append(f"id_role = ${len(params)}")
        if body.departamento is not None:
            params.append(body.departamento)
            sets.append(f"departamento = ${len(params)}")
        if body.cargo is not None:
            params.append(body.cargo)
            sets.append(f"cargo = ${len(params)}")
        if body.activo is not None:
            params.append(body.activo)
            sets.append(f"activo = ${len(params)}")
        params.append(user_id)
        row = await conn.fetchrow(
            f"UPDATE rbac_usuarios SET {', '.join(sets)} WHERE id_usuario = ${len(params)} RETURNING *",
            *params)
        if not row:
            raise HTTPException(status_code=404)
        return {"ok": True, "id_usuario": user_id}


@router.post("/rbac/usuarios/{user_id}/reset-password")
async def reset_password(user_id: int, user: UserInfo = Depends(require_permission('rbac.usuarios'))):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE rbac_usuarios
            SET password_hash=$1, requiere_cambio_password=TRUE, updated_at=NOW()
            WHERE id_usuario=$2
        """, hash_password("12345"), user_id)
        if result == "UPDATE 0":
            raise HTTPException(status_code=404)
    return {"ok": True, "message": "Contraseña reseteada a '12345'"}


# ── Audit Log ─────────────────────────────────────────────────────────────

@router.get("/rbac/audit")
async def get_audit_log(
    limit: int = 100,
    offset: int = 0,
    accion: Optional[str] = None,
    email: Optional[str] = None,
    resultado: Optional[str] = None,
    user: UserInfo = Depends(require_permission('rbac.audit')),
):
    pool = get_pool()
    if not pool:
        return {"logs": [], "total": 0}
    clauses, params = [], []
    if accion:
        params.append(accion)
        clauses.append(f"a.accion = ${len(params)}")
    if email:
        params.append(f"%{email}%")
        clauses.append(f"a.email ILIKE ${len(params)}")
    if resultado:
        params.append(resultado)
        clauses.append(f"a.resultado = ${len(params)}")
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    async with pool.acquire() as conn:
        total = await conn.fetchval(f"SELECT COUNT(*) FROM rbac_audit_log a {where}", *params)
        params.extend([limit, offset])
        rows = await conn.fetch(f"""
            SELECT a.*, u.nombre_completo
            FROM rbac_audit_log a
            LEFT JOIN rbac_usuarios u ON a.id_usuario = u.id_usuario
            {where}
            ORDER BY a.timestamp DESC
            LIMIT ${len(params)-1} OFFSET ${len(params)}
        """, *params)
        result = []
        for r in rows:
            d = dict(r)
            if d.get('timestamp'):
                d['timestamp'] = d['timestamp'].isoformat()
            result.append(d)
        return {"logs": result, "total": total}


# ── Directorio Corporativo ────────────────────────────────────────────────

@router.get("/directorio")
async def get_directorio(
    nivel: Optional[str] = None,
    area: Optional[str] = None,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    pool = get_pool()
    if not pool:
        return []
    clauses, params = ["d.activo = TRUE"], []
    if nivel:
        params.append(nivel)
        clauses.append(f"d.nivel_organizativo = ${len(params)}")
    if area:
        params.append(f"%{area}%")
        clauses.append(f"d.area ILIKE ${len(params)}")
    where = "WHERE " + " AND ".join(clauses)
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT d.*, p.nombre_completo as reporta_a_nombre, p.cargo as reporta_a_cargo
            FROM directorio_corporativo d
            LEFT JOIN directorio_corporativo p ON d.reporta_a = p.id_directivo
            {where}
            ORDER BY
                CASE d.nivel_organizativo
                    WHEN 'C-LEVEL' THEN 1
                    WHEN 'VP' THEN 2
                    WHEN 'DIRECTOR' THEN 3
                    WHEN 'SUBDIRECTOR' THEN 4
                    WHEN 'GERENTE' THEN 5
                    WHEN 'COORDINADOR' THEN 6
                    WHEN 'JEFE_EQUIPO' THEN 7
                END,
                d.nombre_completo
        """, *params)
        result = []
        for r in rows:
            d = dict(r)
            if d.get('fecha_incorporacion'):
                d['fecha_incorporacion'] = d['fecha_incorporacion'].isoformat()
            result.append(d)
        return result


@router.get("/directorio/organigrama")
async def get_organigrama(user: Optional[UserInfo] = Depends(get_current_user)):
    """Return hierarchical org chart."""
    pool = get_pool()
    if not pool:
        return {}
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id_directivo, nombre_completo, cargo, nivel_organizativo,
                   area, reporta_a, email
            FROM directorio_corporativo
            WHERE activo = TRUE
            ORDER BY nivel_organizativo
        """)
        nodes = {r['id_directivo']: dict(r) for r in rows}
        # Build tree
        for nid, node in nodes.items():
            node['subordinados'] = []
        for nid, node in nodes.items():
            parent_id = node.get('reporta_a')
            if parent_id and parent_id in nodes:
                nodes[parent_id]['subordinados'].append(node)
        # Root nodes (no reporta_a)
        roots = [n for n in nodes.values() if not n.get('reporta_a')]
        return {"organigrama": roots, "total_directivos": len(nodes)}


@router.get("/directorio/stats")
async def get_directorio_stats(user: Optional[UserInfo] = Depends(get_current_user)):
    pool = get_pool()
    if not pool:
        return {}
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM directorio_corporativo WHERE activo=TRUE")
        by_nivel = await conn.fetch(
            "SELECT nivel_organizativo, COUNT(*) as cnt FROM directorio_corporativo WHERE activo=TRUE GROUP BY nivel_organizativo")
        by_area = await conn.fetch(
            "SELECT area, COUNT(*) as cnt FROM directorio_corporativo WHERE activo=TRUE GROUP BY area ORDER BY cnt DESC")
        by_ubicacion = await conn.fetch(
            "SELECT ubicacion, COUNT(*) as cnt FROM directorio_corporativo WHERE activo=TRUE GROUP BY ubicacion")
        return {
            "total": total or 0,
            "by_nivel": {r['nivel_organizativo']: r['cnt'] for r in by_nivel},
            "by_area": {r['area']: r['cnt'] for r in by_area},
            "by_ubicacion": {r['ubicacion']: r['cnt'] for r in by_ubicacion},
        }


# ── RBAC Dashboard ────────────────────────────────────────────────────────

@router.get("/rbac/dashboard")
async def rbac_dashboard(user: UserInfo = Depends(require_permission('rbac.ver'))):
    pool = get_pool()
    if not pool:
        return {}
    async with pool.acquire() as conn:
        total_usuarios = await conn.fetchval("SELECT COUNT(*) FROM rbac_usuarios WHERE activo=TRUE")
        total_roles = await conn.fetchval("SELECT COUNT(*) FROM rbac_roles WHERE activo=TRUE")
        total_permisos = await conn.fetchval("SELECT COUNT(*) FROM rbac_permisos")
        usuarios_por_rol = await conn.fetch("""
            SELECT r.code, r.nombre, r.color, COUNT(u.id_usuario) as cnt
            FROM rbac_roles r
            LEFT JOIN rbac_usuarios u ON u.id_role = r.id_role AND u.activo = TRUE
            WHERE r.activo = TRUE
            GROUP BY r.id_role
            ORDER BY r.nivel_jerarquico
        """)
        logins_hoy = await conn.fetchval("""
            SELECT COUNT(*) FROM rbac_audit_log
            WHERE accion = 'LOGIN_OK' AND timestamp >= CURRENT_DATE
        """)
        accesos_denegados = await conn.fetchval("""
            SELECT COUNT(*) FROM rbac_audit_log
            WHERE resultado = 'DENEGADO' AND timestamp >= CURRENT_DATE - INTERVAL '7 days'
        """)
        ultimos_logins = await conn.fetch("""
            SELECT u.nombre_completo, u.email, r.code as role_code, r.color,
                   u.ultimo_login, u.login_count
            FROM rbac_usuarios u
            JOIN rbac_roles r ON u.id_role = r.id_role
            WHERE u.ultimo_login IS NOT NULL
            ORDER BY u.ultimo_login DESC
            LIMIT 10
        """)
        sesiones_activas = await conn.fetchval("""
            SELECT COUNT(*) FROM rbac_sesiones
            WHERE activa = TRUE AND expires_at > NOW()
        """)

        return {
            "total_usuarios": total_usuarios or 0,
            "total_roles": total_roles or 0,
            "total_permisos": total_permisos or 0,
            "sesiones_activas": sesiones_activas or 0,
            "logins_hoy": logins_hoy or 0,
            "accesos_denegados_7d": accesos_denegados or 0,
            "usuarios_por_rol": [dict(r) for r in usuarios_por_rol],
            "ultimos_logins": [
                {**dict(r), "ultimo_login": r['ultimo_login'].isoformat() if r['ultimo_login'] else None}
                for r in ultimos_logins
            ],
        }
