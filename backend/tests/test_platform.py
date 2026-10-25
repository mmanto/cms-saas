"""Tests de la API de plataforma.

Lo barato (validacion de los esquemas de entrada) no toca la base. Lo que si
importa: que dar de baja un club no deje filas huerfanas, porque el backoffice
borra la fila de ``tenants`` y confia en los ``ON DELETE CASCADE`` para el
resto.
"""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.api.platform import TenantPatchIn, TenantUserIn, TenantUserPatchIn
from app.db import PlatformSession
from app.models import Tenant, TenantAsset, TenantBranding, TenantDomain, TenantUser


def test_patch_sin_campos_es_rechazado() -> None:
    with pytest.raises(ValidationError):
        TenantPatchIn()
    with pytest.raises(ValidationError):
        TenantUserPatchIn()


def test_patch_rechaza_estado_desconocido() -> None:
    with pytest.raises(ValidationError):
        TenantPatchIn(status="borrado")

    assert TenantPatchIn(status="suspended").status == "suspended"
    assert TenantPatchIn(name="Club Nuevo").name == "Club Nuevo"


def test_user_patch_acepta_un_campo_por_vez() -> None:
    assert TenantUserPatchIn(password="nueva12345").role is None
    assert TenantUserPatchIn(role="admin").password is None


def test_alta_de_usuario_rol_por_defecto() -> None:
    user = TenantUserIn(email="jugador@club.test", password="prueba1234")

    assert user.role == "member"
    with pytest.raises(ValidationError):  # password corta
        TenantUserIn(email="jugador@club.test", password="corta")
    with pytest.raises(ValidationError):  # rol fuera del enum
        TenantUserIn(email="jugador@club.test", password="prueba1234", role="duenio")


async def test_la_baja_del_club_no_deja_filas_huerfanas(database: bool) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"baja-{suffix}"

    async with PlatformSession() as session:
        async with session.begin():
            tenant = Tenant(slug=slug, name="Club Baja", status="active")
            session.add(tenant)
            await session.flush()
            tenant_id = tenant.id
            session.add(
                TenantDomain(
                    tenant_id=tenant_id, host=f"{slug}.test.localhost", is_primary=True
                )
            )
            session.add(
                TenantUser(
                    tenant_id=tenant_id,
                    email=f"admin@{slug}.test",
                    password_hash="x",
                    role="admin",
                )
            )
            session.add(TenantBranding(tenant_id=tenant_id, display_name="Club Baja"))
            session.add(
                TenantAsset(
                    tenant_id=tenant_id,
                    name="logo",
                    object_key=f"tenants/{tenant_id}/assets/logo.png",
                    content_type="image/png",
                    size_bytes=10,
                )
            )

    try:
        async with PlatformSession() as session:
            async with session.begin():
                tenant = await session.get(Tenant, tenant_id)
                assert tenant is not None
                await session.delete(tenant)
                await session.flush()

        async with PlatformSession() as session:
            for model in (TenantDomain, TenantUser, TenantBranding, TenantAsset):
                left = await session.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(model.tenant_id == tenant_id)
                )
                assert left == 0, f"quedaron {left} filas de {model.__name__}"
            assert (
                await session.scalar(
                    select(func.count()).select_from(Tenant).where(Tenant.id == tenant_id)
                )
                == 0
            )
    finally:
        async with PlatformSession() as session:
            async with session.begin():
                tenant = await session.get(Tenant, tenant_id)
                if tenant is not None:
                    await session.delete(tenant)
