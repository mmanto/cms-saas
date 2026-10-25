"""Provisioning de la plataforma (cross-tenant).

Todo pasa por el motor ``platform`` (BYPASSRLS). Despues de cada cambio de
dominios se reescribe routes.yml para que Traefik empiece a rutear.
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PlatformContext, current_platform_user, get_platform_session
from app.models import PlatformUser, Tenant, TenantAsset, TenantDomain, TenantUser
from app.modules.registry import get_module, modules_for_tenant, set_enabled
from app.provisioning import sync_tenant_routes
from app.security import create_token, hash_password, verify_password
from app.settings import get_settings
from app.storage import delete_prefix, tenant_prefix
from app.tenancy import RESERVED_LABELS, normalize_host, reserved_label, tenant_slug_from_host

logger = logging.getLogger("platform")

router = APIRouter(prefix="/platform", tags=["platform"])

SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$")


class PlatformLoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)


class TenantIn(BaseModel):
    slug: str = Field(min_length=2, max_length=63)
    name: str = Field(min_length=1, max_length=200)
    admin_email: str = Field(min_length=3, max_length=320)
    admin_password: str = Field(min_length=8, max_length=256)


class DomainIn(BaseModel):
    host: str = Field(min_length=4, max_length=253)


class TenantPatchIn(BaseModel):
    """Edicion parcial de un club. Al menos un campo, o es un no-op disfrazado."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: Literal["active", "suspended"] | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> TenantPatchIn:
        if self.name is None and self.status is None:
            raise ValueError("hay que mandar al menos un campo")
        return self


class TenantUserIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    role: Literal["admin", "member"] = "member"


class TenantUserPatchIn(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=256)
    role: Literal["admin", "member"] | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> TenantUserPatchIn:
        if self.password is None and self.role is None:
            raise ValueError("hay que mandar al menos un campo")
        return self


def _tenant_payload(tenant: Tenant) -> dict:
    """Resumen de un club. ``domains`` es lista de objetos, no de hosts."""
    return {
        "id": str(tenant.id),
        "slug": tenant.slug,
        "name": tenant.name,
        "status": tenant.status,
        "domains": [
            {"host": domain.host, "is_primary": domain.is_primary}
            for domain in tenant.domains
        ],
    }


async def _tenant_or_404(session: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="club inexistente")
    return tenant


def _validate_slug(slug: str) -> str:
    slug = slug.strip().lower()
    if not SLUG_RE.match(slug):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="slug invalido: solo minusculas, numeros y guiones internos",
        )
    if slug in RESERVED_LABELS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"slug reservado: {', '.join(RESERVED_LABELS)} los usa la plataforma",
        )
    return slug


def _validate_host(host: str) -> str:
    host = normalize_host(host)
    if len(host) < 4 or "." not in host or "/" in host:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="host invalido")
    return host


@router.post("/auth/login")
async def platform_login(
    payload: PlatformLoginIn,
    session: AsyncSession = Depends(get_platform_session),
) -> dict:
    email = payload.email.strip().lower()
    user = await session.scalar(select(PlatformUser).where(PlatformUser.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="credenciales invalidas")
    return {
        "access_token": create_token(subject=str(user.id), scope="platform"),
        "token_type": "bearer",
    }


@router.get("/tenants")
async def list_tenants(
    ctx: PlatformContext = Depends(current_platform_user),
) -> list[dict]:
    tenants = (await ctx.session.scalars(select(Tenant).order_by(Tenant.slug))).all()
    return [_tenant_payload(tenant) for tenant in tenants]


@router.post("/tenants", status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantIn,
    ctx: PlatformContext = Depends(current_platform_user),
) -> dict:
    settings = get_settings()
    slug = _validate_slug(body.slug)
    base = normalize_host(settings.saas_base_domain)
    host = f"{slug}.{base}"

    if await ctx.session.scalar(select(Tenant).where(Tenant.slug == slug)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="ya existe un club con ese slug")
    if (
        await ctx.session.scalar(select(TenantDomain).where(TenantDomain.host == host))
        is not None
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"el dominio {host} ya esta en uso")

    tenant = Tenant(slug=slug, name=body.name.strip(), status="active")
    ctx.session.add(tenant)
    await ctx.session.flush()

    ctx.session.add(TenantDomain(tenant_id=tenant.id, host=host, is_primary=True))
    ctx.session.add(
        TenantUser(
            tenant_id=tenant.id,
            email=body.admin_email.strip().lower(),
            password_hash=hash_password(body.admin_password),
            role="admin",
        )
    )
    await ctx.session.flush()
    await sync_tenant_routes(ctx.session)
    await ctx.session.refresh(tenant)

    return _tenant_payload(tenant)


@router.post("/tenants/{tenant_id}/domains", status_code=status.HTTP_201_CREATED)
async def add_domain(
    tenant_id: uuid.UUID,
    body: DomainIn,
    ctx: PlatformContext = Depends(current_platform_user),
) -> dict:
    tenant = await _tenant_or_404(ctx.session, tenant_id)

    host = _validate_host(body.host)
    base = normalize_host(get_settings().saas_base_domain)

    # Los labels reservados del dominio base (admin, www, api, app) no son de
    # ningun club: `api.<base>` no es un club todavia, `admin.<base>` es el
    # backoffice y el dia de mañana api/app pueden ser servicios. No se aceptan
    # ni como dominio propio.
    if reserved_label(host, base) is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"{host} esta reservado por la plataforma",
        )

    # Un subdominio del dominio base tiene que llamarse igual que el slug: la
    # resolucion de esos hosts usa el label como slug.
    label = tenant_slug_from_host(host, base)
    if label is not None and label != tenant.slug:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"{host} deberia ser {tenant.slug}.{base}; para otro nombre usa un dominio propio",
        )

    if (
        await ctx.session.scalar(select(TenantDomain).where(TenantDomain.host == host))
        is not None
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"el dominio {host} ya esta en uso")

    is_primary = label is not None and not tenant.domains
    ctx.session.add(TenantDomain(tenant_id=tenant.id, host=host, is_primary=is_primary))
    await ctx.session.flush()
    await sync_tenant_routes(ctx.session)
    return {"tenant": tenant.slug, "host": host, "custom": label is None}


@router.delete("/tenants/{tenant_id}/domains/{host}")
async def remove_domain(
    tenant_id: uuid.UUID,
    host: str,
    ctx: PlatformContext = Depends(current_platform_user),
) -> dict:
    normalized = normalize_host(host)
    domain = await ctx.session.scalar(
        select(TenantDomain).where(
            TenantDomain.tenant_id == tenant_id, TenantDomain.host == normalized
        )
    )
    if domain is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="dominio inexistente")
    if domain.is_primary:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="no se puede borrar el dominio primario del club",
        )
    await ctx.session.delete(domain)
    await ctx.session.flush()
    await sync_tenant_routes(ctx.session)
    return {"removed": normalized}


@router.get("/me")
async def platform_me(
    ctx: PlatformContext = Depends(current_platform_user),
) -> dict:
    """Quien es el admin de plataforma de esta sesion."""
    return {
        "id": str(ctx.user.id),
        "email": ctx.user.email,
        "created_at": ctx.user.created_at.isoformat(),
    }


@router.get("/tenants/{tenant_id}")
async def tenant_detail(
    tenant_id: uuid.UUID,
    ctx: PlatformContext = Depends(current_platform_user),
) -> dict:
    """Ficha completa del club: datos, dominios, usuarios y cuantos assets tiene."""
    tenant = await _tenant_or_404(ctx.session, tenant_id)
    users = (
        await ctx.session.scalars(
            select(TenantUser)
            .where(TenantUser.tenant_id == tenant_id)
            .order_by(TenantUser.email)
        )
    ).all()
    assets = await ctx.session.scalar(
        select(func.count())
        .select_from(TenantAsset)
        .where(TenantAsset.tenant_id == tenant_id)
    )
    return {
        **_tenant_payload(tenant),
        "created_at": tenant.created_at.isoformat(),
        "users": [
            {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
            }
            for user in users
        ],
        "assets": int(assets or 0),
        "modules": await modules_for_tenant(ctx.session, tenant.id),
    }


@router.patch("/tenants/{tenant_id}")
async def patch_tenant(
    tenant_id: uuid.UUID,
    body: TenantPatchIn,
    ctx: PlatformContext = Depends(current_platform_user),
) -> dict:
    """Nombre y estado. Suspender un club no cambia el ruteo: la API ya lo 403ea."""
    tenant = await _tenant_or_404(ctx.session, tenant_id)
    if body.name is not None:
        tenant.name = body.name.strip()
    if body.status is not None:
        tenant.status = body.status
    await ctx.session.flush()
    return _tenant_payload(tenant)


@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: uuid.UUID,
    ctx: PlatformContext = Depends(current_platform_user),
) -> Response:
    """Baja del club: filas por CASCADE, objetos del storage y routes.yml.

    Si el storage falla, la baja igual sale: el club ya no existe en la base y
    a lo sumo quedan objetos huerfanos bajo ``tenants/<id>/``.
    """
    tenant = await _tenant_or_404(ctx.session, tenant_id)
    prefix = tenant_prefix(tenant.id)
    slug = tenant.slug
    await ctx.session.delete(tenant)
    await ctx.session.flush()
    await sync_tenant_routes(ctx.session)
    try:
        await delete_prefix(prefix)
    except Exception as exc:  # noqa: BLE001 - el club ya no existe
        logger.warning("no pude borrar los objetos de %s: %s", slug, exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/tenants/{tenant_id}/users", status_code=status.HTTP_201_CREATED)
async def create_tenant_user(
    tenant_id: uuid.UUID,
    body: TenantUserIn,
    ctx: PlatformContext = Depends(current_platform_user),
) -> dict:
    """Alta de un usuario del club con la password ya hasheada."""
    tenant = await _tenant_or_404(ctx.session, tenant_id)
    email = body.email.strip().lower()
    existing = await ctx.session.scalar(
        select(TenantUser).where(
            TenantUser.tenant_id == tenant.id, TenantUser.email == email
        )
    )
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=f"{email} ya existe en {tenant.slug}"
        )
    user = TenantUser(
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    ctx.session.add(user)
    await ctx.session.flush()
    return {"id": str(user.id), "email": user.email, "role": user.role}


@router.patch("/tenants/{tenant_id}/users/{user_id}")
async def patch_tenant_user(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    body: TenantUserPatchIn,
    ctx: PlatformContext = Depends(current_platform_user),
) -> dict:
    """Reset de password y/o cambio de rol. El usuario se busca dentro del club."""
    user = await ctx.session.scalar(
        select(TenantUser).where(
            TenantUser.id == user_id, TenantUser.tenant_id == tenant_id
        )
    )
    if user is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="usuario inexistente en ese club"
        )
    if body.password is not None:
        user.password_hash = hash_password(body.password)
    if body.role is not None:
        user.role = body.role
    await ctx.session.flush()
    return {"id": str(user.id), "email": user.email, "role": user.role}


class ModuleToggleIn(BaseModel):
    enabled: bool


@router.get("/tenants/{tenant_id}/modules")
async def list_tenant_modules(
    tenant_id: uuid.UUID,
    ctx: PlatformContext = Depends(current_platform_user),
) -> list[dict]:
    """Catalogo de modulos con el switch de ese club."""
    tenant = await _tenant_or_404(ctx.session, tenant_id)
    return await modules_for_tenant(ctx.session, tenant.id)


@router.put("/tenants/{tenant_id}/modules/{name}")
async def toggle_tenant_module(
    tenant_id: uuid.UUID,
    name: str,
    body: ModuleToggleIn,
    ctx: PlatformContext = Depends(current_platform_user),
) -> dict:
    """Enciende/apaga un modulo. Al encender corre el hook de instalacion."""
    tenant = await _tenant_or_404(ctx.session, tenant_id)
    try:
        get_module(name)
    except KeyError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"modulo desconocido: {name}"
        ) from None
    effective = await set_enabled(ctx.session, tenant.id, name, body.enabled)
    return {"name": name, "enabled": effective}


@router.post("/routes/sync")
async def routes_sync(
    ctx: PlatformContext = Depends(current_platform_user),
) -> dict:
    custom = await sync_tenant_routes(ctx.session)
    return {"custom_domains": custom}
