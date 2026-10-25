"""Cifrado de credenciales por tenant (Fernet / AES-128-CBC + HMAC).

La clave vive en ``CREDENTIALS_KEY``. Rotarla implica re-cifrar: guarda la
version vieja, descifra todo y volve a cifrar.
"""

from __future__ import annotations

import json
from functools import lru_cache

from cryptography.fernet import Fernet

from app.settings import get_settings


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    return Fernet(get_settings().credentials_key.encode())


def encrypt_payload(payload: dict[str, str]) -> str:
    blob = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return _fernet().encrypt(blob).decode()


def decrypt_payload(token: str) -> dict[str, str]:
    return json.loads(_fernet().decrypt(token.encode()).decode())


def mask(value: str) -> str:
    if len(value) <= 8:
        return "********"
    return f"{value[:4]}...{value[-4:]}"
