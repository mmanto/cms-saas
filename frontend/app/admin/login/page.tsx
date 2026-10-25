import { redirect } from 'next/navigation';

import { PlatformApiError, platformRequest, platformToken } from '@/lib/platform';

import { LoginForm } from './login-form';

export const dynamic = 'force-dynamic';

/** Con cookie valida no hay nada que loguear: se entra derecho. */
async function sessionAlive(token: string): Promise<boolean> {
  try {
    await platformRequest(token, '/me');
    return true;
  } catch (error) {
    // 401 esperado: la cookie quedo vieja. Cualquier otra cosa si es un error.
    if (error instanceof PlatformApiError) return false;
    throw error;
  }
}

export default async function AdminLoginPage({
  searchParams,
}: {
  searchParams: Promise<{ expirado?: string }>;
}) {
  const { expirado } = await searchParams;
  const token = await platformToken();
  // Si la cookie venciera, redirigir a /admin seria un ida y vuelta infinito:
  // mejor mostrar el formulario.
  if (token && (await sessionAlive(token))) redirect('/admin');

  return (
    <main className="flex min-h-svh items-center justify-center p-6">
      <LoginForm expirado={expirado === '1'} />
    </main>
  );
}
