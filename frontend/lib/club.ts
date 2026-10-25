/**
 * Contrato del panel de artículos del club que comparten el server y el
 * navegador: cookie, rutas, estados y tipos. Nada de `next/headers` aca, porque
 * los formularios (client components) importan este modulo.
 *
 * El fetch y la guarda de sesion viven en `lib/tenant-auth.ts`, que es
 * server-only.
 */

/** Cookie httpOnly con el token del club. La escribe la Server Action de login. */
export const CLUB_COOKIE = 'saas_club_session';

/** Panel de artículos: a donde manda todo lo que necesita sesion. */
export const PANEL_ARTICULOS = '/panel/articulos';
export const PANEL_LOGIN = '/panel/articulos/login';

export interface ClubMe {
  id: string;
  email: string;
  role: string;
  tenant: { id: string; slug: string; name: string };
  host: string;
}

export type ArticleStatus = 'published' | 'draft' | 'archived';

/** Etiquetas de estado: las usan el panel (server) y el formulario (cliente). */
export const ARTICLE_STATUSES: ArticleStatus[] = ['published', 'draft', 'archived'];

export const ARTICLE_STATUS_LABEL: Record<ArticleStatus, string> = {
  published: 'Publicada',
  draft: 'Borrador',
  archived: 'Archivada',
};

/** Artículo como la devuelve el modulo `articles` (incluye borradores y archivadas). */
export interface ClubArticle {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  category: string;
  status: ArticleStatus;
  author: string;
  image_url: string | null;
  created_at: string;
  updated_at: string;
}

/** Error de la API del club, con el status a mano para distinguir 401/404/422. */
export class ClubApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ClubApiError';
  }
}

/** Mensaje para el usuario segun el status que devolvio la API del club. */
export function clubMessageOf(error: unknown): string {
  if (!(error instanceof ClubApiError)) return 'error inesperado';
  if (error.status === 404) return 'El modulo de artículos no esta habilitado en este club.';
  if (error.status === 401 || error.status === 403) return 'Sesion vencida: volve a entrar.';
  return error.message;
}
