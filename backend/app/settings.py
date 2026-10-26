"""Configuracion tipada. Todo llega por variables de entorno.

Dentro del contenedor no se lee ningun .env: docker-compose inyecta el entorno
de forma explicita. El .env solo se usa si corres la app fuera de Docker.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"

    # --- Postgres: tres roles con privilegios distintos ---
    # app       -> RLS activo (API y worker)
    # platform  -> BYPASSRLS (provisioning)
    # migrator  -> duenio del esquema (solo Alembic)
    app_database_url: str
    platform_database_url: str
    migrator_database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 10
    db_pool_recycle_seconds: int = 1800
    db_echo: bool = False

    # --- Redis: broker y cache separados ---
    redis_broker_url: str
    redis_cache_url: str

    # --- Seguridad ---
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60
    credentials_key: str

    # --- Multi-tenancy y Traefik ---
    # Los clubes viven en <slug>.<base>, el backoffice en admin.<base> y el
    # apex es la landing.
    saas_base_domain: str = "cms-sas.localhost"
    # Slug del club que se sirve en el dominio base (apex). Vacio = landing de
    # plataforma. Sirve para que el propio gestor sea un portal (ej. elatech.io).
    saas_base_tenant: str = ""
    traefik_dynamic_dir: str = "/etc/traefik/dynamic"
    traefik_entrypoints: str = "web"
    traefik_cert_resolver: str = ""
    routes_sync_on_startup: bool = True

    # --- Bootstrap ---
    platform_admin_email: str = "admin@cms-sas.localhost"
    platform_admin_password: str = ""
    first_tenant_slug: str = ""
    first_tenant_name: str = ""
    first_tenant_admin_email: str = ""
    first_tenant_admin_password: str = ""

    # --- Object storage (prefijo por tenant) ---
    s3_endpoint_url: str = ""
    s3_region: str = "us-east-1"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "cms-sas"
    s3_auto_create_bucket: bool = False
    s3_presign_ttl_seconds: int = 900


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
