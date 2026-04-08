"""
P97 FASE 3 — Router /api/p96/* (lectura del CEO Dashboard v6)

14 endpoints GET, todos con scope económico aplicado al inicio:
  scope = _load_econ_scope(user.role_code)
  if scope.scope_who == 'NADIE': raise HTTPException(403)
  ... query con filtros de scope ...
  _log_econ_access(user, request.url.path)

NOTA IMPORTANTE: las tablas rbac_econ_scopes / rbac_econ_audit_log
propuestas en P96 FASE B nunca se crearon. Por eso este router incluye
helpers _load_econ_scope y _log_econ_access EMBEBIDOS, basados en
rbac_roles.code (los 23 roles reales). Cuando se materialice la P96
FASE B con tablas reales, estos helpers deben extraerse a auth.py
y compartirse con /api/econ/*.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional, List
import json
import logging

from auth import get_current_user, UserInfo
from database import get_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/p96", tags=["p96"])

# Router secundario SIN prefijo /api/p96 para endpoints globales como /api/me
me_router = APIRouter(tags=["p96-me"])

# P97 FASE 6 — Allowlist de roles autorizados a entrar al CEO Dashboard /p96/
# (16 roles: niveles 0-4 + PMO_JUNIOR añadido en ARQ-01 F5)
P96_ALLOWED_ROLES = {
    'SUPERADMIN', 'CEO', 'CFO', 'CIO', 'CTO', 'CISO',
    'VP_ENGINEERING', 'VP_OPERATIONS', 'VP_PMO',
    'DIRECTOR_INFRA', 'DIRECTOR_SEC', 'DIRECTOR_DATA', 'DIRECTOR_IT',
    'PMO_SENIOR', 'PMO_JUNIOR',
    'AUDITOR',
}


# ─────────────────────────────────────────────────────────────────────
# P97 FASE 6 — /api/me enriquecido con scope económico + p96_allowed
# ─────────────────────────────────────────────────────────────────────
@me_router.get("/api/me")
async def get_me(user: UserInfo = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    scope = _load_econ_scope(user.role_code)
    return {
        "id": user.id_usuario,
        "email": user.email,
        "nombre": user.nombre_completo,
        "role_code": user.role_code,
        "role_nombre": user.role_nombre,
        "scope_who": scope.scope_who,
        "ver_nombres": scope.ver_nombres,
        "ver_salario_ind": scope.ver_salario_ind,
        "silos_visibles": scope.silos_visibles,
        "p96_allowed": user.role_code in P96_ALLOWED_ROLES,
    }


# ─────────────────────────────────────────────────────────────────────
# Mini-RBAC económico embebido (sustituye a rbac_econ_scopes que no existe)
# ─────────────────────────────────────────────────────────────────────
class EconScope:
    """Scope económico de un usuario en función de su role_code."""
    def __init__(self, scope_who: str, silos_visibles: List[str],
                 ver_nombres: bool, ver_salario_ind: bool):
        self.scope_who = scope_who          # TODOS|MI_RAMA|MI_SILO|MIS_PROYECTOS|MI_EQUIPO|YO|AGREGADO|NADIE
        self.silos_visibles = silos_visibles
        self.ver_nombres = ver_nombres
        self.ver_salario_ind = ver_salario_ind


# Mapping completo basado en los 23 role_code reales de rbac_roles
_SCOPE_MAP = {
    # ── GLOBALES (TODOS) ──
    'SUPERADMIN':     ('TODOS', [],                                                              True,  True),
    'CEO':            ('TODOS', [],                                                              True,  False),
    'CFO':            ('TODOS', [],                                                              True,  True),
    'CTO':            ('TODOS', [],                                                              True,  False),
    'CIO':            ('TODOS', [],                                                              True,  False),
    'AUDITOR':        ('TODOS', [],                                                              False, False),
    'VP_PMO':         ('TODOS', [],                                                              True,  False),
    # ── DOMINIO (MI_RAMA) ──
    'CISO':           ('MI_SILO', ['IT-SEGURIDAD'],                                              True,  False),
    'VP_OPERATIONS':  ('MI_RAMA', ['IT-INFRA','IT-RED','IT-CLOUD','IT-VIRTUAL','IT-STORAGE'],    True,  False),
    'VP_ENGINEERING': ('MI_RAMA', ['IT-DATA','IT-APPS'],                                         True,  False),
    # ── SILO ──
    'DIRECTOR_INFRA': ('MI_SILO', ['IT-INFRA','IT-RED','IT-CLOUD','IT-VIRTUAL','IT-STORAGE'],    True,  False),
    'DIRECTOR_SEC':   ('MI_SILO', ['IT-SEGURIDAD'],                                              True,  False),
    'DIRECTOR_DATA':  ('MI_SILO', ['IT-DATA'],                                                   True,  False),
    'DIRECTOR_IT':    ('MI_SILO', ['IT-INFRA','IT-APPS'],                                        True,  False),
    # ── PROYECTOS (filtra por PM) ──
    'PMO_SENIOR':     ('MIS_PROYECTOS', [],                                                      True,  False),
    'PMO_JUNIOR':     ('MIS_PROYECTOS', [],                                                      True,  False),
    # ── EQUIPO ──
    'TEAM_LEAD':      ('MI_EQUIPO', [],                                                          False, False),
    'QA_LEAD':        ('MI_EQUIPO', [],                                                          False, False),
    'DEVOPS_LEAD':    ('MI_EQUIPO', [],                                                          False, False),
    # ── PERSONAL ──
    'TECH_SENIOR':    ('YO', [],                                                                 False, False),
    # ── SIN ACCESO ──
    'TECH_JUNIOR':    ('NADIE', [],                                                              False, False),
    'READONLY':       ('NADIE', [],                                                              False, False),
    'OBSERVADOR':     ('AGREGADO', [],                                                           False, False),
}


def _load_econ_scope(role_code: str) -> EconScope:
    """Devuelve el EconScope del rol. Default = NADIE si rol desconocido."""
    cfg = _SCOPE_MAP.get(role_code, ('NADIE', [], False, False))
    return EconScope(*cfg)


async def _log_econ_access(conn, user: UserInfo, endpoint: str, scope: EconScope, n_filas: int = 0):
    """Registra el acceso económico. Cuando exista rbac_econ_audit_log, hará INSERT.
    Mientras tanto, solo logger.info para trazabilidad operativa.
    """
    logger.info(
        f"[p96-rbac] user={user.id_usuario} role={user.role_code} "
        f"endpoint={endpoint} scope_who={scope.scope_who} filas={n_filas}"
    )
    # TODO P96 FASE B: cuando exista rbac_econ_audit_log:
    # await conn.execute("INSERT INTO rbac_econ_audit_log (id_usuario, endpoint, scope_aplicado, filas_devueltas) VALUES ($1,$2,$3,$4)", user.id_usuario, endpoint, scope.scope_who, n_filas)


def _decode_jsonb(value):
    """asyncpg devuelve JSONB como str — decodificar a dict/list."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


def _anon_name(real_name: Optional[str], user_id_for_hash: int) -> str:
    """Anonimiza un nombre como 'Empleado #N' usando hash determinista."""
    if not real_name:
        return "—"
    # Hash determinista: mismo nombre real → mismo Empleado #N
    h = abs(hash(real_name)) % 999
    return f"Empleado #{h:03d}"


def _require_scope(user: Optional[UserInfo]) -> tuple[UserInfo, EconScope]:
    """Dependency-style: valida user y devuelve (user, scope). 401 si no auth, 403 si NADIE."""
    if not user:
        raise HTTPException(401, "No autenticado")
    scope = _load_econ_scope(user.role_code)
    if scope.scope_who == 'NADIE':
        raise HTTPException(403, f"Sin acceso económico para rol {user.role_code}")
    return user, scope


# ─────────────────────────────────────────────────────────────────────
# 1. GET /api/p96/governors
# ─────────────────────────────────────────────────────────────────────
@router.get("/governors")
async def p96_governors(
    request: Request,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    user, scope = _require_scope(user)
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        if scope.scope_who in ('MI_RAMA', 'MI_SILO') and scope.silos_visibles:
            rows = await conn.fetch(
                "SELECT * FROM p96_governors WHERE silo = ANY($1::text[]) OR silo = 'CROSS' ORDER BY id_gov",
                scope.silos_visibles
            )
        else:
            rows = await conn.fetch("SELECT * FROM p96_governors ORDER BY id_gov")
        result = [dict(r) for r in rows]
        for r in result:
            r['spark'] = _decode_jsonb(r.get('spark'))
            if not scope.ver_nombres:
                r['nombre'] = _anon_name(r.get('nombre'), user.id_usuario)
        await _log_econ_access(conn, user, request.url.path, scope, len(result))
        return result


# ─────────────────────────────────────────────────────────────────────
# 2. GET /api/p96/run/matrix
# ─────────────────────────────────────────────────────────────────────
@router.get("/run/matrix")
async def p96_run_matrix(
    request: Request,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    user, scope = _require_scope(user)
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT layer, crit, cis, opex, inc, heat FROM p96_run_matrix ORDER BY layer, crit"
        )
        result = [dict(r) for r in rows]
        await _log_econ_access(conn, user, request.url.path, scope, len(result))
        return result


# ─────────────────────────────────────────────────────────────────────
# 3. GET /api/p96/run/cis/{layer}    (drill-down de la celda)
# ─────────────────────────────────────────────────────────────────────
@router.get("/run/cis/{layer}")
async def p96_run_cis(
    layer: str,
    request: Request,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    user, scope = _require_scope(user)
    pool = get_pool()
    async with pool.acquire() as conn:
        # v_p96_run_cis tiene mapeo capa → layer (INFRAESTRUCTURA, APLICACION, etc.)
        # El frontend pasa el k corto (INFRA, APPS), hago el mapeo inverso
        layer_real_map = {
            'INFRA': 'INFRAESTRUCTURA',
            'APPS':  'APLICACION',
            'RED':   'RED',
            'SEC':   'SEGURIDAD',
            'DATA':  'NEGOCIO',  # DATA no existe, lo aproximamos
            'CLOUD': 'INFRAESTRUCTURA',  # idem
            'VIRT':  'INFRAESTRUCTURA',
            'STO':   'INFRAESTRUCTURA',
        }
        real_layer = layer_real_map.get(layer.upper(), layer)
        rows = await conn.fetch("SELECT * FROM v_p96_run_cis WHERE layer=$1 ORDER BY opex DESC NULLS LAST", real_layer)
        result = [dict(r) for r in rows]
        if not scope.ver_nombres:
            for r in result:
                r['owner'] = _anon_name(r.get('owner'), user.id_usuario)
        await _log_econ_access(conn, user, request.url.path, scope, len(result))
        return result


# ─────────────────────────────────────────────────────────────────────
# 4. GET /api/p96/run/incidents
#    Devuelve TODAS las incidencias (top 100 por fecha). El frontend filtra
#    client-side por la celda activa del heatmap (decisión estratega F3).
#    Alias /run/incidents/{layer} mantenido por compat: ignora el parámetro.
# ─────────────────────────────────────────────────────────────────────
async def _p96_run_incidents_impl(
    request: Request,
    user: Optional[UserInfo],
):
    user, scope = _require_scope(user)
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM v_p96_run_incidents ORDER BY opened DESC NULLS LAST LIMIT 100"
        )
        result = [dict(r) for r in rows]
        if not scope.ver_nombres:
            for r in result:
                r['owner'] = _anon_name(r.get('owner'), user.id_usuario)
        # Convertir timestamps a string para JSON
        for r in result:
            if r.get('opened'):
                r['opened'] = r['opened'].isoformat()
        await _log_econ_access(conn, user, request.url.path, scope, len(result))
        return result


@router.get("/run/incidents")
async def p96_run_incidents(
    request: Request,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Endpoint canónico (sin parámetro). El frontend filtra por celda en cliente."""
    return await _p96_run_incidents_impl(request, user)


@router.get("/run/incidents/{layer}")
async def p96_run_incidents_legacy(
    layer: str,
    request: Request,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Alias de compatibilidad: ignora `layer` y delega al canónico."""
    return await _p96_run_incidents_impl(request, user)


# ─────────────────────────────────────────────────────────────────────
# 5. GET /api/p96/build/portfolio
# ─────────────────────────────────────────────────────────────────────
@router.get("/build/portfolio")
async def p96_build_portfolio(
    request: Request,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    user, scope = _require_scope(user)
    pool = get_pool()
    async with pool.acquire() as conn:
        # NOTA: la columna real es bac_k (no bac), y pm (no responsable)
        if scope.scope_who in ('MI_RAMA', 'MI_SILO') and scope.silos_visibles:
            rows = await conn.fetch(
                "SELECT * FROM v_p96_build_portfolio WHERE silo = ANY($1::text[]) ORDER BY bac_k DESC NULLS LAST",
                scope.silos_visibles
            )
        elif scope.scope_who == 'MIS_PROYECTOS':
            rows = await conn.fetch(
                "SELECT * FROM v_p96_build_portfolio WHERE pm ILIKE $1 ORDER BY bac_k DESC NULLS LAST",
                f"%{user.nombre_completo}%"
            )
        else:
            rows = await conn.fetch("SELECT * FROM v_p96_build_portfolio ORDER BY bac_k DESC NULLS LAST")
        result = [dict(r) for r in rows]
        if not scope.ver_nombres:
            for r in result:
                r['pm'] = _anon_name(r.get('pm'), user.id_usuario)
        await _log_econ_access(conn, user, request.url.path, scope, len(result))
        return result


# ─────────────────────────────────────────────────────────────────────
# 6. GET /api/p96/build/project/{id}
# ─────────────────────────────────────────────────────────────────────
@router.get("/build/project/{proyecto_id}")
async def p96_build_project_detail(
    proyecto_id: str,
    request: Request,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    user, scope = _require_scope(user)
    pool = get_pool()
    async with pool.acquire() as conn:
        # JOIN para validar scope: el proyecto debe estar en silos_visibles del usuario
        # o ser de MIS_PROYECTOS (PM == user.nombre_completo)
        portfolio_row = await conn.fetchrow(
            "SELECT * FROM v_p96_build_portfolio WHERE id_proyecto=$1", proyecto_id
        )
        if not portfolio_row:
            raise HTTPException(404, f"Proyecto {proyecto_id} no encontrado")
        if scope.scope_who in ('MI_RAMA', 'MI_SILO') and portfolio_row['silo'] not in scope.silos_visibles:
            raise HTTPException(403, "Proyecto fuera de tu ámbito")
        if scope.scope_who == 'MIS_PROYECTOS' and (portfolio_row['pm'] or '').lower() != user.nombre_completo.lower():
            raise HTTPException(403, "Proyecto fuera de tu cartera asignada")

        detail_row = await conn.fetchrow(
            "SELECT * FROM p96_build_project_detail WHERE id_proyecto=$1", proyecto_id
        )
        result = {
            "portfolio": dict(portfolio_row),
            "detail": dict(detail_row) if detail_row else None,
        }
        if result['detail']:
            result['detail']['gates'] = _decode_jsonb(result['detail'].get('gates'))
            result['detail']['team']  = _decode_jsonb(result['detail'].get('team'))
            result['detail']['risks'] = _decode_jsonb(result['detail'].get('risks'))
        if not scope.ver_nombres:
            result['portfolio']['pm'] = _anon_name(result['portfolio'].get('pm'), user.id_usuario)
            if result['detail'] and result['detail'].get('team'):
                # Anonimizar nombres dentro de team JSONB
                team = result['detail']['team']
                if isinstance(team, list):
                    for member in team:
                        if isinstance(member, dict) and 'n' in member:
                            member['n'] = _anon_name(member['n'], user.id_usuario)
        await _log_econ_access(conn, user, request.url.path, scope, 1)
        return result


# ─────────────────────────────────────────────────────────────────────
# 7-12. GET /api/p96/pulse/* (vista estratégica CEO, no filtra por silo)
# ─────────────────────────────────────────────────────────────────────
@router.get("/pulse/kpis")
async def p96_pulse_kpis(request: Request, user: Optional[UserInfo] = Depends(get_current_user)):
    user, scope = _require_scope(user)
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM p96_pulse_kpis ORDER BY k")
        result = [dict(r) for r in rows]
        await _log_econ_access(conn, user, request.url.path, scope, len(result))
        return result


@router.get("/pulse/alerts")
async def p96_pulse_alerts(request: Request, user: Optional[UserInfo] = Depends(get_current_user)):
    user, scope = _require_scope(user)
    pool = get_pool()
    async with pool.acquire() as conn:
        # Ordenar críticas primero: rd > am > gn (no DESC alfabético; usar CASE)
        rows = await conn.fetch("""
            SELECT * FROM p96_pulse_alerts
            ORDER BY CASE sev WHEN 'rd' THEN 0 WHEN 'am' THEN 1 ELSE 2 END, id
        """)
        result = [dict(r) for r in rows]
        for r in result:
            r['meta'] = _decode_jsonb(r.get('meta'))
            if not scope.ver_nombres:
                r['ow'] = _anon_name(r.get('ow'), user.id_usuario)
        await _log_econ_access(conn, user, request.url.path, scope, len(result))
        return result


@router.get("/pulse/blocks")
async def p96_pulse_blocks(request: Request, user: Optional[UserInfo] = Depends(get_current_user)):
    user, scope = _require_scope(user)
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM p96_pulse_blocks ORDER BY id")
        result = [dict(r) for r in rows]
        if not scope.ver_nombres:
            for r in result:
                r['own'] = _anon_name(r.get('own'), user.id_usuario)
        await _log_econ_access(conn, user, request.url.path, scope, len(result))
        return result


@router.get("/pulse/decisions")
async def p96_pulse_decisions(request: Request, user: Optional[UserInfo] = Depends(get_current_user)):
    user, scope = _require_scope(user)
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM p96_pulse_decisions ORDER BY due ASC NULLS LAST")
        result = [dict(r) for r in rows]
        if not scope.ver_nombres:
            for r in result:
                r['own'] = _anon_name(r.get('own'), user.id_usuario)
        for r in result:
            if r.get('due'):
                r['due'] = r['due'].isoformat()
        await _log_econ_access(conn, user, request.url.path, scope, len(result))
        return result


@router.get("/pulse/responsables")
async def p96_pulse_responsables(request: Request, user: Optional[UserInfo] = Depends(get_current_user)):
    user, scope = _require_scope(user)
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM p96_pulse_responsables ORDER BY id")
        result = [dict(r) for r in rows]
        if not scope.ver_nombres:
            for r in result:
                r['nm'] = _anon_name(r.get('nm'), user.id_usuario)
        await _log_econ_access(conn, user, request.url.path, scope, len(result))
        return result


@router.get("/pulse/hitos")
async def p96_pulse_hitos(request: Request, user: Optional[UserInfo] = Depends(get_current_user)):
    user, scope = _require_scope(user)
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM p96_pulse_hitos ORDER BY id")
        result = [dict(r) for r in rows]
        await _log_econ_access(conn, user, request.url.path, scope, len(result))
        return result


# ─────────────────────────────────────────────────────────────────────
# 14. GET /api/p96/strategy/{k}    (k ∈ dafo|pestle|porter|okr)
# ─────────────────────────────────────────────────────────────────────
@router.get("/strategy/{k}")
async def p96_strategy(
    k: str,
    request: Request,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    user, scope = _require_scope(user)
    if k not in ('dafo', 'pestle', 'porter', 'okr'):
        raise HTTPException(400, f"Marco inválido: {k}. Permitidos: dafo, pestle, porter, okr")
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT payload FROM p96_strategy_frameworks WHERE k=$1", k)
        if not row:
            raise HTTPException(404, f"Marco {k} no encontrado")
        await _log_econ_access(conn, user, request.url.path, scope, 1)
        # asyncpg devuelve JSONB como str — decodificar a dict
        payload = row['payload']
        if isinstance(payload, str):
            payload = json.loads(payload)
        return payload
