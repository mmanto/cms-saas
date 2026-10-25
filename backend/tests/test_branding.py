"""Tests del branding por club (sin base de datos).

Lo que se cuida: que sin fila (club nuevo) haya defaults utilizables, que lo que
setea el club gane, y que el logo sea el asset ``logo`` (o null si no lo subio).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.api.branding import DEFAULT_PRIMARY_COLOR, branding_payload
from app.models import Tenant, TenantAsset, TenantBranding

STAMP = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _tenant() -> Tenant:
    return Tenant(slug="lasquintas", name="Las Quintas", status="active")


def _branding(**overrides: str) -> TenantBranding:
    row = TenantBranding(tenant_id=uuid.uuid4())
    for key, value in overrides.items():
        setattr(row, key, value)
    return row


def _logo() -> TenantAsset:
    return TenantAsset(
        tenant_id=uuid.uuid4(),
        name="logo",
        object_key="tenants/x/assets/logo.png",
        content_type="image/png",
        size_bytes=10,
        updated_at=STAMP,
    )


def test_club_sin_branding_usa_su_nombre_y_el_color_por_defecto() -> None:
    assert branding_payload(_tenant(), None, None) == {
        "tenant": "lasquintas",
        "status": "active",
        "display_name": "Las Quintas",
        "primary_color": DEFAULT_PRIMARY_COLOR,
        "logo_url": None,
    }


def test_lo_que_setea_el_club_gana() -> None:
    row = _branding(display_name="Las Quintas FC", primary_color="#12b981")

    payload = branding_payload(_tenant(), row, None)

    assert payload["display_name"] == "Las Quintas FC"
    assert payload["primary_color"] == "#12b981"


def test_el_logo_sale_del_asset_logo() -> None:
    payload = branding_payload(_tenant(), None, _logo())

    assert payload["logo_url"] == f"/api/v1/assets/logo?v={int(STAMP.timestamp())}"


def test_sin_asset_logo_no_hay_url() -> None:
    assert branding_payload(_tenant(), _branding(), None)["logo_url"] is None
