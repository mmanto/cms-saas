"""Bootstrap idempotente: bucket, admin de plataforma y club de ejemplo.

Se ejecuta despues de ``alembic upgrade head`` (servicio ``migrate``). Correrlo
dos veces no duplica nada.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import PlatformSession, dispose_engines
from app.models import PlatformUser, Tenant, TenantDomain, TenantUser
from app.modules.registry import set_enabled
from app.provisioning import sync_tenant_routes
from app.security import hash_password
from app.settings import get_settings
from app.storage import ensure_bucket
from app.tenancy import normalize_host

logging.basicConfig(level=logging.INFO, format="%(levelname)-5s [%(name)s] %(message)s")
logger = logging.getLogger("bootstrap")


async def ensure_platform_admin(session: AsyncSession) -> None:
    settings = get_settings()
    if not settings.platform_admin_email or not settings.platform_admin_password:
        logger.warning("PLATFORM_ADMIN_EMAIL/PASSWORD sin definir: no creo admin")
        return
    email = settings.platform_admin_email.strip().lower()
    existing = await session.scalar(select(PlatformUser).where(PlatformUser.email == email))
    if existing is not None:
        logger.info("admin de plataforma ya existe: %s", email)
        return
    session.add(
        PlatformUser(
            email=email,
            password_hash=hash_password(settings.platform_admin_password),
        )
    )
    await session.flush()
    logger.info("admin de plataforma creado: %s", email)


async def ensure_first_tenant(session: AsyncSession) -> None:
    settings = get_settings()
    slug = settings.first_tenant_slug.strip().lower()
    if not slug:
        return

    tenant = await session.scalar(select(Tenant).where(Tenant.slug == slug))
    if tenant is None:
        tenant = Tenant(
            slug=slug,
            name=settings.first_tenant_name.strip() or slug,
            status="active",
        )
        session.add(tenant)
        await session.flush()
        logger.info("club creado: %s (%s)", tenant.name, tenant.id)

    base = normalize_host(settings.saas_base_domain)
    host = f"{slug}.{base}"
    exists = await session.scalar(select(TenantDomain).where(TenantDomain.host == host))
    if exists is None:
        session.add(TenantDomain(tenant_id=tenant.id, host=host, is_primary=True))
        await session.flush()
        logger.info("dominio del club: %s", host)

    if settings.first_tenant_admin_email and settings.first_tenant_admin_password:
        email = settings.first_tenant_admin_email.strip().lower()
        admin = await session.scalar(
            select(TenantUser).where(
                TenantUser.tenant_id == tenant.id, TenantUser.email == email
            )
        )
        if admin is None:
            session.add(
                TenantUser(
                    tenant_id=tenant.id,
                    email=email,
                    password_hash=hash_password(settings.first_tenant_admin_password),
                    role="admin",
                )
            )
            await session.flush()
            logger.info("admin del club: %s", email)

    # El club de ejemplo nace con el modulo de articulos: la landing que instala
    # el generador ya trae esa seccion. El hook del modulo siembra los articulos
    # de ejemplo solo si el club no tiene ninguno (idempotente: corre en cada up).
    await set_enabled(session, tenant.id, "articles", True)
    logger.info("modulo articles habilitado en %s", tenant.slug)


async def main() -> None:
    settings = get_settings()

    if settings.s3_auto_create_bucket:
        try:
            await ensure_bucket()
            logger.info("bucket %s listo", settings.s3_bucket)
        except Exception as exc:  # el storage no deberia bloquear el arranque
            logger.warning("no pude preparar el bucket %s: %s", settings.s3_bucket, exc)

    async with PlatformSession() as session:
        async with session.begin():
            await ensure_platform_admin(session)
            await ensure_first_tenant(session)
        async with session.begin():
            custom = await sync_tenant_routes(session)
    logger.info("rutas de Traefik sincronizadas (%d dominios propios)", custom)

    await dispose_engines()


if __name__ == "__main__":
    asyncio.run(main())
