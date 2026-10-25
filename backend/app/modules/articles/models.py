"""Articulos por club. RLS por ``tenant_id`` (policy en la migracion 0004).

El modelo vive en el paquete del modulo (no en ``app/models.py``) para que el
plugin se pueda copiar/borrar sin tocar el nucleo. La tabla igual lleva
``tenant_id`` y la policy de aislamiento: un club nunca ve los articulos de otro.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_articles_tenant_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str] = mapped_column(String(400), nullable=False, server_default=text("''"))
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'draft'")
    )
    author: Mapped[str] = mapped_column(
        String(120), nullable=False, server_default=text("'Redaccion'")
    )
    # Imagen opcional: la fila guarda la referencia al objeto, no los bytes.
    image_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
