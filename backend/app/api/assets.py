"""Assets por club: cualquier archivo propio, por nombre.

Un asset es el par (club, nombre) -> objeto en el storage bajo
``tenants/<tenant_id>/assets/<nombre>.<ext>``. La fila guarda la referencia; los
bytes viven en el storage.

La ruta no dice de que club es: ``GET /api/v1/assets/logo`` devuelve el logo de
cada club porque el club sale del ``Host``. El frontend pide siempre la misma URL
relativa y no necesita saber de quien es.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select

from app.api.deps import TenantContext, current_tenant_admin, tenant_context
from app.models import TenantAsset
from app.storage import delete_object, get_bytes, object_key, put_bytes

router = APIRouter(prefix="/assets", tags=["assets"])

# El nombre es la clave del club para su archivo: sin barras ni puntos, y sin
# terminar en separador, para que el nombre y la clave del objeto no puedan
# divergir ni queden claves raras.
NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9_-]{0,61}[a-z0-9])?$")

# Formatos aceptados y extension con la que se guarda el objeto.
ASSET_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/svg+xml": "svg",
    "image/x-icon": "ico",
    "image/vnd.microsoft.icon": "ico",
    "application/pdf": "pdf",
}
MAX_ASSET_BYTES = 2 * 1024 * 1024

# El logo del club es un asset con este nombre: lo usa app/api/branding.py.
LOGO_ASSET = "logo"


def clean_name(name: str | None) -> str:
    candidate = (name or "").strip().lower()
    if not NAME_RE.match(candidate):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="nombre invalido: minusculas, numeros, guiones y guion bajo",
        )
    return candidate


def asset_url(asset: TenantAsset) -> str:
    """URL relativa del asset, con la version del archivo para el cache."""
    return f"/api/v1/assets/{asset.name}?v={int(asset.updated_at.timestamp())}"


def asset_payload(asset: TenantAsset) -> dict[str, Any]:
    return {
        "name": asset.name,
        "url": asset_url(asset),
        "content_type": asset.content_type,
        "size_bytes": asset.size_bytes,
        "updated_at": asset.updated_at.isoformat(),
    }


async def _asset(ctx: TenantContext, name: str) -> TenantAsset | None:
    return await ctx.session.get(TenantAsset, {"tenant_id": ctx.tenant.id, "name": name})


@router.get("")
async def list_assets(ctx: TenantContext = Depends(tenant_context)) -> list[dict[str, Any]]:
    """Lo que el club tiene cargado. Publico: son los archivos de su landing."""
    rows = (await ctx.session.scalars(select(TenantAsset).order_by(TenantAsset.name))).all()
    return [asset_payload(row) for row in rows]


@router.get("/{name}")
async def read_asset(name: str, ctx: TenantContext = Depends(tenant_context)) -> Response:
    """Sirve el asset del club del Host. Si no lo subio: 404."""
    asset = await _asset(ctx, clean_name(name))
    if asset is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"el portal no tiene el asset {clean_name(name)!r}",
        )

    data, stored_type = await get_bytes(asset.object_key)
    return Response(
        content=data,
        media_type=asset.content_type or stored_type or "application/octet-stream",
        headers={
            "Cache-Control": "public, max-age=300",
            "ETag": f'"{int(asset.updated_at.timestamp())}"',
        },
    )


@router.put("/{name}", status_code=status.HTTP_201_CREATED)
async def upload_asset(
    name: str,
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(current_tenant_admin),
) -> dict[str, Any]:
    """Alta o reemplazo: subir el mismo nombre pisa el asset anterior."""
    asset_name = clean_name(name)
    content_type = (file.content_type or "").lower()
    extension = ASSET_TYPES.get(content_type)
    if extension is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"formato no soportado: usa {', '.join(sorted(set(ASSET_TYPES)))}",
        )

    data = await file.read(MAX_ASSET_BYTES + 1)
    if len(data) > MAX_ASSET_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"el archivo supera {MAX_ASSET_BYTES // (1024 * 1024)} MB",
        )

    key = object_key(ctx.tenant.id, "assets", f"{asset_name}.{extension}")
    asset = await _asset(ctx, asset_name)
    previous = asset.object_key if asset is not None and asset.object_key != key else None
    if asset is None:
        asset = TenantAsset(tenant_id=ctx.tenant.id, name=asset_name, object_key=key)
        ctx.session.add(asset)

    await put_bytes(key, data, content_type=content_type)
    asset.object_key = key
    asset.content_type = content_type
    asset.size_bytes = len(data)
    asset.updated_at = datetime.now(timezone.utc)
    await ctx.session.flush()

    # Si cambio el formato, la clave vieja queda huerfana: se borra.
    if previous is not None:
        await delete_object(previous)

    return asset_payload(asset)


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_asset(name: str, ctx: TenantContext = Depends(current_tenant_admin)) -> Response:
    asset = await _asset(ctx, clean_name(name))
    if asset is not None:
        key = asset.object_key
        await ctx.session.delete(asset)
        await ctx.session.flush()
        await delete_object(key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
