import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { CLUB_COOKIE, ClubApiError, PANEL_ARTICULOS, type ClubMe } from '@/lib/club';
import { clubRequest } from '@/lib/tenant-auth';

import { ClubLoginForm } from './login-form';

export const dynamic = 'force-dynamic';

/** Con cookie valida y rol admin no hay nada que loguear: se entra derecho. */
async function sessionAlive(token: string): Promise<boolean> {
  try {
    const me = await clubRequest<ClubMe>('/auth/me', {}, token);
    return me.role === 'admin';
  } catch (error) {
    // 4xx esperado: la cookie quedo vieja. Cualquier otra cosa si es un error.
    if (error instanceof ClubApiError && error.status < 500) return false;
    throw error;
  }
}

export default async function ClubLoginPage({
  searchParams,
}: {
  searchParams: Promise<{ expirado?: string }>;
}) {
  const { expirado } = await searchParams;
  const token = (await cookies()).get(CLUB_COOKIE)?.value;
  // Si la cookie venciera, redirigir al panel seria un ida y vuelta infinito:
  // mejor mostrar el formulario.
  if (token && (await sessionAlive(token))) redirect(PANEL_ARTICULOS);

  return (
    <main className="flex min-h-svh items-center justify-center p-6">
      <ClubLoginForm expirado={expirado === '1'} />
    </main>
  );
}
