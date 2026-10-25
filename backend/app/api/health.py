"""Endpoints operativos. No llevan prefijo /api: no se exponen por el borde.

Traefik solo publica /api, asi que /health y /ready quedan accesibles unicamente
desde dentro de la red (healthcheck de Docker, Prometheus, etc.).
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.db import app_engine
from app.settings import get_settings

router = APIRouter(tags=["ops"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness: no toca dependencias, solo dice que el proceso responde."""
    return {"status": "ok", "environment": get_settings().environment}


@router.get("/ready")
async def ready(response: Response) -> dict[str, object]:
    """Readiness: Postgres y Redis tienen que contestar."""
    checks: dict[str, str] = {}

    try:
        async with app_engine.connect() as connection:
            await connection.execute(text("select 1"))
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error: {type(exc).__name__}"

    redis_client = getattr(ready, "_redis", None)
    if redis_client is not None:
        try:
            await redis_client.ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"error: {type(exc).__name__}"

    healthy = all(value == "ok" for value in checks.values())
    response.status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if healthy else "degraded", "checks": checks}
