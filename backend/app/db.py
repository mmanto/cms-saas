"""Motores y sesiones SQLAlchemy.

En runtime hay dos motores:

* ``app_engine``      -> rol ``saas_app``. RLS activo, el GUC ``app.tenant_id``
  lo fija cada request/job. Es el unico motor que usa la logica de negocio.
* ``platform_engine`` -> rol ``saas_platform``. BYPASSRLS, solo provisioning
  cross-tenant (alta de club, dominios, usuarios de plataforma).

El DSN del migrador (``saas_migrator``) lo consume Alembic, no la app.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.settings import get_settings

_settings = get_settings()


def _build_engine(url: str) -> AsyncEngine:
    return create_async_engine(
        url,
        pool_size=_settings.db_pool_size,
        max_overflow=_settings.db_max_overflow,
        pool_recycle=_settings.db_pool_recycle_seconds,
        pool_pre_ping=True,
        echo=_settings.db_echo,
    )


app_engine: AsyncEngine = _build_engine(_settings.app_database_url)
platform_engine: AsyncEngine = _build_engine(_settings.platform_database_url)

AppSession = async_sessionmaker(app_engine, expire_on_commit=False, autoflush=False)
PlatformSession = async_sessionmaker(platform_engine, expire_on_commit=False, autoflush=False)


async def dispose_engines() -> None:
    await app_engine.dispose()
    await platform_engine.dispose()


def session_factory() -> async_sessionmaker[AsyncSession]:
    """Fabrica de sesiones con RLS para usar en workers."""
    return AppSession
