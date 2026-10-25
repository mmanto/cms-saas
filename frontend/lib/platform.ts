import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { INTERNAL_API_URL } from './env';

/** Cookie httpOnly con el token de plataforma. La escribe una Server Action. */
export const PLATFORM_COOKIE = 'saas_platform_session';

const PLATFORM_API = `${INTERNAL_API_URL}/api/v1/platform`;

export interface PlatformMe {
  id: string;
  email: string;
  created_at: string;
}

export interface TenantDomainInfo {
  host: string;
  is_primary: boolean;
}

export interface TenantSummary {
  id: string;
  slug: string;
  name: string;
  status: string;
  domains: TenantDomainInfo[];
}

export interface TenantUserInfo {
  id: string;
  email: string;
  role: string;
  created_at: string;
}

/** Modulo conectable con el switch de un club. */
export interface ModuleInfo {
  name: string;
  title: string;
  description: string;
  enabled: boolean;
}

export interface TenantDetail extends TenantSummary {
  created_at: string;
  users: TenantUserInfo[];
  assets: number;
  modules: ModuleInfo[];
}

/** Estado que devuelven las Server Actions a los formularios. */
export interface ActionState {
  error?: string;
  ok?: string;
}

/** Error de la API de plataforma, con el status a mano para distinguir el 401. */
export class PlatformApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'PlatformApiError';
  }
}

/**
 * El `detail` de FastAPI: un string en los 4xx de negocio, y la lista de
 * errores de pydantic en los 422. Sin esto, un 422 se ve como "[object Object]".
 */
export function detailMessage(status: number, detail: unknown): string {
  if (typeof detail === 'string' && detail.trim() !== '') return detail;

  if (Array.isArray(detail)) {
    const parts = detail.map((item) => {
      const entry = item as { loc?: unknown[]; msg?: string };
      // `loc` viene como ["body", "slug"]; el nombre del campo alcanza.
      const field = (entry.loc ?? []).slice(1).join('.');
      const problem = entry.msg ?? 'invalido';
      return field === '' ? problem : `${field}: ${problem}`;
    });
    if (parts.length > 0) return parts.join('; ');
  }

  return `la API respondio ${status}`;
}

/**
 * Un request a la API de plataforma, con el token en el header.
 *
 * Sale por la red interna de Docker (no por el borde): el backoffice es
 * server-side, asi que el token nunca viaja al navegador ni hay CORS de por
 * medio.
 */
export async function platformRequest<T>(
  token: string,
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('content-type', 'application/json');
  headers.set('authorization', `Bearer ${token}`);

  const response = await fetch(`${PLATFORM_API}${path}`, {
    ...init,
    cache: 'no-store',
    headers,
  });
  // 204 (baja de club): no hay cuerpo que parsear.
  if (response.status === 204) return undefined as T;

  const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
  if (!response.ok) {
    throw new PlatformApiError(response.status, detailMessage(response.status, body?.detail));
  }
  return body as T;
}

/** Token de la cookie, si hay sesion. */
export async function platformToken(): Promise<string | undefined> {
  return (await cookies()).get(PLATFORM_COOKIE)?.value;
}

/**
 * Sesion valida, o redirect al login. Sin cookie o con el token vencido no se
 * renderiza nada del backoffice.
 */
export async function requirePlatformSession(): Promise<{ token: string; me: PlatformMe }> {
  const token = await platformToken();
  if (!token) redirect('/admin/login');
  try {
    return { token, me: await platformRequest<PlatformMe>(token, '/me') };
  } catch (error) {
    if (error instanceof PlatformApiError && error.status === 401) {
      redirect('/admin/login?expirado=1');
    }
    throw error;
  }
}
