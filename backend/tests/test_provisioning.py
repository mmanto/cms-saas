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


def test_el_wildcard_pide_un_certificado_con_su_san(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """El provider file espera ``domains`` como LISTA de bloques {main, sans}.

    Con un objeto plano Traefik no pide ningun dominio ("no domain was given"):
    el wildcard nunca se emite y todo queda con el certificado default.
    """

    class Settings:
        saas_base_domain = "openpadel.app"
        traefik_cert_resolver = "letsencrypt"
        traefik_entrypoints = "web,websecure"

    monkeypatch.setattr("app.provisioning.get_settings", Settings)
    document = build_dynamic_config([])
    routers = document["http"]["routers"]

    tls = routers["saas-apex-web"]["tls"]
    assert tls["certResolver"] == "letsencrypt"
    assert tls["domains"] == [{"main": "openpadel.app", "sans": ["*.openpadel.app"]}]


def test_admin_y_wildcard_habilitan_tls_con_el_certificado_del_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sin `tls: {}` el router no atiende el entrypoint 443: 404 en HTTPS."""

    class Settings:
        saas_base_domain = "openpadel.app"
        traefik_cert_resolver = "letsencrypt"
        traefik_entrypoints = "web,websecure"

    monkeypatch.setattr("app.provisioning.get_settings", Settings)
    document = build_dynamic_config([("clubnorte.com.ar", "norte")])
    routers = document["http"]["routers"]
    assert routers["saas-admin-web"]["tls"] == {}
    assert routers["saas-admin-api"]["tls"] == {}
    assert routers["saas-wildcard-web"]["tls"] == {}
    assert routers["saas-wildcard-api"]["tls"] == {}

    # El club de un dominio propio pide su propio certificado (una lista no:
    # Traefik lo saca de la regla Host).
    custom = routers["tenant-norte-clubnorte-com-ar-web"]["tls"]
    assert custom == {"certResolver": "letsencrypt"}


def test_sin_resolver_los_routers_quedan_solo_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """En desarrollo no hay 443: ningun router debe declarar TLS."""

    class Settings:
        saas_base_domain = "cms-sas.localhost"
        traefik_cert_resolver = ""
        traefik_entrypoints = "web"

    monkeypatch.setattr("app.provisioning.get_settings", Settings)
    document = build_dynamic_config([])

    for router in document["http"]["routers"].values():
        assert "tls" not in router


def test_el_dominio_base_puede_ser_un_portal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Con SAAS_BASE_TENANT el apex anuncia ese club; admin y wildcard siguen vacios."""

    class Settings:
        saas_base_domain = "elatech.io"
        saas_base_tenant = "elatech"
        traefik_cert_resolver = ""
        traefik_entrypoints = "web"

    monkeypatch.setattr("app.provisioning.get_settings", Settings)
    document = build_dynamic_config([])

    assert tenant_announced(document, "saas-apex-web") == "elatech"
    assert tenant_announced(document, "saas-apex-api") == "elatech"
    assert tenant_announced(document, "saas-admin-web") == ""
    assert tenant_announced(document, "saas-admin-api") == ""
    assert tenant_announced(document, "saas-wildcard-web") == ""
    assert tenant_announced(document, "saas-wildcard-api") == ""

