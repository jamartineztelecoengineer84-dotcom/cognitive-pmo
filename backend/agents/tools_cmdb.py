"""
CMDB Tools para AG-012 Task Advisor
Consultas a la CMDB para enriquecer tarjetas Kanban con contexto técnico real.
"""
import json
from agents.tools import register_tool


@register_tool("query_cmdb_activo")
async def query_cmdb_activo(db, ci_codigo: str = None, id_proyecto: str = None):
    """Busca activo por código CI o por proyecto vinculado"""
    if ci_codigo:
        rows = await db.fetch("""
            SELECT a.id_activo, a.codigo, a.nombre, a.capa, a.tipo, a.subtipo,
                   a.estado_ciclo, a.criticidad, a.entorno, a.ubicacion,
                   a.propietario, a.responsable_tecnico, a.proveedor,
                   a.fabricante, a.modelo, a.version, a.serial_number,
                   a.id_proyecto, a.notas, a.especificaciones,
                   c.nombre as categoria_nombre
            FROM cmdb_activos a
            LEFT JOIN cmdb_categorias c ON a.id_categoria = c.id_categoria
            WHERE a.codigo ILIKE $1 OR a.nombre ILIKE $1
        """, f"%{ci_codigo}%")
    elif id_proyecto:
        rows = await db.fetch("""
            SELECT a.id_activo, a.codigo, a.nombre, a.capa, a.tipo, a.subtipo,
                   a.estado_ciclo, a.criticidad, a.entorno, a.ubicacion,
                   a.propietario, a.responsable_tecnico,
                   a.version, a.id_proyecto, a.especificaciones
            FROM cmdb_activos a
            WHERE a.id_proyecto = $1
        """, id_proyecto)
    else:
        return {"error": "Necesito ci_codigo o id_proyecto"}
    results = []
    for r in rows:
        d = dict(r)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        results.append(d)
    return results if results else [{"message": "No se encontró el activo en la CMDB"}]


@register_tool("query_cmdb_ips")
async def query_cmdb_ips(db, id_activo: int):
    """Obtiene IPs, VLANs y configuración de red del activo"""
    rows = await db.fetch("""
        SELECT ip.direccion_ip, ip.hostname, ip.tipo, ip.estado,
               ip.mac_address, ip.puerto_switch, ip.notas,
               v.vlan_id, v.nombre as vlan_nombre,
               v.subred, v.mascara, v.gateway, v.entorno as vlan_entorno,
               v.proposito
        FROM cmdb_ips ip
        LEFT JOIN cmdb_vlans v ON ip.id_vlan = v.id_vlan
        WHERE ip.id_activo = $1
    """, id_activo)
    return [dict(r) for r in rows] if rows else [{"message": "No hay IPs registradas para este activo"}]


@register_tool("query_cmdb_relaciones")
async def query_cmdb_relaciones(db, id_activo: int):
    """Obtiene dependencias del activo"""
    rows = await db.fetch("""
        SELECT r.tipo_relacion, r.descripcion, r.criticidad,
               a_orig.codigo as origen_codigo, a_orig.nombre as origen_nombre,
               a_orig.criticidad as origen_criticidad,
               a_dest.codigo as destino_codigo, a_dest.nombre as destino_nombre,
               a_dest.criticidad as destino_criticidad,
               CASE WHEN r.id_activo_origen = $1 THEN 'ESTE_DEPENDE_DE'
                    ELSE 'DEPENDE_DE_ESTE' END as direccion
        FROM cmdb_relaciones r
        JOIN cmdb_activos a_orig ON r.id_activo_origen = a_orig.id_activo
        JOIN cmdb_activos a_dest ON r.id_activo_destino = a_dest.id_activo
        WHERE r.id_activo_origen = $1 OR r.id_activo_destino = $1
    """, id_activo)
    return [dict(r) for r in rows] if rows else [{"message": "No hay relaciones registradas"}]


@register_tool("query_cmdb_software")
async def query_cmdb_software(db, id_activo: int):
    """Obtiene software instalado en el activo"""
    rows = await db.fetch("""
        SELECT s.nombre, s.version, s.editor, s.tipo_licencia,
               s.critico_negocio, s.estado,
               asw.version_instalada, asw.fecha_instalacion
        FROM cmdb_activo_software asw
        JOIN cmdb_software s ON asw.id_software = s.id_software
        WHERE asw.id_activo = $1
    """, id_activo)
    if not rows:
        activo = await db.fetchrow(
            "SELECT nombre, version, especificaciones FROM cmdb_activos WHERE id_activo = $1", id_activo)
        if activo:
            specs = activo.get('especificaciones') or {}
            return [{"nota": "Sin software en cmdb_activo_software. Datos del activo:",
                     "version_activo": activo.get('version'),
                     "especificaciones": specs}]
        return [{"message": "Activo no encontrado"}]
    results = []
    for r in rows:
        d = dict(r)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        results.append(d)
    return results


@register_tool("enrich_kanban_card")
async def enrich_kanban_card(db, task_id: str, instructions_json: dict):
    """Actualiza la tarjeta Kanban con instrucciones enriquecidas de AG-012"""
    instructions_json["enriched"] = True
    await db.execute("""
        UPDATE kanban_tareas SET descripcion = $1
        WHERE id = $2
    """, json.dumps(instructions_json, ensure_ascii=False, default=str), task_id)
    return {"status": "enriched", "task_id": task_id}
