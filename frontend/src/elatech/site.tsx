import { createElement } from 'react';
import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';
import Script from 'next/script';

import type { ClubSite } from '@/lib/sites';

import { ElatechHome } from './ElatechHome';

/**
 * Sitio de ElaTech (`elatech.io`).
 *
 * Puerta de la landing original (Vite + Tailwind) al club `elatech` del SaaS:
 * el chrome, las secciones y los estilos viven en `src/elatech/`. Los bloques
 * de capacitaciones y proyectos se alimentan del modulo `articles` de ese club.
 *
 * El chatbot es el widget que ya traia la landing (`index.html`); se carga
 * despues de la hidratacion para no bloquear el primer render.
 */
const CHATBOT_SRC = 'https://chatbot.elatech.io/widget/chatbot-widget.mjs';
const CHATBOT_API_URL = 'https://api-chatbot.elatech.io/api/chatbot';
const CHATBOT_API_KEY = 'a170afa5a0191ebe7c455e08fb807bcdc1ef6b78e284c454932d6eca3a937995';

const metadata: Metadata = {
  title: 'elatech.io | Consultoría y Capacitación Informática',
  description:
    'elatech.io - Consultoría y capacitación informática. Transformamos tu negocio con tecnología. Desarrollo de software, capacitaciones y relevamiento tecnológico.',
  keywords: [
    'consultoría tecnológica',
    'capacitación informática',
    'desarrollo de software',
    'transformación digital',
    'Argentina',
  ],
  authors: [{ name: 'elatech.io' }],
  applicationName: 'elatech.io',
  icons: { icon: '/elatech/logo-e.svg' },
  openGraph: {
    type: 'website',
    locale: 'es_AR',
    siteName: 'elatech.io',
    title: 'elatech.io | Consultoría y Capacitación Informática',
    description:
      'elatech.io - Consultoría y capacitación informática. Transformamos tu negocio con tecnología. Desarrollo de software, capacitaciones y relevamiento tecnológico.',
  },
};

const viewport: Viewport = {
  themeColor: '#0D1B38',
  width: 'device-width',
  initialScale: 1,
};

/** Contenedor del sitio: el CSS cuelga de esta clase. */
function ElatechShell({ children }: { children: ReactNode }) {
  return (
    <div className="elatech-app">
      {children}
      {createElement('chatbot-widget', {
        apikey: CHATBOT_API_KEY,
        apiurl: CHATBOT_API_URL,
      })}
      <Script src={CHATBOT_SRC} strategy="afterInteractive" type="module" />
    </div>
  );
}

export const elatech: ClubSite = {
  id: 'elatech',
  club: 'elatech',
  metadata,
  viewport,
  head: (
    <>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link
        href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&family=Inter:wght@300;400;500;600&display=swap"
        rel="stylesheet"
      />
    </>
  ),
  Shell: ElatechShell,
  home: <ElatechHome />,
  notFound: (
    <main
      style={{
        display: 'grid',
        placeItems: 'center',
        minHeight: '100vh',
        padding: '2rem',
        background: '#fff',
        color: '#111827',
        fontFamily: 'Inter, system-ui, sans-serif',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ margin: '0 0 1rem', fontSize: '2rem' }}>Página no encontrada</h1>
        <a href="/" style={{ color: '#2793b4', fontWeight: 600 }}>
          Volver al inicio
        </a>
      </div>
    </main>
  ),
};
