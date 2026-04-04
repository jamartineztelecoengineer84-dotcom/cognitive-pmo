import asyncio
import json
import logging
from agents.engine import AgentEngine
from agents.config import AGENT_CONFIGS

log = logging.getLogger("sync_worker")


async def sync_loop(db_pool):
    """Propaga cambios de gobernanza cada 10 segundos"""
    log.info("Sync Worker started")
    while True:
        try:
            rows = await db_pool.fetch("""
                SELECT * FROM gobernanza_transacciones
                WHERE sync_status IN ('PENDIENTE', 'EN_PROCESO')
                AND pending_sync != '[]'::jsonb
                ORDER BY timestamp_ejecucion ASC LIMIT 5
            """)
            for tx in rows:
                await _process_tx(db_pool, tx)
        except Exception as e:
            log.error(f"Sync loop error: {e}")
        await asyncio.sleep(10)


async def _process_tx(db, tx):
    pending = tx["pending_sync"]
    if isinstance(pending, str):
        pending = json.loads(pending)
    remaining = list(pending)

    for agent_id in pending:
        if agent_id not in AGENT_CONFIGS:
            log.warning(f"Agent {agent_id} not in AGENT_CONFIGS yet, skipping")
            remaining.remove(agent_id)
            continue
        try:
            engine = AgentEngine(AGENT_CONFIGS[agent_id], db)
            context = json.dumps({
                "tipo": tx["tipo_accion"],
                "recurso": tx["fte_afectado"],
                "proyecto": tx.get("id_proyecto", ""),
                "estado_anterior": tx.get("estado_anterior", ""),
                "estado_nuevo": tx.get("estado_nuevo", ""),
                "motivo": tx.get("motivo", ""),
            }, ensure_ascii=False)
            await engine.invoke(
                f"Notificación de gobernanza: {tx['tipo_accion']}. Contexto: {context}",
                session_id=str(tx["id_transaccion"])
            )
            remaining.remove(agent_id)
            log.info(f"Sync OK: {agent_id} for TX {tx['id_transaccion']}")
        except Exception as e:
            log.error(f"Sync FAIL {agent_id} for TX {tx['id_transaccion']}: {e}")

    new_retry = (tx.get("retry_count") or 0) + (1 if remaining else 0)
    new_status = ("COMPLETADA" if not remaining else
                  "FALLO" if new_retry > 3 else "EN_PROCESO")

    await db.execute("""
        UPDATE gobernanza_transacciones
        SET pending_sync = $1, retry_count = $2, sync_status = $3
        WHERE id_transaccion = $4
    """, json.dumps(remaining), new_retry, new_status, tx["id_transaccion"])

    if new_status == "FALLO":
        try:
            await db.execute("""
                INSERT INTO intelligent_alerts
                (alert_type, severity, title, description, source_agent,
                 affected_entities, status)
                VALUES ('SYNC_FAILURE', 'HIGH',
                        $1, $2, 'SYNC_WORKER', $3, 'ACTIVE')
            """, f"Sync falló tras 3 reintentos: TX {tx['id_transaccion']}",
                f"Tipo: {tx['tipo_accion']}, Recurso: {tx['fte_afectado']}",
                json.dumps({"tx_id": str(tx["id_transaccion"])}))
        except Exception:
            pass
        log.error(f"TX {tx['id_transaccion']} marcada como FALLO")
