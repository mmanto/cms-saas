"""El dominio base como portal (`SAAS_BASE_TENANT`).

El apex no es un subdominio: sin configuracion se resuelve como plataforma. Con
un slug configurado, `resolve_tenant` tiene que devolver ese club aun sin una
fila en `tenant_domains` (el dominio base no es un dominio propio).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete

from app.db import PlatformSession
from app.models import Tenant
from app.tenancy import resolve_tenant


async def test_el_apex_resuelve_al_portal_configurado(
    database: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"apex-{suffix}"
    host = f"{slug}.test"

    async with PlatformSession() as session:
        async with session.begin():
            tenant = Tenant(slug=slug, name="Apex", status="active")
            session.add(tenant)
            await session.flush()
            tenant_id = tenant.id

    class Settings:
        saas_base_tenant = slug

    monkeypatch.setattr("app.tenancy.get_settings", lambda: Settings())
    try:
        async with PlatformSession() as session:
            found = await resolve_tenant(session, host, host)
        assert found is not None
        assert found.id == tenant_id
    finally:
        async with PlatformSession() as session:
            async with session.begin():
                await session.execute(delete(Tenant).where(Tenant.id == tenant_id))


async def test_sin_base_tenant_el_apex_no_es_un_portal(
    database: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Settings:
        saas_base_tenant = ""

    monkeypatch.setattr("app.tenancy.get_settings", lambda: Settings())
    async with PlatformSession() as session:
        assert await resolve_tenant(session, "nadie.test", "nadie.test") is None
