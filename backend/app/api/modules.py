"""Modulos habilitados en el club del request.

Publico: el frontend del club lo usa para decidir que secciones pintar (hoy la
landing consulta el modulo ``articles``). Solo lista los habilitados: un modulo
apagado no existe para ese club.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import TenantContext, tenant_context
from app.modules.registry import enabled_modules

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("")
async def list_enabled_modules(
    ctx: TenantContext = Depends(tenant_context),
) -> list[dict[str, Any]]:
    return await enabled_modules(ctx.session, ctx.tenant.id)
