"""Tests unitarios: resolucion de host -> tenant (sin base de datos)."""

from __future__ import annotations

import pytest

from app.tenancy import RESERVED_LABELS, normalize_host, reserved_label, tenant_slug_from_host

BASE = "openpadel.app"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Club-A.Openpadel.app", "club-a.openpadel.app"),
        ("club-a.openpadel.app:443", "club-a.openpadel.app"),
        ("club-a.openpadel.app.", "club-a.openpadel.app"),
        ("  CLUB-A.OPENPADEL.APP  ", "club-a.openpadel.app"),
        ("[::1]:8080", "::1"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_host(raw: str | None, expected: str) -> None:
    assert normalize_host(raw) == expected


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("club-a.openpadel.app", "club-a"),
        ("club-a.openpadel.app:443", "club-a"),
        ("openpadel.app", None),
        ("a.b.openpadel.app", None),
        ("club.openpadel.app.evil.com", None),
        ("otrodominio.com", None),
        ("", None),
    ],
)
def test_tenant_slug_from_host(host: str, expected: str | None) -> None:
    assert tenant_slug_from_host(normalize_host(host), BASE) == expected


@pytest.mark.parametrize("label", RESERVED_LABELS)
def test_los_labels_reservados_no_son_clubes(label: str) -> None:
    """`admin.<base>` es el backoffice y el resto esta guardado por la plataforma."""
    host = f"{label}.{BASE}"
    assert tenant_slug_from_host(host, BASE) is None
    assert reserved_label(host, BASE) == label


def test_el_admin_host_no_es_un_club_pero_un_club_parecido_si() -> None:
    """Solo el label exacto queda reservado: `admin-club` es un club normal."""
    assert tenant_slug_from_host(f"admin.{BASE}", BASE) is None
    assert tenant_slug_from_host(f"admin-club.{BASE}", BASE) == "admin-club"
    assert reserved_label(f"admin-club.{BASE}", BASE) is None
