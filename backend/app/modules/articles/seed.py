"""Contenido de ejemplo que el modulo instala al habilitarse.

Es el contenido que antes vivia hardcodeado en la landing
(``src/auxiliosrb/data.ts``, ya eliminado). Se
instala **solo si el club no tiene ningun articulo**, asi habilitar el modulo no
pisa contenido real. El hook corre con la sesion de plataforma (BYPASSRLS): por
eso cada fila lleva su ``tenant_id`` explicito.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.models import Article

DEMO_ARTICLES: tuple[dict[str, object], ...] = (
    {
        "title": "Introducción a React 19",
        "slug": "introduccion-react-19",
        "content": (
            "React 19 trae consigo mejoras significativas en rendimiento y nuevas APIs que "
            "simplifican el desarrollo de aplicaciones modernas. En este artículo exploraremos "
            "las principales novedades y cómo aprovecharlas en nuestros proyectos.\n\n"
            "## Server Components\n\n"
            "Los Server Components permiten renderizar componentes en el servidor, reduciendo el "
            "tamaño del bundle y mejorando el tiempo de carga inicial.\n\n"
            "## Actions\n\n"
            "Las Actions simplifican el manejo de formularios y mutaciones de datos, "
            "proporcionando una experiencia de desarrollo más fluida."
        ),
        "excerpt": "Explorando las novedades de React 19 y cómo aprovecharlas en proyectos modernos.",
        "category": "Tecnología",
        "status": "published",
        "author": "María García",
        "created_at": datetime(2025, 12, 15, 10, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2025, 12, 15, 10, 0, tzinfo=timezone.utc),
    },
    {
        "title": "Diseño Minimalista en la Web",
        "slug": "diseno-minimalista-web",
        "content": (
            "El minimalismo en el diseño web no es solo una tendencia estética, sino una "
            "filosofía que prioriza la claridad y la funcionalidad. Menos es más cuando se trata "
            "de crear experiencias digitales memorables.\n\n"
            "## Principios del diseño minimalista\n\n"
            "1. Espacio en blanco generoso\n"
            "2. Tipografía clara y legible\n"
            "3. Paleta de colores reducida\n"
            "4. Jerarquía visual definida"
        ),
        "excerpt": "Principios fundamentales para crear interfaces web limpias y funcionales.",
        "category": "Diseño",
        "status": "published",
        "author": "Carlos López",
        "created_at": datetime(2025, 12, 10, 8, 30, tzinfo=timezone.utc),
        "updated_at": datetime(2025, 12, 12, 14, 20, tzinfo=timezone.utc),
    },
    {
        "title": "Tailwind CSS: Guía Avanzada",
        "slug": "tailwind-css-guia-avanzada",
        "content": (
            "Tailwind CSS ha revolucionado la forma en que escribimos CSS. En esta guía avanzada "
            "aprenderemos técnicas como componentes personalizados, plugins y configuración "
            "avanzada para llevar nuestros proyectos al siguiente nivel."
        ),
        "excerpt": "Técnicas avanzadas de Tailwind CSS para proyectos profesionales.",
        "category": "Tecnología",
        "status": "draft",
        "author": "Ana Martínez",
        "created_at": datetime(2025, 12, 8, 16, 45, tzinfo=timezone.utc),
        "updated_at": datetime(2025, 12, 9, 9, 15, tzinfo=timezone.utc),
    },
    {
        "title": "El Futuro del Desarrollo Web",
        "slug": "futuro-desarrollo-web",
        "content": (
            "La web está evolucionando rápidamente. Desde WebAssembly hasta Edge Computing, las "
            "nuevas tecnologías están transformando cómo construimos aplicaciones. Analizamos las "
            "tendencias que definirán los próximos años."
        ),
        "excerpt": "Tendencias y tecnologías que definirán el desarrollo web en los próximos años.",
        "category": "Tecnología",
        "status": "published",
        "author": "María García",
        "created_at": datetime(2025, 11, 28, 12, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2025, 11, 30, 18, 0, tzinfo=timezone.utc),
    },
    {
        "title": "Accesibilidad Web: Lo Esencial",
        "slug": "accesibilidad-web-esencial",
        "content": (
            "La accesibilidad web no es opcional, es un derecho. Aprende los fundamentos de WCAG "
            "y cómo implementar prácticas accesibles en tus proyectos desde el primer día."
        ),
        "excerpt": "Fundamentos de accesibilidad web y mejores prácticas WCAG.",
        "category": "Diseño",
        "status": "published",
        "author": "Carlos López",
        "created_at": datetime(2025, 11, 20, 9, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2025, 11, 20, 9, 0, tzinfo=timezone.utc),
    },
    {
        "title": "Arquitectura de Software Limpia",
        "slug": "arquitectura-software-limpia",
        "content": (
            "Una arquitectura bien diseñada es la base de cualquier proyecto exitoso. Exploramos "
            "patrones como Clean Architecture, Hexagonal y cómo aplicarlos en aplicaciones "
            "modernas."
        ),
        "excerpt": "Patrones de arquitectura para construir software mantenible y escalable.",
        "category": "Desarrollo",
        "status": "archived",
        "author": "Ana Martínez",
        "created_at": datetime(2025, 10, 15, 11, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2025, 11, 1, 10, 0, tzinfo=timezone.utc),
    },
)


async def seed_demo_articles(session: AsyncSession, tenant_id: uuid.UUID) -> int:
    """Instala el contenido de ejemplo si el club no tiene articulos. Idempotente."""
    existing = await session.scalar(
        select(func.count()).select_from(Article).where(Article.tenant_id == tenant_id)
    )
    if existing:
        return 0
    for data in DEMO_ARTICLES:
        session.add(Article(tenant_id=tenant_id, **data))
    await session.flush()
    return len(DEMO_ARTICLES)
