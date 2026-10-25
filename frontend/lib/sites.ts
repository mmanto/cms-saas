import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';
import { headers } from 'next/headers';
import { notFound } from 'next/navigation';

import { TENANT_HEADER, tenantFromRequest } from './tenant';
import { auxiliosrb } from '@/src/auxiliosrb/site';
import { elatech } from '@/src/elatech/site';

/**
 * Sitios (variantes de UI) de la app compartida.
 *
 * La app es una sola y el club sale del request (`Host` o el header que pone el
 * borde). Si ese club tiene un sitio propio, se pinta ese sitio en vez del shell
 * de la plataforma. Cada sitio es codigo: vive en `src/<sitio>/` y se registra
 * abajo. El generador deja instalado el sitio del tenant de ejemplo
 * (Auxilio RB): el resto de los clubes usa el shell de la plataforma.
 */
export interface ClubSite {
  /** Identificador del sitio (el que usan su layout de rutas y `requireSite`). */
  id: string;
  /** Slug del club que lo usa. */
  club: string;
  metadata: Metadata;
  viewport: Viewport;
  /** Contenido extra del `<head>` (fuentes, preconnect). */
  head: ReactNode;
  /** Envoltorio de la pagina: el chrome del sitio. */
  Shell: (props: { children: ReactNode }) => ReactNode;
  /** Home del sitio: reemplaza la home de la plataforma. */
  home: ReactNode;
  /** 404 del sitio. */
  notFound: ReactNode;
}

/**
 * Sitios instalados. ESTE ES EL PUNTO DE INSTALACION: cada sitio agrega su
 * entrada aca (y su codigo en `src/`). Si el generador reescribe este archivo,
 * volve a poner las entradas.
 */
export const SITES: ClubSite[] = [auxiliosrb, elatech];

export function siteForClub(club: string | null | undefined): ClubSite | null {
  if (!club) return null;
  return SITES.find((site) => site.club === club) ?? null;
}

/** El club del request, como lo resuelve `lib/tenant.ts`. */
export async function requestClub(): Promise<string | null> {
  const requestHeaders = await headers();
  return tenantFromRequest(requestHeaders.get('host'), requestHeaders.get(TENANT_HEADER));
}

/** El sitio `siteId` si el club del request es su club; si no, 404. */
export async function requireSite(siteId: string): Promise<ClubSite> {
  const site = SITES.find((item) => item.id === siteId) ?? null;
  const club = await requestClub();
  if (site === null || site.club !== club) notFound();
  return site;
}
