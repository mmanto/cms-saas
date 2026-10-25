'use client';

import { Fragment } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
  Separator,
  SidebarTrigger,
} from '@mmanto/devbout-ui';

interface Crumb {
  label: string;
  href?: string;
}

/** El nombre del club no esta en la URL: la ficha se rotula "Club". */
function crumbsFor(pathname: string): Crumb[] {
  if (pathname === '/admin') return [{ label: 'Clubes' }];

  if (pathname === '/admin/tenants/new') {
    return [{ label: 'Clubes', href: '/admin' }, { label: 'Nuevo club' }];
  }

  if (pathname.startsWith('/admin/tenants/')) {
    return [{ label: 'Clubes', href: '/admin' }, { label: 'Club' }];
  }

  const last = pathname.split('/').filter(Boolean).pop();
  return [{ label: 'Clubes', href: '/admin' }, { label: last ?? 'Backoffice' }];
}

export function AdminHeader() {
  const pathname = usePathname();
  const items = crumbsFor(pathname);

  return (
    <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
      <div className="flex items-center gap-2 px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator
          orientation="vertical"
          className="mr-2 data-vertical:h-4 data-vertical:self-auto"
        />
        <Breadcrumb>
          <BreadcrumbList>
            {items.map((item, index) => {
              const isLast = index === items.length - 1;

              return (
                <Fragment key={`${item.label}-${index}`}>
                  {index > 0 ? <BreadcrumbSeparator className="hidden md:block" /> : null}
                  <BreadcrumbItem className={isLast ? undefined : 'hidden md:block'}>
                    {isLast ? (
                      <BreadcrumbPage>{item.label}</BreadcrumbPage>
                    ) : item.href ? (
                      <BreadcrumbLink render={<Link href={item.href} />}>
                        {item.label}
                      </BreadcrumbLink>
                    ) : (
                      <span>{item.label}</span>
                    )}
                  </BreadcrumbItem>
                </Fragment>
              );
            })}
          </BreadcrumbList>
        </Breadcrumb>
      </div>
    </header>
  );
}
