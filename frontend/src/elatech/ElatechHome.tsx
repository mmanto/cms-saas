'use client';

import { useEffect, useMemo, useState } from 'react';

import {
  CAPACITACIONES_CATEGORY,
  PROYECTOS_CATEGORY,
  articlesInCategory,
  type ApiArticle,
  type Article,
} from './articles';
import Capacitaciones from './sections/Capacitaciones';
import Contacto from './sections/Contacto';
import Footer from './sections/Footer';
import Hero from './sections/Hero';
import Navbar from './sections/Navbar';
import Nosotros from './sections/Nosotros';
import Proyectos from './sections/Proyectos';
import Relevamiento from './sections/Relevamiento';
import Servicios from './sections/Servicios';

/**
 * Home del sitio ElaTech.
 *
 * "Capacitaciones" y "Proyectos" no son contenido hardcodeado: son artículos del
 * club filtradas por categoria (modulo `articles`). Se pide una sola vez la lista
 * publicada y cada bloque se queda con su categoria. Si el modulo esta apagado
 * (404) o la API no responde, los dos bloques y sus links desaparecen: el sitio
 * no inventa contenido.
 */
export function ElatechHome() {
  const [articles, setArticles] = useState<Article[] | null>(null);
  const [moduleEnabled, setModuleEnabled] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const response = await fetch('/api/v1/articles?limit=200', { cache: 'no-store' });
        if (!alive) return;
        if (response.status === 404) {
          setModuleEnabled(false);
          setArticles([]);
          return;
        }
        if (!response.ok) throw new Error(`/api/v1/articles respondio ${response.status}`);
        const data = (await response.json()) as ApiArticle[];
        if (!alive) return;
        setArticles(
          data.map((article) => ({
            id: article.id,
            title: article.title,
            slug: article.slug,
            content: article.content,
            excerpt: article.excerpt,
            category: article.category,
            author: article.author,
            imageUrl: article.image_url,
            createdAt: article.created_at,
          })),
        );
        setModuleEnabled(true);
      } catch {
        if (!alive) return;
        setModuleEnabled(false);
        setArticles([]);
      }
    };
    void load();
    return () => {
      alive = false;
    };
  }, []);

  const capacitaciones = useMemo(
    () => articlesInCategory(articles ?? [], CAPACITACIONES_CATEGORY),
    [articles],
  );
  const proyectos = useMemo(
    () => articlesInCategory(articles ?? [], PROYECTOS_CATEGORY),
    [articles],
  );

  const showArticles = moduleEnabled;

  return (
    <div className="elatech-page min-h-screen mt-4">
      <Navbar showArticles={showArticles} />
      <main>
        <Hero showArticles={showArticles} />
        <Servicios />
        {showArticles ? <Capacitaciones articles={capacitaciones} /> : null}
        <Nosotros />
        <Relevamiento />
        {showArticles ? <Proyectos articles={proyectos} /> : null}
        <Contacto />
      </main>
      <Footer showArticles={showArticles} />
    </div>
  );
}
