'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { HugeiconsIcon } from '@hugeicons/react';
import {
  Home01Icon,
  LayoutBottomIcon,
  LogoutIcon,
  News01Icon,
  PlusSignIcon,
} from '@hugeicons/core-free-icons';
import {
  Avatar,
  AvatarFallback,
  Badge,
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

import { logoutAction } from './articulos/actions';
import { useTenantBranding } from './tenant-branding-provider';

interface NavItem {
  title: string;
  url: string;
  icon: typeof News01Icon;
  matches: (pathname: string) => boolean;
}

const NAV_ITEMS: NavItem[] = [
  {
    title: 'Artículos',
    url: '/panel/articulos',
    icon: News01Icon,
    matches: (pathname) =>
      pathname === '/panel/articulos' ||
      (pathname.startsWith('/panel/articulos/') && pathname !== '/panel/articulos/nueva'),
  },
  {
    title: 'Nuevo artículo',
    url: '/panel/articulos/nueva',
    icon: PlusSignIcon,
    matches: (pathname) => pathname === '/panel/articulos/nueva',
  },
];

export function PanelSidebar({ email }: { email: string }) {
  const pathname = usePathname();
  const branding = useTenantBranding();
  const clubName = branding?.display_name ?? 'Panel del portal';
  const clubSlug = branding?.tenant ?? 'Artículos';

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" render={<Link href="/panel/articulos" />}>
              {branding?.logo_url ? (
                // El logo llega como ruta relativa o URL del storage del club;
                // next/image exigiria configurar el dominio.
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={branding.logo_url}
                  alt={clubName}
                  width={32}
                  height={32}
                  className="size-8 rounded-lg object-contain"
                />
              ) : (
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <HugeiconsIcon icon={LayoutBottomIcon} strokeWidth={2} className="size-4" />
                </div>
              )}
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">{clubName}</span>
                <span className="truncate text-xs text-muted-foreground">{clubSlug}</span>
              </div>
              {branding && branding.status !== 'active' ? (
                <Badge
                  variant="warning"
                  className="text-[10px] group-data-[collapsible=icon]:hidden"
                >
                  {branding.status}
                </Badge>
              ) : null}
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
            <SidebarMenuItem>
              {/* Navegacion completa: el layout raiz cambia entre panel y sitio. */}
              <SidebarMenuButton tooltip="Ver sitio" render={<a href="/" />}>
                <HugeiconsIcon icon={Home01Icon} strokeWidth={2} />
                <span>Ver sitio</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
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
                <span className="truncate text-muted-foreground">admin del portal</span>
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
