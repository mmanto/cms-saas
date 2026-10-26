'use client';

import { useActionState } from 'react';

import { HugeiconsIcon } from '@hugeicons/react';
import { AlertCircleIcon } from '@hugeicons/core-free-icons';
import { Button, Input } from '@mmanto/devbout-ui';

import type { ActionState } from '@/lib/platform';

import { createTenantAction } from '../../../actions';

export function TenantForm() {
  const [state, formAction] = useActionState<ActionState, FormData>(createTenantAction, {});

  return (
    <form action={formAction} className="grid gap-4">
      <label className="grid gap-2 text-xs font-medium">
        Slug
        <Input
          name="slug"
          required
          pattern="[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?"
          placeholder="portalprueba"
          autoComplete="off"
        />
        <span className="text-xs font-normal text-muted-foreground">
          Minúsculas, números y guiones.
        </span>
      </label>

      <label className="grid gap-2 text-xs font-medium">
        Nombre
        <Input name="name" required maxLength={200} placeholder="Portal Prueba" />
      </label>

      <label className="grid gap-2 text-xs font-medium">
        Email del admin del portal
        <Input
          name="admin_email"
          type="email"
          required
          placeholder="admin@demo.cms-sas.localhost"
          autoComplete="off"
        />
      </label>

      <label className="grid gap-2 text-xs font-medium">
        Password del admin
        <Input
          name="admin_password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
        />
        <span className="text-xs font-normal text-muted-foreground">Mínimo 8 caracteres.</span>
      </label>

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

      <Button type="submit" className="justify-self-start">
        Crear portal
      </Button>
    </form>
  );
}
