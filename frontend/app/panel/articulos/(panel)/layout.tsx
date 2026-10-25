import type { ReactNode } from 'react';

import { SidebarInset, SidebarProvider } from '@mmanto/devbout-ui';

import { requireClubAdmin } from '@/lib/tenant-auth';

import { PanelHeader } from '../../panel-header';
import { PanelSidebar } from '../../panel-sidebar';

/**
 * Shell del panel autenticado: sidebar del club + inset con breadcrumb. El
 * login queda fuera del route group para no mostrar el shell antes de resolver
 * la sesion.
 */
export const dynamic = 'force-dynamic';

export default async function ArticulosLayout({ children }: { children: ReactNode }) {
  const { me } = await requireClubAdmin();

  return (
    <SidebarProvider>
      <PanelSidebar email={me.email} />
      <SidebarInset>
        <PanelHeader />
        <div className="flex flex-1 flex-col gap-4 p-4 pt-0">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  );
}
