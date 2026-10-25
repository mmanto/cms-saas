"""Registro de modulos conectables.

``MODULES`` es el punto de instalacion: cada plugin agrega su entrada aca y el
nucleo lo monta bajo ``/api/v1`` (ver ``app/main.py``). Un modulo sin fila
habilitada en ``tenant_modules`` no atiende requests **y** no aparece en
``GET /api/v1/modules``.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TenantModule
from app.modules import articles as articles_plugin
from app.modules.base import Module
from app.modules.state import set_row

MODULES: dict[str, Module] = {module.name: module for module in (articles_plugin.module,)}


def get_module(name: str) -> Module:
    module = MODULES.get(name)
    if module is None:
        raise KeyError(name)
    return module


def catalog() -> list[dict[str, Any]]:
    """Todos los modulos que existen en el codigo (habilitados o no)."""
    return [
        {"name": module.name, "title": module.title, "description": module.description}
        for module in sorted(MODULES.values(), key=lambda item: item.name)
    ]


async def modules_for_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> list[dict[str, Any]]:
    """Catalogo + switch de ese club. Lo usa el backoffice de plataforma."""
    rows = (
        await session.scalars(
            select(TenantModule).where(TenantModule.tenant_id == tenant_id)
        )
    ).all()
    state = {row.name: row.enabled for row in rows}
    return [
        {**entry, "enabled": state.get(entry["name"], False)} for entry in catalog()
    ]


async def enabled_modules(session: AsyncSession, tenant_id: uuid.UUID) -> list[dict[str, Any]]:
    """Lo que el club tiene prendido: es lo que el frontend consulta."""
    enabled = [entry for entry in await modules_for_tenant(session, tenant_id) if entry["enabled"]]
    return enabled


async def set_enabled(
    session: AsyncSession, tenant_id: uuid.UUID, name: str, enabled: bool
) -> bool:
    """Upsert del switch. Al habilitar corre el hook de instalacion del plugin.

    La sesion la elige quien llama: el backoffice usa la de plataforma
    (BYPASSRLS) porque opera cross-tenant. El hook debe ser idempotente: aca se
    ejecuta en cada ``enabled=true``, no solo en el primero.
    """
    module = get_module(name)
    effective = await set_row(session, tenant_id, name, enabled)
    if effective and module.on_enable is not None:
        await module.on_enable(session, tenant_id)
    return effective
