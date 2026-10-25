'use client';

import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

/** Artículo como la sirve el modulo `articles` (GET /api/v1/articles). */
interface ApiArticle {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  category: string;
  status: string;
  author: string;
  image_url: string | null;
  created_at: string;
  updated_at: string;
}

interface Article {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  category: string;
  status: 'published' | 'draft' | 'archived';
  author: string;
  imageUrl: string | null;
  createdAt: string;
  updatedAt: string;
}

function toArticle(post: ApiArticle): Article {
  return {
    id: post.id,
    title: post.title,
    slug: post.slug,
    content: post.content,
    excerpt: post.excerpt,
    category: post.category,
    status: post.status as Article['status'],
    author: post.author,
    imageUrl: post.image_url,
    createdAt: post.created_at,
    updatedAt: post.updated_at,
  };
}

const NAV_LINKS = [
  { href: '#hero', label: 'Inicio' },
  { href: '#servicios', label: 'Servicios' },
  { href: '#cobertura', label: 'Cobertura' },
  { href: '#articulos', label: 'Artículos' },
  { href: '#contacto', label: 'Contacto' },
];

const SERVICES = [
  {
    title: 'Grúa Liviana',
    description: 'Para autos, motos y vehículos pequeños. Servicio rápido y seguro.',
    img: '/auxiliosrb/f3.webp',
  },
  {
    title: 'Grúa Pesada',
    description: 'Camiones, buses y vehículos de gran tamaño. Equipamiento especializado.',
    img: '/auxiliosrb/f4.webp',
  },
  {
    title: 'Asistencia en Ruta',
    description: 'Cambio de neumáticos, carga de batería y asistencia mecánica básica.',
    img: '/auxiliosrb/f8.webp',
  },
  {
    title: 'Traslados',
    description: 'Traslado de vehículos a talleres, hogares o concesionarias.',
    img: '/auxiliosrb/f6.webp',
  },
];

const COVERAGE_AREAS = [
  'Centro',
  'Zona Norte',
  'Zona Sur',
  'Zona Este',
  'Zona Oeste',
  'Área Metropolitana',
];

const MAP_EMBED_URL =
  'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3271.5900265576583!2d-57.9700394!3d-34.9167366!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x95a2e70015ccf633%3A0x10cd83fc1fd0ba51!2sAuxilios%20RB!5e0!3m2!1ses-419!2sar!4v1768921990157!5m2!1ses-419!2sar';

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

/** Cuerpo del articulo: parrafos, titulos y listas numeradas del contenido. */
function renderContent(content: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let list: string[] = [];

  const flushList = () => {
    if (list.length === 0) return;
    const items = list;
    nodes.push(
      <ol key={`list-${nodes.length}`}>
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ol>,
    );
    list = [];
  };

  for (const line of content.split('\n')) {
    if (line.match(/^\d+\.\s/)) {
      list.push(line.replace(/^\d+\.\s/, ''));
      continue;
    }
    flushList();
    if (line.startsWith('## ')) {
      nodes.push(<h2 key={nodes.length}>{line.replace('## ', '')}</h2>);
    } else if (line.startsWith('### ')) {
      nodes.push(<h3 key={nodes.length}>{line.replace('### ', '')}</h3>);
    } else if (line.trim() === '') {
      nodes.push(<br key={nodes.length} />);
    } else {
      nodes.push(<p key={nodes.length}>{line}</p>);
    }
  }
  flushList();
  return nodes;
}

export function AuxilioHome() {
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [menuOpen, setMenuOpen] = useState(false);
  // `null` = todavia no respondio la API. El modulo apagado (404) o caido deja
  // la seccion afuera: el sitio no inventa artículos locales.
  const [posts, setPosts] = useState<Article[] | null>(null);
  const [moduleEnabled, setModuleEnabled] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const response = await fetch('/api/v1/articles', { cache: 'no-store' });
        if (!alive) return;
        if (response.status === 404) {
          setModuleEnabled(false);
          setPosts([]);
          return;
        }
        if (!response.ok) throw new Error(`/api/v1/articles respondio ${response.status}`);
        const data = (await response.json()) as ApiArticle[];
        if (!alive) return;
        setPosts(data.map(toArticle));
        setModuleEnabled(true);
      } catch {
        // Sin API no hay modulo: la seccion y el link del menu desaparecen.
        if (!alive) return;
        setModuleEnabled(false);
        setPosts([]);
      }
    };
    void load();
    return () => {
      alive = false;
    };
  }, []);

  const publishedArticles = useMemo(
    () => (posts ?? []).filter((post) => post.status === 'published'),
    [posts],
  );
  const categories = useMemo(
    () => Array.from(new Set(publishedArticles.map((post) => post.category))).sort(),
    [publishedArticles],
  );
  const filteredArticles = useMemo(() => {
    if (selectedCategory === 'all') return publishedArticles;
    return publishedArticles.filter((post) => post.category === selectedCategory);
  }, [publishedArticles, selectedCategory]);
  const navLinks = useMemo(
    () => (moduleEnabled ? NAV_LINKS : NAV_LINKS.filter((link) => link.href !== '#articulos')),
    [moduleEnabled],
  );

  const openArticle = (post: Article) => {
    setSelectedArticle(post);
    window.scrollTo(0, 0);
  };

  const backToArticles = () => {
    setSelectedArticle(null);
    requestAnimationFrame(() => {
      document.getElementById('articulos')?.scrollIntoView({ behavior: 'smooth' });
    });
  };

  // ─── ARTICLE DETAIL VIEW ──────────────────────────────────────────────────
  if (selectedArticle) {
    return (
      <div className="ax-article-page">
        <header className="ax-article-bar">
          <div className="ax-article-bar-inner">
            <button className="ax-back" onClick={() => setSelectedArticle(null)}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
              Volver al inicio
            </button>
            <button className="ax-article-brand" onClick={backToArticles}>
              <img src="/auxiliosrb/logo.webp" alt="" width={40} height={45} />
              <span>Auxilio automotor</span>
            </button>
          </div>
        </header>

        <article className="ax-article">
          <div className="ax-meta">
            <span className="ax-article-badge">{selectedArticle.category}</span>
            <span className="ax-date">{formatDate(selectedArticle.createdAt)}</span>
          </div>

          <h1>{selectedArticle.title}</h1>

          {selectedArticle.imageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img className="ax-article-image" src={selectedArticle.imageUrl} alt="" />
          ) : null}

          <p className="ax-excerpt">{selectedArticle.excerpt}</p>

          <div className="ax-article-author">
            <div className="ax-avatar ax-avatar-lg">{selectedArticle.author.charAt(0)}</div>
            <div>
              <p>{selectedArticle.author}</p>
              <small>Última actualización: {formatDate(selectedArticle.updatedAt)}</small>
            </div>
          </div>

          <div className="ax-prose">{renderContent(selectedArticle.content)}</div>

          <div className="ax-article-nav">
            <button className="ax-back" onClick={() => setSelectedArticle(null)}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
              Ver todos los artículos
            </button>
          </div>
        </article>
      </div>
    );
  }

  // ─── LANDING HOME VIEW ────────────────────────────────────────────────────
  const featuredArticle = publishedArticles[0];
  const restArticles = filteredArticles.slice(1);

  return (
    <div>
      <header className="ax-header">
        <nav className="ax-container ax-nav">
          <div className="ax-nav-row">
            <a className="ax-brand" href="#hero">
              <img src="/auxiliosrb/logo.webp" alt="Auxilio RB" width={100} height={113} />
              <span className="ax-brand-name">Auxilio automotor</span>
            </a>

            <ul className="ax-menu">
              {navLinks.map((link) => (
                <li key={link.href}>
                  <a href={link.href}>{link.label}</a>
                </li>
              ))}
            </ul>

            <button
              className="ax-burger"
              aria-label="Abrir menú"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>

          {menuOpen && (
            <ul className="ax-mobile">
              {navLinks.map((link) => (
                <li key={link.href}>
                  <a href={link.href} onClick={() => setMenuOpen(false)}>
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </nav>
      </header>

      <main className="ax-main">
        <section id="hero" className="ax-hero">
          <div className="ax-hero-bg" aria-hidden="true" />
          <div className="ax-hero-overlay" aria-hidden="true" />
          <div className="ax-hero-content">
            <h1>Servicio de Grúa Profesional</h1>
            <p>Atención 24/7 en toda la ciudad. Rápido, seguro y confiable.</p>
            <a href="#contacto" className="ax-btn ax-contact-btn">
              Solicitar Servicio
            </a>
          </div>
        </section>

        {moduleEnabled ? (
        <section id="articulos" className="ax-section">
          <div className="ax-container">
            <div className="ax-section-head">
              <h2>Artículos</h2>
              <p>
                Exploramos las últimas tendencias y mejores prácticas en el mundo del desarrollo
                web y el diseño digital.
              </p>
            </div>

            <div className="ax-filters">
              <button
                className={`ax-chip${selectedCategory === 'all' ? ' is-active' : ''}`}
                onClick={() => setSelectedCategory('all')}
              >
                Todos
              </button>
              {categories.map((category) => (
                <button
                  key={category}
                  className={`ax-chip${selectedCategory === category ? ' is-active' : ''}`}
                  onClick={() => setSelectedCategory(category)}
                >
                  {category}
                </button>
              ))}
            </div>

            {featuredArticle && selectedCategory === 'all' && (
              <button className="ax-featured" onClick={() => openArticle(featuredArticle)}>
                <div className="ax-featured-grid">
                  <div className="ax-featured-visual">
                    {featuredArticle.imageUrl ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img className="ax-featured-img" src={featuredArticle.imageUrl} alt="" />
                    ) : (
                      <div>
                        <div className="ax-featured-icon">
                          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"
                            />
                          </svg>
                        </div>
                        <p className="ax-featured-label">Artículo destacado</p>
                      </div>
                    )}
                  </div>

                  <div className="ax-featured-body">
                    <div className="ax-meta">
                      <span className="ax-badge">{featuredArticle.category}</span>
                      <span className="ax-date">{formatDate(featuredArticle.createdAt)}</span>
                    </div>
                    <h3>{featuredArticle.title}</h3>
                    <p>{featuredArticle.excerpt}</p>
                    <div className="ax-author">
                      <div className="ax-avatar">{featuredArticle.author.charAt(0)}</div>
                      <span>{featuredArticle.author}</span>
                    </div>
                  </div>
                </div>
              </button>
            )}

            <div>
              <div className="ax-posts-head">
                <h3>{selectedCategory === 'all' ? 'Todos los artículos' : selectedCategory}</h3>
                <span className="ax-count">{filteredArticles.length} artículos</span>
              </div>

              {filteredArticles.length === 0 ? (
                <div className="ax-empty">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="1"
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <p>No hay artículos en esta categoría</p>
                </div>
              ) : (
                <div className="ax-posts">
                  {(selectedCategory === 'all' ? restArticles : filteredArticles).map((post) => (
                    <button key={post.id} className="ax-post" onClick={() => openArticle(post)}>
                      <div className="ax-post-visual" aria-hidden="true">
                        {post.imageUrl ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={post.imageUrl} alt="" />
                        ) : (
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                            />
                          </svg>
                        )}
                      </div>
                      <div className="ax-post-body">
                        <div className="ax-meta">
                          <span className="ax-badge">{post.category}</span>
                          <span className="ax-date">{formatDate(post.createdAt)}</span>
                        </div>
                        <h4>{post.title}</h4>
                        <p>{post.excerpt}</p>
                        <div className="ax-author">
                          <div className="ax-avatar">{post.author.charAt(0)}</div>
                          <span>{post.author}</span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>
        ) : null}

        <section id="servicios" className="ax-section ax-section-alt">
          <div className="ax-container">
            <div className="ax-section-head">
              <h2>Nuestros Servicios</h2>
              <p>
                Brindamos servicio de grúa y traslado de vehículos, realizando remolques y
                traslados programados o de urgencia, con cobertura a cualquier parte del país.
                Nos especializamos en el traslado de autos y utilitarios, así como también en el
                transporte de cargas generales, ofreciendo un servicio seguro, confiable y
                puntual. La atención es directa y personalizada, a través de teléfono y WhatsApp,
                para coordinar rápidamente cada traslado según las necesidades del cliente.
              </p>
            </div>

            <div className="ax-services">
              {SERVICES.map((service) => (
                <div key={service.title} className="ax-service-card">
                  <img src={service.img} alt="" />
                  <h3>{service.title}</h3>
                  <p>{service.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="cobertura" className="ax-section ax-section-alt">
          <div className="ax-container">
            <div className="ax-section-head">
              <h2>Cobertura</h2>
              <p>Servicio disponible en toda la ciudad y zonas aledañas las 24 horas del día.</p>
            </div>

            <div className="ax-coverage">
              <div className="ax-map-ph" aria-hidden="true" />

              <div className="ax-areas">
                <h3>Áreas de Cobertura</h3>
                <ul>
                  {COVERAGE_AREAS.map((area) => (
                    <li key={area}>
                      <svg
                        className="ax-check"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                      {area}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section className="ax-map-section">
          <iframe
            src={MAP_EMBED_URL}
            title="Ubicación de Auxilios RB"
            width="80%"
            height="100%"
            style={{ border: 0 }}
            allowFullScreen
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
        </section>

        <section id="contacto" className="ax-section">
          <div className="ax-container">
            <div className="ax-section-head">
              <h2>Contacto</h2>
              <p>
                Comunícate con nosotros para solicitar nuestro servicio. Estamos disponibles 24/7.
              </p>
            </div>

            <div className="ax-contact-grid">
              <a
                href="https://wa.me/5492213645344"
                target="_blank"
                rel="noopener noreferrer"
                className="ax-contact-card ax-whatsapp ax-contact-btn"
              >
                <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
                </svg>
                <div>
                  <h3>WhatsApp</h3>
                  <p>+54 9 221 364 5344</p>
                  <small>Opción principal</small>
                </div>
              </a>

              <a href="tel:+5492213645344" className="ax-contact-card ax-phone ax-contact-btn">
                <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z" />
                </svg>
                <div>
                  <h3>Teléfono</h3>
                  <p>221 364 5344</p>
                  <small>Llamada directa</small>
                </div>
              </a>
            </div>

            <p className="ax-hours">Atención las 24 horas, los 7 días de la semana</p>
          </div>
        </section>
      </main>

      <footer className="ax-footer">
        <div className="ax-container">
          <div className="ax-footer-row">
            <div className="ax-footer-brand">
              <img src="/auxiliosrb/logo.webp" alt="" width={100} height={113} />
              <span>Auxilio automotor</span>
            </div>
            <p>© {new Date().getFullYear()} GrúaLanding. Todos los derechos reservados.</p>
            <div className="ax-footer-links">
              <a href="#hero">Inicio</a>
              <a href="#servicios">Servicios</a>
              <a href="#contacto">Contacto</a>
              {/* Navegacion completa: el layout raiz cambia entre sitio y panel. */}
              {moduleEnabled ? <a href="/panel/articulos">Gestionar artículos</a> : null}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
