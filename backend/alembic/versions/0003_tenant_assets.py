"""assets por club (logo, favicon, imagenes) y el logo como asset

``tenant_assets`` es el mecanismo generico: (club, nombre) -> objeto en el
storage. El logo del branding deja de tener columnas propias y pasa a ser el
asset ``logo``; los logos ya subidos se migran a la tabla nueva (el objeto sigue
con su clave vieja, que es valida: la clave es una referencia, no una
convencion).

Revision ID: 0003_tenant_assets
Revises: 0002_tenant_branding
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_tenant_assets"
down_revision = "0002_tenant_branding"
branch_labels = None
depends_on = None

TENANT_POLICY = "tenant_isolation"
APP_ROLE = "saas_app"


def _tenant_expression() -> str:
    return "tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid"


def upgrade() -> None:
    op.create_table(
        "tenant_assets",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=63), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("tenant_id", "name"),
    )

    expression = _tenant_expression()
    op.execute("ALTER TABLE tenant_assets ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {TENANT_POLICY} ON tenant_assets "
        f"FOR ALL USING ({expression}) WITH CHECK ({expression})"
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_assets TO {APP_ROLE}")

    # El logo pasa a ser un asset. Para los ya subidos no conocemos el tamano: 0.
    op.execute(
        """
        INSERT INTO tenant_assets
            (tenant_id, name, object_key, content_type, size_bytes, updated_at)
        SELECT tenant_id,
               'logo',
               logo_key,
               coalesce(logo_content_type, 'application/octet-stream'),
               0,
               coalesce(logo_updated_at, now())
        FROM tenant_branding
        WHERE logo_key IS NOT NULL
        """
    )
    op.drop_column("tenant_branding", "logo_key")
    op.drop_column("tenant_branding", "logo_content_type")
    op.drop_column("tenant_branding", "logo_updated_at")


def downgrade() -> None:
    op.add_column("tenant_branding", sa.Column("logo_key", sa.String(length=512)))
    op.add_column("tenant_branding", sa.Column("logo_content_type", sa.String(length=100)))
    op.add_column("tenant_branding", sa.Column("logo_updated_at", sa.DateTime(timezone=True)))
    op.execute(
        """
        UPDATE tenant_branding AS b
        SET logo_key = a.object_key,
            logo_content_type = a.content_type,
            logo_updated_at = a.updated_at
        FROM tenant_assets AS a
        WHERE a.tenant_id = b.tenant_id AND a.name = 'logo'
        """
    )
    op.execute(f"DROP POLICY IF EXISTS {TENANT_POLICY} ON tenant_assets")
    op.drop_table("tenant_assets")
