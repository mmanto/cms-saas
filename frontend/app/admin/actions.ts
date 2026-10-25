'use server';

import { revalidatePath } from 'next/cache';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import {
  PLATFORM_COOKIE,
  PlatformApiError,
  platformRequest,
  platformToken,
  type ActionState,
} from '@/lib/platform';

/** O el dato que devolvio la API, o un estado para el formulario. */
type ApiResult<T> = { data: T } | { state: ActionState };

function field(formData: FormData, name: string): string {
  return String(formData.get(name) ?? '').trim();
}

/** Valor crudo: en un password los espacios cuentan, asi que no se trimea. */
function raw(formData: FormData, name: string): string {
  return String(formData.get(name) ?? '');
}

function messageOf(error: unknown): string {
  return error instanceof PlatformApiError ? error.message : 'error inesperado';
}

/**
 * Corre una llamada a la API de plataforma con la cookie de la sesion.
 *
 * Aca adentro NUNCA se llama `redirect()`: Next la implementa tirando una
 * excepcion (NEXT_REDIRECT) y el catch la tragaria. El redirect lo hace la
 * accion, despues de que esto volvio bien.
 */
async function callApi<T>(fn: (token: string) => Promise<T>): Promise<ApiResult<T>> {
  const token = await platformToken();
  if (!token) return { state: { error: 'Sesion vencida: volve a entrar.' } };

  try {
    return { data: await fn(token) };
  } catch (error) {
    if (error instanceof PlatformApiError && error.status === 401) {
      (await cookies()).delete(PLATFORM_COOKIE);
      return { state: { error: 'Sesion vencida: volve a entrar.' } };
    }
    return { state: { error: messageOf(error) } };
  }
}

export async function loginAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const email = field(formData, 'email').toLowerCase();
  let token: string;
  try {
    // El login es lo unico que no lleva token: se lo pide a la API igual.
    const body = await platformRequest<{ access_token: string }>('', '/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password: raw(formData, 'password') }),
    });
    token = body.access_token;
  } catch (error) {
    if (error instanceof PlatformApiError && error.status === 401) {
      return { error: 'Credenciales invalidas' };
    }
    return { error: messageOf(error) };
  }

  // httpOnly: el token de plataforma no lo ve el JS del navegador.
  (await cookies()).set(PLATFORM_COOKIE, token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 60 * 60,
  });
  redirect('/admin');
}

export async function logoutAction(): Promise<void> {
  (await cookies()).delete(PLATFORM_COOKIE);
  redirect('/admin/login');
}

export async function createTenantAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const result = await callApi((token) =>
    platformRequest<{ id: string }>(token, '/tenants', {
      method: 'POST',
      body: JSON.stringify({
        slug: field(formData, 'slug').toLowerCase(),
        name: field(formData, 'name'),
        admin_email: field(formData, 'admin_email').toLowerCase(),
        admin_password: raw(formData, 'admin_password'),
      }),
    }),
  );
  if ('state' in result) return result.state;

  revalidatePath('/admin');
  redirect(`/admin/tenants/${result.data.id}`);
}

export async function patchTenantAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const tenantId = field(formData, 'tenant_id');
  const result = await callApi((token) =>
    platformRequest<unknown>(token, `/tenants/${tenantId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        name: field(formData, 'name'),
        status: field(formData, 'status'),
      }),
    }),
  );
  if ('state' in result) return result.state;

  revalidatePath(`/admin/tenants/${tenantId}`);
  return { ok: 'Guardado' };
}

export async function addDomainAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const tenantId = field(formData, 'tenant_id');
  const result = await callApi((token) =>
    platformRequest<unknown>(token, `/tenants/${tenantId}/domains`, {
      method: 'POST',
      body: JSON.stringify({ host: field(formData, 'host').toLowerCase() }),
    }),
  );
  if ('state' in result) return result.state;

  revalidatePath(`/admin/tenants/${tenantId}`);
  return { ok: 'Dominio agregado' };
}

export async function createUserAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const tenantId = field(formData, 'tenant_id');
  const result = await callApi((token) =>
    platformRequest<unknown>(token, `/tenants/${tenantId}/users`, {
      method: 'POST',
      body: JSON.stringify({
        email: field(formData, 'email').toLowerCase(),
        password: raw(formData, 'password'),
        role: field(formData, 'role'),
      }),
    }),
  );
  if ('state' in result) return result.state;

  revalidatePath(`/admin/tenants/${tenantId}`);
  return { ok: 'Usuario creado' };
}

export async function resetUserPasswordAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const tenantId = field(formData, 'tenant_id');
  const userId = field(formData, 'user_id');
  const result = await callApi((token) =>
    platformRequest<unknown>(token, `/tenants/${tenantId}/users/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify({ password: raw(formData, 'password') }),
    }),
  );
  if ('state' in result) return result.state;

  revalidatePath(`/admin/tenants/${tenantId}`);
  return { ok: 'Password actualizado' };
}

/** Quitar un dominio propio. Si ya no estaba, la pagina se recarga igual. */
export async function removeDomainAction(formData: FormData): Promise<void> {
  const tenantId = field(formData, 'tenant_id');
  const host = field(formData, 'host');
  const result = await callApi((token) =>
    platformRequest<unknown>(
      token,
      `/tenants/${tenantId}/domains/${encodeURIComponent(host)}`,
      { method: 'DELETE' },
    ),
  );
  if ('state' in result) return;

  revalidatePath(`/admin/tenants/${tenantId}`);
}

/** Baja del club: filas por CASCADE, objetos del storage y routes.yml. */
export async function deleteTenantAction(formData: FormData): Promise<void> {
  const tenantId = field(formData, 'tenant_id');
  const result = await callApi((token) =>
    platformRequest<unknown>(token, `/tenants/${tenantId}`, { method: 'DELETE' }),
  );
  if ('state' in result) return;

  revalidatePath('/admin');
  redirect('/admin');
}

/** Prender/apagar un modulo conectable del club. */
export async function toggleModuleAction(formData: FormData): Promise<void> {
  const tenantId = field(formData, 'tenant_id');
  const name = field(formData, 'module');
  const enabled = field(formData, 'enabled') === 'true';
  const result = await callApi((token) =>
    platformRequest<unknown>(
      token,
      `/tenants/${tenantId}/modules/${encodeURIComponent(name)}`,
      { method: 'PUT', body: JSON.stringify({ enabled }) },
    ),
  );
  if ('state' in result) return;

  revalidatePath(`/admin/tenants/${tenantId}`);
}

export async function syncRoutesAction(): Promise<void> {
  const result = await callApi((token) =>
    platformRequest<unknown>(token, '/routes/sync', { method: 'POST' }),
  );
  if ('state' in result) return;

  revalidatePath('/admin');
}
