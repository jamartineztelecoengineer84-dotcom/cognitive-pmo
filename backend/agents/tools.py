import json
from datetime import datetime, timedelta
from uuid import uuid4

# ═══════════════════════════════════════════════════════════════
# REGISTRO CENTRAL DE TOOLS
# ═══════════════════════════════════════════════════════════════

TOOL_REGISTRY = {}


def register_tool(name):
    """Decorador para registrar tools automáticamente"""
    def decorator(fn):
        TOOL_REGISTRY[name] = fn
        return fn
    return decorator


# ═══════════════════════════════════════════════════════════════
# TOOL SCHEMAS (JSON para Claude tool_use)
# ═══════════════════════════════════════════════════════════════

QUERY_CATALOGO_SCHEMA = {
    "name": "query_catalogo",
    "description": "Busca incidencias similares en el catálogo de incidencias conocidas usando similaridad de texto (pg_trgm). Devuelve las más parecidas con su prioridad sugerida, SLA, skills requeridas y complejidad.",
    "input_schema": {
        "type": "object",
        "properties": {
            "texto": {"type": "string", "description": "Descripción de la incidencia a buscar"},
            "limit": {"type": "integer", "description": "Máximo de resultados (default 5)", "default": 5}
        },
        "required": ["texto"]
    }
}

CREATE_INCIDENT_SCHEMA = {
    "name": "create_incident",
    "description": "Crea un registro de incidencia en la tabla incidencias_run con ticket_id generado, prioridad, SLA, y todos los metadatos. Devuelve el ticket_id y la fecha límite del SLA.",
    "input_schema": {
        "type": "object",
        "properties": {
            "descripcion": {"type": "string", "description": "Descripción completa de la incidencia"},
            "prioridad": {"type": "string", "enum": ["P1", "P2", "P3", "P4"]},
            "categoria": {"type": "string", "description": "Categoría: Base de Datos, Red, Seguridad, etc."},
            "sla_horas": {"type": "number", "description": "Horas de SLA según prioridad"},
            "area_afectada": {"type": "string", "description": "Área: Producción, Pre-producción, etc."},
            "impacto_negocio": {"type": "string", "description": "Descripción del impacto en negocio"},
            "servicio_afectado": {"type": "string", "description": "Servicio ITSM afectado"},
            "ci_afectado": {"type": "string", "description": "Código del CI de la CMDB afectado"},
            "urgencia": {"type": "string", "description": "Alta, Media, Baja"},
            "impacto": {"type": "string", "description": "Alto, Medio, Bajo"}
        },
        "required": ["descripcion", "prioridad", "categoria", "sla_horas", "area_afectada"]
    }
}

CREATE_TASKS_SCHEMA = {
    "name": "create_tasks",
    "description": "Crea múltiples tareas de resolución en kanban_tareas vinculadas a un ticket de incidencia. Cada tarea tiene título, skill requerida y horas estimadas. La primera tarea se mueve automáticamente a 'En Progreso'.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ticket_id": {"type": "string", "description": "ID del ticket de incidencia"},
            "prioridad": {"type": "string", "description": "Prioridad heredada de la incidencia"},
            "tareas": {
                "type": "array",
                "description": "Lista de tareas a crear",
                "items": {
                    "type": "object",
                    "properties": {
                        "titulo": {"type": "string"},
                        "skill_requerida": {"type": "string"},
                        "horas_estimadas": {"type": "number"},
                        "silo": {"type": "string", "description": "Silo técnico: DevOps, BBDD, Soporte, Backend, Redes, Seguridad, Windows, Frontend, QA"},
                        "sla_tarea_minutos": {"type": "number", "description": "Minutos de SLA para esta tarea"},
                        "requiere_negocio": {"type": "boolean", "description": "true si la tarea necesita coordinación con un área de negocio"},
                        "area_negocio": {"type": "string", "description": "Área de negocio afectada si requiere_negocio es true"}
                    },
                    "required": ["titulo", "skill_requerida", "horas_estimadas"]
                }
            }
        },
        "required": ["ticket_id", "tareas"]
    }
}


# ═══════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS — Fase 2: AG-001 Dispatcher
# ═══════════════════════════════════════════════════════════════

@register_tool("query_catalogo")
async def query_catalogo(db, texto: str, limit: int = 5):
    """Busca en catálogo de incidencias por similaridad (pg_trgm)"""
    rows = await db.fetch("""
        SELECT id_catalogo, incidencia, complejidad,
               prioridad_sugerida, skills_requeridas,
               sla_objetivo_horas, area_afectada, nivel_minimo,
               ROUND(similarity(incidencia, $1)::numeric, 2) as score
        FROM catalogo_incidencias
        WHERE similarity(incidencia, $1) > 0.15
        ORDER BY similarity(incidencia, $1) DESC
        LIMIT $2
    """, texto, limit)
    results = []
    for r in rows:
        d = dict(r)
        # Convertir tipos para JSON
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
            elif isinstance(v, (list, dict)):
                pass  # ya es serializable
        results.append(d)
    return results if results else [{"message": "No se encontró match en el catálogo. Clasifica manualmente."}]


@register_tool("create_incident")
async def create_incident(db, descripcion: str, prioridad: str,
                          categoria: str, sla_horas: float,
                          area_afectada: str, **kwargs):
    """Crea incidencia en incidencias_run"""
    ticket_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:4].upper()}"
    await db.execute("""
        INSERT INTO incidencias_run
        (ticket_id, incidencia_detectada, prioridad_ia, categoria,
         sla_limite, area_afectada, impacto_negocio, servicio_afectado,
         ci_afectado, urgencia, impacto, agente_origen,
         timestamp_creacion, estado)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,'AG-001',now(),'QUEUED')
    """, ticket_id, descripcion, prioridad, categoria,
        sla_horas, area_afectada,
        kwargs.get('impacto_negocio', ''),
        kwargs.get('servicio_afectado', ''),
        kwargs.get('ci_afectado', ''),
        kwargs.get('urgencia', 'Media'),
        kwargs.get('impacto', 'Medio'))

    sla_limite = datetime.now() + timedelta(hours=sla_horas)
    return {
        "ticket_id": ticket_id,
        "prioridad": prioridad,
        "sla_horas": sla_horas,
        "sla_limite": sla_limite.strftime("%Y-%m-%d %H:%M"),
        "status": "created"
    }


@register_tool("create_tasks")
async def create_tasks(db, ticket_id: str, tareas: list,
                       prioridad: str = "P3"):
    """Crea tareas en kanban_tareas vinculadas al ticket"""
    # Mapear P1-P4 a valores del constraint kanban
    prio_map = {"P1": "Crítica", "P2": "Alta", "P3": "Media", "P4": "Baja"}
    kanban_prio = prio_map.get(prioridad, prioridad)
    # Validar contra valores permitidos
    if kanban_prio not in ("Crítica", "Alta", "Media", "Baja"):
        kanban_prio = "Alta"
    created = []
    for i, t in enumerate(tareas):
        task_id = f"KT-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:4].upper()}"
        # Primera tarea va a "En Progreso", resto a "Backlog"
        columna = "En Progreso" if i == 0 else "Backlog"
        await db.execute("""
            INSERT INTO kanban_tareas
            (id, titulo, descripcion, tipo, prioridad, columna,
             id_incidencia, horas_estimadas, fecha_creacion)
            VALUES ($1, $2, $3, 'RUN', $4, $5, $6, $7, now())
        """, task_id, t['titulo'],
            json.dumps({
                "skill_requerida": t.get('skill_requerida', ''),
                "silo": t.get('silo', 'Soporte'),
                "sla_tarea_minutos": t.get('sla_tarea_minutos', 60),
                "requiere_negocio": t.get('requiere_negocio', False),
                "area_negocio": t.get('area_negocio', ''),
                "orden": i + 1,
                "enriched": False
            }, ensure_ascii=False),
            kanban_prio, columna, ticket_id,
            t.get('horas_estimadas', 2))
        created.append({
            "task_id": task_id,
            "titulo": t['titulo'],
            "skill": t.get('skill_requerida', ''),
            "columna": columna
        })
    return {
        "ticket_id": ticket_id,
        "tasks_created": len(created),
        "tasks": created
    }


# ═══════════════════════════════════════════════════════════════
# TOOL SCHEMAS — Fase 3: AG-002 Resource Manager + AG-004 Buffer
# ═══════════════════════════════════════════════════════════════

QUERY_STAFF_BY_SKILL_SCHEMA = {
    "name": "query_staff_by_skill",
    "description": "Busca técnicos que tengan las skills requeridas. Devuelve nombre, nivel, silo, carga actual, estado, y skills match.",
    "input_schema": {
        "type": "object",
        "properties": {
            "skills": {"type": "array", "items": {"type": "string"}, "description": "Skills a buscar"},
            "silo": {"type": "string", "description": "Filtrar por silo (opcional)"},
            "max_carga": {"type": "integer", "description": "Carga máxima aceptable (default 35)", "default": 35}
        },
        "required": ["skills"]
    }
}

ASSIGN_TECHNICIAN_SCHEMA = {
    "name": "assign_technician",
    "description": "Asigna un técnico a una tarea Kanban. Actualiza kanban_tareas.id_tecnico y la carga del técnico.",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string"},
            "id_recurso": {"type": "string"},
            "ticket_id": {"type": "string"}
        },
        "required": ["task_id", "id_recurso", "ticket_id"]
    }
}

QUERY_BUILD_ASSIGNMENTS_SCHEMA = {
    "name": "query_build_assignments",
    "description": "Consulta en qué proyectos BUILD está asignado un técnico. Devuelve proyectos, tareas y prioridad estratégica.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id_recurso": {"type": "string", "description": "ID del técnico"}
        },
        "required": ["id_recurso"]
    }
}

FIND_N4_SILO_FALLBACK_SCHEMA = {
    "name": "find_n4_silo_fallback",
    "description": "Busca un técnico N3-N4 del mismo silo con carga <35h como plan B. Excluye técnicos ya descartados.",
    "input_schema": {
        "type": "object",
        "properties": {
            "silo": {"type": "string", "description": "Silo de especialidad"},
            "exclude": {"type": "array", "items": {"type": "string"}, "description": "IDs de técnicos a excluir"}
        },
        "required": ["silo"]
    }
}

WRITE_GOVERNANCE_TX_SCHEMA = {
    "name": "write_governance_tx",
    "description": "Registra una decisión de reasignación en gobernanza_transacciones para trazabilidad y propagación vía Sync Worker.",
    "input_schema": {
        "type": "object",
        "properties": {
            "tipo": {"type": "string", "description": "REASIGNACION_RECURSO, REPLANIFICACION_PROYECTO, etc."},
            "id_proyecto": {"type": "string"},
            "fte_afectado": {"type": "string", "description": "ID del técnico afectado"},
            "estado_anterior": {"type": "string"},
            "estado_nuevo": {"type": "string"},
            "motivo": {"type": "string"},
            "pending_sync": {"type": "array", "items": {"type": "string"}, "description": "Agent IDs a notificar"},
            "depth": {"type": "integer", "description": "Profundidad de cascada (1-3)"},
            "correlation_id": {"type": "string", "description": "ID para vincular cascadas"}
        },
        "required": ["tipo", "fte_afectado", "motivo", "pending_sync"]
    }
}


# ═══════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS — Fase 3
# ═══════════════════════════════════════════════════════════════

@register_tool("query_staff_by_skill")
async def query_staff_by_skill(db, skills: list, silo: str = None,
                                max_carga: int = 35):
    """Busca técnicos por skills - búsqueda flexible por categoría y nombre"""
    conditions = []
    params = []
    for skill in skills:
        param_idx = len(params) + 1
        conditions.append(f"(skills_json::text ILIKE '%' || ${param_idx} || '%')")
        params.append(skill)

    if not conditions:
        return []

    where_skills = " OR ".join(conditions)

    query = f"""
        SELECT id_recurso, nombre, nivel, silo_especialidad,
               skill_principal, carga_actual, estado_run,
               total_skills, skills_json
        FROM pmo_staff_skills
        WHERE ({where_skills})
        AND carga_actual <= ${len(params) + 1}
    """
    params.append(max_carga)

    if silo:
        query += f" AND silo_especialidad = ${len(params) + 1}"
        params.append(silo)

    query += " ORDER BY carga_actual ASC LIMIT 20"

    rows = await db.fetch(query, *params)

    # Fallback: si no hay resultados, buscar N3-N4 disponibles
    if not rows and skills:
        fallback_query = """
            SELECT id_recurso, nombre, nivel, silo_especialidad,
                   skill_principal, carga_actual, estado_run,
                   total_skills, skills_json
            FROM pmo_staff_skills
            WHERE nivel IN ('N3', 'N4')
            AND carga_actual <= $1
            ORDER BY carga_actual ASC LIMIT 10
        """
        rows = await db.fetch(fallback_query, max_carga)

    results = []
    for r in rows:
        d = dict(r)
        tech_skills_text = str(d.get('skills_json', ''))
        matched = sum(1 for s in skills if s.lower() in tech_skills_text.lower())
        d['skills_matched'] = matched
        d['match_pct'] = round(matched / max(len(skills), 1) * 100)
        d['libre'] = (d.get('carga_actual') or 0) < max_carga
        if isinstance(d.get('skills_json'), list):
            d['skills_list'] = [str(s) for s in d['skills_json'][:10]]
        else:
            d['skills_list'] = []
        del d['skills_json']
        results.append(d)

    return results


@register_tool("assign_technician")
async def assign_technician(db, task_id: str, id_recurso: str,
                            ticket_id: str):
    """Asigna técnico a tarea Kanban"""
    await db.execute("""
        UPDATE kanban_tareas SET id_tecnico = $1
        WHERE id = $2
    """, id_recurso, task_id)
    await db.execute("""
        UPDATE incidencias_run SET tecnico_asignado = $1,
        timestamp_asignacion = now()
        WHERE ticket_id = $2 AND tecnico_asignado IS NULL
    """, id_recurso, ticket_id)
    # Incrementar carga del técnico
    horas = await db.fetchval(
        "SELECT COALESCE(horas_estimadas, 2) FROM kanban_tareas WHERE id = $1", task_id)
    await db.execute("""
        UPDATE pmo_staff_skills
        SET carga_actual = LEAST(carga_actual + $1, 200)
        WHERE id_recurso = $2
    """, int(horas or 2), id_recurso)
    return {"status": "assigned", "task_id": task_id, "tecnico": id_recurso}


@register_tool("query_build_assignments")
async def query_build_assignments(db, id_recurso: str):
    """Consulta proyectos BUILD del técnico"""
    rows = await db.fetch("""
        SELECT kt.id_proyecto, cb.nombre_proyecto,
               cb.prioridad_estrategica,
               kt.titulo, kt.horas_estimadas, kt.columna
        FROM kanban_tareas kt
        JOIN cartera_build cb ON kt.id_proyecto = cb.id_proyecto
        WHERE kt.id_tecnico = $1 AND kt.columna NOT IN ('Completado')
    """, id_recurso)
    result = [dict(r) for r in rows]
    for d in result:
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
    return result if result else [{"message": f"Técnico {id_recurso} no tiene asignaciones BUILD activas"}]


@register_tool("find_n4_silo_fallback")
async def find_n4_silo_fallback(db, silo: str, exclude: list = None):
    """Busca técnico N3-N4 del silo como fallback"""
    rows = await db.fetch("""
        SELECT id_recurso, nombre, nivel, carga_actual,
               skill_principal, estado_run
        FROM pmo_staff_skills
        WHERE silo_especialidad = $1
        AND nivel IN ('N3', 'N4')
        AND carga_actual < 35
        AND estado_run = 'DISPONIBLE'
        AND id_recurso != ALL($2::text[])
        ORDER BY CASE nivel WHEN 'N4' THEN 1 WHEN 'N3' THEN 2 END,
                 carga_actual ASC
        LIMIT 3
    """, silo, exclude or [])
    return [dict(r) for r in rows] if rows else [{"message": f"No hay N3-N4 disponibles en silo {silo}"}]


@register_tool("write_governance_tx")
async def write_governance_tx(db, tipo: str, fte_afectado: str,
                              motivo: str, pending_sync: list,
                              id_proyecto: str = None,
                              estado_anterior: str = "",
                              estado_nuevo: str = "",
                              depth: int = 1,
                              correlation_id: str = None):
    """Registra transacción de gobernanza"""
    tx_id = f"GOV-{uuid4().hex[:8].upper()}"
    if not correlation_id:
        correlation_id = tx_id
    await db.execute("""
        INSERT INTO gobernanza_transacciones
        (id_transaccion, tipo_accion, id_proyecto, fte_afectado,
         estado_anterior, estado_nuevo, motivo, agente_origen,
         pending_sync, depth, correlation_id, sync_status)
        VALUES ($1,$2,$3,$4,$5,$6,$7,'AG-004',$8,$9,$10,'PENDIENTE')
    """, tx_id, tipo, id_proyecto or '', fte_afectado,
        estado_anterior, estado_nuevo, motivo,
        json.dumps(pending_sync), depth, correlation_id)
    return {"tx_id": tx_id, "correlation_id": correlation_id, "depth": depth}


# ═══════════════════════════════════════════════════════════════
# TOOL SCHEMAS — Fase 4: AG-005 Estratega + AG-006 Res.Mgr PMO + AG-007 Planificador
# ═══════════════════════════════════════════════════════════════

DECOMPOSE_PMBOK_SCHEMA = {
    "name": "decompose_pmbok",
    "description": "Descompone un proyecto en paquetes de trabajo EDT/WBS siguiendo PMBOK. Devuelve datos del proyecto y catálogo de skills disponibles para asignar.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id_proyecto": {"type": "string"},
            "nombre_proyecto": {"type": "string"},
            "objetivos": {"type": "string", "description": "Objetivos SMART del proyecto"},
            "duracion_semanas": {"type": "integer"},
            "restricciones": {"type": "string"}
        },
        "required": ["id_proyecto", "nombre_proyecto"]
    }
}

ASSIGN_SKILLS_TO_TASKS_SCHEMA = {
    "name": "assign_skills_to_tasks",
    "description": "Valida y asigna skills del catálogo de 100 skills a las tareas del proyecto. Busca el skill más relevante.",
    "input_schema": {
        "type": "object",
        "properties": {
            "tareas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "titulo": {"type": "string"},
                        "skill_sugerida": {"type": "string"}
                    }
                }
            }
        },
        "required": ["tareas"]
    }
}

CREATE_BUILD_PROJECT_SCHEMA = {
    "name": "create_build_project",
    "description": "Almacena el plan del proyecto con EDT, tareas y dependencias en build_project_plans.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id_proyecto": {"type": "string"},
            "nombre": {"type": "string"},
            "plan_data": {"type": "object", "description": "JSON completo con EDT, tareas, dependencias, equipo"}
        },
        "required": ["id_proyecto", "nombre", "plan_data"]
    }
}

FORM_TEAM_SCHEMA = {
    "name": "form_team",
    "description": "Registra la composición del equipo del proyecto. Asigna técnicos a paquetes de trabajo.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id_proyecto": {"type": "string"},
            "asignaciones": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id_recurso": {"type": "string"},
                        "nombre": {"type": "string"},
                        "rol": {"type": "string"},
                        "paquetes_asignados": {"type": "array", "items": {"type": "string"}},
                        "horas_semana": {"type": "number"}
                    }
                }
            }
        },
        "required": ["id_proyecto", "asignaciones"]
    }
}

NOTIFY_GOVERNANCE_SCHEMA = {
    "name": "notify_governance",
    "description": "Notifica a gobernanza sobre gaps de skills, ajustes de equipo u otras decisiones.",
    "input_schema": {
        "type": "object",
        "properties": {
            "tipo": {"type": "string", "description": "SKILL_GAP, TEAM_ADJUSTMENT, SUPERVISOR_ASSIGNED"},
            "id_proyecto": {"type": "string"},
            "detalle": {"type": "string"}
        },
        "required": ["tipo", "detalle"]
    }
}

CALC_CRITICAL_PATH_SCHEMA = {
    "name": "calc_critical_path",
    "description": "Calcula ruta crítica CPM. Recibe tareas con dependencias, devuelve ES/EF/LS/LF/holgura, ruta crítica y tareas paralelizables.",
    "input_schema": {
        "type": "object",
        "properties": {
            "tareas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "titulo": {"type": "string"},
                        "duracion_semanas": {"type": "number"},
                        "depende_de": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["id", "duracion_semanas"]
                }
            }
        },
        "required": ["tareas"]
    }
}

GENERATE_GANTT_MERMAID_SCHEMA = {
    "name": "generate_gantt_mermaid",
    "description": "Genera código Mermaid para diagrama Gantt con tareas paralelas visualizadas.",
    "input_schema": {
        "type": "object",
        "properties": {
            "titulo": {"type": "string"},
            "tareas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "titulo": {"type": "string"},
                        "paquete": {"type": "string"},
                        "duracion_semanas": {"type": "number"},
                        "depende_de": {"type": "array", "items": {"type": "string"}},
                        "fecha_inicio": {"type": "string"},
                        "holgura": {"type": "number"}
                    }
                }
            }
        },
        "required": ["titulo", "tareas"]
    }
}

CREATE_KANBAN_CARDS_SCHEMA = {
    "name": "create_kanban_cards",
    "description": "Crea tarjetas Kanban solo para la fase indicada del proyecto. Primera tarjeta va a 'En Progreso'.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id_proyecto": {"type": "string"},
            "fase": {"type": "string", "description": "Fase: Inicio, Diseño, Ejecución..."},
            "tareas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "titulo": {"type": "string"},
                        "skill": {"type": "string"},
                        "horas": {"type": "number"},
                        "asignado_a": {"type": "string"}
                    }
                }
            }
        },
        "required": ["id_proyecto", "tareas"]
    }
}


# ═══════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS — Fase 4
# ═══════════════════════════════════════════════════════════════

@register_tool("decompose_pmbok")
async def decompose_pmbok(db, id_proyecto: str, nombre_proyecto: str,
                          objetivos: str = "", duracion_semanas: int = 20,
                          restricciones: str = ""):
    """Consulta datos del proyecto y catálogo de skills"""
    row = await db.fetchrow(
        "SELECT * FROM cartera_build WHERE id_proyecto = $1", id_proyecto)
    proyecto = {}
    if row:
        proyecto = dict(row)
        for k, v in proyecto.items():
            if hasattr(v, 'isoformat'):
                proyecto[k] = v.isoformat()
    else:
        proyecto = {"id_proyecto": id_proyecto, "nombre_proyecto": nombre_proyecto}
    skills = await db.fetch(
        "SELECT nombre_skill, categoria, silo FROM catalogo_skills ORDER BY categoria")
    return {
        "proyecto": proyecto,
        "skills_disponibles": [dict(s) for s in skills],
        "duracion_semanas": duracion_semanas,
        "restricciones": restricciones,
        "objetivos": objetivos,
    }


@register_tool("assign_skills_to_tasks")
async def assign_skills_to_tasks(db, tareas: list):
    """Valida skills contra catálogo"""
    results = []
    for t in tareas:
        skill_name = t.get('skill_sugerida', '')
        row = await db.fetchrow("""
            SELECT nombre_skill, categoria, silo
            FROM catalogo_skills
            WHERE nombre_skill ILIKE $1
            LIMIT 1
        """, f"%{skill_name}%")
        results.append({
            "id": t['id'],
            "titulo": t['titulo'],
            "skill_asignada": dict(row) if row else {
                "nombre_skill": skill_name, "nota": "No encontrado en catálogo"
            }
        })
    return results


@register_tool("create_build_project")
async def create_build_project(db, id_proyecto: str, nombre: str,
                                plan_data: dict):
    """Guarda plan de proyecto"""
    plan_id = f"PLAN-{uuid4().hex[:8].upper()}"
    presupuesto = plan_data.get('presupuesto', 0)
    duracion = plan_data.get('duracion_semanas', 20)
    await db.execute("""
        INSERT INTO build_project_plans (id, id_proyecto, nombre,
            presupuesto, duracion_semanas, plan_data)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb)
        ON CONFLICT (id) DO UPDATE SET plan_data = $6::jsonb
    """, plan_id, id_proyecto, nombre, presupuesto, duracion,
        json.dumps(plan_data, ensure_ascii=False, default=str))
    return {"plan_id": plan_id, "status": "created"}


@register_tool("form_team")
async def form_team(db, id_proyecto: str, asignaciones: list):
    """Registra equipo del proyecto"""
    for a in asignaciones:
        horas = a.get('horas_semana', 0)
        if horas > 0 and a.get('id_recurso'):
            await db.execute("""
                UPDATE pmo_staff_skills
                SET carga_actual = LEAST(carga_actual + $1, 200)
                WHERE id_recurso = $2
            """, int(horas), a['id_recurso'])
    return {
        "id_proyecto": id_proyecto,
        "equipo_size": len(asignaciones),
        "asignaciones": asignaciones,
    }


@register_tool("notify_governance")
async def notify_governance(db, tipo: str, detalle: str,
                            id_proyecto: str = ""):
    """Registra notificación de gobernanza"""
    tx_id = f"GOV-{uuid4().hex[:8].upper()}"
    await db.execute("""
        INSERT INTO gobernanza_transacciones
        (id_transaccion, tipo_accion, id_proyecto, motivo, agente_origen,
         sync_status)
        VALUES ($1, $2, $3, $4, 'AG-006', 'COMPLETADA')
    """, tx_id, tipo, id_proyecto, detalle)
    return {"tx_id": tx_id, "tipo": tipo}


@register_tool("calc_critical_path")
async def calc_critical_path(db, tareas: list):
    """Calcula ruta crítica CPM"""
    task_map = {t['id']: t for t in tareas}
    # Inicializar
    for t in tareas:
        t.setdefault('depende_de', [])
        t.setdefault('duracion_semanas', 2)
    # Pasada hacia adelante (topological order)
    resolved = set()
    max_iter = len(tareas) * 2
    for _ in range(max_iter):
        for t in tareas:
            if t['id'] in resolved:
                continue
            deps = t['depende_de']
            if all(d in resolved for d in deps):
                if not deps:
                    t['es'] = 0
                else:
                    t['es'] = max(task_map[d]['ef'] for d in deps if d in task_map)
                t['ef'] = t['es'] + t['duracion_semanas']
                resolved.add(t['id'])
        if len(resolved) == len(tareas):
            break
    # Pasada hacia atrás
    project_end = max(t.get('ef', 0) for t in tareas)
    for t in reversed(tareas):
        successors = [s for s in tareas if t['id'] in s.get('depende_de', [])]
        if not successors:
            t['lf'] = project_end
        else:
            t['lf'] = min(s.get('ls', project_end) for s in successors)
        t['ls'] = t['lf'] - t['duracion_semanas']
        t['holgura'] = t['ls'] - t.get('es', 0)
    ruta_critica = [t['id'] for t in tareas if t.get('holgura', 1) == 0]
    # Identificar paralelizables
    for t in tareas:
        paralelas = [o['id'] for o in tareas
                     if o['id'] != t['id']
                     and o.get('es') == t.get('es')
                     and t['id'] not in o.get('depende_de', [])
                     and o['id'] not in t.get('depende_de', [])]
        t['paralela_con'] = paralelas
    # Calcular ahorro
    duracion_secuencial = sum(t['duracion_semanas'] for t in tareas)
    return {
        "tareas": tareas,
        "ruta_critica": ruta_critica,
        "duracion_total_semanas": project_end,
        "duracion_secuencial_semanas": duracion_secuencial,
        "ahorro_semanas": duracion_secuencial - project_end,
        "tareas_paralelas": sum(1 for t in tareas if t.get('paralela_con')),
    }


@register_tool("generate_gantt_mermaid")
async def generate_gantt_mermaid(db, titulo: str, tareas: list):
    """Genera código Mermaid para Gantt"""
    lines = ["gantt", f"  title {titulo}", "  dateFormat YYYY-MM-DD"]
    current_section = ""
    for t in tareas:
        section = t.get('paquete', 'General')
        if section != current_section:
            lines.append(f"  section {section}")
            current_section = section
        status = "crit," if t.get('holgura', 1) == 0 else ""
        deps = t.get('depende_de', [])
        after = f"after {deps[0]}" if deps else t.get('fecha_inicio', '2026-04-01')
        duracion = f"{t.get('duracion_semanas', 2)}w"
        lines.append(f"  {t.get('titulo', 'Tarea')} :{status}{t['id']}, {after}, {duracion}")
    return {"mermaid": "\n".join(lines)}


@register_tool("create_kanban_cards")
async def create_kanban_cards(db, id_proyecto: str, tareas: list,
                               fase: str = "Inicio"):
    """Crea tarjetas Kanban para una fase del proyecto"""
    created = []
    for i, t in enumerate(tareas):
        task_id = f"BLD-{uuid4().hex[:6].upper()}"
        columna = "En Progreso" if i == 0 else "Backlog"
        await db.execute("""
            INSERT INTO kanban_tareas
            (id, titulo, descripcion, tipo, prioridad, columna,
             id_proyecto, id_tecnico, horas_estimadas, fecha_creacion)
            VALUES ($1,$2,$3,'BUILD','Media',$4,$5,$6,$7,now())
        """, task_id, t.get('titulo', ''),
            json.dumps({"skill": t.get('skill', ''), "fase": fase,
                        "enriched": False}, ensure_ascii=False),
            columna, id_proyecto,
            t.get('asignado_a', None),
            t.get('horas', 0))
        created.append({"task_id": task_id, "titulo": t.get('titulo', '')})
    return {"fase": fase, "cards_created": len(created), "cards": created}


# ═══════════════════════════════════════════════════════════════
# TOOL SCHEMAS — Fase 5: AG-012 Task Advisor (CMDB tools)
# ═══════════════════════════════════════════════════════════════

QUERY_CMDB_ACTIVO_SCHEMA = {
    "name": "query_cmdb_activo",
    "description": "Busca un activo en la CMDB por código CI o por proyecto vinculado. Devuelve servidor, SO, versión, criticidad, propietario, entorno, especificaciones.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ci_codigo": {"type": "string", "description": "Código del CI (ej: SRV-PRO-001) o parte del nombre"},
            "id_proyecto": {"type": "string", "description": "ID del proyecto para buscar activos vinculados"}
        }
    }
}

QUERY_CMDB_IPS_SCHEMA = {
    "name": "query_cmdb_ips",
    "description": "Obtiene las IPs, VLANs, gateway, hostname y configuración de red de un activo.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id_activo": {"type": "integer", "description": "ID numérico del activo (obtenido de query_cmdb_activo)"}
        },
        "required": ["id_activo"]
    }
}

QUERY_CMDB_RELACIONES_SCHEMA = {
    "name": "query_cmdb_relaciones",
    "description": "Obtiene las dependencias de un activo: qué otros activos dependen de él y de cuáles depende.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id_activo": {"type": "integer", "description": "ID numérico del activo"}
        },
        "required": ["id_activo"]
    }
}

QUERY_CMDB_SOFTWARE_SCHEMA = {
    "name": "query_cmdb_software",
    "description": "Obtiene el software instalado en un activo con versiones y si es crítico para el negocio.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id_activo": {"type": "integer", "description": "ID numérico del activo"}
        },
        "required": ["id_activo"]
    }
}

ENRICH_KANBAN_CARD_SCHEMA = {
    "name": "enrich_kanban_card",
    "description": "Actualiza una tarjeta Kanban con las instrucciones técnicas enriquecidas generadas por AG-012. El JSON debe incluir contexto_cmdb, instrucciones paso a paso, y checklist.",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "ID de la tarjeta Kanban"},
            "instructions_json": {
                "type": "object",
                "description": "JSON con tipo, contexto_cmdb, instrucciones y checklist"
            }
        },
        "required": ["task_id", "instructions_json"]
    }
}

# Import CMDB tool implementations (they self-register via @register_tool)
import agents.tools_cmdb  # noqa: F401

# ═══════════════════════════════════════════════════════════════
# TOOL SCHEMAS — Fase 6: AG-003 Demand Forecaster
# ═══════════════════════════════════════════════════════════════

RUN_PROPHET_SCHEMA = {
    "name": "run_prophet",
    "description": "Ejecuta Facebook Prophet sobre datos históricos de incidencias. Devuelve predicción semanal con intervalos de confianza.",
    "input_schema": {
        "type": "object",
        "properties": {
            "weeks_ahead": {"type": "integer", "description": "Semanas a predecir (default 12)", "default": 12},
            "categoria": {"type": "string", "description": "Filtrar por categoría de incidencia (opcional)"}
        }
    }
}

QUERY_CAPACITY_SCHEMA = {
    "name": "query_capacity",
    "description": "Obtiene la capacidad actual del equipo técnico por silo: total técnicos, horas disponibles, carga promedio.",
    "input_schema": {
        "type": "object",
        "properties": {}
    }
}

STORE_FORECAST_SCHEMA = {
    "name": "store_forecast",
    "description": "Almacena la predicción y recomendaciones en whatif_simulations.",
    "input_schema": {
        "type": "object",
        "properties": {
            "prediction": {"type": "object", "description": "JSON con predicción semanal"},
            "recommendations": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number", "description": "Nivel de confianza 0-1"}
        },
        "required": ["prediction", "recommendations"]
    }
}


# ═══════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS — Fase 6
# ═══════════════════════════════════════════════════════════════

@register_tool("run_prophet")
async def run_prophet(db, weeks_ahead: int = 12, categoria: str = None):
    """Ejecuta Prophet REAL sobre datos históricos de incidencias"""
    query = """
        SELECT DATE(timestamp_creacion) as ds, COUNT(*) as y
        FROM incidencias_run
        WHERE timestamp_creacion IS NOT NULL
    """
    params = []
    if categoria:
        query += " AND categoria = $1"
        params.append(categoria)
    query += " GROUP BY ds ORDER BY ds"

    rows = await db.fetch(query, *params)

    if len(rows) < 7:
        # Generar datos sintéticos basados en lo que hay
        total_inc = await db.fetchval("SELECT COUNT(*) FROM incidencias_run")
        return {
            "warning": "Datos históricos limitados",
            "rows_found": len(rows),
            "total_incidencias": total_inc,
            "synthetic_forecast": True,
            "data": [
                {"semana": f"S+{i+1}", "prediccion": round(max(total_inc / 7, 2) * (1 + (i % 3) * 0.15), 1),
                 "rango_bajo": round(max(total_inc / 7, 1) * 0.7, 1),
                 "rango_alto": round(max(total_inc / 7, 3) * 1.4, 1)}
                for i in range(weeks_ahead)
            ],
            "trend": "estable",
            "nota": "Predicción basada en promedio histórico (datos insuficientes para Prophet completo)"
        }

    try:
        import pandas as pd
        from prophet import Prophet

        df = pd.DataFrame([{"ds": r["ds"], "y": r["y"]} for r in rows])
        df["ds"] = pd.to_datetime(df["ds"])

        m = Prophet(
            weekly_seasonality=True,
            yearly_seasonality=len(rows) > 365,
            daily_seasonality=False
        )
        m.fit(df)

        future = m.make_future_dataframe(periods=weeks_ahead * 7)
        forecast = m.predict(future)

        result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(weeks_ahead * 7)
        result["ds"] = pd.to_datetime(result["ds"])
        weekly = result.set_index("ds").resample("W").agg({
            "yhat": "mean", "yhat_lower": "mean", "yhat_upper": "mean"
        }).reset_index()

        weekly_data = []
        for _, row in weekly.iterrows():
            weekly_data.append({
                "semana": row["ds"].strftime("%Y-%m-%d"),
                "prediccion": round(float(row["yhat"]), 1),
                "rango_bajo": round(float(row["yhat_lower"]), 1),
                "rango_alto": round(float(row["yhat_upper"]), 1)
            })

        return {
            "weeks_predicted": len(weekly_data),
            "data": weekly_data,
            "historical_avg": round(float(df["y"].mean()), 1),
            "historical_max": int(df["y"].max()),
            "trend": "creciente" if weekly_data[-1]["prediccion"] > float(df["y"].mean()) else "estable"
        }
    except ImportError:
        # Prophet no instalado — fallback con estadísticas simples
        import statistics
        values = [r["y"] for r in rows]
        avg = statistics.mean(values)
        return {
            "prophet_unavailable": True,
            "fallback": "statistical",
            "weeks_predicted": weeks_ahead,
            "data": [
                {"semana": f"S+{i+1}", "prediccion": round(avg * (1 + (i % 4) * 0.1), 1),
                 "rango_bajo": round(avg * 0.6, 1), "rango_alto": round(avg * 1.5, 1)}
                for i in range(weeks_ahead)
            ],
            "historical_avg": round(avg, 1),
            "historical_max": max(values),
            "trend": "estable"
        }
    except Exception as e:
        return {"error": f"Prophet error: {str(e)}"}


@register_tool("query_capacity")
async def query_capacity(db):
    """Capacidad actual del equipo por silo"""
    rows = await db.fetch("""
        SELECT silo_especialidad,
               COUNT(*) as total_tecnicos,
               SUM(GREATEST(40 - carga_actual, 0)) as horas_disponibles,
               ROUND(AVG(carga_actual)::numeric, 1) as carga_promedio,
               COUNT(*) FILTER (WHERE estado_run = 'DISPONIBLE') as disponibles,
               COUNT(*) FILTER (WHERE estado_run = 'OCUPADO') as ocupados
        FROM pmo_staff_skills
        GROUP BY silo_especialidad
        ORDER BY silo_especialidad
    """)
    result = []
    for r in rows:
        d = dict(r)
        for k, v in d.items():
            if hasattr(v, '__float__'):
                d[k] = float(v)
        result.append(d)
    return result


@register_tool("store_forecast")
async def store_forecast(db, prediction: dict, recommendations: list,
                         confidence: float = 0.7):
    """Almacena predicción en whatif_simulations"""
    sim_id = f"FC-{uuid4().hex[:8].upper()}"
    await db.execute("""
        INSERT INTO whatif_simulations
        (id, simulation_name, scenario_type, input_params,
         simulation_result, confidence_level, recommendations, created_by)
        VALUES ($1, $2, 'DEMAND_FORECAST', $3, $4, $5, $6, 'AG-003')
    """, sim_id,
        f"Forecast {datetime.now().strftime('%Y-%m-%d')}",
        json.dumps({"generated_at": datetime.now().isoformat()}),
        json.dumps(prediction, default=str),
        confidence,
        recommendations)
    return {"simulation_id": sim_id, "status": "stored"}


# ═══════════════════════════════════════════════════════════════
# TOOL SCHEMA + IMPL — Budget (AG-007 Planificador)
# ═══════════════════════════════════════════════════════════════

CREATE_BUDGET_SCHEMA = {
    "name": "create_budget",
    "description": "Crea un presupuesto desglosado en la tabla presupuestos con CAPEX, OPEX, RRHH, labor y contingencia. Calcula automáticamente los totales y el BAC.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id_proyecto": {"type": "string"},
            "nombre": {"type": "string"},
            "responsable": {"type": "string", "description": "PM responsable"},
            "horas_internas": {"type": "number", "description": "Total horas del equipo interno"},
            "tarifa_hora": {"type": "number", "description": "Coste/hora en EUR (default 65)", "default": 65},
            "capex_hardware": {"type": "number", "default": 0},
            "capex_software": {"type": "number", "default": 0},
            "capex_infraestructura": {"type": "number", "default": 0},
            "opex_licencias_sw": {"type": "number", "default": 0},
            "opex_cloud_infra": {"type": "number", "default": 0},
            "opex_mantenimiento": {"type": "number", "default": 0},
            "opex_formacion": {"type": "number", "default": 0},
            "rrhh_formacion": {"type": "number", "default": 0},
            "rrhh_viajes_dietas": {"type": "number", "default": 0},
            "proveedores_externos": {"type": "number", "default": 0},
            "contingencia_pct": {"type": "number", "description": "% contingencia (default 10)", "default": 10},
            "gestion_pct": {"type": "number", "description": "% reserva gestion (default 5)", "default": 5}
        },
        "required": ["id_proyecto", "nombre", "horas_internas"]
    }
}

@register_tool("create_budget")
async def create_budget(db, id_proyecto: str, nombre: str,
                        horas_internas: float, responsable: str = "PM",
                        tarifa_hora: float = 65,
                        capex_hardware: float = 0, capex_software: float = 0,
                        capex_infraestructura: float = 0,
                        opex_licencias_sw: float = 0, opex_cloud_infra: float = 0,
                        opex_mantenimiento: float = 0, opex_formacion: float = 0,
                        rrhh_formacion: float = 0, rrhh_viajes_dietas: float = 0,
                        proveedores_externos: float = 0,
                        contingencia_pct: float = 10, gestion_pct: float = 5):
    """Crea presupuesto desglosado en tabla presupuestos"""
    budget_id = f"BUD-{uuid4().hex[:8].upper()}"

    total_labor = round(horas_internas * tarifa_hora, 2)
    total_capex = capex_hardware + capex_software + capex_infraestructura
    total_opex = opex_licencias_sw + opex_cloud_infra + opex_mantenimiento + opex_formacion
    total_rrhh = rrhh_formacion + rrhh_viajes_dietas
    subtotal = total_labor + proveedores_externos + total_opex + total_capex + total_rrhh
    reserva_contingencia = round(subtotal * contingencia_pct / 100, 2)
    reserva_gestion = round(subtotal * gestion_pct / 100, 2)
    bac_total = round(subtotal + reserva_contingencia + reserva_gestion, 2)

    await db.execute("""
        INSERT INTO presupuestos
        (id_presupuesto, id_proyecto, nombre_presupuesto, responsable,
         horas_internas, tarifa_hora_interna,
         capex_hardware, capex_software, capex_infraestructura,
         opex_licencias_sw, opex_cloud_infra, opex_mantenimiento, opex_formacion,
         rrhh_formacion, rrhh_viajes_dietas,
         proveedores_externos,
         reserva_contingencia_pct, reserva_gestion_pct,
         total_labor, total_proveedores, total_opex, total_capex, total_rrhh,
         total_reservas, bac_total, estado)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,
                $16::jsonb,$17,$18,$19,$20,$21,$22,$23,$24,$25,'BORRADOR')
    """, budget_id, id_proyecto, nombre, responsable,
        horas_internas, tarifa_hora,
        capex_hardware, capex_software, capex_infraestructura,
        opex_licencias_sw, opex_cloud_infra, opex_mantenimiento, opex_formacion,
        rrhh_formacion, rrhh_viajes_dietas,
        json.dumps([{"nombre": "Externos", "importe": proveedores_externos}]),
        contingencia_pct, gestion_pct,
        total_labor, proveedores_externos, total_opex, total_capex, total_rrhh,
        reserva_contingencia + reserva_gestion, bac_total)

    return {
        "budget_id": budget_id,
        "desglose": {
            "labor": total_labor,
            "proveedores": proveedores_externos,
            "capex": total_capex,
            "opex": total_opex,
            "rrhh": total_rrhh,
            "contingencia": reserva_contingencia,
            "gestion": reserva_gestion,
            "bac_total": bac_total
        }
    }


# ═══════════════════════════════════════════════════════════════
# TOOL — Directorio Corporativo (contactos de negocio)
# ═══════════════════════════════════════════════════════════════

QUERY_DIRECTORIO_SCHEMA = {
    "name": "query_directorio",
    "description": "Busca contactos del directorio corporativo por área o cargo. Usar cuando una tarea requiere coordinación con negocio (Trading, Operaciones, Compliance, etc.) y no hay técnicos IT adecuados.",
    "input_schema": {
        "type": "object",
        "properties": {
            "area": {"type": "string", "description": "Área a buscar: Trading y Mercados, Operaciones Bancarias, Banca Digital, Compliance, Gestión de Riesgos, Tesorería, Banca Empresas, Medios de Pago, Atención al Cliente, Recursos Humanos"},
            "cargo": {"type": "string", "description": "Cargo a buscar (opcional)"}
        },
        "required": ["area"]
    }
}

@register_tool("query_directorio")
async def query_directorio(db, area: str, cargo: str = None):
    """Busca contactos del directorio corporativo por área de negocio"""
    query = """
        SELECT id_directivo, nombre_completo, cargo, area, email, telefono, bio
        FROM directorio_corporativo
        WHERE activo = true AND (
            area ILIKE '%' || $1 || '%'
            OR cargo ILIKE '%' || $1 || '%'
            OR bio ILIKE '%' || $1 || '%'
        )
    """
    params = [area]
    if cargo:
        query += " AND cargo ILIKE '%' || $2 || '%'"
        params.append(cargo)
    query += " ORDER BY nivel_organizativo ASC LIMIT 5"
    rows = await db.fetch(query, *params)
    return [dict(r) for r in rows] if rows else [{"message": "No se encontraron contactos en área: " + area}]
