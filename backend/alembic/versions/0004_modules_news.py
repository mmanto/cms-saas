"""modulos conectables (tenant_modules) y noticias por club (news_posts)

``tenant_modules`` es el switch generico de los plugins: PK (tenant_id, name),
fila ausente = apagado. ``news_posts`` es la tabla del modulo ``news``; vive en
su paquete (``app/modules/news/models.py``) pero el esquema se audita aca, como
el resto.

Ambas llevan RLS con la misma policy que las tablas del nucleo: el modulo no
puede ver ni escribir filas de otro club aunque comparta proceso y conexion.

No se backfillea ningun club: habilitar un modulo es una decision explicita
(backoffice o ``PUT /api/v1/platform/tenants/{id}/modules/{name}``). El club de
ejemplo lo habilita ``app/bootstrap.py``, que corre despues de esta migracion.

Revision ID: 0004_modules_news
Revises: 0003_tenant_assets
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_modules_news"
down_revision = "0003_tenant_assets"
branch_labels = None
depends_on = None

TENANT_POLICY = "tenant_isolation"
APP_ROLE = "saas_app"
TENANT_TABLES = ("tenant_modules", "news_posts")


def _tenant_expression() -> str:
    return "tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid"


def upgrade() -> None:
    op.create_table(
        "tenant_modules",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column(
            "enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("tenant_id", "name"),
    )

    op.create_table(
        "news_posts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "excerpt", sa.String(length=400), server_default=sa.text("''"), nullable=False
        ),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default=sa.text("'draft'"), nullable=False
        ),
        sa.Column(
            "author",
            sa.String(length=120),
            server_default=sa.text("'Redaccion'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_news_posts_tenant_slug"),
    )
    op.create_index("ix_news_posts_tenant_id", "news_posts", ["tenant_id"])

    expression = _tenant_expression()
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {TENANT_POLICY} ON {table} "
            f"FOR ALL USING ({expression}) WITH CHECK ({expression})"
        )
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_modules, news_posts TO {APP_ROLE}"
    )


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {TENANT_POLICY} ON {table}")
    op.drop_index("ix_news_posts_tenant_id", table_name="news_posts")
    op.drop_table("news_posts")
    op.drop_table("tenant_modules")
