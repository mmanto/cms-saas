"""Modelos. El aislamiento NO se declara aca: las policies de RLS se crean en
la migracion (``alembic/versions/0001_tenancy.py``), asi el esquema queda
auditable en un solo lugar.

Tablas con ``tenant_id`` (RLS habilitado):
    tenant_users, tenant_credentials, tenant_branding, tenant_assets,
    tenant_modules

Los modulos conectables (plugins) suman sus propias tablas con RLS desde su
paquete: hoy ``articles`` (``app/modules/articles/models.py``).

Tablas globales (sin RLS, registro de la plataforma):
    tenants, tenant_domains, platform_users

Lo propio de un club que no es una fila (logos, imagenes, adjuntos) va al object
storage bajo ``tenants/<tenant_id>/...``: la fila guarda la clave del objeto, no
los bytes. Ver ``app/storage.py``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = _pk()
    slug: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'active'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    domains: Mapped[list["TenantDomain"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan", lazy="selectin"
    )


class TenantDomain(Base):
    __tablename__ = "tenant_domains"

    id: Mapped[uuid.UUID] = _pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    host: Mapped[str] = mapped_column(String(253), unique=True, nullable=False)
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    tenant: Mapped[Tenant] = relationship(back_populates="domains")


class TenantUser(Base):
    """Usuario de un club. RLS por tenant_id: cada club ve solo los suyos."""

    __tablename__ = "tenant_users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_users_tenant_email"),
    )

    id: Mapped[uuid.UUID] = _pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'member'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TenantCredential(Base):
    """Credenciales de integraciones por club, cifradas con Fernet.

    AFIP/ARCA, MercadoPago y WhatsApp son por club: nunca van a variables de
    entorno globales.
    """

    __tablename__ = "tenant_credentials"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "provider", name="uq_tenant_credentials_tenant_provider"
        ),
    )

    id: Mapped[uuid.UUID] = _pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class TenantBranding(Base):
    """Branding del club: lo que hace que la misma app se vea distinta en cada
    host. Una fila por club (``tenant_id`` es la PK).

    Aca va solo el nombre visible y el color. El logo es un asset mas
    (``tenant_assets``, nombre ``logo``): los archivos no se guardan en la fila.
    """

    __tablename__ = "tenant_branding"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(120))
    primary_color: Mapped[str | None] = mapped_column(String(9))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class TenantAsset(Base):
    """Un archivo propio del club (logo, favicon, imagen de la landing...).

    La clave es (``tenant_id``, ``name``): el nombre lo elige el club y el objeto
    vive bajo ``tenants/<tenant_id>/assets/<name>.<ext>``. Subir el mismo nombre
    reemplaza el archivo. Ver ``app/api/assets.py``.
    """

    __tablename__ = "tenant_assets"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(63), primary_key=True)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class TenantModule(Base):
    """Switch de un modulo conectable para un club.

    La fila ausente significa apagado. ``config`` queda para opciones propias del
    plugin (hoy ningun modulo lo usa) y ``name`` es la clave estable del registro
    (``app/modules/registry.py``). Ver ``app/modules/state.py``.
    """

    __tablename__ = "tenant_modules"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(40), primary_key=True)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class PlatformUser(Base):
    """Administrador de la plataforma. Sin RLS: es global y solo lo toca el
    router de provisioning a traves del motor plataforma."""

    __tablename__ = "platform_users"

    id: Mapped[uuid.UUID] = _pk()
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
