import type { ReactNode } from 'react';
import Link from 'next/link';
import { notFound } from 'next/navigation';

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

import {
  PlatformApiError,
  platformRequest,
  requirePlatformSession,
  type TenantDetail,
} from '@/lib/platform';

import { deleteTenantAction, removeDomainAction, toggleModuleAction } from '../../../actions';
import { DomainForm, PatchForm, ResetPasswordForm, UserForm } from './forms';

export const dynamic = 'force-dynamic';

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl border bg-card">
      <div className="border-b p-4">
        <h2 className="font-heading heading-section font-medium">{title}</h2>
        {description ? <p className="mt-1 text-xs text-muted-foreground">{description}</p> : null}
      </div>
      <div className="p-4">{children}</div>
    </section>
  );
}

export default async function TenantPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { token } = await requirePlatformSession();

  let tenant: TenantDetail;
  try {
    tenant = await platformRequest<TenantDetail>(token, `/tenants/${id}`);
  } catch (error) {
    if (error instanceof PlatformApiError && error.status === 404) notFound();
    throw error;
  }

  return (
    <>
      <div className="flex flex-col gap-1">
        <Link
          href="/admin"
          className="text-xs text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          ← Clubes
        </Link>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <h1 className="font-heading heading-screen font-medium">{tenant.name}</h1>
          <Badge variant={tenant.status === 'active' ? 'success' : 'warning'}>
            {tenant.status}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          <code>{tenant.slug}</code> · creado el{' '}
          {new Date(tenant.created_at).toLocaleDateString('es-AR')} · {tenant.assets} archivo(s)
        </p>
      </div>

      <Section title="Datos">
        <PatchForm tenant={tenant} />
      </Section>

      <Section
        title="Dominios"
        description="El subdominio del dominio base lo cubre el router wildcard. Los dominios propios se escriben en routes.yml y Traefik los toma solo."
      >
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="px-4">Host</TableHead>
              <TableHead className="px-4">Primario</TableHead>
              <TableHead className="px-4" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {tenant.domains.map((domain) => (
              <TableRow key={domain.host}>
                <TableCell className="px-4">
                  <a
                    href={`http://${domain.host}`}
                    className="underline-offset-4 hover:underline"
                  >
                    {domain.host}
                  </a>
                </TableCell>
                <TableCell className="px-4">{domain.is_primary ? '★' : ''}</TableCell>
                <TableCell className="px-4">
                  {domain.is_primary ? null : (
                    <form action={removeDomainAction}>
                      <input type="hidden" name="tenant_id" value={tenant.id} />
                      <input type="hidden" name="host" value={domain.host} />
                      <Button type="submit" variant="destructive" size="sm">
                        Quitar
                      </Button>
                    </form>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="mt-4 border-t pt-4">
          <DomainForm tenantId={tenant.id} />
        </div>
      </Section>

      <Section title="Usuarios">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="px-4">Email</TableHead>
              <TableHead className="px-4">Rol</TableHead>
              <TableHead className="px-4">Password</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tenant.users.map((user) => (
              <TableRow key={user.id}>
                <TableCell className="px-4">{user.email}</TableCell>
                <TableCell className="px-4">
                  <Badge variant="secondary">{user.role}</Badge>
                </TableCell>
                <TableCell className="px-4">
                  <ResetPasswordForm
                    tenantId={tenant.id}
                    userId={user.id}
                    email={user.email}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="mt-4 border-t pt-4">
          <UserForm tenantId={tenant.id} />
        </div>
      </Section>

      <Section
        title="Módulos"
        description="Los módulos conectables se encienden por club. Uno apagado no atiende su API y su sección no se pinta en el sitio."
      >
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="px-4">Módulo</TableHead>
              <TableHead className="px-4">Estado</TableHead>
              <TableHead className="px-4" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {tenant.modules.map((module) => (
              <TableRow key={module.name}>
                <TableCell className="whitespace-normal px-4">
                  <strong className="font-medium">{module.title}</strong>
                  <span className="mt-0.5 block text-xs text-muted-foreground">
                    {module.description}
                  </span>
                </TableCell>
                <TableCell className="px-4">
                  <Badge variant={module.enabled ? 'success' : 'outline'}>
                    {module.enabled ? 'habilitado' : 'apagado'}
                  </Badge>
                </TableCell>
                <TableCell className="px-4">
                  <form action={toggleModuleAction}>
                    <input type="hidden" name="tenant_id" value={tenant.id} />
                    <input type="hidden" name="module" value={module.name} />
                    <input
                      type="hidden"
                      name="enabled"
                      value={module.enabled ? 'false' : 'true'}
                    />
                    <Button type="submit" variant="outline" size="sm">
                      {module.enabled ? 'Apagar' : 'Habilitar'}
                    </Button>
                  </form>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Section>

      <Section
        title="Zona de baja"
        description="Borra el club, sus dominios, usuarios, branding y archivos. No se puede deshacer."
      >
        <form action={deleteTenantAction}>
          <input type="hidden" name="tenant_id" value={tenant.id} />
          <Button type="submit" variant="destructive">
            Eliminar club
          </Button>
        </form>
      </Section>
    </>
  );
}
