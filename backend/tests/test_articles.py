"""Tests del modulo de articulos y del registro de modulos.

Lo barato (sin base): slug, payload y que un modulo apagado falle cerrado. Lo
que necesita Postgres: que el switch sea por club, que RLS aisle los articulos y
que la gestion exija rol admin del club.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.db import AppSession, PlatformSession
from app.main import app
from app.models import Tenant, TenantDomain, TenantUser
from app.modules.gate import require_public
from app.modules.articles.api import (
    IMAGE_TYPES,
    MAX_IMAGE_BYTES,
    article_image_url,
    article_payload,
    slugify,
)
from app.modules.articles.models import Article
from app.modules.articles.seed import DEMO_ARTICLES, seed_demo_articles
from app.modules.registry import catalog, modules_for_tenant, set_enabled
from app.modules.state import set_row
from app.security import hash_password
from app.settings import get_settings
from app.tenancy import bind_tenant

STAMP = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _article(**overrides: object) -> Article:
    post = Article(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        title="Titulo",
        slug="titulo",
        content="Cuerpo",
        excerpt="Resumen",
        category="Tecnologia",
        status="published",
        author="Redaccion",
        created_at=STAMP,
        updated_at=STAMP,
    )
    for key, value in overrides.items():
        setattr(post, key, value)
    return post


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Introducción a React 19", "introduccion-a-react-19"),
        ("  Diseño   Minimalista  ", "diseno-minimalista"),
        ("Tailwind CSS: Guía Avanzada", "tailwind-css-guia-avanzada"),
        ("###", "articulo"),
        ("a" * 200, "a" * 120),
    ],
)
def test_slug_estable(raw: str, expected: str) -> None:
    assert slugify(raw) == expected


def test_la_imagen_es_opcional_y_su_url_lleva_la_version() -> None:
    post = _article()
    assert article_payload(post)["image_url"] is None

    post.image_key = "tenants/x/articles/y.png"
    post.image_updated_at = STAMP

    version = int(STAMP.timestamp() * 1_000_000)
    assert article_image_url(post) == f"/api/v1/articles/titulo/image?v={version}"
    assert IMAGE_TYPES["image/png"] == "png"
    assert "image/svg+xml" not in IMAGE_TYPES
    assert MAX_IMAGE_BYTES == 5 * 1024 * 1024


def test_el_payload_expone_lo_que_necesita_la_landing() -> None:
    payload = article_payload(_article())

    assert payload == {
        "id": payload["id"],
        "title": "Titulo",
        "slug": "titulo",
        "content": "Cuerpo",
        "excerpt": "Resumen",
        "category": "Tecnologia",
        "status": "published",
        "author": "Redaccion",
        "image_url": None,
        "created_at": STAMP.isoformat(),
        "updated_at": STAMP.isoformat(),
    }
    assert len(payload["id"]) == 36


def test_el_catalogo_instala_articles_apagado_por_defecto() -> None:
    entries = {entry["name"]: entry for entry in catalog()}

    assert "articles" in entries
    assert entries["articles"]["title"] == "Artículos"
    assert set(entries["articles"]) == {"name", "title", "description"}


async def test_un_modulo_apagado_falla_cerrado(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sin fila habilitada la ruta publica responde 404, no 500 ni lista vacia."""

    async def disabled(*_args: object, **_kwargs: object) -> bool:
        return False

    monkeypatch.setattr("app.modules.gate.is_enabled", disabled)
    dependency = require_public("articles")

    class Ctx:
        class session:  # noqa: N801 - doble del TenantContext
            pass

        class tenant:  # noqa: N801
            id = uuid.uuid4()

        host = "demo.test"

    with pytest.raises(HTTPException) as error:
        await dependency(Ctx())
    assert error.value.status_code == 404
    assert "articles" in error.value.detail


def _headers(slug: str) -> dict[str, str]:
    return {"host": f"{slug}.{get_settings().saas_base_domain}"}


async def _create_tenant(session, slug: str) -> uuid.UUID:
    tenant = Tenant(slug=slug, name=f"Club {slug}", status="active")
    session.add(tenant)
    await session.flush()
    session.add(
        TenantDomain(
            tenant_id=tenant.id,
            host=f"{slug}.{get_settings().saas_base_domain}",
            is_primary=True,
        )
    )
    await session.flush()
    return tenant.id


@pytest.mark.asyncio
async def test_el_switch_y_los_articulos_son_por_club(database: bool) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug_a, slug_b = f"article-a-{suffix}", f"article-b-{suffix}"

    async with PlatformSession() as session:
        async with session.begin():
            tenant_a = await _create_tenant(session, slug_a)
            tenant_b = await _create_tenant(session, slug_b)

    try:
        # A: habilitar por la via real instala el contenido de ejemplo.
        async with PlatformSession() as session:
            async with session.begin():
                assert await set_enabled(session, tenant_a, "articles", True) is True
                # B: mismo modulo, pero encendido a mano y sin sembrar contenido.
                assert await set_row(session, tenant_b, "articles", True) is True

        async with PlatformSession() as session:
            async with session.begin():
                states = {
                    entry["name"]: entry["enabled"]
                    for entry in await modules_for_tenant(session, tenant_a)
                }
                assert states["articles"] is True

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response_a = await client.get("/api/v1/articles", headers=_headers(slug_a))
            response_b = await client.get("/api/v1/articles", headers=_headers(slug_b))
            modules_a = await client.get("/api/v1/modules", headers=_headers(slug_a))

        assert response_a.status_code == 200
        published = [post for post in DEMO_ARTICLES if post["status"] == "published"]
        assert len(response_a.json()) == len(published)
        assert {post["status"] for post in response_a.json()} == {"published"}

        assert response_b.status_code == 200
        assert response_b.json() == []  # habilitado, pero sin articulos propios

        assert modules_a.status_code == 200
        assert [entry["name"] for entry in modules_a.json()] == ["articles"]

        # RLS: el rol de la API de B no ve los articulos de A.
        async with AppSession() as session:
            async with session.begin():
                await bind_tenant(session, tenant_b)
                assert await session.scalar(
                    select(func.count()).select_from(Article)
                ) == 0
            async with session.begin():
                await bind_tenant(session, tenant_a)
                assert await session.scalar(
                    select(func.count()).select_from(Article)
                ) == len(DEMO_ARTICLES)
    finally:
        async with PlatformSession() as session:
            async with session.begin():
                for tenant_id in (tenant_a, tenant_b):
                    tenant = await session.get(Tenant, tenant_id)
                    if tenant is not None:
                        await session.delete(tenant)


@pytest.mark.asyncio
async def test_modulo_apagado_responde_404_en_la_api(database: bool) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"article-off-{suffix}"

    async with PlatformSession() as session:
        async with session.begin():
            tenant_id = await _create_tenant(session, slug)

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/articles", headers=_headers(slug))
            modules = await client.get("/api/v1/modules", headers=_headers(slug))

        assert response.status_code == 404
        assert "no esta habilitado" in response.json()["detail"]
        assert modules.status_code == 200
        assert modules.json() == []
    finally:
        async with PlatformSession() as session:
            async with session.begin():
                tenant = await session.get(Tenant, tenant_id)
                if tenant is not None:
                    await session.delete(tenant)


@pytest.mark.asyncio
async def test_la_gestion_exige_rol_admin_del_club(database: bool) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"article-admin-{suffix}"
    email = f"admin@{slug}.test"
    password = "prueba1234"

    async with PlatformSession() as session:
        async with session.begin():
            tenant_id = await _create_tenant(session, slug)
            session.add(
                TenantUser(
                    tenant_id=tenant_id,
                    email=email,
                    password_hash=hash_password(password),
                    role="admin",
                )
            )
            await set_enabled(session, tenant_id, "articles", True)

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            anonymous = await client.post(
                "/api/v1/articles",
                headers=_headers(slug),
                json={
                    "title": "Nota",
                    "content": "Cuerpo",
                    "category": "General",
                    "status": "published",
                },
            )
            login = await client.post(
                "/api/v1/auth/login",
                headers=_headers(slug),
                json={"email": email, "password": password},
            )
            token = login.json()["access_token"]
            auth = {**_headers(slug), "authorization": f"Bearer {token}"}
            created = await client.post(
                "/api/v1/articles",
                headers=auth,
                json={
                    "title": "Nota desde la API",
                    "content": "Cuerpo",
                    "category": "General",
                    "status": "published",
                },
            )
            drafts = await client.get("/api/v1/articles/all", headers=auth)
            public = await client.get("/api/v1/articles", headers=_headers(slug))

        assert anonymous.status_code == 401
        assert login.status_code == 200
        assert created.status_code == 201
        assert created.json()["slug"] == "nota-desde-la-api"
        assert len(drafts.json()) == len(DEMO_ARTICLES) + 1
        assert "nota-desde-la-api" in {post["slug"] for post in public.json()}
    finally:
        async with PlatformSession() as session:
            async with session.begin():
                tenant = await session.get(Tenant, tenant_id)
                if tenant is not None:
                    await session.delete(tenant)


@pytest.mark.asyncio
async def test_el_seed_no_pisa_contenido_existente(database: bool) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"article-seed-{suffix}"

    async with PlatformSession() as session:
        async with session.begin():
            tenant_id = await _create_tenant(session, slug)
            await seed_demo_articles(session, tenant_id)

        async with session.begin():
            assert await seed_demo_articles(session, tenant_id) == 0
            total = await session.scalar(
                select(func.count()).select_from(Article).where(Article.tenant_id == tenant_id)
            )
            assert total == len(DEMO_ARTICLES)

    async with PlatformSession() as session:
        async with session.begin():
            tenant = await session.get(Tenant, tenant_id)
            if tenant is not None:
                await session.delete(tenant)



@pytest.mark.asyncio
async def test_los_alias_internos_creen_en_x_saas_host(
    database: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fuera de /api el club sale de ``X-SaaS-Host``; dentro de /api, del Host.

    El SSR del frontend no tiene el Host del navegador y lo reenvia en ese
    header. Las rutas internas existen justamente para eso, pero el override no
    puede valer en /api: si no, cualquier cliente externo se declararia otro
    club con un header propio. Se fuerza produccion porque en desarrollo el
    override es deliberado (pegarle al contenedor sin Traefik).
    """
    monkeypatch.setattr(get_settings(), "environment", "production")

    suffix = uuid.uuid4().hex[:8]
    slug = f"article-alias-{suffix}"

    async with PlatformSession() as session:
        async with session.begin():
            tenant_id = await _create_tenant(session, slug)
            await set_enabled(session, tenant_id, "articles", True)

    # El Host del request NO es el del club: si el alias no mirara X-SaaS-Host,
    # esto no resolveria ningun club.
    club_host = f"{slug}.{get_settings().saas_base_domain}"
    headers = {"host": "otro.host", "x-saas-host": club_host}

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            internal = await client.get("/articles", headers=headers)
            external = await client.get("/api/v1/articles", headers=headers)
            api_by_host = await client.get("/api/v1/articles", headers={"host": club_host})

        published = [post for post in DEMO_ARTICLES if post["status"] == "published"]
        assert internal.status_code == 200
        assert len(internal.json()) == len(published)

        # En /api el X-SaaS-Host se ignora: "otro.host" no es ningun club.
        assert external.status_code == 404
        assert "otro.host" in external.json()["detail"]

        # La misma ruta, con el Host real del club, sigue funcionando.
        assert api_by_host.status_code == 200
        assert len(api_by_host.json()) == len(published)
    finally:
        async with PlatformSession() as session:
            async with session.begin():
                tenant = await session.get(Tenant, tenant_id)
                if tenant is not None:
                    await session.delete(tenant)


@pytest.mark.asyncio
async def test_la_gestion_puede_editar_publicar_y_borrar(database: bool) -> None:
    """El panel del club opera por la API: editar, cambiar estado y borrar.

    El update reescribe ``updated_at`` con ``onupdate=func.now()``: si el flush
    deja la columna expirada, el payload revienta con MissingGreenlet y el
    admin ve un 500.
    """
    suffix = uuid.uuid4().hex[:8]
    slug = f"article-editor-{suffix}"
    email = f"editor@{slug}.test"
    password = "prueba1234"

    async with PlatformSession() as session:
        async with session.begin():
            tenant_id = await _create_tenant(session, slug)
            session.add(
                TenantUser(
                    tenant_id=tenant_id,
                    email=email,
                    password_hash=hash_password(password),
                    role="admin",
                )
            )
            await set_enabled(session, tenant_id, "articles", True)

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            login = await client.post(
                "/api/v1/auth/login",
                headers=_headers(slug),
                json={"email": email, "password": password},
            )
            auth = {**_headers(slug), "authorization": f"Bearer {login.json()['access_token']}"}

            created = await client.post(
                "/api/v1/articles",
                headers=auth,
                json={
                    "title": "Nota original",
                    "content": "Cuerpo",
                    "category": "General",
                    "status": "draft",
                },
            )
            post_id = created.json()["id"]

            edited = await client.put(
                f"/api/v1/articles/{post_id}",
                headers=auth,
                json={"title": "Nota corregida", "content": "Cuerpo nuevo"},
            )
            published = await client.put(
                f"/api/v1/articles/{post_id}", headers=auth, json={"status": "published"}
            )
            public = await client.get("/api/v1/articles", headers=_headers(slug))
            removed = await client.delete(f"/api/v1/articles/{post_id}", headers=auth)
            missing = await client.delete(f"/api/v1/articles/{post_id}", headers=auth)

        assert edited.status_code == 200
        assert edited.json()["title"] == "Nota corregida"
        assert edited.json()["slug"] == created.json()["slug"]  # el slug no se regenera

        assert published.status_code == 200
        assert published.json()["status"] == "published"
        # Editar el titulo no toca el slug: la URL del articulo no se rompe.
        assert "nota-original" in {post["slug"] for post in public.json()}

        assert removed.status_code == 204
        assert missing.status_code == 404
    finally:
        async with PlatformSession() as session:
            async with session.begin():
                tenant = await session.get(Tenant, tenant_id)
                if tenant is not None:
                    await session.delete(tenant)


@pytest.mark.asyncio
async def test_la_imagen_del_articulo_se_sube_sirve_reemplaza_y_borra(
    database: bool,
) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"article-image-{suffix}"
    email = f"admin@{slug}.test"
    password = "prueba1234"

    async with PlatformSession() as session:
        async with session.begin():
            tenant_id = await _create_tenant(session, slug)
            session.add(
                TenantUser(
                    tenant_id=tenant_id,
                    email=email,
                    password_hash=hash_password(password),
                    role="admin",
                )
            )
            await set_enabled(session, tenant_id, "articles", True)

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            login = await client.post(
                "/api/v1/auth/login",
                headers=_headers(slug),
                json={"email": email, "password": password},
            )
            token = login.json()["access_token"]
            auth = {**_headers(slug), "authorization": f"Bearer {token}"}

            created = await client.post(
                "/api/v1/articles",
                headers=auth,
                json={
                    "title": "Con imagen",
                    "content": "Cuerpo",
                    "category": "General",
                    "status": "published",
                },
            )
            article = created.json()
            assert article["image_url"] is None
            article_id = article["id"]

            first = b"\x89PNG\r\n\x1a\nimagen-de-prueba"
            uploaded = await client.put(
                f"/api/v1/articles/{article_id}/image",
                headers=auth,
                files={"file": ("foto.png", first, "image/png")},
            )
            assert uploaded.status_code == 201
            image_url = uploaded.json()["image_url"]
            assert image_url is not None
            assert image_url.startswith(f"/api/v1/articles/{article['slug']}/image?v=")

            served = await client.get(image_url, headers=_headers(slug))
            assert served.status_code == 200
            assert served.content == first
            assert served.headers["content-type"] == "image/png"
            assert served.headers["cache-control"].startswith("public")

            second = b"\xff\xd8\xff\xe0imagen-jpeg"
            replaced = await client.put(
                f"/api/v1/articles/{article_id}/image",
                headers=auth,
                files={"file": ("foto.jpg", second, "image/jpeg")},
            )
            assert replaced.status_code == 201
            assert replaced.json()["image_url"] != image_url
            served_jpeg = await client.get(
                replaced.json()["image_url"], headers=_headers(slug)
            )
            assert served_jpeg.content == second
            assert served_jpeg.headers["content-type"] == "image/jpeg"

            unsupported = await client.put(
                f"/api/v1/articles/{article_id}/image",
                headers=auth,
                files={"file": ("x.svg", b"<svg/>", "image/svg+xml")},
            )
            assert unsupported.status_code == 415

            removed = await client.delete(
                f"/api/v1/articles/{article_id}/image", headers=auth
            )
            assert removed.status_code == 204
            after = await client.get(
                f"/api/v1/articles/{article['slug']}", headers=_headers(slug)
            )
            assert after.json()["image_url"] is None
            assert (
                await client.get(replaced.json()["image_url"], headers=_headers(slug))
            ).status_code == 404
    finally:
        async with PlatformSession() as session:
            async with session.begin():
                tenant = await session.get(Tenant, tenant_id)
                if tenant is not None:
                    await session.delete(tenant)
