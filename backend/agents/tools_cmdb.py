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
        UPDATE kanban_tareas SET descripcion = (COALESCE(descripcion::jsonb, '{}'::jsonb) || $1::jsonb)::text
        WHERE id = $2
    """, json.dumps(instructions_json, ensure_ascii=False, default=str), task_id)
    return {"status": "enriched", "task_id": task_id}


# ============================================================================
# TOOLS AG-011: Gabinete de Cambios con cruce BUILD/RUN
# ============================================================================

@register_tool("query_calendario_periodos")
async def query_calendario_periodos(db, params: dict = None):
    """Query periodos de demanda."""
    rows = await db.fetch("SELECT * FROM calendario_periodos_demanda ORDER BY fecha_inicio ASC")
    results = []
    for r in rows:
        d = dict(r)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        results.append(d)
    return results


@register_tool("query_demand_history")
async def query_demand_history(db, id_activo: int, meses: int = 12):
    """Historico demanda por activo."""
    rows = await db.fetch("""
        SELECT h.*, a.codigo, a.nombre, a.criticidad, a.capa
        FROM cmdb_demand_history h JOIN cmdb_activos a ON a.id_activo = h.id_activo
        WHERE h.id_activo = $1 ORDER BY h.mes DESC LIMIT $2
    """, int(id_activo), int(meses))
    results = []
    for r in rows:
        d = dict(r)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        results.append(d)
    return results


@register_tool("query_change_windows")
async def query_change_windows(db, estado: str = "ACTIVA", id_activo: int = None, periodo: str = None):
    """Ventanas CAB activas. Params opcionales: id_activo, periodo, estado"""
    query = """SELECT cw.*, a.codigo, a.nombre as activo_nombre, a.criticidad
        FROM cmdb_change_windows cw JOIN cmdb_activos a ON a.id_activo = cw.id_activo
        WHERE cw.estado = $1"""
    args = [estado]
    idx = 2
    if id_activo:
        query += f" AND cw.id_activo = ${idx}"
        args.append(int(id_activo))
        idx += 1
    if periodo:
        query += f" AND cw.periodo = ${idx}"
        args.append(periodo)
    query += " ORDER BY a.criticidad, a.codigo"
    rows = await db.fetch(query, *args)
    results = []
    for r in rows:
        d = dict(r)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        results.append(d)
    return results


@register_tool("query_cab_contexto_build")
async def query_cab_contexto_build(db):
    """Cruce BUILD: proyectos activos + sprints + kanban por activo."""
    sprints = await db.fetch("""
        SELECT si.id_proyecto, si.sprint_number, si.titulo, si.estado, si.silo,
               s.fecha_inicio, s.fecha_fin, s.nombre as sprint_nombre
        FROM build_sprint_items si
        JOIN build_sprints s ON s.id_proyecto = si.id_proyecto AND s.sprint_number = si.sprint_number
        WHERE si.estado NOT IN ('DONE','COMPLETADO')
        ORDER BY si.id_proyecto, si.sprint_number""")
    live = await db.fetch("""SELECT id_proyecto, nombre, pm_asignado, estado, sprint_actual,
                           total_sprints, gate_actual FROM build_live WHERE estado != 'CERRADO'""")
    kanban = await db.fetch("""SELECT id_proyecto, count(*) as tareas_activas
        FROM kanban_tareas WHERE tipo='BUILD' AND columna IN ('En Progreso','Code Review','Testing','Despliegue')
        GROUP BY id_proyecto""")
    return {
        "proyectos_activos": [dict(r) for r in live],
        "sprint_items_pendientes": [dict(r) for r in sprints],
        "kanban_por_proyecto": [dict(r) for r in kanban]
    }


@register_tool("query_cab_contexto_run")
async def query_cab_contexto_run(db):
    """Cruce RUN: incidencias P1/P2 activas + tareas RUN en kanban."""
    inc = await db.fetch("""SELECT ticket_id, incidencia_detectada, prioridad_ia, estado,
                          ci_afectado, tecnico_asignado, sla_limite,
                          timestamp_creacion
        FROM incidencias_run WHERE estado IN ('QUEUED','EN_CURSO','ESCALADO')
        AND prioridad_ia IN ('P1','P2') ORDER BY prioridad_ia, timestamp_creacion""")
    live = await db.fetch("""SELECT ticket_id, incidencia_detectada, prioridad, estado,
                           tecnico_asignado, sla_horas, progreso_pct
        FROM incidencias_live WHERE estado = 'IN_PROGRESS' ORDER BY prioridad""")
    kanban = await db.fetch("""SELECT id_incidencia, count(*) as tareas_activas
        FROM kanban_tareas WHERE tipo='RUN' AND columna IN ('En Progreso','Bloqueado')
        GROUP BY id_incidencia""")
    results_inc = []
    for r in inc:
        d = dict(r)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        results_inc.append(d)
    return {
        "incidencias_criticas_abiertas": results_inc,
        "incidencias_live": [dict(r) for r in live],
        "kanban_run_activo": [dict(r) for r in kanban]
    }


@register_tool("create_change_proposal")
async def create_change_proposal(db, periodo: str, propuesta_json: dict, tiempo_generacion_segundos: int = 0):
    """Crear propuesta CAB en cmdb_change_proposals."""
    count = await db.fetchval(
        "SELECT COALESCE(MAX(numero_propuesta),0) FROM cmdb_change_proposals WHERE periodo=$1", periodo)
    numero = (count or 0) + 1
    row = await db.fetchrow("""
        INSERT INTO cmdb_change_proposals (periodo, numero_propuesta, propuesta_json, tiempo_generacion_segundos)
        VALUES ($1,$2,$3::jsonb,$4) RETURNING id, periodo, numero_propuesta, estado""",
        periodo, numero, json.dumps(propuesta_json, default=str), tiempo_generacion_segundos)
    d = dict(row)
    for k, v in d.items():
        if hasattr(v, 'isoformat'):
            d[k] = v.isoformat()
    return d


@register_tool("create_cab_alerts")
async def create_cab_alerts(db, alerts: list, periodo: str = ""):
    """Insertar alertas CAB en intelligent_alerts para gov-run y gov-build."""
    inserted = 0
    for a in alerts:
        await db.execute("""
            INSERT INTO intelligent_alerts (alert_type, severity, title, description,
                source_agent, affected_entities, trigger_condition, recommended_actions, status)
            VALUES ($1,$2,$3,$4,'AG-011',$5::jsonb,$6::jsonb,$7::jsonb,'ACTIVE')""",
            a.get("alert_type", "CAB_PROPOSAL_READY"),
            a.get("severity", "MEDIUM"),
            a.get("title", "Alerta CAB"),
            a.get("description", ""),
            json.dumps(a.get("affected_entities", {})),
            json.dumps({"source": "AG-011", "periodo": periodo}),
            json.dumps(a.get("recommended_actions", []))
        )
        inserted += 1
    return {"alerts_inserted": inserted}
