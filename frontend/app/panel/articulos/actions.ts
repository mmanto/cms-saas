'use server';

import { revalidatePath } from 'next/cache';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import type { ActionState } from '@/lib/platform';
import {
  CLUB_COOKIE,
  ClubApiError,
  PANEL_LOGIN,
  PANEL_ARTICULOS,
  clubMessageOf,
} from '@/lib/club';
import { clubRequest } from '@/lib/tenant-auth';

/** O el dato que devolvio la API, o un estado para el formulario. */
type ApiResult<T> = { data: T } | { state: ActionState };

function field(formData: FormData, name: string): string {
  return String(formData.get(name) ?? '').trim();
}

/** Valor crudo: en un password los espacios cuentan, asi que no se trimea. */
function raw(formData: FormData, name: string): string {
  return String(formData.get(name) ?? '');
}

/** El `slug` vacio se manda como null: que lo derive la API del titulo. */
function articleBody(formData: FormData): Record<string, unknown> {
  return {
    title: field(formData, 'title'),
    slug: field(formData, 'slug') || null,
    content: raw(formData, 'content'),
    excerpt: field(formData, 'excerpt'),
    category: field(formData, 'category'),
    status: field(formData, 'status'),
    author: field(formData, 'author'),
  };
}

/** Sube o borra la imagen del articulo, si el formulario lo pide. */
async function saveArticleImage(
  formData: FormData,
  articleId: string,
  token: string,
): Promise<void> {
  if (formData.get('remove_image') === '1') {
    await clubRequest<unknown>(`/articles/${articleId}/image`, { method: 'DELETE' }, token);
    return;
  }

  const image = formData.get('image');
  if (!(image instanceof File) || image.size === 0) return;

  const upload = new FormData();
  upload.set('file', image);
  await clubRequest<unknown>(
    `/articles/${articleId}/image`,
    { method: 'PUT', body: upload },
    token,
  );
}

/**
 * Corre una llamada a la API del club con la cookie de la sesion.
 *
 * Aca adentro NUNCA se llama `redirect()`: Next la implementa tirando una
 * excepcion (NEXT_REDIRECT) y el catch la tragaria. El redirect lo hace la
 * accion, despues de que esto volvio bien.
 */
async function callApi<T>(fn: (token: string) => Promise<T>): Promise<ApiResult<T>> {
  const token = (await cookies()).get(CLUB_COOKIE)?.value;
  if (!token) return { state: { error: 'Sesion vencida: volve a entrar.' } };

  try {
    return { data: await fn(token) };
  } catch (error) {
    if (error instanceof ClubApiError && (error.status === 401 || error.status === 403)) {
      (await cookies()).delete(CLUB_COOKIE);
      return { state: { error: 'Sesion vencida: volve a entrar.' } };
    }
    return { state: { error: clubMessageOf(error) } };
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
    const body = await clubRequest<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password: raw(formData, 'password') }),
    });
    token = body.access_token;
  } catch (error) {
    if (error instanceof ClubApiError && error.status === 401) {
      return { error: 'Credenciales invalidas' };
    }
    return { error: clubMessageOf(error) };
  }

  // httpOnly: el token del club no lo ve el JS del navegador. Una hora, que es
  // lo que dura el token (ACCESS_TOKEN_TTL_MINUTES).
  (await cookies()).set(CLUB_COOKIE, token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 60 * 60,
  });
  redirect(PANEL_ARTICULOS);
}

export async function logoutAction(): Promise<void> {
  (await cookies()).delete(CLUB_COOKIE);
  redirect(PANEL_LOGIN);
}

export async function createArticleAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const result = await callApi(async (token) => {
    const created = await clubRequest<{ id: string }>(
      '/articles',
      { method: 'POST', body: JSON.stringify(articleBody(formData)) },
      token,
    );
    await saveArticleImage(formData, created.id, token);
    return created;
  });
  if ('state' in result) return result.state;

  revalidatePath(PANEL_ARTICULOS);
  redirect(PANEL_ARTICULOS);
}

export async function updateArticleAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const id = field(formData, 'id');
  const result = await callApi(async (token) => {
    const updated = await clubRequest<unknown>(
      `/articles/${id}`,
      { method: 'PUT', body: JSON.stringify(articleBody(formData)) },
      token,
    );
    await saveArticleImage(formData, id, token);
    return updated;
  });
  if ('state' in result) return result.state;

  revalidatePath(PANEL_ARTICULOS);
  redirect(PANEL_ARTICULOS);
}

/** Publicar / despublicar / archivar desde la lista. */
export async function setStatusAction(formData: FormData): Promise<void> {
  const id = field(formData, 'id');
  const status = field(formData, 'status');
  const result = await callApi((token) =>
    clubRequest<unknown>(
      `/articles/${id}`,
      { method: 'PUT', body: JSON.stringify({ status }) },
      token,
    ),
  );
  if ('state' in result) return;

  revalidatePath(PANEL_ARTICULOS);
}

/** Baja de un artículo. Si ya no estaba (404), la lista se recarga igual. */
export async function deleteArticleAction(formData: FormData): Promise<void> {
  const id = field(formData, 'id');
  const token = (await cookies()).get(CLUB_COOKIE)?.value;
  if (!token) redirect(PANEL_LOGIN);

  try {
    await clubRequest<unknown>(`/articles/${id}`, { method: 'DELETE' }, token);
  } catch (error) {
    // 404 = ya no existe, o el modulo se apago: el resultado que busca el
    // usuario (que el artículo no este) es el mismo.
    if (!(error instanceof ClubApiError && error.status === 404)) throw error;
  }

  revalidatePath(PANEL_ARTICULOS);
  redirect(PANEL_ARTICULOS);
}
