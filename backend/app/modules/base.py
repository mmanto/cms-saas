"""Contrato de un modulo conectable (plugin).

Un modulo agrega funcionalidad propia a todos los clubes, pero **se enciende por
club**: ``tenant_modules`` guarda el switch. El modulo aporta su router (se monta
bajo ``/api/v1``) y, opcionalmente, un hook de instalacion que corre la primera
vez que se habilita para un club.

Regla de aislamiento: el modulo NO sabe de que club es el request. Recibe el
``TenantContext`` resuelto por el borde y deja que RLS filtre; el switch se
consulta con el mismo ``tenant_id`` del contexto.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

# Hook de instalacion: recibe una sesion cross-tenant (la de plataforma, cuando
# el alta la hace el backoffice) o la del club. Tiene que ser idempotente.
InstallHook = Callable[[AsyncSession, uuid.UUID], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class Module:
    """Un plugin instalado en el codigo.

    ``name`` es la clave estable que se guarda en ``tenant_modules`` y viaja en la
    API; no se renombra sin migracion. ``router`` se monta bajo ``/api/v1``.
    """

    name: str
    title: str
    description: str
    router: APIRouter
    on_enable: InstallHook | None = None
