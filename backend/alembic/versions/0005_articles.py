"""el concepto "noticia" pasa a "articulo": news_posts -> articles

El modelo vive en ingles (``Article`` / tabla ``articles``) y la UI en castellano
(articulos). La tabla conserva filas, RLS, policy y grants: se renombra, no se
recrea. Tambien se renombran el constraint y el indice para que el esquema no
siga diciendo ``news``.

``tenant_modules.name`` es la clave del registro de plugins
(``app/modules/registry.py``): el modulo ``news`` pasa a llamarse ``articles``,
asi que las filas habilitadas se migran con el rename.

Revision ID: 0005_articles
Revises: 0004_modules_news
"""

from __future__ import annotations

from alembic import op

revision = "0005_articles"
down_revision = "0004_modules_news"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("news_posts", "articles")
    op.execute(
        "ALTER TABLE articles RENAME CONSTRAINT "
        "uq_news_posts_tenant_slug TO uq_articles_tenant_slug"
    )
    op.execute(
        "ALTER TABLE articles RENAME CONSTRAINT news_posts_pkey TO articles_pkey"
    )
    op.execute(
        "ALTER TABLE articles RENAME CONSTRAINT "
        "news_posts_tenant_id_fkey TO articles_tenant_id_fkey"
    )
    op.execute("ALTER INDEX ix_news_posts_tenant_id RENAME TO ix_articles_tenant_id")
    op.execute("UPDATE tenant_modules SET name = 'articles' WHERE name = 'news'")


def downgrade() -> None:
    op.execute("UPDATE tenant_modules SET name = 'news' WHERE name = 'articles'")
    op.execute("ALTER INDEX ix_articles_tenant_id RENAME TO ix_news_posts_tenant_id")
    op.execute(
        "ALTER TABLE articles RENAME CONSTRAINT "
        "articles_tenant_id_fkey TO news_posts_tenant_id_fkey"
    )
    op.execute(
        "ALTER TABLE articles RENAME CONSTRAINT articles_pkey TO news_posts_pkey"
    )
    op.execute(
        "ALTER TABLE articles RENAME CONSTRAINT "
        "uq_articles_tenant_slug TO uq_news_posts_tenant_slug"
    )
    op.rename_table("articles", "news_posts")
