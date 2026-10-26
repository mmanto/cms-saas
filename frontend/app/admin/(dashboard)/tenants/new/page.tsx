import Link from 'next/link';

import { BASE_DOMAIN } from '@/lib/env';
import { requirePlatformSession } from '@/lib/platform';

import { TenantForm } from './tenant-form';

export const dynamic = 'force-dynamic';

export default async function NewTenantPage() {
  await requirePlatformSession();

  return (
    <>
      <div className="flex flex-col gap-1">
        <Link
          href="/admin"
          className="text-xs text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          ← Portales
        </Link>
        <h1 className="mt-1 font-heading heading-screen font-medium">Nuevo portal</h1>
        <p className="text-sm text-muted-foreground">
          El dominio primario se crea como <code>&lt;slug&gt;.{BASE_DOMAIN}</code>.
        </p>
      </div>

      <section className="max-w-lg rounded-xl border bg-card p-4">
        <TenantForm />
      </section>
    </>
  );
}
