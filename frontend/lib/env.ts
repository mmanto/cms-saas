/** Configuracion del frontend. Solo las NEXT_PUBLIC_* llegan al navegador. */

/**
 * Dominio base del SaaS: los clubes viven en `<slug>.<base>`, el backoffice en
 * `admin.<base>` y el apex es la landing. Chrome/Edge resuelven `*.localhost`
 * al loopback.
 */
export const BASE_DOMAIN: string = process.env.SAAS_BASE_DOMAIN ?? 'cms-sas.localhost';

/**
 * Label reservado del backoffice de plataforma. Espeja `ADMIN_LABEL` de
 * `backend/app/tenancy.py`: ningún club puede tener ese slug.
 */
export const ADMIN_LABEL = 'admin';

/** Host del backoffice de plataforma: `admin.<base>`. */
export const ADMIN_HOST: string = `${ADMIN_LABEL}.${BASE_DOMAIN.toLowerCase()}`;

/** Base de la API tal como la ve el navegador: relativa y del mismo origen. */
export const API_BASE: string = process.env.NEXT_PUBLIC_API_BASE ?? '/api';

// En SSR hay que salir sin dar la vuelta por el borde: la red interna.
export const INTERNAL_API_URL: string =
  process.env.INTERNAL_API_URL || 'http://127.0.0.1:8000';

/**
 * Club que se sirve en el dominio base (apex). Vacio = la landing de
 * plataforma. Lo setea el operador para que el propio gestor sea un portal
 * (ej. elatech.io). El backend lo usa igual en `resolve_tenant`.
 */
export const BASE_TENANT: string | null =
  process.env.SAAS_BASE_TENANT?.trim().toLowerCase() || null;

/**
 * Instancia dedicada a un solo club (una app por club): si esta seteado, el
 * frontend sabe que club es y no deduce nada. Vacio = instancia compartida.
 */
export const PINNED_TENANT: string | null =
  process.env.SAAS_TENANT?.trim().toLowerCase() || null;
