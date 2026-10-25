import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';

import type { ClubSite } from '@/lib/sites';

import { AuxilioHome } from './AuxilioHome';

/**
 * Sitio del tenant de ejemplo (Auxilio RB).
 *
 * Reemplaza el shell de la plataforma en el host de ese club: header, hero,
 * servicios, cobertura, mapa, artículos (con articulos locales) y contacto. El
 * CSS vive en `styles/auxiliosrb.css` (clases `ax-*`, resets bajo
 * `.auxiliosrb-app`) y se importa desde `app/layout.tsx`.
 */
const metadata: Metadata = {
  title: 'Auxilio RB - Servicio de Grúa Profesional 24/7',
  description:
    'Servicio de grúa profesional 24/7. Rápido, seguro y confiable en toda la ciudad.',
  applicationName: 'Auxilio RB',
  icons: { icon: '/auxiliosrb/favicon.svg' },
  openGraph: {
    type: 'website',
    locale: 'es_AR',
    title: 'Auxilio RB - Servicio de Grúa Profesional 24/7',
    description:
      'Servicio de grúa profesional 24/7. Rápido, seguro y confiable en toda la ciudad.',
    images: ['/auxiliosrb/f1.webp'],
  },
};

const viewport: Viewport = {
  themeColor: '#22c55e',
  width: 'device-width',
  initialScale: 1,
};

/** Contenedor del sitio: el CSS cuelga de esta clase. */
function AuxilioShell({ children }: { children: ReactNode }) {
  return <div className="auxiliosrb-app">{children}</div>;
}

export const auxiliosrb: ClubSite = {
  id: 'auxiliosrb',
  club: 'demo',
  metadata,
  viewport,
  head: (
    <>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link
        href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
        rel="stylesheet"
      />
    </>
  ),
  Shell: AuxilioShell,
  home: <AuxilioHome />,
  notFound: (
    <main
      style={{
        display: 'grid',
        placeItems: 'center',
        minHeight: '100vh',
        padding: '2rem',
        background: '#fff',
        color: '#111827',
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ margin: '0 0 1rem', fontSize: '2rem' }}>Página no encontrada</h1>
        <a href="/" style={{ color: '#16a34a', fontWeight: 600 }}>
          Volver al inicio
        </a>
      </div>
    </main>
  ),
};
