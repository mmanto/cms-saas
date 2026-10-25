import { useState, useEffect, useCallback, useMemo } from 'react';
import { Menu, X } from 'lucide-react';

const navLinks = [
  { name: 'Servicios',      href: '#servicios',      needsArticles: false },
  { name: 'Capacitaciones', href: '#capacitaciones', needsArticles: true },
  { name: 'Nosotros',       href: '#nosotros',       needsArticles: false },
  { name: 'Relevamiento',   href: '#relevamiento',   needsArticles: false },
  { name: 'Proyectos',      href: '#proyectos',      needsArticles: true },
  { name: 'Contacto',       href: '#contacto',       needsArticles: false },
];

export default function Navbar({ showArticles }: { showArticles: boolean }) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('');

  const links = useMemo(
    () => navLinks.filter((link) => showArticles || !link.needsArticles),
    [showArticles],
  );

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > window.innerHeight * 0.5);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const ids = links.map(l => l.href.replace('#', ''));
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) setActiveSection(entry.target.id);
        });
      },
      { threshold: 0.3, rootMargin: '-64px 0px 0px 0px' }
    );
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [links]);

  const scrollToSection = useCallback((href: string) => {
    const element = document.querySelector(href);
    if (element) element.scrollIntoView({ behavior: 'smooth' });
    setMobileMenuOpen(false);
  }, []);

  return (
    <nav
      className="fixed top-4 left-0 right-0 z-50 transition-all duration-300"
      style={{
        backgroundColor: scrolled ? 'rgba(42, 59, 77, 0.97)' : 'transparent',
        backdropFilter:   scrolled ? 'blur(12px)' : 'none',
      }}
    >
      <div className="page-container px-0">
        <div className="flex justify-between items-center h-16">

          {/* Logo */}
          <a
            href="#"
            onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
            className="logo-elatech"
          >
            elatech
          </a>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-8">
            {links.map((link) => {
              const id = link.href.replace('#', '');
              const isActive = activeSection === id;
              return (
                <button
                  key={link.name}
                  onClick={() => scrollToSection(link.href)}
                  className="text-nav relative py-1 transition-colors duration-200"
                  style={{ color: isActive ? 'white' : 'rgba(255,255,255,0.65)' }}
                >
                  {link.name}
                  <span
                    className="absolute bottom-0 left-0 h-[2px] transition-all duration-200 ease-out"
                    style={{
                      width: isActive ? '100%' : '0%',
                      backgroundColor: '#2793b4',
                    }}
                  />
                </button>
              );
            })}
            <button
              onClick={() => scrollToSection('#contacto')}
              className="text-cta px-5 py-2.5 rounded-lg transition-colors border"
              style={{ color: 'white', borderColor: 'rgba(255,255,255,0.25)', backgroundColor: 'rgba(255,255,255,0.08)' }}
            >
              Consultar
            </button>
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden p-2 text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? 'Cerrar menú' : 'Abrir menú'}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div
          className="md:hidden border-t py-4"
          style={{ backgroundColor: '#0D1B38', borderColor: 'rgba(255,255,255,0.1)' }}
        >
          <div className="flex flex-col gap-1 px-4">
            {links.map((link) => (
              <button
                key={link.name}
                onClick={() => scrollToSection(link.href)}
                className="text-nav px-4 py-3 text-left rounded-lg transition-colors"
                style={{ color: 'rgba(255,255,255,0.8)' }}
              >
                {link.name}
              </button>
            ))}
            <button
              onClick={() => scrollToSection('#contacto')}
              className="text-cta mt-2 px-5 py-3 rounded-lg border text-white"
              style={{ borderColor: 'rgba(255,255,255,0.25)', backgroundColor: 'rgba(255,255,255,0.08)' }}
            >
              Consultar
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
