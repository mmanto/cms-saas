"""Dependencias: contexto de tenant, sesion de plataforma y autenticacion."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AppSession, PlatformSession
from app.models import PlatformUser, Tenant, TenantUser
from app.security import decode_token
from app.settings import get_settings
from app.tenancy import bind_tenant, normalize_host, resolve_tenant


@dataclass(slots=True)
class TenantContext:
    tenant: Tenant
    session: AsyncSession
    host: str
    user: TenantUser | None = None


@dataclass(slots=True)
class PlatformContext:
    """Sesion cross-tenant (BYPASSRLS) + el admin de plataforma que la pidio."""

    session: AsyncSession
    user: PlatformUser


async def get_platform_session() -> AsyncIterator[AsyncSession]:
    """Sesion con BYPASSRLS. Solo para el router de plataforma.

    El ``session.begin()`` es lo que commitea: sin el, SQLAlchemy cierra la
    sesion y hace rollback silencioso de todas las escrituras del endpoint.
    """
    async with PlatformSession() as session:
        async with session.begin():
            yield session


def _request_host(request: Request) -> str:
    settings = get_settings()
    explicit = request.headers.get("x-saas-host")
    # El override existe para el SSR. En desarrollo, para pegarle al contenedor
    # sin pasar por Traefik; en cualquier entorno, para las rutas internas (fuera
    # de /api, que el borde NO enruta: solo /api llega a FastAPI desde afuera).
    # En /api manda unicamente el Host real: el navegador no puede declararse otro
    # club con un header propio.
    internal = not request.url.path.startswith("/api")
    if explicit and (settings.environment == "development" or internal):
        return explicit
    return request.headers.get("host", "")


async def tenant_context(request: Request) -> AsyncIterator[TenantContext]:
    """Resuelve el club desde el Host y fija la transaccion en ese tenant.

    Un solo ``session.begin()`` por request: todo lo que corra adentro ve
    exactamente las filas de ese club, y el GUC se descarta al commitear.
    """
    settings = get_settings()
    host = _request_host(request)

    async with AppSession() as session:
        async with session.begin():
            tenant = await resolve_tenant(session, host, settings.saas_base_domain)
            if tenant is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    detail=f"no hay ningun club configurado para el host {normalize_host(host)!r}",
                )
            if tenant.status != "active":
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, detail="el club esta inactivo"
                )
            await bind_tenant(session, tenant.id)
            yield TenantContext(tenant=tenant, session=session, host=normalize_host(host))


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="falta el token Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization.split(" ", 1)[1].strip()


def _claims(authorization: str | None) -> dict:
    try:
        return decode_token(_bearer(authorization))
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="token invalido") from exc


async def current_tenant_user(
    ctx: TenantContext = Depends(tenant_context),
    authorization: str | None = Header(default=None),
) -> TenantContext:
    """Autentica al usuario del club y valida que el token sea de ESE club."""
    claims = _claims(authorization)
    if claims.get("scope") != "tenant":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="el token no es de club")
    if claims.get("tid") != str(ctx.tenant.id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="el token pertenece a otro club",
        )
    user = await ctx.session.get(TenantUser, uuid.UUID(claims["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="usuario inexistente")
    ctx.user = user
    return ctx


async def current_tenant_admin(ctx: TenantContext = Depends(current_tenant_user)) -> TenantContext:
    """Como ``current_tenant_user``, pero exige rol ``admin`` del club."""
    if ctx.user is None or ctx.user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="hace falta rol admin del club")
    return ctx


async def current_platform_user(
    session: AsyncSession = Depends(get_platform_session),
    authorization: str | None = Header(default=None),
) -> PlatformContext:
    """Autentica al admin de plataforma y devuelve sesion (BYPASSRLS) + usuario."""
    claims = _claims(authorization)
    if claims.get("scope") != "platform":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="el token no es de plataforma")
    user = await session.get(PlatformUser, uuid.UUID(claims["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="usuario inexistente")
    return PlatformContext(session=session, user=user)
