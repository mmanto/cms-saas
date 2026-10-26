"""Resolucion de tenant y binding de RLS.

El tenant se resuelve por ``Host``:

1. coincidencia exacta en ``tenant_domains`` (dominio propio del club);
2. si es un subdominio directo del dominio base, por slug.

Una vez resuelto, se fija ``app.tenant_id`` con ``set_config(..., is_local=true)``
dentro de la transaccion del request. Es local a la transaccion a proposito: al
volver la conexion al pool el valor desaparece, asi que ninguna query puede
quedar ejecutandose con el tenant de otro request.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tenant, TenantDomain
from app.settings import get_settings

TENANT_GUC = "app.tenant_id"


def normalize_host(raw: str | None) -> str:
    """Deja el host en minusculas y sin puerto, punto final ni IPv6 brackets."""
    if not raw:
        return ""
    host = raw.split(",")[0].strip().lower()
    if host.startswith("["):
        host = host.split("]")[0].lstrip("[")
    elif host.count(":") == 1:
        host = host.split(":")[0]
    return host.strip(".")


# Labels del dominio base que NO son clubes: en `<label>.<base>` el label es
# reservado y no se resuelve por slug. `ADMIN_LABEL` tiene ademas sus propios
# routers en el borde (ver `app/provisioning.py`) y el resto de la lista es para
# que ningun club se quede con un host que el dia de mañana haga falta
# (`www`, `api`, `app`). El frontend espeja esta lista en `lib/tenant.ts`.
ADMIN_LABEL = "admin"
RESERVED_LABELS = (ADMIN_LABEL, "www", "api", "app")


def _base_label(host: str, base_domain: str) -> str | None:
    """Label de primer nivel de ``host`` si cuelga directo del dominio base."""
    base = normalize_host(base_domain)
    if not base:
        return None
    suffix = "." + base
    if not host.endswith(suffix):
        return None
    label = host[: -len(suffix)]
    if not label or "." in label:
        return None
    return label


def reserved_label(host: str, base_domain: str) -> str | None:
    """Label reservado si ``host`` es ``<reservado>.<base_domain>``, si no ``None``."""
    label = _base_label(host, base_domain)
    return label if label in RESERVED_LABELS else None


def tenant_slug_from_host(host: str, base_domain: str) -> str | None:
    """Devuelve el slug si ``host`` es ``<slug>.<base_domain>``.

    Un dominio propio, un subdominio anidado (``a.b.base``) o un **label
    reservado** (``admin.base``, ``www.base``, ...) devuelven ``None``: los dos
    primeros se resuelven por la tabla de dominios, el tercero no es de ningun
    club.
    """
    label = _base_label(host, base_domain)
    if label is None or label in RESERVED_LABELS:
        return None
    return label


async def resolve_tenant(
    session: AsyncSession, host: str, base_domain: str
) -> Tenant | None:
    normalized = normalize_host(host)
    if not normalized:
        return None

    # El dominio base puede ser un portal en si mismo (el del gestor). Lo elige
    # el operador con SAAS_BASE_TENANT; si esta vacio, el apex sigue siendo la
    # landing de plataforma.
    base = normalize_host(base_domain)
    if base and normalized == base:
        base_slug = get_settings().saas_base_tenant.strip().lower()
        if base_slug:
            tenant = await session.scalar(select(Tenant).where(Tenant.slug == base_slug))
            if tenant is not None:
                return tenant

    by_domain = await session.scalar(
        select(Tenant)
        .join(TenantDomain, TenantDomain.tenant_id == Tenant.id)
        .where(TenantDomain.host == normalized)
    )
    if by_domain is not None:
        return by_domain

    slug = tenant_slug_from_host(normalized, base_domain)
    if slug is None:
        return None
    return await session.scalar(select(Tenant).where(Tenant.slug == slug))


async def bind_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Fija el tenant de la transaccion en curso. Requiere estar en una."""
    await session.execute(
        text("select set_config(:key, :value, true)"),
        {"key": TENANT_GUC, "value": str(tenant_id)},
    )


async def tenant_row_count(session: AsyncSession, table: str) -> int:
    """Cuenta filas visibles en la transaccion actual (util para verificar RLS)."""
    result = await session.execute(text("select count(*) from " + table))
    return int(result.scalar_one())


async def assert_tenant_binding(session: AsyncSession) -> uuid.UUID:
    """Devuelve el tenant_id con el que esta corriendo la transaccion."""
    value = await session.scalar(text("select current_setting(:key, true)"), {"key": TENANT_GUC})
    if not value:
        raise RuntimeError("la transaccion no tiene tenant fijado (app.tenant_id vacio)")
    return uuid.UUID(value)
