"""Tests del config dinamico de Traefik (sin base de datos).

Lo que se cuida aca es el club que anuncia cada router: los del dominio base
tienen que VACIAR el header para que un cliente no pueda declararse otro club, y
los de dominio propio tienen que anunciar su slug.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.provisioning import TENANT_HEADER, build_dynamic_config


def tenant_announced(document: dict[str, Any], router: str) -> str:
    """Valor que deja el middleware de ese router en ``TENANT_HEADER``."""
    names = document["http"]["routers"][router]["middlewares"]
    assert len(names) == 1, "cada router tiene que anunciar el club una sola vez"
    middleware = document["http"]["middlewares"][names[0]]
    return middleware["headers"]["customRequestHeaders"][TENANT_HEADER]


def test_dominio_propio_anuncia_su_club() -> None:
    document = build_dynamic_config([("clubnorte.com.ar", "norte")])
    web = "tenant-norte-clubnorte-com-ar-web"
    api = "tenant-norte-clubnorte-com-ar-api"

    assert document["http"]["routers"][web]["rule"] == "Host(`clubnorte.com.ar`)"
    assert tenant_announced(document, web) == "norte"
    assert tenant_announced(document, api) == "norte"


def test_routers_del_dominio_base_tapan_el_header_del_cliente() -> None:
    document = build_dynamic_config([])
    base_routers = sorted(name for name in document["http"]["routers"] if name.startswith("saas-"))

    assert base_routers == [
        "saas-admin-api",
        "saas-admin-web",
        "saas-apex-api",
        "saas-apex-web",
        "saas-wildcard-api",
        "saas-wildcard-web",
    ]
    for router in base_routers:
        assert tenant_announced(document, router) == ""


def test_el_host_del_backoffice_le_gana_al_wildcard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`admin.<base>` tambien matchea el wildcard: sus routers van arriba."""

    class Settings:
        saas_base_domain = "openpadel.app"
        traefik_cert_resolver = ""
        traefik_entrypoints = "web"

    monkeypatch.setattr("app.provisioning.get_settings", Settings)
    document = build_dynamic_config([])
    routers = document["http"]["routers"]

    assert routers["saas-admin-web"]["rule"] == "Host(`admin.openpadel.app`)"
    assert routers["saas-admin-web"]["priority"] > routers["saas-wildcard-web"]["priority"]
    assert routers["saas-admin-api"]["priority"] > routers["saas-wildcard-api"]["priority"]
    assert tenant_announced(document, "saas-admin-web") == ""
    assert tenant_announced(document, "saas-admin-api") == ""


def test_sin_dominio_base_solo_quedan_los_dominios_propios(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Settings:
        saas_base_domain = ""
        traefik_cert_resolver = ""
        traefik_entrypoints = "web"

    monkeypatch.setattr("app.provisioning.get_settings", Settings)
    document = build_dynamic_config([("clubnorte.com.ar", "norte")])

    assert "saas-wildcard-web" not in document["http"]["routers"]
    assert tenant_announced(document, "tenant-norte-clubnorte-com-ar-web") == "norte"
