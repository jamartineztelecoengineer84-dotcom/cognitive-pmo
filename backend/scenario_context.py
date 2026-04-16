"""ARQ-03 F3 — Contexto de escenario por request HTTP.

Propaga el escenario activo (header X-Scenario) desde el middleware HTTP
hasta el setup callback del pool asyncpg vía contextvars.ContextVar, sin
tocar los ~100+ handlers existentes que usan pool.acquire() directo.

Flujo:
  1. Middleware HTTP lee X-Scenario, valida contra whitelist
  2. set_current_scenario(name) guarda el valor en el ContextVar
  3. Handler hace pool.acquire() (sin saber del escenario)
  4. asyncpg invoca pool_setup_callback(conn) que lee el ContextVar
     y ejecuta SET search_path = <scenario>, compartido, public
  5. El handler ejecuta sus queries con search_path correcto
  6. Al cerrar el context manager, asyncpg devuelve la conexión al pool
  7. La siguiente acquire vuelve a invocar el callback con el escenario
     del NUEVO request, sin arrastre.

ContextVars propagan por await y por asyncio.create_task (Python 3.7+),
así que tasks lanzadas por el handler heredan el escenario del request.
"""
import contextvars
from fastapi import HTTPException


SCENARIOS_VALIDOS = {
    "primitiva",
    "sc_iberico",
    "sc_litoral",
    "sc_norte",
    "sc_piloto0",
}

DEFAULT_SCENARIO = "primitiva"


_scenario_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "scenario", default=DEFAULT_SCENARIO
)


def get_current_scenario() -> str:
    """Devuelve el escenario activo en el contexto async actual."""
    return _scenario_ctx.get()


def set_current_scenario(name: str) -> contextvars.Token:
    """Setea el escenario activo y devuelve el token para resetearlo."""
    return _scenario_ctx.set(name)


def reset_current_scenario(token: contextvars.Token) -> None:
    """Restaura el contexto previo al set_current_scenario."""
    _scenario_ctx.reset(token)


def validate_scenario(name: str | None) -> str:
    """Valida un nombre de escenario contra el whitelist.

    - None o vacío → DEFAULT_SCENARIO
    - No en whitelist → HTTPException 400
    - Válido → devuelve el nombre tal cual
    """
    if not name:
        return DEFAULT_SCENARIO
    if name not in SCENARIOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"X-Scenario inválido: {name!r}. "
                f"Válidos: {sorted(SCENARIOS_VALIDOS)}"
            ),
        )
    return name


async def pool_setup_callback(conn) -> None:
    """Setup callback para asyncpg.create_pool().

    Se ejecuta en CADA pool.acquire() (no solo al crear la conexión —
    eso sería el callback `init`). Lee el ContextVar del escenario activo
    y fija el search_path en la conexión cedida al handler.

    Seguridad frente a inyección SQL: el f-string es seguro porque
    `scenario` solo puede contener valores del SCENARIOS_VALIDOS
    (validados en el middleware HTTP). Como defensa en profundidad,
    re-validamos aquí: si el ContextVar contuviera un valor inesperado
    (caso imposible vía flujo normal), caemos al DEFAULT_SCENARIO.
    """
    scenario = get_current_scenario()
    if scenario not in SCENARIOS_VALIDOS:
        scenario = DEFAULT_SCENARIO
    await conn.execute(
        f"SET search_path = {scenario}, compartido, public"
    )
