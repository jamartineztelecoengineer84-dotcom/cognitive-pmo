import asyncpg
import os
import logging

from scenario_context import pool_setup_callback

logger = logging.getLogger(__name__)

_pool = None


async def init_pool():
    global _pool
    try:
        dsn = (
            f"postgresql://{os.getenv('DB_USER', 'jose_admin')}"
            f":{os.getenv('DB_PASSWORD', '')}"
            f"@{os.getenv('DB_HOST', 'postgres')}"
            f":{os.getenv('DB_PORT', '5432')}"
            f"/{os.getenv('DB_NAME', 'cognitive_pmo')}"
        )
        _pool = await asyncpg.create_pool(
            dsn,
            min_size=1,
            max_size=10,
            command_timeout=30,
            timeout=10,
            setup=pool_setup_callback,  # ARQ-03 F3
        )
        logger.info("AsyncPG pool created successfully")
    except Exception as e:
        logger.warning(f"Could not create asyncpg pool: {e}")
        _pool = None


def get_pool():
    return _pool


async def close_pool():
    global _pool
    if _pool:
        try:
            await _pool.close()
            logger.info("AsyncPG pool closed")
        except Exception as e:
            logger.warning(f"Error closing pool: {e}")
        _pool = None
