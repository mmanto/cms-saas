"""Branding por club: nombre visible, color y logo.

La app es la misma para todos los clubes: lo que cambia es el club que resolvio
Traefik a partir del Host. El club sale SIEMPRE del request, nunca del body ni de
un query param: con RLS activo, un club no puede tocar el branding de otro.

El nombre y el color son una fila de ``tenant_branding``. El logo, en cambio, es
un asset mas (``app/api/assets.py``): el asset ``logo`` del club, servido por
``GET /api/v1/assets/logo``. Misma URL para todos los clubes, contenido distinto.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.assets import LOGO_ASSET, asset_url
from app.api.deps import TenantContext, current_tenant_admin, tenant_context
from app.db import AppSession
from app.models import Tenant, TenantAsset, TenantBranding
from app.settings import get_settings
from app.tenancy import bind_tenant, normalize_host, resolve_tenant

router = APIRouter(prefix="/branding", tags=["branding"])
internal_router = APIRouter(tags=["internal"])

DEFAULT_PRIMARY_COLOR = "#4f7cff"


class BrandingIn(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    primary_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


def branding_payload(
    tenant: Tenant, row: TenantBranding | None, logo: TenantAsset | None
) -> dict[str, Any]:
    """Branding efectivo: lo que seteo el club, con defaults para lo que no.

    El logo es el asset ``logo`` (mismo storage y mismas rutas que cualquier otro
    asset); si el club no lo subio, `logo_url` va en null y la UI usa su default.
    """
    return {
        "tenant": tenant.slug,
        "status": tenant.status,
        "display_name": (row.display_name if row else None) or tenant.name,
        "primary_color": (row.primary_color if row else None) or DEFAULT_PRIMARY_COLOR,
        "logo_url": asset_url(logo) if logo is not None else None,
    }


async def _row(ctx: TenantContext) -> TenantBranding | None:
    return await ctx.session.get(TenantBranding, ctx.tenant.id)


async def _logo(ctx: TenantContext) -> TenantAsset | None:
    """El logo es el asset llamado ``logo``: mismo storage, mismas rutas."""
    return await ctx.session.get(TenantAsset, {"tenant_id": ctx.tenant.id, "name": LOGO_ASSET})


async def _upsert(ctx: TenantContext) -> TenantBranding:
    row = await _row(ctx)
    if row is None:
        row = TenantBranding(tenant_id=ctx.tenant.id)
        ctx.session.add(row)
    return row


@router.get("")
async def read_branding(ctx: TenantContext = Depends(tenant_context)) -> dict[str, Any]:
    """Publico: lo que el navegador del club necesita para pintarse."""
    return branding_payload(ctx.tenant, await _row(ctx), await _logo(ctx))


@router.put("")
async def write_branding(
    payload: BrandingIn,
    ctx: TenantContext = Depends(current_tenant_admin),
) -> dict[str, Any]:
    """Nombre visible y color. Solo el admin del club (RLS + rol).

    El logo no se sube por aca: es el asset ``logo`` (``PUT /api/v1/assets/logo``).
    """
    row = await _upsert(ctx)
    if payload.display_name is not None:
        row.display_name = payload.display_name.strip()
    if payload.primary_color is not None:
        row.primary_color = payload.primary_color.lower()
    await ctx.session.flush()
    return branding_payload(ctx.tenant, row, await _logo(ctx))


@internal_router.get("/tenant-branding")
async def tenant_branding(request: Request) -> dict[str, Any]:
    """El branding que el SSR del frontend necesita antes de renderizar.

    No lleva prefijo /api a proposito: el borde solo enruta /api, asi que este
    endpoint no se alcanza desde afuera y el header ``X-SaaS-Host`` (que el
    navegador no puede mandar) es confiable. Es la unica forma de que el server
    de Next, que no tiene el Host del cliente, diga de que club quiere el
    branding.
    """
    settings = get_settings()
    host = normalize_host(request.headers.get("x-saas-host") or request.headers.get("host", ""))

    async with AppSession() as session:
        async with session.begin():
            tenant = await resolve_tenant(session, host, settings.saas_base_domain)
            if tenant is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    detail=f"no hay ningun portal configurado para el host {host!r}",
                )
            await bind_tenant(session, tenant.id)
            row = await session.get(TenantBranding, tenant.id)
            logo = await session.get(
                TenantAsset, {"tenant_id": tenant.id, "name": LOGO_ASSET}
            )
            return branding_payload(tenant, row, logo)
