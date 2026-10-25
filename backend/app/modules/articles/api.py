"""API del modulo de articulos.

Lectura publica (la landing del club) y gestion con rol admin del club. Todas
las rutas exigen que el modulo ``articles`` este habilitado en ese club: apagado,
responden 404. El club sale del ``Host``, nunca del body, asi que RLS alcanza
para que un club no toque los articulos de otro.

``content`` es texto plano con marcas minimas (``##``/``###`` y listas
numeradas), que es lo que sabe renderizar la landing.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TenantContext
from app.modules.gate import require_admin, require_public
from app.modules.articles.models import Article
from app.storage import delete_object, get_bytes, object_key, put_bytes

router = APIRouter(prefix="/articles", tags=["articles"])

SLUG_MAX = 120
SLUG_RE = re.compile(r"[^a-z0-9]+")
PostStatus = Literal["published", "draft", "archived"]

DEFAULT_AUTHOR = "Redaccion"

# Imagen del articulo: solo raster (nada de SVG servido inline) y con tope.
IMAGE_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/avif": "avif",
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class ArticleIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=SLUG_MAX)
    content: str = Field(min_length=1, max_length=50000)
    excerpt: str = Field(default="", max_length=400)
    category: str = Field(min_length=1, max_length=60)
    status: PostStatus = "draft"
    author: str = Field(default=DEFAULT_AUTHOR, min_length=1, max_length=120)


class ArticlePatchIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=SLUG_MAX)
    content: str | None = Field(default=None, min_length=1, max_length=50000)
    excerpt: str | None = Field(default=None, max_length=400)
    category: str | None = Field(default=None, min_length=1, max_length=60)
    status: PostStatus | None = None
    author: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def _at_least_one(self) -> ArticlePatchIn:
        if all(
            value is None
            for value in (
                self.title,
                self.slug,
                self.content,
                self.excerpt,
                self.category,
                self.status,
                self.author,
            )
        ):
            raise ValueError("hay que mandar al menos un campo")
        return self


def slugify(value: str) -> str:
    """Slug estable: sin acentos, minusculas y guiones simples."""
    ascii_value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    slug = SLUG_RE.sub("-", ascii_value.lower()).strip("-")
    return slug[:SLUG_MAX].strip("-") or "articulo"


async def unique_slug(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    desired: str,
    exclude_id: uuid.UUID | None = None,
) -> str:
    """``desired`` o ``desired-2``, ``desired-3``... dentro del club."""
    base = slugify(desired)
    candidate = base
    suffix = 2
    while True:
        stmt = select(Article.id).where(
            Article.tenant_id == tenant_id, Article.slug == candidate
        )
        if exclude_id is not None:
            stmt = stmt.where(Article.id != exclude_id)
        if await session.scalar(stmt) is None:
            return candidate
        candidate = f"{base[: SLUG_MAX - len(str(suffix)) - 1]}-{suffix}"
        suffix += 1


def article_image_url(post: Article) -> str | None:
    """URL publica de la imagen, versionada por la fecha de subida."""
    if post.image_key is None or post.image_updated_at is None:
        return None
    version = int(post.image_updated_at.timestamp() * 1_000_000)
    return f"/api/v1/articles/{post.slug}/image?v={version}"


def article_payload(post: Article) -> dict[str, Any]:
    return {
        "id": str(post.id),
        "title": post.title,
        "slug": post.slug,
        "content": post.content,
        "excerpt": post.excerpt,
        "category": post.category,
        "status": post.status,
        "author": post.author,
        "image_url": article_image_url(post),
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
    }


async def _article_or_404(ctx: TenantContext, post_id: uuid.UUID) -> Article:
    post = await ctx.session.get(Article, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="articulo inexistente")
    return post


# ── Lectura publica (la landing del club) ──────────────────────────────────


@router.get("")
async def list_published(
    category: str | None = Query(default=None, max_length=60),
    limit: int = Query(default=100, ge=1, le=200),
    ctx: TenantContext = Depends(require_public("articles")),
) -> list[dict[str, Any]]:
    stmt = select(Article).where(Article.status == "published")
    if category:
        stmt = stmt.where(Article.category == category)
    stmt = stmt.order_by(Article.created_at.desc()).limit(limit)
    posts = (await ctx.session.scalars(stmt)).all()
    return [article_payload(post) for post in posts]


# ── Gestion (admin del club) ───────────────────────────────────────────────


# Antes de "/{slug}" a proposito: si no, "all" se lo come el path param.
@router.get("/all")
async def list_all(
    status_filter: PostStatus | None = Query(default=None, alias="status"),
    ctx: TenantContext = Depends(require_admin("articles")),
) -> list[dict[str, Any]]:
    """Incluye borradores y archivadas: es la vista de gestion."""
    stmt = select(Article)
    if status_filter is not None:
        stmt = stmt.where(Article.status == status_filter)
    stmt = stmt.order_by(Article.created_at.desc())
    posts = (await ctx.session.scalars(stmt)).all()
    return [article_payload(post) for post in posts]


@router.get("/{slug}")
async def read_article(
    slug: str, ctx: TenantContext = Depends(require_public("articles"))
) -> dict[str, Any]:
    post = await ctx.session.scalar(
        select(Article).where(Article.slug == slug, Article.status == "published")
    )
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="articulo inexistente")
    return article_payload(post)


@router.get("/{slug}/image")
async def read_article_image(
    slug: str, ctx: TenantContext = Depends(require_public("articles"))
) -> Response:
    """Imagen del articulo, en su propia respuesta para poder cachearla.

    No exige `status=published`: la URL solo se publica en el payload, asi el
    panel puede mostrar el preview de un borrador. Un articulo inexistente o sin
    imagen responde 404.
    """
    post = await ctx.session.scalar(select(Article).where(Article.slug == slug))
    if post is None or post.image_key is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="el articulo no tiene imagen")

    data, stored_type = await get_bytes(post.image_key)
    return Response(
        content=data,
        media_type=post.image_content_type or stored_type or "application/octet-stream",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_article(
    body: ArticleIn, ctx: TenantContext = Depends(require_admin("articles"))
) -> dict[str, Any]:
    slug = await unique_slug(ctx.session, ctx.tenant.id, body.slug or body.title)
    post = Article(
        tenant_id=ctx.tenant.id,
        title=body.title.strip(),
        slug=slug,
        content=body.content,
        excerpt=body.excerpt.strip(),
        category=body.category.strip(),
        status=body.status,
        author=body.author.strip(),
    )
    ctx.session.add(post)
    await ctx.session.flush()
    return article_payload(post)


@router.put("/{post_id}")
async def update_article(
    post_id: uuid.UUID,
    body: ArticlePatchIn,
    ctx: TenantContext = Depends(require_admin("articles")),
) -> dict[str, Any]:
    post = await _article_or_404(ctx, post_id)
    if body.status is not None:
        post.status = body.status
    if body.title is not None:
        post.title = body.title.strip()
    if body.slug is not None:
        post.slug = await unique_slug(ctx.session, ctx.tenant.id, body.slug, exclude_id=post.id)
    if body.content is not None:
        post.content = body.content
    if body.excerpt is not None:
        post.excerpt = body.excerpt.strip()
    if body.category is not None:
        post.category = body.category.strip()
    if body.author is not None:
        post.author = body.author.strip()
    await ctx.session.flush()
    # `updated_at` tiene `onupdate=func.now()`: el flush la deja expirada y el
    # payload la leeria con un lazy load fuera del greenlet (MissingGreenlet).
    await ctx.session.refresh(post)
    return article_payload(post)


@router.put("/{post_id}/image", status_code=status.HTTP_201_CREATED)
async def upload_article_image(
    post_id: uuid.UUID,
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(require_admin("articles")),
) -> dict[str, Any]:
    """Alta o reemplazo de la imagen del articulo."""
    post = await _article_or_404(ctx, post_id)

    content_type = (file.content_type or "").lower()
    extension = IMAGE_TYPES.get(content_type)
    if extension is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"formato no soportado: usa {', '.join(sorted(IMAGE_TYPES))}",
        )

    data = await file.read(MAX_IMAGE_BYTES + 1)
    if len(data) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="la imagen esta vacia")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"la imagen supera {MAX_IMAGE_BYTES // (1024 * 1024)} MB",
        )

    key = object_key(ctx.tenant.id, "articles", f"{post.id}.{extension}")
    previous = post.image_key if post.image_key != key else None

    await put_bytes(key, data, content_type=content_type)
    post.image_key = key
    post.image_content_type = content_type
    post.image_updated_at = datetime.now(timezone.utc)
    await ctx.session.flush()
    # `updated_at` tiene `onupdate`: el flush la expira y el payload la leeria
    # con un lazy load fuera del greenlet (MissingGreenlet).
    await ctx.session.refresh(post)

    # Si cambio el formato, la clave vieja queda huerfana: se borra.
    if previous is not None:
        await delete_object(previous)

    return article_payload(post)


@router.delete("/{post_id}/image", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article_image(
    post_id: uuid.UUID, ctx: TenantContext = Depends(require_admin("articles"))
) -> Response:
    post = await _article_or_404(ctx, post_id)
    key = post.image_key
    if key is not None:
        post.image_key = None
        post.image_content_type = None
        post.image_updated_at = None
        await ctx.session.flush()
        await delete_object(key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    post_id: uuid.UUID, ctx: TenantContext = Depends(require_admin("articles"))
) -> Response:
    post = await _article_or_404(ctx, post_id)
    key = post.image_key
    await ctx.session.delete(post)
    await ctx.session.flush()
    if key is not None:
        await delete_object(key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
