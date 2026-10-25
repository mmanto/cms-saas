import { useEffect, useRef, useState } from 'react';
import { CalendarDays, GraduationCap, User } from 'lucide-react';

import { formatArticleDate, type Article } from '../articles';

/**
 * Bloque de capacitaciones. El contenido NO vive en el codigo: son los artículos
 * del club con categoria "Capacitacion" (ver `../articles.ts`). El club las publica
 * desde el panel y el sitio las pinta aca.
 */
export default function Capacitaciones({ articles }: { articles: Article[] }) {
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
    const cards = sectionRef.current?.querySelectorAll('.cap-card');
    cards?.forEach((card) => observer.observe(card));
    return () => observer.disconnect();
  }, [articles]);

  const scrollToContact = () => {
    document.querySelector('#contacto')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section
      id="capacitaciones"
      ref={sectionRef}
      className="py-28 lg:py-36 px-4 sm:px-6 lg:px-8"
      style={{ backgroundColor: '#f3f4f6' }}
    >
      <div className="page-container">
        {/* Header */}
        <div className="text-center mb-20">
          <span className="text-label block mb-5" style={{ color: '#2793b4' }}>
            Formación Profesional
          </span>
          <h2 className="text-h2 text-gray-900">
            Capacitaciones <span style={{ fontStyle: 'italic', color: '#2793b4' }}>Tecnológicas</span>
          </h2>
          <p className="text-body text-gray-500 max-w-2xl mx-auto mt-6">
            Programas de formación diseñados para mantener a tu equipo actualizado
            en las herramientas y prácticas más demandadas del mercado.
          </p>
        </div>

        {/* Grid */}
        {articles.length === 0 ? (
          <div
            className="rounded-3xl p-10 mb-14 text-center"
            style={{ backgroundColor: '#ffffff', border: '1px solid #d1dce8' }}
          >
            <p className="text-body text-gray-500">
              Todavía no hay capacitaciones publicadas.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-14">
            {articles.map((article, index) => {
              const isVisible = visibleCards.has(index);
              return (
                <article
                  key={article.id}
                  data-index={index}
                  className={`cap-card rounded-3xl overflow-hidden transition-all duration-500 hover:-translate-y-1 ${
                    isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
                  }`}
                  style={{
                    transitionDelay: `${index * 80}ms`,
                    backgroundColor: '#ffffff',
                    border: '1px solid #d1dce8',
                  }}
                >
                  <div className="h-[2px] w-full" style={{ backgroundColor: '#2793b4' }} />
                  {article.imageUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={article.imageUrl}
                      alt=""
                      className="w-full object-cover"
                      style={{ height: '180px' }}
                    />
                  ) : null}
                  <div className="p-10">
                    <div className="flex items-start gap-4 mb-6">
                      <div
                        className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0"
                        style={{ backgroundColor: '#EEF8FC', color: '#2793b4' }}
                      >
                        <GraduationCap className="w-7 h-7" />
                      </div>
                      <div>
                        <h3 className="text-h3 text-gray-900 mb-2">{article.title}</h3>
                        <p className="text-body-small text-gray-500">{article.excerpt}</p>
                      </div>
                    </div>

                    <div
                      className="flex flex-wrap gap-5"
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

        {/* CTA */}
        <div className="text-center">
          <p className="text-body-small text-gray-500 mb-5">
            ¿Necesitas una capacitación personalizada para tu equipo?
          </p>
          <button
            onClick={scrollToContact}
            className="text-cta inline-flex items-center justify-center rounded-lg px-7 py-4 text-white transition-opacity hover:opacity-90"
            style={{ backgroundColor: '#2793b4' }}
          >
            Solicitar Información
          </button>
        </div>
      </div>
    </section>
  );
}
