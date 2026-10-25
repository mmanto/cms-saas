import { INTERNAL_API_URL } from './env';

/** GET /health: liveness de la API, no toca dependencias. */
export interface Health {
  status: string;
  environment: string;
}

/**
 * Liveness de la API. Sale por la red interna de Docker: /health no se expone
 * por el borde a proposito (ver backend/app/api/health.py).
 */
export async function fetchHealth(): Promise<Health> {
  const response = await fetch(`${INTERNAL_API_URL}/health`, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`/health respondio ${response.status}`);
  }
  return (await response.json()) as Health;
}
