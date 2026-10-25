import Link from 'next/link';

import { HugeiconsIcon } from '@hugeicons/react';
import { PlusSignIcon, RefreshIcon } from '@hugeicons/core-free-icons';
import {
  Badge,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@mmanto/devbout-ui';

import { platformRequest, requirePlatformSession, type TenantSummary } from '@/lib/platform';

import { syncRoutesAction } from '../actions';

export const dynamic = 'force-dynamic';

/** El dominio primario primero: es el que el operador usa para entrar al club. */
function primaryFirst(tenant: TenantSummary): TenantSummary['domains'] {
  return [...tenant.domains].sort((a, b) => Number(b.is_primary) - Number(a.is_primary));
}

function statusVariant(status: string): 'success' | 'warning' | 'outline' {
  if (status === 'active') return 'success';
  if (status === 'suspended') return 'warning';
  return 'outline';
}

export default async function AdminHome() {
  const { token, me } = await requirePlatformSession();
  const tenants = await platformRequest<TenantSummary[]>(token, '/tenants');

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-col gap-1">
          <h1 className="font-heading heading-screen font-medium">Clubes</h1>
          <p className="text-sm text-muted-foreground">
            Operá los clubes de la plataforma. Sesión: <span className="text-foreground">{me.email}</span>
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <form action={syncRoutesAction}>
            <Button type="submit" variant="outline">
              <HugeiconsIcon icon={RefreshIcon} strokeWidth={2} />
              Sincronizar rutas
            </Button>
          </form>
          <Button render={<Link href="/admin/tenants/new" />}>
            <HugeiconsIcon icon={PlusSignIcon} strokeWidth={2} />
            Nuevo club
          </Button>
        </div>
      </div>

      {tenants.length === 0 ? (
        <div className="rounded-xl border border-dashed p-8 text-center">
          <p className="text-sm font-medium">Sin clubes todavía</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Creá el primero para empezar a operar la plataforma.
          </p>
        </div>
      ) : (
        <section className="overflow-hidden rounded-xl border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="px-4">Slug</TableHead>
                <TableHead className="px-4">Nombre</TableHead>
                <TableHead className="px-4">Estado</TableHead>
                <TableHead className="px-4">Dominios</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tenants.map((tenant) => (
                <TableRow key={tenant.id}>
                  <TableCell className="px-4">
                    <Link
                      href={`/admin/tenants/${tenant.id}`}
                      className="font-medium underline-offset-4 hover:underline"
                    >
                      {tenant.slug}
                    </Link>
                  </TableCell>
                  <TableCell className="px-4">{tenant.name}</TableCell>
                  <TableCell className="px-4">
                    <Badge variant={statusVariant(tenant.status)}>{tenant.status}</Badge>
                  </TableCell>
                  <TableCell className="px-4">
                    <div className="flex flex-col gap-0.5">
                      {primaryFirst(tenant).map((domain) => (
                        <span key={domain.host} className="text-xs">
                          <a
                            href={`http://${domain.host}`}
                            className="underline-offset-4 hover:underline"
                          >
                            {domain.host}
                          </a>
                          {domain.is_primary ? ' ★' : ''}
                        </span>
                      ))}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>
      )}
    </>
  );
}
