import type { Metadata } from 'next';
import { headers } from 'next/headers';
import type { ReactNode } from 'react';

import { fetchBranding } from '@/lib/branding';
import { forwardedHost } from '@/lib/tenant';

import '../backoffice.css';
import { AppThemeProvider } from '../providers';
import { TenantBrandingProvider } from './tenant-branding-provider';

// El branding depende del Host: no hay nada que prerenderizar.
export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: {
    default: 'Panel del portal',
    template: '%s · Panel del portal',
  },
};

/**
 * Entrada del panel del club: el mismo design system que el backoffice de
 * plataforma (`app/backoffice.css`), con el branding del club en contexto para
 * el shell y el login. `proxy.ts` saca estas rutas del shell del sitio para
 * que sus resets no pisen las utilidades de Tailwind.
 */
export default async function PanelLayout({ children }: { children: ReactNode }) {
  const branding = await fetchBranding(forwardedHost(await headers()));

  return (
    <AppThemeProvider>
      <TenantBrandingProvider branding={branding}>
        <div className="min-h-svh bg-background font-sans text-foreground antialiased">
          {children}
        </div>
      </TenantBrandingProvider>
    </AppThemeProvider>
  );
}
