import Link from 'next/link';

import { HugeiconsIcon } from '@hugeicons/react';
import { PlusSignIcon } from '@hugeicons/core-free-icons';
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

import { PANEL_ARTICULOS, ARTICLE_STATUS_LABEL, type ArticleStatus } from '@/lib/club';
import { requireClubAdmin } from '@/lib/tenant-auth';

import { setStatusAction } from '../actions';
import { clubArticles } from '../data';
import { ModuloApagado } from '../notices';

export const dynamic = 'force-dynamic';

/** `updated_at` viene en ISO: al dia, sin hora, en castellano. */
function fecha(iso: string): string {
  return new Date(iso).toLocaleDateString('es-AR');
}

function statusVariant(status: ArticleStatus): 'success' | 'warning' | 'outline' {
  if (status === 'published') return 'success';
  if (status === 'draft') return 'warning';
  return 'outline';
}

export default async function ArticulosPage() {
  const { token, me } = await requireClubAdmin();
  const articles = await clubArticles(token);

  if (articles === null) return <ModuloApagado />;

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-col gap-1">
          <h1 className="font-heading heading-screen font-medium">
            Artículos de {me.tenant.name}
          </h1>
          <p className="text-sm text-muted-foreground">
            Publicá, despublicá o editá los artículos del club.
          </p>
        </div>
        <Button render={<Link href={`${PANEL_ARTICULOS}/nueva`} />}>
          <HugeiconsIcon icon={PlusSignIcon} strokeWidth={2} />
          Nuevo artículo
        </Button>
      </div>

      {articles.length === 0 ? (
        <div className="rounded-xl border border-dashed p-8 text-center">
          <p className="text-sm font-medium">Todavía no hay artículos</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Creá la primera para que aparezca en el sitio del club.
          </p>
          <Button
            variant="outline"
            className="mt-4"
            render={<Link href={`${PANEL_ARTICULOS}/nueva`} />}
          >
            Crear artículo
          </Button>
        </div>
      ) : (
        <section className="overflow-hidden rounded-xl border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="px-4">Título</TableHead>
                <TableHead className="px-4">Categoría</TableHead>
                <TableHead className="px-4">Estado</TableHead>
                <TableHead className="px-4">Actualizada</TableHead>
                <TableHead className="px-4">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {articles.map((article) => (
                <TableRow key={article.id}>
                  <TableCell className="px-4">
                    <Link
                      href={`${PANEL_ARTICULOS}/${article.id}`}
                      className="font-medium underline-offset-4 hover:underline"
                    >
                      {article.title}
                    </Link>
                  </TableCell>
                  <TableCell className="px-4">{article.category}</TableCell>
                  <TableCell className="px-4">
                    <Badge variant={statusVariant(article.status)}>
                      {ARTICLE_STATUS_LABEL[article.status]}
                    </Badge>
                  </TableCell>
                  <TableCell className="px-4 text-muted-foreground">
                    {fecha(article.updated_at)}
                  </TableCell>
                  <TableCell className="px-4">
                    <form action={setStatusAction}>
                      <input type="hidden" name="id" value={article.id} />
                      <input
                        type="hidden"
                        name="status"
                        value={article.status === 'published' ? 'draft' : 'published'}
                      />
                      <Button type="submit" variant="outline" size="sm">
                        {article.status === 'published' ? 'Despublicar' : 'Publicar'}
                      </Button>
                    </form>
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
