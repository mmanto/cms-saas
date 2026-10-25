"""branding por club: lo que hace que la misma app se vea distinta

Tabla ``tenant_branding``: una fila por club (``tenant_id`` es la PK) con RLS,
igual que ``tenant_users`` y ``tenant_credentials``. El logo no se guarda aca:
se guarda la clave del objeto en el storage
(``tenants/<tenant_id>/branding/logo.<ext>``).

Revision ID: 0002_tenant_branding
Revises: 0001_tenancy
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_tenant_branding"
down_revision = "0001_tenancy"
branch_labels = None
depends_on = None

TENANT_POLICY = "tenant_isolation"
APP_ROLE = "saas_app"


def _tenant_expression() -> str:
    return "tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid"


def upgrade() -> None:
    op.create_table(
        "tenant_branding",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("primary_color", sa.String(length=9), nullable=True),
        sa.Column("logo_key", sa.String(length=512), nullable=True),
        sa.Column("logo_content_type", sa.String(length=100), nullable=True),
        sa.Column("logo_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("tenant_id"),
    )

    expression = _tenant_expression()
    op.execute("ALTER TABLE tenant_branding ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {TENANT_POLICY} ON tenant_branding "
        f"FOR ALL USING ({expression}) WITH CHECK ({expression})"
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_branding TO {APP_ROLE}")


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS {TENANT_POLICY} ON tenant_branding")
    op.drop_table("tenant_branding")
