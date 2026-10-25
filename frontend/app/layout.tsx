import type { Metadata, Viewport } from 'next';
import type { CSSProperties, ReactNode } from 'react';
import { headers } from 'next/headers';
import { Geist_Mono, Inter } from 'next/font/google';

import { FALLBACK_BRANDING, fetchBranding } from '@/lib/branding';
import { ADMIN_HOST } from '@/lib/env';
import { requestClub, siteForClub } from '@/lib/sites';
import { PANEL_HEADER, forwardedHost } from '@/lib/tenant';

// Cada sitio trae su propio CSS, acotado a su contenedor: Auxilio RB con clases
// `ax-*` bajo `.auxiliosrb-app` y ElaTech con Tailwind v4 bajo `.elatech-app`
// (sin preflight global). Importarlos aca permite servirlos desde Next sin
// tocar el shell de la plataforma ni el backoffice.
import '../src/auxiliosrb/styles/auxiliosrb.css';
import '../src/elatech/styles/elatech.css';

// El layout depende del Host (branding y sitio por club): nada de esto se puede
// prerenderizar.
export const dynamic = 'force-dynamic';

// El backoffice usa la tipografia del design system (Inter + Geist Mono). Se
// exponen como variables CSS en <html> solo en ese host: el sitio del club no
// carga la hoja de Tailwind, asi que no hereda estos valores.
const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });
const fontMono = Geist_Mono({ subsets: ['latin'], variable: '--font-mono' });

const PLATFORM_METADATA: Metadata = {
  title: 'SaaS Clubes',
  description: 'Plataforma multi-tenant para clubes',
};

/** Metadatos del club del request: los de su sitio, o los de la plataforma. */
export async function generateMetadata(): Promise<Metadata> {
  return siteForClub(await requestClub())?.metadata ?? PLATFORM_METADATA;
}

/** Viewport del club del request: lo aporta el sitio; la plataforma no agrega nada. */
export async function generateViewport(): Promise<Viewport> {
  return siteForClub(await requestClub())?.viewport ?? {};
}

export default async function RootLayout({ children }: { children: ReactNode }) {
  const site = siteForClub(await requestClub());
  const requestHeaders = await headers();

  // Los backoffices (plataforma y panel del club) tienen su propio shell
  // (sidebar + tokens del design system): ni el chrome de la plataforma ni el
  // del sitio se pintan, y el body no lleva estilos inline, que ganarian sobre
  // `html`/`body` de `app/backoffice.css`. `proxy.ts` marca las rutas /panel/*.
  const isBackoffice =
    requestHeaders.get(PANEL_HEADER) === '1' ||
    forwardedHost(requestHeaders) === ADMIN_HOST;

  if (isBackoffice) {
    return (
      <html
        lang="es"
        suppressHydrationWarning
        className={`${inter.variable} ${fontMono.variable}`}
      >
        <body>{children}</body>
      </html>
    );
  }

  // Club con sitio propio: su chrome y su <head>, sin el de la plataforma.
  if (site) {
    return (
      <html lang="es">
        <head>{site.head}</head>
        <body>
          <site.Shell>{children}</site.Shell>
        </body>
      </html>
    );
  }

  const branding =
    (await fetchBranding(requestHeaders.get('host') ?? '')) ?? FALLBACK_BRANDING;

  return (
    <html lang="es">
      <body
        style={
          {
            margin: 0,
            fontFamily: 'system-ui, -apple-system, Segoe UI, sans-serif',
            background: '#0b1020',
            color: '#e8ebf5',
            // Un solo color por club: el resto de la UI lo usa con var(--brand).
            '--brand': branding.primary_color,
          } as CSSProperties
        }
      >
        <header
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid #1d2740',
          }}
        >
          {branding.logo_url ? (
            <img src={branding.logo_url} alt={branding.display_name} height={36} />
          ) : (
            <span
              style={{
                width: 36,
                height: 36,
                borderRadius: 8,
                background: 'var(--brand)',
                display: 'inline-block',
              }}
            />
          )}
          <strong>{branding.display_name}</strong>
        </header>
        {branding.tenant !== '' && branding.status !== 'active' ? (
          <div style={{ padding: '0.75rem 1.5rem', background: '#3b1d1d', color: '#ffb4b4' }}>
            este club esta inactivo: la API esta cerrada.
          </div>
        ) : null}
        {children}
      </body>
    </html>
  );
}
