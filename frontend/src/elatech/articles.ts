/**
 * Contrato del modulo `articles` tal como lo consumen los bloques del sitio.
 *
 * La landing de ElaTech tiene dos bloques que no son contenido propio del
 * codigo: "Capacitaciones" y "Proyectos" son artículos del club filtrados por
 * categoria (GET /api/v1/articles?category=...). El panel del club es el que
 * publica; el sitio solo pinta lo que la API devuelve.
 */

/** Artículo público, ya normalizado para la UI. */
export interface Article {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  category: string;
  author: string;
  imageUrl: string | null;
  createdAt: string;
}

/** Artículo como lo devuelve la API (`created_at`/`updated_at` en snake_case). */
export interface ApiArticle {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  category: string;
  status: string;
  author: string;
  image_url: string | null;
  created_at: string;
  updated_at: string;
}

/** Categorias que alimentan los dos bloques del sitio. */
export const CAPACITACIONES_CATEGORY = 'Capacitación';
export const PROYECTOS_CATEGORY = 'Proyectos';

/** Normaliza para comparar: sin acentos, sin mayusculas y sin espacios de mas. */
export function normalizeCategory(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase();
}

/** Artículos de una categoria (el valor sale del panel, asi que se compara laxo). */
export function articlesInCategory(articles: readonly Article[], category: string): Article[] {
  const wanted = normalizeCategory(category);
  return articles.filter((article) => normalizeCategory(article.category) === wanted);
}

export function formatArticleDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return new Intl.DateTimeFormat('es-AR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date);
}
