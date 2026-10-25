import type { ReactNode } from 'react';

import { SidebarInset, SidebarProvider } from '@mmanto/devbout-ui';

import { requirePlatformSession } from '@/lib/platform';

import { AdminHeader } from '../admin-header';
import { AdminSidebar } from '../admin-sidebar';

/**
 * Shell del backoffice autenticado: sidebar fija (colapsable) + inset con el
 * header de navegacion. El login queda fuera de este route group para que no
 * aparezca antes de resolver la sesion.
 */
export const dynamic = 'force-dynamic';

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const { me } = await requirePlatformSession();

  return (
    <SidebarProvider>
      <AdminSidebar email={me.email} />
      <SidebarInset>
        <AdminHeader />
        <div className="flex flex-1 flex-col gap-4 p-4 pt-0">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  );
}
