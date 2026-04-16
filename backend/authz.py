"""F5 · Autorización por rol — defensa en profundidad server-side.

Uso:
1. Middleware `role_gate_middleware` registrado en main.py aplica restricción por
   prefijo de path para las colecciones /api/pm/*, /api/tech/*, /api/p96/*.
2. Dependencia `require_role(allowed)` para uso puntual en endpoints.

Excepciones (cualquier autenticado):
- /api/pm/me, /api/tech/me, /api/me, /auth/me, /auth/login, /auth/logout, /docs, /openapi.json
"""
from typing import Iterable, Optional, Set
import json
import base64

from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from auth import get_current_user, UserInfo


# ── Política ────────────────────────────────────────────────────────
PM_ROLES: Set[str] = {"PMO_SENIOR", "PMO_JUNIOR", "SUPERADMIN"}
TECH_ROLES: Set[str] = {"TECH_SENIOR", "TECH_JUNIOR", "SUPERADMIN"}
P96_ROLES: Set[str] = {
    "CEO", "CFO", "CIO", "CTO", "CISO", "VP_PMO",
    "DIRECTOR_INFRA", "DIRECTOR_SEC", "DIRECTOR_DATA", "DIRECTOR_IT",
    "AUDITOR", "SUPERADMIN",
}

# Landings oficiales (coincide con routeByRole del frontend)
ROLE_LANDINGS = {
    "SUPERADMIN": "/",
    "CEO": "/p96/", "CFO": "/p96/", "CIO": "/p96/", "CTO": "/p96/", "CISO": "/p96/",
    "VP_PMO": "/p96/",
    "DIRECTOR_INFRA": "/p96/", "DIRECTOR_SEC": "/p96/",
    "DIRECTOR_DATA": "/p96/", "DIRECTOR_IT": "/p96/", "AUDITOR": "/p96/",
    "VP_OPERATIONS": "/gov-run.html", "VP_ENGINEERING": "/gov-build.html",
    "PMO_SENIOR": "/pm/", "PMO_JUNIOR": "/pm/",
    "TECH_SENIOR": "/tech-dashboard.html", "TECH_JUNIOR": "/tech-dashboard.html",
}

# Endpoints que cualquier autenticado puede tocar aunque matcheen el prefijo
EXEMPT_PATHS: Set[str] = {
    "/api/pm/me", "/api/tech/me", "/api/me", "/auth/me",
    "/auth/login", "/auth/logout",
}


def require_role(allowed: Iterable[str]):
    """Dependency: 403 si el rol del usuario no está permitido."""
    allowed_set = set(allowed)
    async def _check(user: Optional[UserInfo] = Depends(get_current_user)) -> UserInfo:
        if user is None:
            raise HTTPException(status_code=401, detail="Autenticación requerida")
        if user.role_code not in allowed_set:
            raise HTTPException(status_code=403, detail="Rol no autorizado para este recurso")
        return user
    return _check


def _extract_role_from_bearer(auth_header: Optional[str]) -> Optional[str]:
    """Decodifica payload JWT sin validar firma (solo para gating rápido de middleware).
    La validación real sigue ocurriendo en get_current_user via auth.py."""
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header[7:].strip()
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("role")
    except Exception:
        return None


def _allowed_for_path(path: str, role: str) -> bool:
    if path in EXEMPT_PATHS:
        return True
    if path.startswith("/api/pm/"):
        return role in PM_ROLES
    if path.startswith("/api/tech/"):
        return role in TECH_ROLES
    if path.startswith("/api/p96/"):
        return role in P96_ROLES
    return True   # fuera del alcance F5


async def role_gate_middleware(request: Request, call_next):
    """Middleware global: 401 si no hay token para rutas protegidas,
    403 si el rol no está permitido. Endpoints EXEMPT_PATHS pasan."""
    path = request.url.path
    # Solo intervenimos en los tres prefijos F5
    needs_gate = (
        path.startswith("/api/pm/") or
        path.startswith("/api/tech/") or
        path.startswith("/api/p96/")
    )
    if not needs_gate or path in EXEMPT_PATHS:
        return await call_next(request)

    role = _extract_role_from_bearer(request.headers.get("authorization"))
    if not role:
        return JSONResponse(status_code=401, content={"detail": "Autenticación requerida"})
    if not _allowed_for_path(path, role):
        return JSONResponse(status_code=403, content={"detail": f"Rol {role} no autorizado para {path}"})
    return await call_next(request)
