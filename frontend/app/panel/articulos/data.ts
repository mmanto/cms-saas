import { redirect } from 'next/navigation';

import { ClubApiError, PANEL_LOGIN, type ClubArticle } from '@/lib/club';
import { clubRequest } from '@/lib/tenant-auth';

/**
 * Todos los artículos del club (publicadas, borradores y archivadas), o `null`
 * si el modulo esta apagado en este club: para el panel ese es un estado, no un
 * error. Un token vencido, en cambio, manda al login.
 */
export async function clubArticles(token: string): Promise<ClubArticle[] | null> {
  try {
    return await clubRequest<ClubArticle[]>('/articles/all', {}, token);
  } catch (error) {
    if (error instanceof ClubApiError && error.status === 404) return null;
    // El token puede vencer entre `requireClubAdmin` y la query: mismo criterio.
    if (error instanceof ClubApiError && (error.status === 401 || error.status === 403)) {
      redirect(`${PANEL_LOGIN}?expirado=1`);
    }
    throw error;
  }
}
