"""Estado del switch ``tenant_modules`` por club.

La fila ausente significa **apagado**: el modulo se habilita explicitamente (el
backoffice crea la fila). Asi un club nuevo no hereda funcionalidad que no pidio.

``is_enabled``/``enabled_names`` corren con la sesion del club (RLS activo):
pasar un ``tenant_id`` distinto del fijado en la transaccion devuelve vacio, no
las filas del otro club. ``set_row`` escribe con la sesion que le den; la usa el
provisioning de plataforma (BYPASSRLS).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TenantModule


async def is_enabled(session: AsyncSession, tenant_id: uuid.UUID, name: str) -> bool:
    row = await session.get(TenantModule, {"tenant_id": tenant_id, "name": name})
    return bool(row is not None and row.enabled)


async def enabled_names(session: AsyncSession, tenant_id: uuid.UUID) -> list[str]:
    rows = await session.scalars(
        select(TenantModule.name)
        .where(TenantModule.tenant_id == tenant_id, TenantModule.enabled.is_(True))
        .order_by(TenantModule.name)
    )
    return list(rows)


async def set_row(
    session: AsyncSession, tenant_id: uuid.UUID, name: str, enabled: bool
) -> bool:
    """Upsert del switch. Devuelve el estado efectivo."""
    row = await session.get(TenantModule, {"tenant_id": tenant_id, "name": name})
    if row is None:
        row = TenantModule(tenant_id=tenant_id, name=name, enabled=enabled)
        session.add(row)
    else:
        row.enabled = enabled
    await session.flush()
    return row.enabled
