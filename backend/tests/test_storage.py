"""Tests del prefijo por tenant en las claves de objeto (sin S3).

Es el invariante que evita que una URL firmada de un club apunte a un objeto de
otro: toda clave pasa por ``object_key``.
"""

from __future__ import annotations

import uuid

import pytest

from app.storage import object_key

TENANT = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTRO = uuid.UUID("22222222-2222-2222-2222-222222222222")


def test_toda_clave_va_prefijada_por_el_club() -> None:
    assert object_key(TENANT, "actas", "2026", "acta.pdf") == (
        "tenants/11111111-1111-1111-1111-111111111111/actas/2026/acta.pdf"
    )


def test_dos_clubes_no_comparten_clave() -> None:
    assert object_key(TENANT, "logo.png") != object_key(OTRO, "logo.png")


@pytest.mark.parametrize("entrada", ["../etc/passwd", "./../x", "a//b", "actas/2026", "  acta.pdf  "])
def test_claves_no_escapan_del_prefijo(entrada: str) -> None:
    key = object_key(TENANT, entrada)
    assert key.startswith(f"tenants/{TENANT}/")
    assert ".." not in key
    assert "//" not in key


@pytest.mark.parametrize("entrada", ["", ".", "..", "/", "///", "./.."])
def test_rechaza_claves_sin_nombre(entrada: str) -> None:
    with pytest.raises(ValueError):
        object_key(TENANT, entrada)
