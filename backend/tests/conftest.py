"""Configuracion de tests.

Los tests de integracion necesitan Postgres con los roles creados; si no hay
base disponible se saltean en vez de fallar, para poder correr la suite en
cualquier maquina.
"""

from __future__ import annotations

import os

# Defaults para que los imports funcionen sin entorno (tests unitarios).
os.environ.setdefault("APP_DATABASE_URL", "postgresql+asyncpg://saas_app:x@127.0.0.1:5432/cms_sas")
os.environ.setdefault("PLATFORM_DATABASE_URL", "postgresql+asyncpg://saas_platform:x@127.0.0.1:5432/cms_sas")
os.environ.setdefault("MIGRATOR_DATABASE_URL", "postgresql+asyncpg://saas_migrator:x@127.0.0.1:5432/cms_sas")
os.environ.setdefault("REDIS_BROKER_URL", "redis://:x@127.0.0.1:6379/0")
os.environ.setdefault("REDIS_CACHE_URL", "redis://:x@127.0.0.1:6380/0")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault(
    "CREDENTIALS_KEY", "5nQ3S0IydCkR2m9tK0e0l6cZ8xW1vU4aB7dF2gH5jK8="
)
os.environ.setdefault("ENVIRONMENT", "test")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy import text  # noqa: E402


async def _database_available() -> bool:
    from app.db import platform_engine

    try:
        async with platform_engine.connect() as connection:
            await connection.execute(text("select 1"))
        return True
    except Exception:
        return False


@pytest_asyncio.fixture(scope="session")
async def database() -> bool:
    available = await _database_available()
    if not available:
        pytest.skip("sin base de datos disponible: se saltean los tests de integracion")
    return True
