"""Test de aislamiento real entre dos clubes (requiere Postgres)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete, insert, select, text
from sqlalchemy.exc import DBAPIError

from app.db import AppSession, PlatformSession
from app.models import Tenant, TenantAsset, TenantBranding, TenantDomain, TenantUser
from app.tenancy import bind_tenant

pytestmark = pytest.mark.asyncio


async def _create_tenant(session, slug: str, host: str) -> uuid.UUID:
    tenant = Tenant(slug=slug, name=f"Club {slug}", status="active")
    session.add(tenant)
    await session.flush()
    session.add(TenantDomain(tenant_id=tenant.id, host=host, is_primary=True))
    await session.flush()
    return tenant.id


async def test_app_role_no_puede_saltear_rls(database: bool) -> None:
    """El rol de la API no es superuser ni puede saltear RLS."""
    async with PlatformSession() as session:
        row = (
            await session.execute(
                text(
                    "select rolbypassrls, rolsuper from pg_roles where rolname = 'saas_app'"
                )
            )
        ).one()
    assert row.rolbypassrls is False
    assert row.rolsuper is False


async def test_aislamiento_entre_dos_clubes(database: bool) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug_a, slug_b = f"a-{suffix}", f"b-{suffix}"
    host_a, host_b = f"{slug_a}.test.localhost", f"{slug_b}.test.localhost"

    async with PlatformSession() as session:
        async with session.begin():
            tenant_a = await _create_tenant(session, slug_a, host_a)
            tenant_b = await _create_tenant(session, slug_b, host_b)

    try:
        # Alta de usuarios con el rol de la API y el tenant fijado.
        async with AppSession() as session:
            async with session.begin():
                await bind_tenant(session, tenant_a)
                session.add(
                    TenantUser(
                        tenant_id=tenant_a, email=f"admin@{slug_a}.test", password_hash="x"
                    )
                )
            async with session.begin():
                await bind_tenant(session, tenant_b)
                session.add(
                    TenantUser(
                        tenant_id=tenant_b, email=f"admin@{slug_b}.test", password_hash="x"
                    )
                )

        # Fijado en A: solo ve lo de A.
        async with AppSession() as session:
            async with session.begin():
                await bind_tenant(session, tenant_a)
                visible = (await session.scalars(select(TenantUser))).all()
                assert {row.tenant_id for row in visible} == {tenant_a}

                # No puede modificar filas de B (UPDATE afecta 0 filas).
                updated = await session.execute(
                    text("update tenant_users set role = 'hacked' where tenant_id = :tid"),
                    {"tid": str(tenant_b)},
                )
                assert updated.rowcount == 0

                # No puede borrar filas de B.
                deleted = await session.execute(
                    delete(TenantUser).where(TenantUser.tenant_id == tenant_b)
                )
                assert deleted.rowcount == 0

        # Sin GUC fijado: cero filas (falla cerrado).
        async with AppSession() as session:
            async with session.begin():
                counted = await session.scalar(text("select count(*) from tenant_users"))
                assert counted == 0

        # Regresion: en una conexion del pool que YA tuvo un SET LOCAL,
        # current_setting(..., true) devuelve cadena vacia en vez de NULL. Tiene
        # que seguir filtrando todas las filas y no reventar con
        # `invalid input syntax for type uuid: ""`.
        async with AppSession() as session:
            async with session.begin():
                await session.execute(
                    text("select set_config('app.tenant_id', '', true)")
                )
                counted = await session.scalar(text("select count(*) from tenant_users"))
                assert counted == 0

        # WITH CHECK: no puede insertar a nombre de otro club.
        async with AppSession() as session:
            with pytest.raises(DBAPIError):
                async with session.begin():
                    await bind_tenant(session, tenant_a)
                    await session.execute(
                        insert(TenantUser).values(
                            tenant_id=tenant_b,
                            email="intruso@test.localhost",
                            password_hash="x",
                        )
                    )

        # El rol de la API no puede escribir el registro global.
        async with AppSession() as session:
            with pytest.raises(DBAPIError):
                async with session.begin():
                    await session.execute(
                        insert(TenantDomain).values(
                            tenant_id=tenant_a, host=f"intruso-{suffix}.test.localhost"
                        )
                    )
    finally:
        async with PlatformSession() as session:
            async with session.begin():
                await session.execute(
                    delete(Tenant).where(Tenant.slug.in_([slug_a, slug_b]))
                )


async def test_lo_propio_de_cada_club_esta_aislado(database: bool) -> None:
    """Branding y assets (cualquier tabla con tenant_id) no se ven ni se pisan
    desde otro club."""
    suffix = uuid.uuid4().hex[:8]
    slug_a, slug_b = f"brand-a-{suffix}", f"brand-b-{suffix}"

    async with PlatformSession() as session:
        async with session.begin():
            tenant_a = await _create_tenant(session, slug_a, f"{slug_a}.test.localhost")
            tenant_b = await _create_tenant(session, slug_b, f"{slug_b}.test.localhost")

    try:
        async with AppSession() as session:
            async with session.begin():
                await bind_tenant(session, tenant_a)
                session.add(
                    TenantBranding(
                        tenant_id=tenant_a,
                        display_name="Club A",
                        primary_color="#111111",
                    )
                )
                session.add(
                    TenantAsset(
                        tenant_id=tenant_a,
                        name="logo",
                        object_key="tenants/a/assets/logo.png",
                        content_type="image/png",
                        size_bytes=10,
                    )
                )

        async with AppSession() as session:
            async with session.begin():
                await bind_tenant(session, tenant_b)
                # B no ve las filas de A...
                assert (await session.scalars(select(TenantBranding))).all() == []
                assert (await session.scalars(select(TenantAsset))).all() == []
                # ...ni las puede modificar (UPDATE afecta 0 filas).
                branding_update = await session.execute(
                    text("update tenant_branding set display_name = 'hacked'")
                )
                assert branding_update.rowcount == 0
                asset_update = await session.execute(
                    text("update tenant_assets set object_key = 'hacked'")
                )
                assert asset_update.rowcount == 0

        # ...ni insertar a nombre de A (WITH CHECK).
        async with AppSession() as session:
            with pytest.raises(DBAPIError):
                async with session.begin():
                    await bind_tenant(session, tenant_b)
                    await session.execute(
                        insert(TenantAsset).values(
                            tenant_id=tenant_a,
                            name="logo",
                            object_key="x",
                            content_type="image/png",
                            size_bytes=1,
                        )
                    )
    finally:
        async with PlatformSession() as session:
            async with session.begin():
                await session.execute(
                    delete(Tenant).where(Tenant.slug.in_([slug_a, slug_b]))
                )
