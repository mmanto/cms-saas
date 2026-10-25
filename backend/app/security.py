"""Hashing de passwords y tokens JWT."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from functools import lru_cache

import jwt
from pwdlib import PasswordHash

from app.settings import get_settings


@lru_cache(maxsize=1)
def _hasher() -> PasswordHash:
    return PasswordHash.recommended()  # argon2


def hash_password(raw: str) -> str:
    return _hasher().hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return _hasher().verify(raw, hashed)


def create_token(*, subject: str, scope: str, tenant_id: str | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, object] = {
        "sub": subject,
        "scope": scope,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
    }
    if tenant_id is not None:
        payload["tid"] = tenant_id
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
