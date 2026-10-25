'use client';

import Link from 'next/link';
import { useActionState, useState } from 'react';

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
  Textarea,
} from '@mmanto/devbout-ui';

import { PANEL_ARTICULOS, ARTICLE_STATUS_LABEL, ARTICLE_STATUSES, type ClubArticle } from '@/lib/club';
import type { ActionState } from '@/lib/platform';

/**
 * Alta y edicion de un artículo: el mismo formulario. `action` es la Server
 * Action que corresponde (crear o actualizar) y `article` viene solo al editar.
 */
export function ArticleForm({
  action,
  categorias,
  article,
}: {
  action: (prev: ActionState, formData: FormData) => Promise<ActionState>;
  categorias: string[];
  article?: ClubArticle;
}) {
  const [state, formAction] = useActionState<ActionState, FormData>(action, {});
  const [preview, setPreview] = useState<string | null>(article?.image_url ?? null);
  const [removeImage, setRemoveImage] = useState(false);

  return (
    <form action={formAction} className="grid max-w-2xl gap-4">
      <h1 className="font-heading heading-screen font-medium">
        {article ? 'Editar artículo' : 'Nuevo artículo'}
      </h1>
      {article ? <input type="hidden" name="id" value={article.id} /> : null}

      <label className="grid gap-2 text-xs font-medium">
        Título
        <Input
          name="title"
          required
          maxLength={200}
          defaultValue={article?.title ?? ''}
          autoComplete="off"
        />
      </label>

      <label className="grid gap-2 text-xs font-medium">
        Slug
        <Input
          name="slug"
          maxLength={120}
          defaultValue={article?.slug ?? ''}
          placeholder="se genera del título"
          autoComplete="off"
        />
        <span className="text-xs font-normal text-muted-foreground">Opcional.</span>
      </label>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="grid gap-2 text-xs font-medium">
          Categoría
          <Input
            name="category"
            required
            maxLength={60}
            list="categorias"
            defaultValue={article?.category ?? ''}
            autoComplete="off"
          />
          <datalist id="categorias">
            {categorias.map((categoria) => (
              <option key={categoria} value={categoria} />
            ))}
          </datalist>
        </label>

        <label className="grid gap-2 text-xs font-medium">
          Autor
          <Input
            name="author"
            required
            maxLength={120}
            defaultValue={article?.author ?? 'Redacción'}
            autoComplete="off"
          />
        </label>
      </div>

      <label className="grid gap-2 text-xs font-medium">
        Resumen
        <Input
          name="excerpt"
          maxLength={400}
          defaultValue={article?.excerpt ?? ''}
          placeholder="Opcional: se usa en el listado del sitio"
          autoComplete="off"
        />
      </label>

      <div className="grid gap-2 text-xs font-medium">
        Imagen
        {preview && !removeImage ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={preview}
            alt=""
            className="h-40 w-full max-w-sm rounded-lg border object-cover"
          />
        ) : null}
        <input
          type="file"
          name="image"
          accept="image/png,image/jpeg,image/webp,image/gif,image/avif"
          onChange={(event) => {
            const file = event.target.files?.[0];
            setRemoveImage(false);
            setPreview(file ? URL.createObjectURL(file) : (article?.image_url ?? null));
          }}
          className="block w-full text-xs font-normal text-muted-foreground file:mr-3 file:rounded-md file:border-0 file:bg-secondary file:px-3 file:py-2 file:text-xs file:font-medium"
        />
        <span className="text-xs font-normal text-muted-foreground">
          PNG, JPG, WEBP, GIF o AVIF. Hasta 5 MB.
        </span>
        {article?.image_url ? (
          <label className="flex items-center gap-2 text-xs font-normal text-muted-foreground">
            <input
              type="checkbox"
              name="remove_image"
              value="1"
              checked={removeImage}
              onChange={(event) => {
                setRemoveImage(event.target.checked);
                setPreview(event.target.checked ? null : article.image_url);
              }}
            />
            Quitar imagen actual
          </label>
        ) : null}
      </div>

      <div className="grid gap-2 text-xs font-medium">
        Estado
        <Select
          name="status"
          defaultValue={article?.status ?? 'draft'}
          items={ARTICLE_STATUSES.map((estado) => ({
            value: estado,
            label: ARTICLE_STATUS_LABEL[estado],
          }))}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ARTICLE_STATUSES.map((estado) => (
              <SelectItem key={estado} value={estado}>
                {ARTICLE_STATUS_LABEL[estado]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <label className="grid gap-2 text-xs font-medium">
        Contenido
        <Textarea
          name="content"
          required
          rows={14}
          maxLength={50000}
          defaultValue={article?.content ?? ''}
          className="min-h-64 font-mono text-xs leading-relaxed"
        />
        <span className="text-xs font-normal text-muted-foreground">
          ## título, ### subtítulo, listas con 1. 2. 3.
        </span>
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
      {state.ok ? (
        <p className="flex items-center gap-1.5 text-xs text-success">
          <HugeiconsIcon icon={Tick02Icon} strokeWidth={2} className="size-3.5" />
          {state.ok}
        </p>
      ) : null}

      <div className="flex flex-wrap items-center gap-2">
        <Button type="submit">Guardar</Button>
        <Button variant="ghost" render={<Link href={PANEL_ARTICULOS} />}>
          Cancelar
        </Button>
      </div>
    </form>
  );
}
