import { notFound } from 'next/navigation';

import { requireClubAdmin } from '@/lib/tenant-auth';

import { deleteArticleAction, updateArticleAction } from '../../actions';
import { DeleteArticleButton } from '../../delete-article-button';
import { clubArticles } from '../../data';
import { ModuloApagado } from '../../notices';
import { ArticleForm } from '../../article-form';

export const dynamic = 'force-dynamic';

export default async function EditarArticuloPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const { token } = await requireClubAdmin();
  const articles = await clubArticles(token);
  if (articles === null) return <ModuloApagado />;

  const article = articles.find((item) => item.id === id);
  if (article === undefined) notFound();

  const categorias = [...new Set(articles.map((item) => item.category))].sort();

  return (
    <>
      <ArticleForm action={updateArticleAction} categorias={categorias} article={article} />

      <section className="max-w-2xl rounded-xl border border-destructive/30 bg-card">
        <div className="border-b border-destructive/20 p-4">
          <h2 className="font-heading heading-section font-medium">Zona de baja</h2>
        </div>
        <div className="p-4">
          <p className="text-sm text-muted-foreground">
            La baja es definitiva: si solo querés sacarla del sitio, despublicala.
          </p>
          <form action={deleteArticleAction} className="mt-4">
            <input type="hidden" name="id" value={article.id} />
            <DeleteArticleButton />
          </form>
        </div>
      </section>
    </>
  );
}
