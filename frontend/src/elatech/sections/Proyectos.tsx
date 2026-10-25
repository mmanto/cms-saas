import { useEffect, useRef, useState } from 'react';
import { CalendarDays, FolderKanban, User } from 'lucide-react';

import { formatArticleDate, type Article } from '../articles';

/**
 * Bloque de proyectos. Igual que las capacitaciones, son artículos del club con
 * categoria "Proyectos": el contenido sale de la API, no del codigo.
 */
export default function Proyectos({ articles }: { articles: Article[] }) {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [visibleCards, setVisibleCards] = useState<Set<number>>(new Set());

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const index = parseInt(entry.target.getAttribute('data-index') || '0');
            setVisibleCards((prev) => new Set([...prev, index]));
          }
        });
      },
      { threshold: 0.2, rootMargin: '0px 0px -50px 0px' }
    );
    const cards = sectionRef.current?.querySelectorAll('.project-card');
    cards?.forEach((card) => observer.observe(card));
    return () => observer.disconnect();
  }, [articles]);

  return (
    <section
      id="proyectos"
      ref={sectionRef}
      className="py-28 lg:py-36 px-4 sm:px-6 lg:px-8 bg-white"
    >
      <div className="page-container">
        {/* Header */}
        <div className="text-center mb-20">
          <span className="text-label block mb-5" style={{ color: '#2793b4' }}>
            Nuestro Trabajo
          </span>
          <h2 className="text-h2 text-gray-900">
            Nuestros <span style={{ fontStyle: 'italic', color: '#2793b4' }}>Proyectos</span>
          </h2>
          <p className="text-body text-gray-500 max-w-2xl mx-auto mt-6">
            Conocé algunos de los proyectos que desarrollamos para nuestros clientes.
          </p>
        </div>

        {/* Grid */}
        {articles.length === 0 ? (
          <div
            className="rounded-3xl p-10 text-center"
            style={{ border: '1px solid #d1dce8' }}
          >
            <p className="text-body text-gray-500">
              Todavía no hay proyectos publicados.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {articles.map((article, index) => {
              const isVisible = visibleCards.has(index);
              return (
                <article
                  key={article.id}
                  data-index={index}
                  className={`project-card rounded-3xl overflow-hidden border border-gray-100 hover:shadow-md transition-all duration-500 hover:-translate-y-1 ${
                    isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
                  }`}
                  style={{ transitionDelay: `${index * 100}ms` }}
                >
                  {/* Portada: la imagen del artículo o el placeholder del sitio. */}
                  {article.imageUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={article.imageUrl}
                      alt=""
                      className="w-full object-cover"
                      style={{ height: '180px' }}
                    />
                  ) : (
                    <div
                      className="w-full flex items-center justify-center"
                      style={{ height: '180px', backgroundColor: '#0D1B38' }}
                    >
                      <FolderKanban className="w-10 h-10" style={{ color: '#2793b4' }} />
                    </div>
                  )}

                  {/* Contenido */}
                  <div className="p-8">
                    <h3 className="text-h3 text-gray-900 mb-3">{article.title}</h3>
                    <p className="text-body-small text-gray-500">{article.excerpt}</p>

                    <div
                      className="flex flex-wrap gap-5 mt-6"
                      style={{ borderTop: '1px solid #e8eef5', paddingTop: '1.25rem' }}
                    >
                      <div className="flex items-center gap-2 text-body-small text-gray-500">
                        <CalendarDays className="w-4 h-4" />
                        <span>{formatArticleDate(article.createdAt)}</span>
                      </div>
                      <div className="flex items-center gap-2 text-body-small text-gray-500">
                        <User className="w-4 h-4" />
                        <span>{article.author}</span>
                      </div>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
