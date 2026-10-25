import { cookies, headers } from 'next/headers';
import { redirect } from 'next/navigation';

import { CLUB_COOKIE, ClubApiError, PANEL_LOGIN, type ClubMe } from './club';
import { INTERNAL_API_URL } from './env';
import { detailMessage } from './platform';
import { forwardedHost } from './tenant';

/**
 * Un request a la API del club por la red interna.
 *
 * Va SIN `/api` a proposito: esas son las rutas internas, las unicas donde el
 * backend acepta `X-SaaS-Host`. El SSR no tiene el Host del navegador, asi que
 * el club viaja en ese header (el navegador no puede mandarlo: el borde solo
 * enruta `/api`).
 */
export async function clubRequest<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const host = forwardedHost(await headers());
  if (host === '') throw new ClubApiError(400, 'no pude resolver el host del club');

  const requestHeaders = new Headers(init.headers);
  requestHeaders.set('x-saas-host', host);
  // FormData arma su propio boundary: fijar JSON rompe el multipart.
  if (!(init.body instanceof FormData)) {
    requestHeaders.set('content-type', 'application/json');
  }
  if (token) requestHeaders.set('authorization', `Bearer ${token}`);

  const response = await fetch(`${INTERNAL_API_URL}${path}`, {
    ...init,
    cache: 'no-store',
    headers: requestHeaders,
  });
  // 204 (baja de artículo): no hay cuerpo que parsear.
  if (response.status === 204) return undefined as T;

  const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
  if (!response.ok) {
    throw new ClubApiError(response.status, detailMessage(response.status, body?.detail));
  }
  return body as T;
}

/**
 * Sesion de admin del club, o redirect al login. Sin cookie, token vencido o
 * rol que no es `admin` no se renderiza nada del panel.
 *
 * Aca NO se borra la cookie: un server component no puede escribir cookies y
 * el token vencido se pisa solo en el proximo login.
 */
export async function requireClubAdmin(): Promise<{ token: string; me: ClubMe }> {
  const token = (await cookies()).get(CLUB_COOKIE)?.value;
  if (!token) redirect(PANEL_LOGIN);

  let me: ClubMe;
  try {
    me = await clubRequest<ClubMe>('/auth/me', {}, token);
  } catch (error) {
    if (error instanceof ClubApiError && (error.status === 401 || error.status === 403)) {
      redirect(`${PANEL_LOGIN}?expirado=1`);
    }
    throw error;
  }

  if (me.role !== 'admin') redirect(`${PANEL_LOGIN}?expirado=1`);
  return { token, me };
}
