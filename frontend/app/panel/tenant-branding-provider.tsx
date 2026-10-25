'use client';

import * as React from 'react';

import type { Branding } from '@/lib/branding';

const TenantBrandingContext = React.createContext<Branding | null>(null);

/**
 * Branding del club resuelto en el server (SSR): nombre, logo y estado. Las
 * variables CSS del tenant no se usan aca; el design system mantiene sus
 * tokens y el shell muestra la identidad del club con estos datos.
 */
export function TenantBrandingProvider({
  branding,
  children,
}: {
  branding: Branding | null;
  children: React.ReactNode;
}) {
  return (
    <TenantBrandingContext.Provider value={branding}>
      {children}
    </TenantBrandingContext.Provider>
  );
}

export function useTenantBranding(): Branding | null {
  return React.useContext(TenantBrandingContext);
}
