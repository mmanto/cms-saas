import { INTERNAL_API_URL } from './env';

/** Branding del club. Lo arma el backend: ver backend/app/api/branding.py. */
export interface Branding {
  tenant: string;
  /** `active` o `suspended`: la app avisa si el club esta inactivo. */
  status: string;
  display_name: string;
  primary_color: string;
  logo_url: string | null;
}

/** Lo que se muestra si el host no tiene club o la API no contesta. */
export const FALLBACK_BRANDING: Branding = {
  tenant: '',
  status: 'active',
  display_name: 'SaaS Portales',
  primary_color: '#4f7cff',
  logo_url: null,
};

/**
 * Branding del club del request, para el SSR.
 *
 * Pega al endpoint interno (fuera de `/api`, el borde no lo enruta) porque el
 * server de Next no puede mandar el `Host` del navegador: se lo pasa en
 * `X-SaaS-Host`. El navegador, en cambio, usa `/api/v1/branding`: mismo origen,
 * mismo Host, mismo club. Ninguno de los dos "pregunta de quien es el host":
 * lo resuelve el backend igual que para cualquier otro request.
 */
export async function fetchBranding(host: string): Promise<Branding | null> {
  if (!host) return null;

  try {
    const response = await fetch(`${INTERNAL_API_URL}/tenant-branding`, {
      cache: 'no-store',
      headers: { 'x-saas-host': host },
    });
    if (!response.ok) return null;
    return (await response.json()) as Branding;
  } catch {
    return null;
  }
}
