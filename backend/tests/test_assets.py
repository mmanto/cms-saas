"""Tests de los assets por club (sin base de datos).

Lo que se cuida: que el nombre no pueda apuntar a otro objeto (el nombre es parte
de la clave en el storage), que la URL sea relativa al club del Host y que la
version del archivo viaje en la URL.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.api.assets import (
    ASSET_TYPES,
    LOGO_ASSET,
    MAX_ASSET_BYTES,
    asset_payload,
    asset_url,
    clean_name,
)
from app.models import TenantAsset

STAMP = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _asset(name: str = "logo") -> TenantAsset:
    return TenantAsset(
        tenant_id=uuid.uuid4(),
        name=name,
        object_key=f"tenants/x/assets/{name}.png",
        content_type="image/png",
        size_bytes=1234,
        updated_at=STAMP,
    )


@pytest.mark.parametrize("name", ["logo", "hero-1", "fondo_portada", "a" * 63])
def test_nombres_validos(name: str) -> None:
    """63 es el maximo: es el ancho de la columna."""
    assert clean_name(name) == name


@pytest.mark.parametrize(
    "name",
    ["", "   ", "con espacio", "../logo", "a/b", "logo.png", "-logo", "logo-", "a" * 64],
)
def test_nombres_invalidos(name: str) -> None:
    """Sin barras, puntos ni separadores al borde: el nombre va en la clave del
    objeto y no queremos que un nombre raro apunte a otro objeto."""
    with pytest.raises(HTTPException) as error:
        clean_name(name)
    assert error.value.status_code == 400


def test_el_nombre_se_normaliza_a_minusculas() -> None:
    assert clean_name("  Logo  ") == "logo"


def test_la_url_es_relativa_al_club_y_lleva_la_version() -> None:
    url = asset_url(_asset())

    assert url == f"/api/v1/assets/logo?v={int(STAMP.timestamp())}"
    assert url.startswith("/api/v1/assets/")


def test_el_payload_expone_lo_que_necesita_el_frontend() -> None:
    payload = asset_payload(_asset("hero"))

    assert payload["name"] == "hero"
    assert payload["content_type"] == "image/png"
    assert payload["size_bytes"] == 1234
    assert payload["url"].startswith("/api/v1/assets/hero?v=")
    assert payload["updated_at"] == STAMP.isoformat()


def test_el_logo_del_branding_es_un_asset_con_nombre_fijo() -> None:
    assert LOGO_ASSET == "logo"
    assert ASSET_TYPES["image/svg+xml"] == "svg"
    assert ASSET_TYPES["image/x-icon"] == "ico"
    assert MAX_ASSET_BYTES == 2 * 1024 * 1024
