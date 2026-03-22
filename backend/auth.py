"""
COGNITIVE PMO - RBAC Authentication & Authorization Module
JWT-based authentication with role-based access control.
"""

import os
import json
import hashlib
import hmac
import base64
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from functools import wraps

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from database import get_pool

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "cognitive-pmo-rbac-secret-key-2026-change-in-prod")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
security = HTTPBearer(auto_error=False)


# ── Models ────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    usuario: dict
    permisos: List[str]
    role: dict


class UserInfo(BaseModel):
    id_usuario: int
    email: str
    nombre_completo: str
    id_role: int
    role_code: str
    role_nombre: str
    departamento: Optional[str] = None
    cargo: Optional[str] = None
    permisos: List[str] = []


# ── JWT Simple Implementation ─────────────────────────────────────────────
def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _b64decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    s += '=' * padding
    return base64.urlsafe_b64decode(s)


def _sign(payload: str) -> str:
    return _b64encode(
        hmac.new(JWT_SECRET.encode(), payload.encode(), hashlib.sha256).digest()
    )


def create_jwt(claims: dict) -> str:
    header = _b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64encode(json.dumps(claims, default=str).encode())
    signature = _sign(f"{header}.{payload}")
    return f"{header}.{payload}.{signature}"


def decode_jwt(token: str) -> Optional[dict]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header, payload, signature = parts
        expected_sig = _sign(f"{header}.{payload}")
        if not hmac.compare_digest(signature, expected_sig):
            return None
        claims = json.loads(_b64decode(payload))
        if claims.get('exp') and float(claims['exp']) < time.time():
            return None
        return claims
    except Exception:
        return None


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── Auth Dependencies ─────────────────────────────────────────────────────
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[UserInfo]:
    """Extract and validate JWT from Authorization header. Returns None if no auth."""
    if not credentials:
        return None

    claims = decode_jwt(credentials.credentials)
    if not claims:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT u.id_usuario, u.email, u.nombre_completo, u.id_role,
                       u.departamento, u.cargo, u.activo,
                       r.code as role_code, r.nombre as role_nombre
                FROM rbac_usuarios u
                JOIN rbac_roles r ON u.id_role = r.id_role
                WHERE u.id_usuario = $1 AND u.activo = TRUE
            """, claims.get('sub'))

            if not row:
                raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

            permisos = await conn.fetch("""
                SELECT p.code
                FROM rbac_role_permisos rp
                JOIN rbac_permisos p ON rp.id_permiso = p.id_permiso
                WHERE rp.id_role = $1
            """, row['id_role'])

            return UserInfo(
                id_usuario=row['id_usuario'],
                email=row['email'],
                nombre_completo=row['nombre_completo'],
                id_role=row['id_role'],
                role_code=row['role_code'],
                role_nombre=row['role_nombre'],
                departamento=row['departamento'],
                cargo=row['cargo'],
                permisos=[p['code'] for p in permisos],
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        raise HTTPException(status_code=500, detail="Error de autenticación")


def require_permission(*required_permisos: str):
    """Decorator/dependency factory: require user to have ALL listed permissions."""
    async def dependency(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    ) -> UserInfo:
        user = await get_current_user(request, credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Autenticación requerida")

        # SUPERADMIN bypasses all checks
        if user.role_code == 'SUPERADMIN':
            return user

        missing = [p for p in required_permisos if p not in user.permisos]
        if missing:
            # Log the denied access
            pool = get_pool()
            if pool:
                try:
                    async with pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO rbac_audit_log (id_usuario, email, accion, modulo, recurso, detalle, ip_address, resultado)
                            VALUES ($1, $2, 'ACCESO_DENEGADO', $3, $4, $5, $6, 'DENEGADO')
                        """, user.id_usuario, user.email,
                            required_permisos[0].split('.')[0] if required_permisos else 'unknown',
                            request.url.path,
                            json.dumps({"missing_permisos": missing}),
                            request.client.host if request.client else None)
                except Exception:
                    pass

            raise HTTPException(
                status_code=403,
                detail=f"Permisos insuficientes. Requiere: {', '.join(missing)}"
            )
        return user
    return dependency


# ── Login Endpoint Logic ──────────────────────────────────────────────────
async def authenticate_user(email: str, password: str, request: Request) -> LoginResponse:
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")

    pw_hash = hash_password(password)
    ip = request.client.host if request.client else None

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT u.*, r.code as role_code, r.nombre as role_nombre,
                       r.color as role_color, r.icono as role_icono,
                       r.nivel_jerarquico
                FROM rbac_usuarios u
                JOIN rbac_roles r ON u.id_role = r.id_role
                WHERE u.email = $1 AND u.password_hash = $2
            """, email, pw_hash)

            if not row:
                # Log failed attempt
                await conn.execute("""
                    INSERT INTO rbac_audit_log (email, accion, detalle, ip_address, resultado)
                    VALUES ($1, 'LOGIN_FALLIDO', '{"reason":"credenciales_invalidas"}', $2, 'DENEGADO')
                """, email, ip)
                raise HTTPException(status_code=401, detail="Credenciales inválidas")

            if not row['activo']:
                raise HTTPException(status_code=403, detail="Cuenta desactivada")

            # Get permissions
            permisos = await conn.fetch("""
                SELECT p.code, p.modulo, p.accion, p.descripcion
                FROM rbac_role_permisos rp
                JOIN rbac_permisos p ON rp.id_permiso = p.id_permiso
                WHERE rp.id_role = $1
                ORDER BY p.modulo, p.accion
            """, row['id_role'])

            # Create JWT
            claims = {
                "sub": row['id_usuario'],
                "email": row['email'],
                "role": row['role_code'],
                "nombre": row['nombre_completo'],
                "exp": (datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)).timestamp(),
                "iat": datetime.utcnow().timestamp(),
            }
            token = create_jwt(claims)

            # Update login tracking
            await conn.execute("""
                UPDATE rbac_usuarios
                SET ultimo_login = NOW(), login_count = login_count + 1, updated_at = NOW()
                WHERE id_usuario = $1
            """, row['id_usuario'])

            # Log success
            await conn.execute("""
                INSERT INTO rbac_audit_log (id_usuario, email, accion, modulo, detalle, ip_address, resultado)
                VALUES ($1, $2, 'LOGIN_OK', 'auth', $3, $4, 'OK')
            """, row['id_usuario'], row['email'],
                json.dumps({"role": row['role_code']}), ip)

            # Store session
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            user_agent = request.headers.get('user-agent', '')
            await conn.execute("""
                INSERT INTO rbac_sesiones (id_usuario, token_hash, ip_address, user_agent, expires_at)
                VALUES ($1, $2, $3, $4, $5)
            """, row['id_usuario'], token_hash, ip, user_agent,
                datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS))

            return LoginResponse(
                token=token,
                usuario={
                    "id_usuario": row['id_usuario'],
                    "email": row['email'],
                    "nombre_completo": row['nombre_completo'],
                    "departamento": row['departamento'],
                    "cargo": row['cargo'],
                    "id_recurso": row['id_recurso'],
                    "id_directivo": row['id_directivo'],
                    "ultimo_login": row['ultimo_login'].isoformat() if row['ultimo_login'] else None,
                    "login_count": (row['login_count'] or 0) + 1,
                    "requiere_cambio_password": row['requiere_cambio_password'],
                    "avatar_url": row['avatar_url'],
                },
                permisos=[p['code'] for p in permisos],
                role={
                    "code": row['role_code'],
                    "nombre": row['role_nombre'],
                    "color": row['role_color'],
                    "icono": row['role_icono'],
                    "nivel_jerarquico": row['nivel_jerarquico'],
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=500, detail=f"Error de autenticación: {str(e)}")
