'use client';

import { useActionState } from 'react';

import { HugeiconsIcon } from '@hugeicons/react';
import { AlertCircleIcon, LayoutBottomIcon } from '@hugeicons/core-free-icons';
import { Button, Input } from '@mmanto/devbout-ui';

import type { ActionState } from '@/lib/platform';

import { useTenantBranding } from '../../tenant-branding-provider';
import { loginAction } from '../actions';

export function ClubLoginForm({ expirado }: { expirado: boolean }) {
  const [state, formAction] = useActionState<ActionState, FormData>(loginAction, {});
  const branding = useTenantBranding();
  const clubName = branding?.display_name ?? 'Artículos del club';

  return (
    <form action={formAction} className="flex w-full max-w-sm flex-col gap-6">
      <div className="flex flex-col items-center gap-2 text-center">
        {branding?.logo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={branding.logo_url}
            alt={clubName}
            width={40}
            height={40}
            className="size-10 rounded-xl object-contain"
          />
        ) : (
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <HugeiconsIcon icon={LayoutBottomIcon} strokeWidth={2} className="size-5" />
          </div>
        )}
        <div className="flex flex-col gap-1">
          <h1 className="font-heading heading-screen font-medium">{clubName}</h1>
          <p className="text-xs text-muted-foreground">Panel de artículos del club</p>
        </div>
      </div>

      <div className="flex flex-col gap-5 rounded-xl border bg-card p-6 shadow-sm">
        <div className="flex flex-col gap-1">
          <h2 className="font-heading heading-section font-medium">Iniciar sesión</h2>
          <p className="text-xs/relaxed text-muted-foreground">
            Entrá con tu usuario admin del club.
          </p>
        </div>

        {expirado ? (
          <p className="text-xs text-muted-foreground">Sesión vencida: volvé a entrar.</p>
        ) : null}

        <div className="grid gap-2">
          <label htmlFor="email" className="text-xs font-medium">
            Email
          </label>
          <Input
            id="email"
            name="email"
            type="email"
            required
            autoComplete="username"
            aria-invalid={state.error ? true : undefined}
          />
        </div>

        <div className="grid gap-2">
          <label htmlFor="password" className="text-xs font-medium">
            Password
          </label>
          <Input
            id="password"
            name="password"
            type="password"
            required
            autoComplete="current-password"
            aria-invalid={state.error ? true : undefined}
          />
        </div>

        {state.error ? (
          <p role="alert" className="flex items-start gap-1.5 text-xs text-destructive">
            <HugeiconsIcon
              icon={AlertCircleIcon}
              strokeWidth={2}
              className="mt-0.5 size-3.5 shrink-0"
            />
            {state.error}
          </p>
        ) : null}

        <Button type="submit" className="w-full">
          Entrar
        </Button>
      </div>

      <p className="text-center text-xs text-muted-foreground">
        {/* Navegacion completa: el layout raiz cambia entre panel y sitio. */}
        <a href="/" className="underline-offset-4 hover:text-foreground hover:underline">
          ← Volver al sitio
        </a>
      </p>
    </form>
  );
}
