import { ADMIN_LABEL, BASE_DOMAIN, PINNED_TENANT } from './env';

/**
 * Header donde el borde anuncia el club (lo pone Traefik, no el cliente).
 * Ver backend/app/provisioning.py: los routers de dominio propio lo setean y
 * los del dominio base lo vacian.
 */
export const TENANT_HEADER = 'x-saas-tenant';

/**
 * Header que agrega `proxy.ts` a las rutas `/panel/*`: el layout raiz lo usa
 * para sacar el panel del shell del sitio. Es presentacion, no autorizacion.
 */
export const PANEL_HEADER = 'x-saas-panel';

const SLUG_RE = /^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$/;

/**
 * Labels del dominio base que NO son clubes: espeja `RESERVED_LABELS` de
 * `backend/app/tenancy.py`. `admin.<base>` es el backoffice de plataforma y el
 * resto esta guardado para servicios de la plataforma (`www`, `api`, `app`).
 */
const RESERVED_LABELS = new Set([ADMIN_LABEL, 'www', 'api', 'app']);

/**
 * Slug del club segun el Host que resolvio Traefik, o null en el dominio raiz,
 * en un label reservado (`admin.<base>`) o en un subdominio anidado.
 */
export function tenantFromHost(host: string | null | undefined): string | null {
  const clean = (host ?? '').split(':')[0]?.toLowerCase() ?? '';
  const suffix = `.${BASE_DOMAIN.toLowerCase()}`;
  if (!clean.endsWith(suffix)) return null;
  const label = clean.slice(0, -suffix.length);
  if (label === '' || label.includes('.') || RESERVED_LABELS.has(label)) return null;
  return label;
}

/**
 * Host real del request, sin puerto.
 *
 * Traefik pasa el `Host` original, pero el POST de una Server Action puede
 * llegar con el `Host` reescrito al del server de Next: el original viaja
 * siempre en `X-Forwarded-Host`, asi que manda ese cuando esta.
 */
export function forwardedHost(headerBag: { get(name: string): string | null }): string {
  const raw = headerBag.get('x-forwarded-host') ?? headerBag.get('host') ?? '';
  return raw.split(':')[0]?.toLowerCase() ?? '';
}

/**
 * Club del request, sin preguntarle nada a la API. Orden:
 *
 * 1. `SAAS_TENANT`: instancia dedicada a un club (una app por club).
 * 2. el subdominio del dominio base (`<slug>.<base>`): sale del Host
 *    que resolvio Traefik, asi que el cliente no lo puede inventar.
 * 3. `X-Saas-Tenant`: lo setea Traefik para los dominios propios (un host
 *    propio no dice de que club es).
 *
 * Los datos NO necesitan el slug: `/api/v1/...` se resuelve por Host en el
 * backend (RLS por tenant), asi que el frontend usa el slug solo para decidir
 * que mostrar.
 */
export function tenantFromRequest(
  host: string | null | undefined,
  tenantHeader: string | null | undefined,
): string | null {
  if (PINNED_TENANT) return PINNED_TENANT;

  const fromHost = tenantFromHost(host);
  if (fromHost) return fromHost;

  const announced = (tenantHeader ?? '').trim().toLowerCase();
  return SLUG_RE.test(announced) ? announced : null;
}
