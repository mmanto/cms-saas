'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { HugeiconsIcon } from '@hugeicons/react';
import {
  DashboardSquare01Icon,
  LayoutBottomIcon,
  LogoutIcon,
  PlusSignIcon,
} from '@hugeicons/core-free-icons';
import {
  Avatar,
  AvatarFallback,
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@mmanto/devbout-ui';

import { logoutAction } from './actions';

interface NavItem {
  title: string;
  url: string;
  icon: typeof DashboardSquare01Icon;
  /** Solo este item se marca en la ficha de un club. */
  matches: (pathname: string) => boolean;
}

const NAV_ITEMS: NavItem[] = [
  {
    title: 'Portales',
    url: '/admin',
    icon: DashboardSquare01Icon,
    matches: (pathname) =>
      pathname === '/admin' ||
      (pathname.startsWith('/admin/tenants/') && pathname !== '/admin/tenants/new'),
  },
  {
    title: 'Nuevo portal',
    url: '/admin/tenants/new',
    icon: PlusSignIcon,
    matches: (pathname) => pathname === '/admin/tenants/new',
  },
];

export function AdminSidebar({ email }: { email: string }) {
  const pathname = usePathname();

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" render={<Link href="/admin" />}>
              <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                <HugeiconsIcon icon={LayoutBottomIcon} strokeWidth={2} className="size-4" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">SaaS Portales</span>
                <span className="truncate text-xs text-muted-foreground">Backoffice</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu>
            {NAV_ITEMS.map((item) => (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton
                  isActive={item.matches(pathname)}
                  tooltip={item.title}
                  render={<Link href={item.url} />}
                >
                  <HugeiconsIcon icon={item.icon} strokeWidth={2} />
                  <span>{item.title}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <div className="flex items-center gap-2 px-2 py-1.5 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0">
              <Avatar className="size-7">
                <AvatarFallback className="text-[0.625rem]">
                  {email.slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="grid flex-1 text-left text-xs leading-tight group-data-[collapsible=icon]:hidden">
                <span className="truncate font-medium">{email}</span>
                <span className="truncate text-muted-foreground">admin de plataforma</span>
              </div>
            </div>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <form action={logoutAction}>
              <SidebarMenuButton type="submit" tooltip="Salir">
                <HugeiconsIcon icon={LogoutIcon} strokeWidth={2} />
                <span>Salir</span>
              </SidebarMenuButton>
            </form>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
