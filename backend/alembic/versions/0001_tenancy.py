"""espina dorsal de tenancy: tenants, dominios, usuarios, credenciales y RLS

Creacion de tablas + habilitacion de Row Level Security.

Criterio de aislamiento
-----------------------
* ``tenant_users`` y ``tenant_credentials`` tienen ``tenant_id`` y RLS.
* La policy usa ``nullif(current_setting('app.tenant_id', true), '')::uuid``.
  Si el GUC no esta fijado la comparacion da NULL -> ninguna fila visible: falla
  cerrado. El ``nullif`` cubre el caso de una conexion del pool que ya tuvo un
  ``SET LOCAL``: ahi PostgreSQL devuelve cadena vacia en vez de NULL.
* NO se usa FORCE ROW LEVEL SECURITY: el rol migrador es duenio de las tablas y
  necesita poder correr backfills. El aislamiento se sostiene porque ``saas_app``
  (el rol de la API) no es owner y tiene ``NOBYPASSRLS``.
* Las tablas globales (``tenants``, ``tenant_domains``) quedan fuera de RLS porque
  hay que resolver un host ANTES de saber el tenant. A ``saas_app`` se le revoca
  la escritura sobre ellas: el alta de clubes la hace el rol de plataforma.

Revision ID: 0001_tenancy
Revises:
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_tenancy"
down_revision = None
branch_labels = None
depends_on = None

TENANT_ID = "tenant_id"
TENANT_SCOPED_TABLES = ("tenant_users", "tenant_credentials")
APP_ROLE = "saas_app"
TENANT_POLICY = "tenant_isolation"


def _tenant_expression() -> str:
    # nullif es imprescindible: una vez que un SET LOCAL corrio en una conexion
    # del pool, current_setting(..., true) devuelve cadena vacia en vez de NULL
    # al terminar la transaccion. Sin nullif, ''::uuid explota con un 500 en
    # lugar de filtrar todas las filas.
    return f"{TENANT_ID} = nullif(current_setting('app.tenant_id', true), '')::uuid"


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("slug", sa.String(length=63), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )

    op.create_table(
        "tenant_domains",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("host", sa.String(length=253), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("host", name="uq_tenant_domains_host"),
    )
    op.create_index("ix_tenant_domains_tenant_id", "tenant_domains", ["tenant_id"])

    op.create_table(
        "tenant_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), server_default=sa.text("'member'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_tenant_users_tenant_email"),
    )
    op.create_index("ix_tenant_users_tenant_id", "tenant_users", ["tenant_id"])

    op.create_table(
        "tenant_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "provider", name="uq_tenant_credentials_tenant_provider"),
    )
    op.create_index("ix_tenant_credentials_tenant_id", "tenant_credentials", ["tenant_id"])

    op.create_table(
        "platform_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_platform_users_email"),
    )

    expression = _tenant_expression()
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {TENANT_POLICY} ON {table} "
            f"FOR ALL USING ({expression}) WITH CHECK ({expression})"
        )

    # El registro de la plataforma es de lectura para la API. Escritura solo con
    # el rol de plataforma (BYPASSRLS + dueño de la operacion de provisioning).
    op.execute(f"REVOKE INSERT, UPDATE, DELETE ON tenants, tenant_domains FROM {APP_ROLE}")
    op.execute(f"REVOKE ALL ON platform_users FROM {APP_ROLE}")

    # Los privilegios por defecto se aplican a partir de ahora: reforzamos lo
    # que ya existe por si los roles se crearon despues de las tablas.
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_users, tenant_credentials TO {APP_ROLE}"
    )
    op.execute(f"GRANT SELECT ON tenants, tenant_domains TO {APP_ROLE}")


def downgrade() -> None:
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {TENANT_POLICY} ON {table}")
    op.drop_table("platform_users")
    op.drop_index("ix_tenant_credentials_tenant_id", table_name="tenant_credentials")
    op.drop_table("tenant_credentials")
    op.drop_index("ix_tenant_users_tenant_id", table_name="tenant_users")
    op.drop_table("tenant_users")
    op.drop_index("ix_tenant_domains_tenant_id", table_name="tenant_domains")
    op.drop_table("tenant_domains")
    op.drop_table("tenants")
