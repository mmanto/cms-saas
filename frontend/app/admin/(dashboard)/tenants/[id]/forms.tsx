'use client';

import { useActionState } from 'react';

import { HugeiconsIcon } from '@hugeicons/react';
import { AlertCircleIcon, Tick02Icon } from '@hugeicons/core-free-icons';
import {
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@mmanto/devbout-ui';

import type { ActionState } from '@/lib/platform';

import {
  addDomainAction,
  createUserAction,
  patchTenantAction,
  resetUserPasswordAction,
} from '../../../actions';

/** El resultado de la ultima Server Action, si hubo algo que decir. */
function Status({ state }: { state: ActionState }) {
  if (state.error) {
    return (
      <p role="alert" className="flex items-start gap-1.5 text-xs text-destructive">
        <HugeiconsIcon
          icon={AlertCircleIcon}
          strokeWidth={2}
          className="mt-0.5 size-3.5 shrink-0"
        />
        {state.error}
      </p>
    );
  }

  if (state.ok) {
    return (
      <p className="flex items-center gap-1.5 text-xs text-success">
        <HugeiconsIcon icon={Tick02Icon} strokeWidth={2} className="size-3.5" />
        {state.ok}
      </p>
    );
  }

  return null;
}

export function PatchForm({
  tenant,
}: {
  tenant: { id: string; name: string; status: string };
}) {
  const [state, formAction] = useActionState<ActionState, FormData>(patchTenantAction, {});

  return (
    <form action={formAction} className="grid max-w-md gap-4">
      <input type="hidden" name="tenant_id" value={tenant.id} />

      <label className="grid gap-2 text-xs font-medium">
        Nombre
        <Input name="name" defaultValue={tenant.name} required maxLength={200} />
      </label>

      <div className="grid gap-2 text-xs font-medium">
        Estado
        <Select name="status" defaultValue={tenant.status}>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="active">active</SelectItem>
            <SelectItem value="suspended">suspended</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Status state={state} />

      <Button type="submit" className="justify-self-start">
        Guardar
      </Button>
    </form>
  );
}

export function DomainForm({ tenantId }: { tenantId: string }) {
  const [state, formAction] = useActionState<ActionState, FormData>(addDomainAction, {});

  return (
    <form action={formAction} className="grid max-w-md gap-4">
      <input type="hidden" name="tenant_id" value={tenantId} />

      <label className="grid gap-2 text-xs font-medium">
        Dominio propio
        <Input name="host" required placeholder="portalnorte.com.ar" autoComplete="off" />
      </label>

      <Status state={state} />

      <Button type="submit" variant="outline" className="justify-self-start">
        Agregar dominio
      </Button>
    </form>
  );
}

export function UserForm({ tenantId }: { tenantId: string }) {
  const [state, formAction] = useActionState<ActionState, FormData>(createUserAction, {});

  return (
    <form action={formAction} className="grid max-w-md gap-4">
      <input type="hidden" name="tenant_id" value={tenantId} />

      <label className="grid gap-2 text-xs font-medium">
        Email
        <Input name="email" type="email" required autoComplete="off" />
      </label>

      <label className="grid gap-2 text-xs font-medium">
        Password
        <Input name="password" type="password" required minLength={8} autoComplete="new-password" />
        <span className="text-xs font-normal text-muted-foreground">Mínimo 8 caracteres.</span>
      </label>

      <div className="grid gap-2 text-xs font-medium">
        Rol
        <Select name="role" defaultValue="member">
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="member">member</SelectItem>
            <SelectItem value="admin">admin</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Status state={state} />

      <Button type="submit" className="justify-self-start">
        Crear usuario
      </Button>
    </form>
  );
}

export function ResetPasswordForm({
  tenantId,
  userId,
  email,
}: {
  tenantId: string;
  userId: string;
  email: string;
}) {
  const [state, formAction] = useActionState<ActionState, FormData>(
    resetUserPasswordAction,
    {},
  );

  return (
    <form action={formAction} className="flex flex-wrap items-center gap-2">
      <input type="hidden" name="tenant_id" value={tenantId} />
      <input type="hidden" name="user_id" value={userId} />
      <Input
        name="password"
        type="password"
        required
        minLength={8}
        autoComplete="new-password"
        placeholder={`Nueva password de ${email}`}
        className="max-w-64"
      />
      <Status state={state} />
      <Button type="submit" variant="outline" size="sm">
        Cambiar
      </Button>
    </form>
  );
}
