import { requireClubAdmin } from '@/lib/tenant-auth';

import { createArticleAction } from '../../actions';
import { clubArticles } from '../../data';
import { ModuloApagado } from '../../notices';
import { ArticleForm } from '../../article-form';

export const dynamic = 'force-dynamic';

export default async function NuevoArticuloPage() {
  const { token } = await requireClubAdmin();
  const articles = await clubArticles(token);
  if (articles === null) return <ModuloApagado />;

  // Categorias ya usadas por el club: la categoria sigue siendo texto libre,
  // el datalist solo sugiere.
  const categorias = [...new Set(articles.map((article) => article.category))].sort();

  return <ArticleForm action={createArticleAction} categorias={categorias} />;
}
