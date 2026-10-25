"""Object storage con aislamiento por tenant.

Regla unica: toda clave pasa por ``object_key``. Asi ningun path queda sin el
prefijo del club y una URL firmada de un tenant no puede apuntar a otro.

boto3 es sincronico: las llamadas se despachan a un hilo para no bloquear el
event loop.
"""

from __future__ import annotations

import uuid
from functools import lru_cache

import anyio
import anyio.to_thread
import boto3
from botocore.config import Config

from app.settings import get_settings

TENANT_PREFIX = "tenants"


def object_key(tenant_id: uuid.UUID | str, *parts: str) -> str:
    """Arma la clave de un objeto siempre bajo el prefijo del club.

    Rechaza claves vacias a proposito: una clave sin nombre terminaria siendo el
    prefijo del club, que no es un objeto valido.
    """
    clean = [segment for segment in (_clean(p) for p in parts) if segment]
    if not clean:
        raise ValueError("object_key necesita al menos un segmento de nombre")
    return "/".join([TENANT_PREFIX, str(tenant_id), *clean])


def _clean(part: str) -> str:
    """Descarta segmentos vacios, "." y ".." para que ninguna clave pueda salir
    del prefijo del club."""
    segments = [s.strip() for s in part.split("/") if s.strip() not in ("", ".", "..")]
    return "/".join(segments)


@lru_cache(maxsize=1)
def _client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url or None,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key or None,
        aws_secret_access_key=settings.s3_secret_key or None,
        config=Config(signature_version="s3v4", retries={"max_attempts": 5}),
    )


async def ensure_bucket() -> None:
    """Crea el bucket si no existe. Solo en desarrollo: en produccion el bucket
    lo maneja la plataforma (S3/R2) y la app no tiene permiso de crearlo."""
    settings = get_settings()

    def _run() -> None:
        client = _client()
        try:
            client.head_bucket(Bucket=settings.s3_bucket)
        except Exception:
            client.create_bucket(Bucket=settings.s3_bucket)

    await anyio.to_thread.run_sync(_run)


async def presign_get(key: str, *, ttl: int | None = None) -> str:
    settings = get_settings()
    expires = ttl or settings.s3_presign_ttl_seconds

    def _run() -> str:
        return _client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": key},
            ExpiresIn=expires,
        )

    return await anyio.to_thread.run_sync(_run)


async def put_bytes(key: str, data: bytes, *, content_type: str) -> str:
    settings = get_settings()

    def _run() -> None:
        _client().put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    await anyio.to_thread.run_sync(_run)
    return key


async def get_bytes(key: str) -> tuple[bytes, str | None]:
    """Baja un objeto. Devuelve (contenido, content_type)."""
    settings = get_settings()

    def _run() -> tuple[bytes, str | None]:
        response = _client().get_object(Bucket=settings.s3_bucket, Key=key)
        body = response["Body"]
        try:
            return body.read(), response.get("ContentType")
        finally:
            body.close()

    return await anyio.to_thread.run_sync(_run)


async def delete_object(key: str) -> None:
    """Idempotente: borrar una clave que no existe no es un error."""
    settings = get_settings()

    def _run() -> None:
        _client().delete_object(Bucket=settings.s3_bucket, Key=key)

    await anyio.to_thread.run_sync(_run)


def tenant_prefix(tenant_id: uuid.UUID | str) -> str:
    """Prefijo de todos los objetos de un club. Sirve para borrarlo entero."""
    return f"{TENANT_PREFIX}/{tenant_id}/"


async def delete_prefix(prefix: str) -> int:
    """Borra todo lo que cuelga de un prefijo y devuelve cuantos objetos borro.

    Se pagina con list_objects_v2 y se borra por lotes de 1000 claves (el tope
    de cada delete_objects). Un prefijo sin objetos no es error: devuelve 0.
    """
    settings = get_settings()

    def _run() -> int:
        client = _client()
        total = 0
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=settings.s3_bucket, Prefix=prefix):
            keys = [{"Key": item["Key"]} for item in page.get("Contents", [])]
            for start in range(0, len(keys), 1000):
                batch = keys[start : start + 1000]
                client.delete_objects(
                    Bucket=settings.s3_bucket, Delete={"Objects": batch}
                )
                total += len(batch)
        return total

    return await anyio.to_thread.run_sync(_run)
