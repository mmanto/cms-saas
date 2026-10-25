"""Rutas de Traefik manejadas por la aplicacion (provider ``file``).

Traefik lee ``<TRAEFIK_DYNAMIC_DIR>/routes.yml`` y recarga solo al detectar el
cambio. Ese archivo tiene:

* los routers del dominio base: el apex (la landing), ``admin.<base>`` (el
  backoffice de plataforma) y el wildcard de los clubes (estaticos);
* un par de routers por **dominio propio** de cada club.

Los subdominios ``<slug>.<base>`` NO generan reglas: los cubre el router
wildcard. Solo los dominios propios y el host del backoffice necesitan entrada
explicita, asi que un club nuevo no reescribe nada.

Cada router ademas anuncia el club en un header (``TENANT_HEADER``): el frontend
lo lee del request en vez de preguntar de quien es el host. Los que no son de un
club (apex, wildcard y ``admin.<base>``) lo VACIAN, asi un cliente no puede
declararse otro club con un header propio.

Escribe JSON a proposito: es YAML valido, asi que el provider file lo parsea sin
sumar PyYAML como dependencia. La extension tiene que ser ``.yml``: el provider
file de Traefik ignora los ``.json`` (con el nombre viejo no aplicaba NADA: ni
routers, ni TLS, ni middlewares).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tenant, TenantDomain
from app.settings import get_settings
from app.tenancy import ADMIN_LABEL, normalize_host, reserved_label, tenant_slug_from_host

WEB_SERVICE = "nextjs@docker"
API_SERVICE = "fastapi@docker"
API_PREFIX = "/api"

ROUTES_FILENAME = "routes.yml"

# El club viaja al frontend en este header y lo pone siempre el borde: los
# routers de dominio propio lo setean con el slug del club y los del dominio
# base lo vacian, asi que un cliente no puede declararse otro club con un header
# propio. El frontend lo lee del request: no le pregunta el club a nadie.
TENANT_HEADER = "X-Saas-Tenant"

# Prioridades. Un request a /api/x matchea varios routers a la vez: gana el de
# numero mas alto, asi el router de API siempre le pasa por encima al de web.
PRIORITY_DOCKER_FALLBACK_API = 100
PRIORITY_WILDCARD_WEB = 100
PRIORITY_WILDCARD_API = 200
PRIORITY_CUSTOM_WEB = 150
PRIORITY_CUSTOM_API = 250
# `admin.<base>` tambien matchea el wildcard (y podria matchearlo el router de un
# dominio propio que un club registre con ese host), asi que va arriba de todo:
# el backoffice solo existe en su host.
PRIORITY_ADMIN_WEB = 300
PRIORITY_ADMIN_API = 400


def entrypoints() -> list[str]:
    raw = get_settings().traefik_entrypoints
    return [item.strip() for item in raw.split(",") if item.strip()] or ["web"]


def _tls(*, issue_cert: bool = False, wildcard: bool = False) -> dict[str, Any]:
    settings = get_settings()
    resolver = settings.traefik_cert_resolver.strip()
    if not resolver:
        # Desarrollo sin ACME: los routers quedan solo en el entrypoint HTTP.
        return {}
    if wildcard:
        base = normalize_host(settings.saas_base_domain)
        return {"certResolver": resolver, "domains": {"main": base, "sans": [f"*.{base}"]}}
    if issue_cert:
        return {"certResolver": resolver}
    # Sin resolver propio: Traefik sirve el certificado wildcard del store.
    return {}


def _router(
    *,
    rule: str,
    service: str,
    priority: int,
    tls: dict[str, Any],
    middlewares: list[str] | None = None,
) -> dict[str, Any]:
    router: dict[str, Any] = {
        "rule": rule,
        "service": service,
        "priority": priority,
        "entryPoints": entrypoints(),
    }
    if middlewares:
        router["middlewares"] = middlewares
    if tls:
        router["tls"] = tls
    return router


def build_dynamic_config(custom_domains: list[tuple[str, str]]) -> dict[str, Any]:
    """``custom_domains``: pares (host, slug) de los dominios propios.

    Cada router anuncia el club en ``TENANT_HEADER``: los de dominio propio con
    su slug, los que no son de un club (apex, wildcard y ``admin.<base>``) vacio
    (asi tapan cualquier header que invente el cliente). El frontend lee ese
    valor del request. El frontend espeja los labels reservados en
    ``lib/tenant.ts``.
    """
    base = normalize_host(get_settings().saas_base_domain)
    routers: dict[str, Any] = {}
    middlewares: dict[str, Any] = {}

    def add_router(
        name: str, *, rule: str, service: str, priority: int, tls: dict[str, Any], slug: str
    ) -> None:
        middleware = f"{name}-tenant"
        middlewares[middleware] = {"headers": {"customRequestHeaders": {TENANT_HEADER: slug}}}
        routers[name] = _router(
            rule=rule,
            service=service,
            priority=priority,
            tls=tls,
            middlewares=[middleware],
        )

    if base:
        add_router(
            "saas-apex-web",
            rule=f"Host(`{base}`)",
            service=WEB_SERVICE,
            priority=PRIORITY_WILDCARD_WEB,
            tls=_tls(wildcard=True),
            slug="",
        )
        add_router(
            "saas-apex-api",
            rule=f"Host(`{base}`) && PathPrefix(`{API_PREFIX}`)",
            service=API_SERVICE,
            priority=PRIORITY_WILDCARD_API,
            tls=_tls(),
            slug="",
        )
        # El backoffice vive en su propio host: `admin` es un label reservado,
        # asi que ningun club puede resolver como ese club (ver
        # `app/tenancy.py`), y estos routers le ganan al wildcard.
        admin_host = f"{ADMIN_LABEL}.{base}"
        add_router(
            "saas-admin-web",
            rule=f"Host(`{admin_host}`)",
            service=WEB_SERVICE,
            priority=PRIORITY_ADMIN_WEB,
            tls=_tls(),
            slug="",
        )
        add_router(
            "saas-admin-api",
            rule=f"Host(`{admin_host}`) && PathPrefix(`{API_PREFIX}`)",
            service=API_SERVICE,
            priority=PRIORITY_ADMIN_API,
            tls=_tls(),
            slug="",
        )
        # Un unico router wildcard atiende a todos los clubes: no hay que
        # registrar nada al dar de alta un subdominio. El club lo saca el
        # frontend del propio Host.
        add_router(
            "saas-wildcard-web",
            rule=f"Host(`*.{base}`)",
            service=WEB_SERVICE,
            priority=PRIORITY_WILDCARD_WEB,
            tls=_tls(),
            slug="",
        )
        add_router(
            "saas-wildcard-api",
            rule=f"Host(`*.{base}`) && PathPrefix(`{API_PREFIX}`)",
            service=API_SERVICE,
            priority=PRIORITY_WILDCARD_API,
            tls=_tls(),
            slug="",
        )

    for host, slug in custom_domains:
        label = host.replace(".", "-")
        add_router(
            f"tenant-{slug}-{label}-web",
            rule=f"Host(`{host}`)",
            service=WEB_SERVICE,
            priority=PRIORITY_CUSTOM_WEB,
            tls=_tls(issue_cert=True),
            slug=slug,
        )
        add_router(
            f"tenant-{slug}-{label}-api",
            rule=f"Host(`{host}`) && PathPrefix(`{API_PREFIX}`)",
            service=API_SERVICE,
            priority=PRIORITY_CUSTOM_API,
            tls=_tls(issue_cert=True),
            slug=slug,
        )

    return {"http": {"routers": routers, "middlewares": middlewares}}


def write_dynamic_config(document: dict[str, Any]) -> Path:
    directory = Path(get_settings().traefik_dynamic_dir)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / ROUTES_FILENAME
    payload = json.dumps(document, indent=2, sort_keys=True) + "\n"

    # Escritura atomica: Traefik vigila el archivo, nunca debe leerlo a medias.
    handle, tmp_name = tempfile.mkstemp(dir=directory, prefix=".routes-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as tmp:
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, target)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return target


async def collect_custom_domains(session: AsyncSession) -> list[tuple[str, str]]:
    base = normalize_host(get_settings().saas_base_domain)
    rows = (
        await session.execute(
            select(TenantDomain.host, Tenant.slug)
            .join(Tenant, Tenant.id == TenantDomain.tenant_id)
            .where(Tenant.status == "active")
            .order_by(TenantDomain.host)
        )
    ).all()

    custom: list[tuple[str, str]] = []
    seen: set[str] = set()
    for host, slug in rows:
        host = normalize_host(host)
        if not host or host == base or host in seen:
            continue
        if tenant_slug_from_host(host, base) == slug:
            continue  # lo cubre el router wildcard
        if reserved_label(host, base) is not None:
            continue  # host de la plataforma (admin.<base>), nunca de un club
        seen.add(host)
        custom.append((host, slug))
    return custom


async def sync_tenant_routes(session: AsyncSession) -> int:
    """Reescribe routes.yml a partir de la base. Devuelve los dominios propios."""
    custom = await collect_custom_domains(session)
    write_dynamic_config(build_dynamic_config(custom))
    return len(custom)
