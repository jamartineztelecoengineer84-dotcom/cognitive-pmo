"""
COGNITIVE PMO - CMDB API
Configuration Management Database for IT Banking Infrastructure
"""
import json, logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from database import get_pool
from auth import get_current_user, require_permission, UserInfo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cmdb")


def _ser(row):
    if not row: return None
    d = dict(row)
    for k,v in d.items():
        if hasattr(v,'isoformat'): d[k]=v.isoformat()
    return d


# ── Dashboard / Stats ─────────────────────────────────────────
@router.get("/dashboard")
async def cmdb_dashboard(user: Optional[UserInfo] = Depends(get_current_user)):
    pool = get_pool()
    if not pool: return {}
    async with pool.acquire() as c:
        total = await c.fetchval("SELECT COUNT(*) FROM cmdb_activos")
        by_capa = await c.fetch("SELECT capa, COUNT(*) as cnt FROM cmdb_activos GROUP BY capa ORDER BY cnt DESC")
        by_estado = await c.fetch("SELECT estado_ciclo, COUNT(*) as cnt FROM cmdb_activos GROUP BY estado_ciclo")
        by_criticidad = await c.fetch("SELECT criticidad, COUNT(*) as cnt FROM cmdb_activos GROUP BY criticidad")
        by_entorno = await c.fetch("SELECT entorno, COUNT(*) as cnt FROM cmdb_activos GROUP BY entorno")
        criticos = await c.fetchval("SELECT COUNT(*) FROM cmdb_activos WHERE criticidad='CRITICA'")
        coste = await c.fetchval("SELECT COALESCE(SUM(coste_mensual),0) FROM cmdb_activos")
        total_vlans = await c.fetchval("SELECT COUNT(*) FROM cmdb_vlans")
        total_ips = await c.fetchval("SELECT COUNT(*) FROM cmdb_ips")
        total_soft = await c.fetchval("SELECT COUNT(*) FROM cmdb_software")
        total_rel = await c.fetchval("SELECT COUNT(*) FROM cmdb_relaciones")
        coste_soft = await c.fetchval("SELECT COALESCE(SUM(coste_anual),0) FROM cmdb_software WHERE estado='ACTIVO'")
        obsoletos = await c.fetchval("SELECT COUNT(*) FROM cmdb_software WHERE estado IN ('OBSOLETO','SIN_SOPORTE')")
        return {
            "total_activos": total or 0, "activos_criticos": criticos or 0,
            "coste_mensual_infra": float(coste or 0), "coste_anual_software": float(coste_soft or 0),
            "total_vlans": total_vlans or 0, "total_ips": total_ips or 0,
            "total_software": total_soft or 0, "total_relaciones": total_rel or 0,
            "software_obsoleto": obsoletos or 0,
            "by_capa": {r['capa']:r['cnt'] for r in by_capa},
            "by_estado": {r['estado_ciclo']:r['cnt'] for r in by_estado},
            "by_criticidad": {r['criticidad']:r['cnt'] for r in by_criticidad},
            "by_entorno": {r['entorno']:r['cnt'] for r in by_entorno},
        }


# ── Activos (CIs) ─────────────────────────────────────────────
@router.get("/activos")
async def get_activos(capa: Optional[str]=None, tipo: Optional[str]=None,
    criticidad: Optional[str]=None, entorno: Optional[str]=None,
    estado: Optional[str]=None, search: Optional[str]=None,
    limit: int=200, offset: int=0,
    user: Optional[UserInfo] = Depends(get_current_user)):
    pool = get_pool()
    if not pool: return {"activos":[],"total":0}
    clauses, params = [], []
    if capa: params.append(capa); clauses.append(f"a.capa=${len(params)}")
    if tipo: params.append(tipo); clauses.append(f"a.tipo=${len(params)}")
    if criticidad: params.append(criticidad); clauses.append(f"a.criticidad=${len(params)}")
    if entorno: params.append(entorno); clauses.append(f"a.entorno=${len(params)}")
    if estado: params.append(estado); clauses.append(f"a.estado_ciclo=${len(params)}")
    if search: params.append(f"%{search}%"); clauses.append(f"(a.nombre ILIKE ${len(params)} OR a.codigo ILIKE ${len(params)} OR a.tipo ILIKE ${len(params)})")
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    async with pool.acquire() as c:
        total = await c.fetchval(f"SELECT COUNT(*) FROM cmdb_activos a {where}", *params)
        params.extend([limit, offset])
        rows = await c.fetch(f"""
            SELECT a.*, cat.color as cat_color, cat.icono as cat_icono
            FROM cmdb_activos a LEFT JOIN cmdb_categorias cat ON a.id_categoria=cat.id_categoria
            {where} ORDER BY a.criticidad, a.nombre LIMIT ${len(params)-1} OFFSET ${len(params)}
        """, *params)
        return {"activos": [_ser(r) for r in rows], "total": total}


@router.get("/activos/{id_activo}")
async def get_activo_detail(id_activo: int, user: Optional[UserInfo] = Depends(get_current_user)):
    pool = get_pool()
    if not pool: raise HTTPException(404)
    async with pool.acquire() as c:
        row = await c.fetchrow("SELECT a.*, cat.color, cat.icono FROM cmdb_activos a LEFT JOIN cmdb_categorias cat ON a.id_categoria=cat.id_categoria WHERE a.id_activo=$1", id_activo)
        if not row: raise HTTPException(404)
        deps = await c.fetch("""
            SELECT r.*, ao.codigo as origen_codigo, ao.nombre as origen_nombre,
                   ad.codigo as destino_codigo, ad.nombre as destino_nombre
            FROM cmdb_relaciones r
            JOIN cmdb_activos ao ON r.id_activo_origen=ao.id_activo
            JOIN cmdb_activos ad ON r.id_activo_destino=ad.id_activo
            WHERE r.id_activo_origen=$1 OR r.id_activo_destino=$1
        """, id_activo)
        ips = await c.fetch("SELECT i.*, v.nombre as vlan_nombre, v.vlan_id FROM cmdb_ips i LEFT JOIN cmdb_vlans v ON i.id_vlan=v.id_vlan WHERE i.id_activo=$1", id_activo)
        soft = await c.fetch("SELECT s.*, asw.version_instalada FROM cmdb_activo_software asw JOIN cmdb_software s ON asw.id_software=s.id_software WHERE asw.id_activo=$1", id_activo)
        return {
            "activo": _ser(row),
            "dependencias": [_ser(d) for d in deps],
            "ips": [_ser(i) for i in ips],
            "software": [_ser(s) for s in soft],
        }


class ActivoCreate(BaseModel):
    codigo: str
    nombre: str
    capa: str
    tipo: str
    subtipo: Optional[str] = None
    estado_ciclo: str = "OPERATIVO"
    criticidad: str = "MEDIA"
    entorno: str = "PRODUCCION"
    ubicacion: Optional[str] = None
    propietario: Optional[str] = None
    responsable_tecnico: Optional[str] = None
    proveedor: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    version: Optional[str] = None
    coste_mensual: float = 0
    id_proyecto: Optional[str] = None
    notas: Optional[str] = None
    especificaciones: dict = {}

@router.post("/activos")
async def create_activo(body: ActivoCreate, user: UserInfo = Depends(require_permission('catalogo.editar'))):
    pool = get_pool()
    if not pool: raise HTTPException(503)
    async with pool.acquire() as c:
        cat = await c.fetchrow("SELECT id_categoria FROM cmdb_categorias WHERE nombre=$1", body.tipo)
        cat_id = cat['id_categoria'] if cat else None
        try:
            row = await c.fetchrow("""
                INSERT INTO cmdb_activos (codigo,nombre,id_categoria,capa,tipo,subtipo,estado_ciclo,criticidad,entorno,
                    ubicacion,propietario,responsable_tecnico,proveedor,fabricante,modelo,version,coste_mensual,id_proyecto,notas,especificaciones)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20::jsonb) RETURNING *
            """, body.codigo, body.nombre, cat_id, body.capa, body.tipo, body.subtipo,
                body.estado_ciclo, body.criticidad, body.entorno, body.ubicacion,
                body.propietario, body.responsable_tecnico, body.proveedor, body.fabricante,
                body.modelo, body.version, body.coste_mensual, body.id_proyecto, body.notas,
                json.dumps(body.especificaciones))
            return _ser(row)
        except Exception as e:
            if 'unique' in str(e).lower(): raise HTTPException(409, f"Código '{body.codigo}' ya existe")
            raise HTTPException(500, str(e))


@router.put("/activos/{id_activo}")
async def update_activo(id_activo: int, body: dict, user: UserInfo = Depends(require_permission('catalogo.editar'))):
    pool = get_pool()
    if not pool: raise HTTPException(503)
    allowed = ['nombre','capa','tipo','subtipo','estado_ciclo','criticidad','entorno','ubicacion',
               'propietario','responsable_tecnico','proveedor','fabricante','modelo','version',
               'coste_mensual','id_proyecto','notas']
    sets, params = ["updated_at=NOW()"], []
    for k in allowed:
        if k in body and body[k] is not None:
            params.append(body[k]); sets.append(f"{k}=${len(params)}")
    if 'especificaciones' in body:
        params.append(json.dumps(body['especificaciones'])); sets.append(f"especificaciones=${len(params)}::jsonb")
    params.append(id_activo)
    async with pool.acquire() as c:
        row = await c.fetchrow(f"UPDATE cmdb_activos SET {','.join(sets)} WHERE id_activo=${len(params)} RETURNING *", *params)
        if not row: raise HTTPException(404)
        return _ser(row)


# ── Categorías ─────────────────────────────────────────────────
@router.get("/categorias")
async def get_categorias(user: Optional[UserInfo] = Depends(get_current_user)):
    pool = get_pool()
    if not pool: return []
    async with pool.acquire() as c:
        rows = await c.fetch("SELECT * FROM cmdb_categorias ORDER BY capa, nombre")
        return [dict(r) for r in rows]


# ── Relaciones / Dependencias ──────────────────────────────────
@router.get("/relaciones")
async def get_relaciones(user: Optional[UserInfo] = Depends(get_current_user)):
    pool = get_pool()
    if not pool: return []
    async with pool.acquire() as c:
        rows = await c.fetch("""
            SELECT r.*, ao.codigo as origen_codigo, ao.nombre as origen_nombre, ao.capa as origen_capa,
                   ad.codigo as destino_codigo, ad.nombre as destino_nombre, ad.capa as destino_capa
            FROM cmdb_relaciones r
            JOIN cmdb_activos ao ON r.id_activo_origen=ao.id_activo
            JOIN cmdb_activos ad ON r.id_activo_destino=ad.id_activo
            ORDER BY r.criticidad
        """)
        return [_ser(r) for r in rows]


class RelacionCreate(BaseModel):
    id_activo_origen: int
    id_activo_destino: int
    tipo_relacion: str
    descripcion: Optional[str] = None
    criticidad: str = "MEDIA"

@router.post("/relaciones")
async def create_relacion(body: RelacionCreate, user: UserInfo = Depends(require_permission('catalogo.editar'))):
    pool = get_pool()
    if not pool: raise HTTPException(503)
    async with pool.acquire() as c:
        row = await c.fetchrow("""
            INSERT INTO cmdb_relaciones (id_activo_origen,id_activo_destino,tipo_relacion,descripcion,criticidad)
            VALUES ($1,$2,$3,$4,$5) RETURNING *
        """, body.id_activo_origen, body.id_activo_destino, body.tipo_relacion, body.descripcion, body.criticidad)
        return _ser(row)


# ── VLANs ──────────────────────────────────────────────────────
@router.get("/vlans")
async def get_vlans(user: Optional[UserInfo] = Depends(get_current_user)):
    pool = get_pool()
    if not pool: return []
    async with pool.acquire() as c:
        rows = await c.fetch("""
            SELECT v.*, COUNT(i.id_ip) as ips_asignadas
            FROM cmdb_vlans v LEFT JOIN cmdb_ips i ON v.id_vlan=i.id_vlan
            GROUP BY v.id_vlan ORDER BY v.vlan_id
        """)
        return [_ser(r) for r in rows]


class VlanCreate(BaseModel):
    vlan_id: int
    nombre: str
    subred: str
    gateway: Optional[str] = None
    entorno: str = "PRODUCCION"
    ubicacion: Optional[str] = None
    proposito: Optional[str] = None
    total_ips: int = 254

@router.post("/vlans")
async def create_vlan(body: VlanCreate, user: UserInfo = Depends(require_permission('catalogo.editar'))):
    pool = get_pool()
    if not pool: raise HTTPException(503)
    async with pool.acquire() as c:
        try:
            row = await c.fetchrow("""
                INSERT INTO cmdb_vlans (vlan_id,nombre,subred,gateway,entorno,ubicacion,proposito,total_ips)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *
            """, body.vlan_id, body.nombre, body.subred, body.gateway, body.entorno, body.ubicacion, body.proposito, body.total_ips)
            return _ser(row)
        except Exception as e:
            if 'unique' in str(e).lower(): raise HTTPException(409, f"VLAN {body.vlan_id} ya existe")
            raise HTTPException(500, str(e))


@router.put("/vlans/{id_vlan}")
async def update_vlan(id_vlan: int, body: dict, user: UserInfo = Depends(require_permission('catalogo.editar'))):
    pool = get_pool()
    if not pool: raise HTTPException(503)
    allowed = ['vlan_id','nombre','subred','gateway','entorno','ubicacion','proposito','total_ips']
    sets, params = [], []
    for k in allowed:
        if k in body:
            params.append(body[k]); sets.append(f"{k}=${len(params)}")
    if not sets: raise HTTPException(400, "No fields to update")
    params.append(id_vlan)
    async with pool.acquire() as c:
        row = await c.fetchrow(f"UPDATE cmdb_vlans SET {','.join(sets)} WHERE id_vlan=${len(params)} RETURNING *", *params)
        if not row: raise HTTPException(404)
        return _ser(row)


@router.delete("/vlans/{id_vlan}")
async def delete_vlan(id_vlan: int, user: UserInfo = Depends(require_permission('catalogo.editar'))):
    pool = get_pool()
    if not pool: raise HTTPException(503)
    async with pool.acquire() as c:
        row = await c.fetchrow("DELETE FROM cmdb_vlans WHERE id_vlan=$1 RETURNING id_vlan", id_vlan)
        if not row: raise HTTPException(404)
        return {"deleted": True, "id_vlan": id_vlan}


# ── IPs ────────────────────────────────────────────────────────
@router.get("/ips")
async def get_ips(vlan_id: Optional[int]=None, estado: Optional[str]=None,
    search: Optional[str]=None, limit: int=200, offset: int=0,
    user: Optional[UserInfo] = Depends(get_current_user)):
    pool = get_pool()
    if not pool: return {"ips":[],"total":0}
    clauses, params = [], []
    if vlan_id: params.append(vlan_id); clauses.append(f"i.id_vlan=${len(params)}")
    if estado: params.append(estado); clauses.append(f"i.estado=${len(params)}")
    if search: params.append(f"%{search}%"); clauses.append(f"(i.direccion_ip ILIKE ${len(params)} OR i.hostname ILIKE ${len(params)})")
    where = "WHERE "+" AND ".join(clauses) if clauses else ""
    async with pool.acquire() as c:
        total = await c.fetchval(f"SELECT COUNT(*) FROM cmdb_ips i {where}", *params)
        params.extend([limit, offset])
        rows = await c.fetch(f"""
            SELECT i.*, v.nombre as vlan_nombre, v.vlan_id as vlan_num, v.subred,
                   a.nombre as activo_nombre, a.codigo as activo_codigo
            FROM cmdb_ips i
            LEFT JOIN cmdb_vlans v ON i.id_vlan=v.id_vlan
            LEFT JOIN cmdb_activos a ON i.id_activo=a.id_activo
            {where} ORDER BY i.direccion_ip LIMIT ${len(params)-1} OFFSET ${len(params)}
        """, *params)
        return {"ips": [_ser(r) for r in rows], "total": total}


class IpCreate(BaseModel):
    direccion_ip: str
    id_vlan: Optional[int] = None
    id_activo: Optional[int] = None
    hostname: Optional[str] = None
    tipo: str = "ESTATICA"
    estado: str = "ASIGNADA"
    mac_address: Optional[str] = None
    notas: Optional[str] = None

@router.post("/ips")
async def create_ip(body: IpCreate, user: UserInfo = Depends(require_permission('catalogo.editar'))):
    pool = get_pool()
    if not pool: raise HTTPException(503)
    async with pool.acquire() as c:
        try:
            row = await c.fetchrow("""
                INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,mac_address,notas)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *
            """, body.direccion_ip, body.id_vlan, body.id_activo, body.hostname, body.tipo, body.estado, body.mac_address, body.notas)
            return _ser(row)
        except Exception as e:
            if 'unique' in str(e).lower(): raise HTTPException(409, f"IP '{body.direccion_ip}' ya existe")
            raise HTTPException(500, str(e))


@router.put("/ips/{id_ip}")
async def update_ip(id_ip: int, body: dict, user: UserInfo = Depends(require_permission('catalogo.editar'))):
    pool = get_pool()
    if not pool: raise HTTPException(503)
    allowed = ['direccion_ip','id_vlan','id_activo','hostname','tipo','estado','mac_address','notas']
    sets, params = [], []
    for k in allowed:
        if k in body:
            params.append(body[k]); sets.append(f"{k}=${len(params)}")
    if not sets: raise HTTPException(400, "No fields to update")
    params.append(id_ip)
    async with pool.acquire() as c:
        row = await c.fetchrow(f"UPDATE cmdb_ips SET {','.join(sets)} WHERE id_ip=${len(params)} RETURNING *", *params)
        if not row: raise HTTPException(404)
        return _ser(row)


@router.delete("/ips/{id_ip}")
async def delete_ip(id_ip: int, user: UserInfo = Depends(require_permission('catalogo.editar'))):
    pool = get_pool()
    if not pool: raise HTTPException(503)
    async with pool.acquire() as c:
        row = await c.fetchrow("DELETE FROM cmdb_ips WHERE id_ip=$1 RETURNING id_ip", id_ip)
        if not row: raise HTTPException(404)
        return {"deleted": True, "id_ip": id_ip}


# ── Software ───────────────────────────────────────────────────
@router.get("/software")
async def get_software(user: Optional[UserInfo] = Depends(get_current_user)):
    pool = get_pool()
    if not pool: return []
    async with pool.acquire() as c:
        rows = await c.fetch("SELECT * FROM cmdb_software ORDER BY critico_negocio DESC, nombre")
        return [_ser(r) for r in rows]


# ── Mapa de impacto (cascade) ──────────────────────────────────
@router.get("/impacto/{id_activo}")
async def get_impacto(id_activo: int, user: Optional[UserInfo] = Depends(get_current_user)):
    """Get cascade impact: what breaks if this asset fails"""
    pool = get_pool()
    if not pool: return {"impacto":[]}
    async with pool.acquire() as c:
        # BFS: find all assets that depend on this one (directly or transitively)
        rows = await c.fetch("""
            WITH RECURSIVE cascade AS (
                SELECT id_activo_origen as id_afectado, id_activo_destino as id_causa, tipo_relacion, criticidad, 1 as depth
                FROM cmdb_relaciones WHERE id_activo_destino=$1 AND tipo_relacion IN ('DEPENDE_DE','EJECUTA_EN','CONECTA_A')
                UNION
                SELECT r.id_activo_origen, r.id_activo_destino, r.tipo_relacion, r.criticidad, c.depth+1
                FROM cmdb_relaciones r JOIN cascade c ON r.id_activo_destino=c.id_afectado
                WHERE r.tipo_relacion IN ('DEPENDE_DE','EJECUTA_EN','CONECTA_A') AND c.depth < 5
            )
            SELECT DISTINCT a.id_activo, a.codigo, a.nombre, a.capa, a.tipo, a.criticidad,
                   c.tipo_relacion, c.criticidad as rel_criticidad, c.depth
            FROM cascade c JOIN cmdb_activos a ON c.id_afectado=a.id_activo
            ORDER BY c.depth, a.criticidad
        """, id_activo)
        origen = await c.fetchrow("SELECT codigo, nombre, capa, criticidad FROM cmdb_activos WHERE id_activo=$1", id_activo)
        return {
            "origen": _ser(origen),
            "impacto": [_ser(r) for r in rows],
            "total_afectados": len(rows),
        }


# ── Compliance / Health ────────────────────────────────────────
@router.get("/compliance")
async def cmdb_compliance(user: Optional[UserInfo] = Depends(get_current_user)):
    pool = get_pool()
    if not pool: return {}
    async with pool.acquire() as c:
        obsoleto_sw = await c.fetch("SELECT nombre, version, estado FROM cmdb_software WHERE estado IN ('OBSOLETO','SIN_SOPORTE')")
        sin_responsable = await c.fetchval("SELECT COUNT(*) FROM cmdb_activos WHERE responsable_tecnico IS NULL OR responsable_tecnico=''")
        sin_proyecto = await c.fetchval("SELECT COUNT(*) FROM cmdb_activos WHERE id_proyecto IS NULL AND capa IN ('APLICACION','NEGOCIO')")
        degradados = await c.fetch("SELECT codigo, nombre, tipo, estado_ciclo FROM cmdb_activos WHERE estado_ciclo IN ('DEGRADADO','MANTENIMIENTO')")
        # Certificates expiring
        certs_exp = await c.fetch("""
            SELECT codigo, nombre, especificaciones->>'expira' as expira
            FROM cmdb_activos WHERE tipo='Certificado SSL/TLS'
        """)
        return {
            "software_obsoleto": [dict(r) for r in obsoleto_sw],
            "activos_sin_responsable": sin_responsable or 0,
            "activos_sin_proyecto": sin_proyecto or 0,
            "activos_degradados": [_ser(r) for r in degradados],
            "certificados": [_ser(r) for r in certs_exp],
        }


# ── Costes / Budget ──────────────────────────────────────────
class CosteCreate(BaseModel):
    id_activo: Optional[int] = None
    concepto: str
    categoria: str
    tipo: str
    importe: float
    moneda: str = "EUR"
    periodicidad: str = "MENSUAL"
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    proveedor: Optional[str] = None
    centro_coste: Optional[str] = None
    id_proyecto: Optional[str] = None
    notas: Optional[str] = None


@router.get("/costes")
async def get_costes(categoria: Optional[str]=None, tipo: Optional[str]=None,
    id_activo: Optional[int]=None, id_proyecto: Optional[str]=None,
    user: Optional[UserInfo] = Depends(get_current_user)):
    pool = get_pool()
    if not pool: return []
    clauses, params = [], []
    if categoria: params.append(categoria); clauses.append(f"co.categoria=${len(params)}")
    if tipo: params.append(tipo); clauses.append(f"co.tipo=${len(params)}")
    if id_activo: params.append(id_activo); clauses.append(f"co.id_activo=${len(params)}")
    if id_proyecto: params.append(id_proyecto); clauses.append(f"co.id_proyecto=${len(params)}")
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    async with pool.acquire() as c:
        rows = await c.fetch(f"""
            SELECT co.*, a.nombre as activo_nombre, a.codigo as activo_codigo
            FROM cmdb_costes co LEFT JOIN cmdb_activos a ON co.id_activo=a.id_activo
            {where} ORDER BY co.created_at DESC
        """, *params)
        return [_ser(r) for r in rows]


@router.post("/costes")
async def create_coste(body: CosteCreate, user: UserInfo = Depends(require_permission('catalogo.editar'))):
    pool = get_pool()
    if not pool: raise HTTPException(503)
    async with pool.acquire() as c:
        row = await c.fetchrow("""
            INSERT INTO cmdb_costes (id_activo,concepto,categoria,tipo,importe,moneda,periodicidad,
                fecha_inicio,fecha_fin,proveedor,centro_coste,id_proyecto,notas)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8::date,$9::date,$10,$11,$12,$13) RETURNING *
        """, body.id_activo, body.concepto, body.categoria, body.tipo, body.importe,
            body.moneda, body.periodicidad, body.fecha_inicio, body.fecha_fin,
            body.proveedor, body.centro_coste, body.id_proyecto, body.notas)
        return _ser(row)


@router.put("/costes/{id_coste}")
async def update_coste(id_coste: int, body: dict, user: UserInfo = Depends(require_permission('catalogo.editar'))):
    pool = get_pool()
    if not pool: raise HTTPException(503)
    allowed = ['id_activo','concepto','categoria','tipo','importe','moneda','periodicidad',
               'fecha_inicio','fecha_fin','proveedor','centro_coste','id_proyecto','notas']
    sets, params = [], []
    for k in allowed:
        if k in body:
            params.append(body[k]); sets.append(f"{k}=${len(params)}")
    if not sets: raise HTTPException(400, "No fields to update")
    params.append(id_coste)
    async with pool.acquire() as c:
        row = await c.fetchrow(f"UPDATE cmdb_costes SET {','.join(sets)} WHERE id_coste=${len(params)} RETURNING *", *params)
        if not row: raise HTTPException(404)
        return _ser(row)


@router.delete("/costes/{id_coste}")
async def delete_coste(id_coste: int, user: UserInfo = Depends(require_permission('catalogo.editar'))):
    pool = get_pool()
    if not pool: raise HTTPException(503)
    async with pool.acquire() as c:
        row = await c.fetchrow("DELETE FROM cmdb_costes WHERE id_coste=$1 RETURNING id_coste", id_coste)
        if not row: raise HTTPException(404)
        return {"deleted": True, "id_coste": id_coste}


@router.get("/costes/dashboard")
async def costes_dashboard(user: Optional[UserInfo] = Depends(get_current_user)):
    pool = get_pool()
    if not pool: return {}
    async with pool.acquire() as c:
        total_capex = await c.fetchval("SELECT COALESCE(SUM(importe),0) FROM cmdb_costes WHERE tipo='CAPEX'")
        total_opex = await c.fetchval("SELECT COALESCE(SUM(importe),0) FROM cmdb_costes WHERE tipo='OPEX'")
        by_cat = await c.fetch("SELECT categoria, SUM(importe) as total FROM cmdb_costes GROUP BY categoria ORDER BY total DESC")
        by_proyecto = await c.fetch("SELECT COALESCE(id_proyecto,'SIN PROYECTO') as proyecto, SUM(importe) as total FROM cmdb_costes GROUP BY id_proyecto ORDER BY total DESC LIMIT 10")
        # Monthly burn rate: sum of MENSUAL + TRIMESTRAL/3 + ANUAL/12 + UNICO (not recurring)
        burn = await c.fetchval("""
            SELECT COALESCE(SUM(
                CASE periodicidad
                    WHEN 'MENSUAL' THEN importe
                    WHEN 'TRIMESTRAL' THEN importe/3
                    WHEN 'ANUAL' THEN importe/12
                    ELSE 0
                END
            ),0) FROM cmdb_costes
        """)
        top_assets = await c.fetch("""
            SELECT a.codigo, a.nombre, SUM(co.importe) as total
            FROM cmdb_costes co JOIN cmdb_activos a ON co.id_activo=a.id_activo
            GROUP BY a.id_activo, a.codigo, a.nombre ORDER BY total DESC LIMIT 10
        """)
        top_proveedores = await c.fetch("""
            SELECT COALESCE(proveedor,'Sin proveedor') as proveedor, SUM(importe) as total
            FROM cmdb_costes GROUP BY proveedor ORDER BY total DESC LIMIT 5
        """)
        return {
            "total_capex": float(total_capex or 0),
            "total_opex": float(total_opex or 0),
            "burn_rate_mensual": float(burn or 0),
            "by_categoria": {r['categoria']:float(r['total']) for r in by_cat},
            "by_proyecto": {r['proyecto']:float(r['total']) for r in by_proyecto},
            "top_assets": [{"codigo":r['codigo'],"nombre":r['nombre'],"total":float(r['total'])} for r in top_assets],
            "top_proveedores": {r['proveedor']:float(r['total']) for r in top_proveedores},
        }
