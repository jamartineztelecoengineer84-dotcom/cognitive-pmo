# Cognitive PMO — Backend

API FastAPI + PostgreSQL para el sistema Cognitive PMO.

## Desarrollo

```bash
# Dependencias de desarrollo (incluye pytest, httpx, pytest-asyncio)
pip install -r requirements-dev.txt
```

## Tests

```bash
# Ejecutar la suite completa dentro del contenedor api
docker compose exec api python -m pytest tests/ -v

# Solo los tests P97 (smoke + RBAC econ /api/p96/* y /api/me)
docker compose exec api python -m pytest tests/test_p96_router.py -v
```
