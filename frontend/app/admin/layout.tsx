import type { Metadata } from 'next';
import { headers } from 'next/headers';
import { notFound } from 'next/navigation';
import type { ReactNode } from 'react';

import { ADMIN_HOST } from '@/lib/env';
import { forwardedHost } from '@/lib/tenant';

import '../backoffice.css';
import { AppThemeProvider } from '../providers';

// La guarda depende del Host del request: no hay nada que prerenderizar.
export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: {
    default: 'Backoffice',
    template: '%s · Backoffice SaaS Clubes',
  },
};

/**
 * El backoffice vive SOLO en `admin.<dominio base>`: en el apex (que es la
 * landing) y en el host de un club no existe, y devuelve 404. Un admin de
 * plataforma no tiene por que estar parado en el host de nadie. El borde le da
 * a ese host sus propios routers (ver `backend/app/provisioning.py`).
 *
 * El shell con sidebar vive en `(dashboard)/layout.tsx` para que el login
 * (fuera del route group) no lo muestre antes de resolver la sesion.
 */
export default async function AdminLayout({ children }: { children: ReactNode }) {
  const requestHeaders = await headers();
  if (forwardedHost(requestHeaders) !== ADMIN_HOST) notFound();

  return (
    <AppThemeProvider>
      <div className="min-h-svh bg-background font-sans text-foreground antialiased">
        {children}
      </div>
    </AppThemeProvider>
  );
}
