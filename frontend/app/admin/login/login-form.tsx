'use client';

import { useActionState } from 'react';

import { HugeiconsIcon } from '@hugeicons/react';
import { AlertCircleIcon, LayoutBottomIcon } from '@hugeicons/core-free-icons';
import { Button, Input } from '@mmanto/devbout-ui';

import type { ActionState } from '@/lib/platform';

import { loginAction } from '../actions';

export function LoginForm({ expirado }: { expirado: boolean }) {
  const [state, formAction] = useActionState<ActionState, FormData>(loginAction, {});

  return (
    <form action={formAction} className="flex w-full max-w-sm flex-col gap-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <HugeiconsIcon icon={LayoutBottomIcon} strokeWidth={2} className="size-5" />
        </div>
        <div className="flex flex-col gap-1">
          <h1 className="font-heading heading-screen font-medium">SaaS Clubes</h1>
          <p className="text-xs text-muted-foreground">Backoffice de plataforma</p>
        </div>
      </div>

      <div className="flex flex-col gap-5 rounded-xl border bg-card p-6 shadow-sm">
        <div className="flex flex-col gap-1">
          <h2 className="font-heading heading-section font-medium">Iniciar sesión</h2>
          <p className="text-xs/relaxed text-muted-foreground">
            Entrá con tu usuario de plataforma.
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

      <p className="text-center text-[0.625rem] text-muted-foreground">
        SaaS Clubes · backoffice de plataforma
      </p>
    </form>
  );
}
