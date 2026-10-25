"""Dependencias que exigen que un modulo este habilitado en el club.

Se apoyan en ``tenant_context``/``current_tenant_admin``, asi que el switch se
consulta dentro de la misma transaccion y con el mismo tenant que la query del
endpoint. Un modulo apagado responde 404: para ese club la ruta no existe.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, status

from app.api.deps import TenantContext, current_tenant_admin, tenant_context
from app.modules.state import is_enabled


def _disabled(name: str) -> HTTPException:
    return HTTPException(
        status.HTTP_404_NOT_FOUND,
        detail=f"el modulo {name} no esta habilitado en este club",
    )


def require_public(name: str) -> Callable[..., Coroutine[Any, Any, TenantContext]]:
    """Ruta publica del modulo (lectura del sitio)."""

    async def dependency(ctx: TenantContext = Depends(tenant_context)) -> TenantContext:
        if not await is_enabled(ctx.session, ctx.tenant.id, name):
            raise _disabled(name)
        return ctx

    return dependency


def require_admin(name: str) -> Callable[..., Coroutine[Any, Any, TenantContext]]:
    """Ruta de gestion del modulo: exige rol admin del club."""

    async def dependency(
        ctx: TenantContext = Depends(current_tenant_admin),
    ) -> TenantContext:
        if not await is_enabled(ctx.session, ctx.tenant.id, name):
            raise _disabled(name)
        return ctx

    return dependency
