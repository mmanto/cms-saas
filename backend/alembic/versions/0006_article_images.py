"""imagen opcional por articulo

El archivo no se guarda en Postgres: la fila guarda la clave del objeto en el
storage (``tenants/<tenant_id>/articles/<article_id>.<ext>``), el content type y
la fecha de subida (version para el cache de la URL publica).

Revision ID: 0006_article_images
Revises: 0005_articles
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_article_images"
down_revision = "0005_articles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articles", sa.Column("image_key", sa.String(length=512), nullable=True)
    )
    op.add_column(
        "articles",
        sa.Column("image_content_type", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "articles",
        sa.Column("image_updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("articles", "image_updated_at")
    op.drop_column("articles", "image_content_type")
    op.drop_column("articles", "image_key")
