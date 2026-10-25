"""Tests de cifrado de credenciales por tenant (sin base de datos)."""

from __future__ import annotations

import pytest
from cryptography.fernet import InvalidToken

from app.crypto import decrypt_payload, encrypt_payload, mask


def test_roundtrip() -> None:
    payload = {"cuit": "30123456789", "certificate_password": "secreto"}
    token = encrypt_payload(payload)
    assert "secreto" not in token
    assert decrypt_payload(token) == payload


def test_cifrado_no_revela_el_texto_plano() -> None:
    payload = {"cuit": "30123456789", "certificate_password": "secreto-distintivo-42"}
    token = encrypt_payload(payload)
    assert "secreto-distintivo-42" not in token
    assert decrypt_payload(token) == payload


def test_contenidos_distintos_dan_tokens_distintos() -> None:
    assert encrypt_payload({"a": "1"}) != encrypt_payload({"a": "2"})


def test_token_ajeno_falla() -> None:
    with pytest.raises(InvalidToken):
        decrypt_payload("gAAAAABm0000000000000000000000000000000000000000")


@pytest.mark.parametrize(
    ("value", "expected"),
    [("123456789", "1234...6789"), ("12345678", "********"), ("corto", "********")],
)
def test_mask(value: str, expected: str) -> None:
    assert mask(value) == expected
