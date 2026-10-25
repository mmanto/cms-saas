import { headers } from 'next/headers';

import { fetchHealth } from '@/lib/api';
import { ADMIN_HOST, API_BASE, BASE_DOMAIN, PINNED_TENANT } from '@/lib/env';
import { requestClub, siteForClub } from '@/lib/sites';
import { TENANT_HEADER, tenantFromHost, tenantFromRequest } from '@/lib/tenant';

export const dynamic = 'force-dynamic';

export default async function Home() {
  // Si el club del request tiene sitio propio, su home reemplaza la de la plataforma.
  const site = siteForClub(await requestClub());
  if (site) return site.home;

  const requestHeaders = await headers();
  const host = requestHeaders.get('host') ?? '';
  const tenant = tenantFromRequest(host, requestHeaders.get(TENANT_HEADER));
  const tenantSource = PINNED_TENANT
    ? 'SAAS_TENANT'
    : tenantFromHost(host)
      ? 'subdominio del dominio base'
      : tenant
        ? 'header del borde'
        : 'sin club';

  let apiStatus = 'sin verificar';
  try {
    const health = await fetchHealth();
    apiStatus = `${health.status} (${health.environment})`;
  } catch (error) {
    apiStatus = `error: ${error instanceof Error ? error.name : 'desconocido'}`;
  }

  return (
    <main style={{ maxWidth: 720, margin: '0 auto', padding: '4rem 1.5rem' }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', color: 'var(--brand)' }}>
        {tenant ? `Club: ${tenant}` : 'Plataforma SaaS Clubes'}
      </h1>
      <p style={{ color: '#9aa4bf' }}>
        Host resuelto por Traefik: <code>{host}</code>
        {tenant ? ` · club via ${tenantSource}` : ''}
      </p>
      <dl style={{ marginTop: '2rem', lineHeight: 1.9 }}>
        <dt style={{ color: '#9aa4bf' }}>Dominio base</dt>
        <dd>
          <code>{BASE_DOMAIN}</code>
        </dd>
        <dt style={{ color: '#9aa4bf' }}>API</dt>
        <dd>
          <code>
            {API_BASE}/v1/... (estado: {apiStatus})
          </code>
        </dd>
        <dt style={{ color: '#9aa4bf' }}>Login del club</dt>
        <dd>
          <code>POST {API_BASE}/v1/auth/login</code>
        </dd>
      </dl>
      <p style={{ marginTop: '2rem', color: '#9aa4bf', fontSize: '0.9rem' }}>
        Este host es la landing de la plataforma: los clubes viven en{' '}
        <code>&lt;slug&gt;.{BASE_DOMAIN}</code> y el backoffice en{' '}
        <code>{ADMIN_HOST}</code>.
      </p>
      {tenant === null ? (
        <p style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
          <a href={`//${ADMIN_HOST}/admin`} style={{ color: 'var(--brand)' }}>
            Backoffice de plataforma →
          </a>
        </p>
      ) : null}
    </main>
  );
}
