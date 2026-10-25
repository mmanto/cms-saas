"""Punto de entrada de la API.

Todo lo publico vive bajo /api (es lo unico que Traefik enruta desde afuera).
Los endpoints operativos quedan fuera de ese prefijo a proposito.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI

from app.api import assets, auth, branding, credentials, health, modules, platform
from app.db import AppSession, PlatformSession, dispose_engines
from app.modules.registry import MODULES
from app.provisioning import sync_tenant_routes
from app.settings import get_settings
from app.storage import ensure_bucket

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
)
logger = logging.getLogger("api")

API_PREFIX = "/api"
API_VERSION = "v1"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.s3_auto_create_bucket:
        try:
            await ensure_bucket()
        except Exception as exc:
            logger.warning("no pude preparar el bucket: %s", exc)

    # Best effort: si la escritura falla, el cron del worker reintenta cada 5
    # minutos y ademas el arranque no debe depender del volumen de Traefik.
    try:
        async with PlatformSession() as session:
            async with session.begin():
                custom = await sync_tenant_routes(session)
        logger.info("rutas de Traefik sincronizadas (%d dominios propios)", custom)
    except Exception as exc:
        logger.warning("no pude sincronizar rutas de Traefik: %s", exc)

    try:
        redis_client = await create_pool(RedisSettings.from_dsn(settings.redis_cache_url))
        health.ready._redis = redis_client  # type: ignore[attr-defined]
    except Exception as exc:
        logger.warning("no pude conectar a redis de cache: %s", exc)

    yield

    redis_client = getattr(health.ready, "_redis", None)
    if redis_client is not None:
        await redis_client.aclose()
    await dispose_engines()


app = FastAPI(
    title="SaaS Clubes API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=None,
    openapi_url=f"{API_PREFIX}/openapi.json",
)

app.include_router(health.router)
app.include_router(auth.router, prefix=f"{API_PREFIX}/{API_VERSION}")
app.include_router(credentials.router, prefix=f"{API_PREFIX}/{API_VERSION}")
app.include_router(assets.router, prefix=f"{API_PREFIX}/{API_VERSION}")
app.include_router(branding.router, prefix=f"{API_PREFIX}/{API_VERSION}")
app.include_router(modules.router, prefix=f"{API_PREFIX}/{API_VERSION}")
app.include_router(platform.router, prefix=f"{API_PREFIX}/{API_VERSION}")

# Modulos conectables: cada plugin monta su router bajo /api/v1. El switch por
# club lo resuelven las dependencias del propio modulo (app/modules/gate.py).
for _module in MODULES.values():
    app.include_router(_module.router, prefix=f"{API_PREFIX}/{API_VERSION}")
# Sin prefijo /api: el borde solo enruta /api, asi que estos solo se alcanzan
# desde adentro de la red (los usa el SSR del frontend).
app.include_router(branding.internal_router)

# Alias internos, SIN /api: solo se alcanzan desde la red interna (el borde
# enruta exclusivamente /api). Los usa el SSR del frontend, que no tiene el Host
# del navegador y lo pasa en X-SaaS-Host. Fuera del OpenAPI a proposito.
app.include_router(auth.router, include_in_schema=False)
for _module in MODULES.values():
    app.include_router(_module.router, include_in_schema=False)
