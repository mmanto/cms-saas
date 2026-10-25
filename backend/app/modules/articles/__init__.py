"""Modulo de articulos: API, modelo y contenido inicial.

Se enciende por club desde ``tenant_modules``. Al habilitarlo se instala el
contenido de ejemplo solo si el club no tiene articulos (ver ``seed.py``).
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.api import router
from app.modules.articles.seed import seed_demo_articles
from app.modules.base import Module


async def on_enable(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    await seed_demo_articles(session, tenant_id)


module = Module(
    name="articles",
    title="Artículos",
    description="Artículos del club con categorías, estado de publicación y API de gestión.",
    router=router,
    on_enable=on_enable,
)
