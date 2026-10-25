"""Jobs del worker ARQ.

Todo job que toque datos de un club tiene que pasar por ``bind_tenant``: el rol
del worker no puede saltear RLS.
"""

from __future__ import annotations

import logging
import uuid

from app.db import AppSession, PlatformSession
from app.provisioning import sync_tenant_routes
from app.tenancy import assert_tenant_binding, tenant_row_count

logger = logging.getLogger("worker")


async def sync_tenant_routes_task(ctx: dict) -> int:
    """Reconcilia las rutas de Traefik con la base.

    Corre cada 5 minutos: si alguien edito routes.yml a mano o la escritura
    quedo a medias, esto lo arregla.
    """
    async with PlatformSession() as session:
        async with session.begin():
            custom = await sync_tenant_routes(session)
    logger.info("rutas sincronizadas: %d dominios propios", custom)
    return custom


async def purge_tenant_cache_task(ctx: dict, tenant_id: str) -> int:
    """Borra las claves de cache de un club."""
    cache = ctx["cache"]
    pattern = f"tenant:{tenant_id}:*"
    deleted = 0
    async for key in cache.scan_iter(match=pattern, count=200):
        await cache.delete(key)
        deleted += 1
    logger.info("cache purgada del tenant %s (%d claves)", tenant_id, deleted)
    return deleted


async def tenant_stats_task(ctx: dict, tenant_id: str) -> dict:
    """Ejemplo de trabajo con RLS fuera de un request HTTP.

    Si el binding no se aplicara, este job veria cero filas (en vez de las de
    otro club, que es lo importante) y ``assert_tenant_binding`` lo delata.
    """
    async with AppSession() as session:
        async with session.begin():
            from app.tenancy import bind_tenant

            await bind_tenant(session, uuid.UUID(tenant_id))
            bound = await assert_tenant_binding(session)
            users = await tenant_row_count(session, "tenant_users")
    return {"tenant_id": str(bound), "users": users}
