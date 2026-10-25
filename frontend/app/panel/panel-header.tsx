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

function crumbsFor(pathname: string): Crumb[] {
  if (pathname === '/panel/articulos') return [{ label: 'Artículos' }];

  if (pathname === '/panel/articulos/nueva') {
    return [{ label: 'Artículos', href: '/panel/articulos' }, { label: 'Nuevo artículo' }];
  }

  if (pathname.startsWith('/panel/articulos/')) {
    return [{ label: 'Artículos', href: '/panel/articulos' }, { label: 'Editar artículo' }];
  }

  return [{ label: 'Artículos', href: '/panel/articulos' }];
}

export function PanelHeader() {
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
