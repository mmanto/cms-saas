"""Configuracion del worker ARQ."""

from __future__ import annotations

import logging

from arq import cron
from arq.connections import RedisSettings, create_pool

from app.db import dispose_engines
from app.settings import get_settings
from app.tasks import purge_tenant_cache_task, sync_tenant_routes_task, tenant_stats_task

logging.basicConfig(
    level=getattr(logging, get_settings().log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
)
logger = logging.getLogger("arq")


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_broker_url)


async def startup(ctx: dict) -> None:
    settings = get_settings()
    ctx["cache"] = await create_pool(RedisSettings.from_dsn(settings.redis_cache_url))
    logger.info("worker listo (entorno=%s)", settings.environment)


async def shutdown(ctx: dict) -> None:
    cache = ctx.pop("cache", None)
    if cache is not None:
        await cache.aclose()
    await dispose_engines()


class WorkerSettings:
    functions = [sync_tenant_routes_task, purge_tenant_cache_task, tenant_stats_task]
    cron_jobs = [cron(sync_tenant_routes_task, minute=set(range(0, 60, 5)), run_at_startup=True)]
    redis_settings = _redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 300
    keep_result = 3600
    health_check_interval = 30
    max_tries = 3
