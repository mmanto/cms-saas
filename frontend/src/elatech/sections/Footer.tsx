import { Linkedin, Github, Instagram, Twitter } from 'lucide-react';

const footerLinks = {
  servicios: [
    { name: 'Desarrollo de Software',  href: '#servicios',      needsArticles: false },
    { name: 'Capacitaciones',          href: '#capacitaciones', needsArticles: true },
    { name: 'Relevamiento Tecnológico',href: '#relevamiento',   needsArticles: false },
    { name: 'Gestión de Proyectos IT', href: '#servicios',      needsArticles: false },
    { name: 'Asesoramiento en IA',     href: '#servicios',      needsArticles: false },
  ],
  empresa: [
    { name: 'Quienes Somos',   href: '#nosotros', needsArticles: false },
    { name: 'Nuestra Misión',  href: '#nosotros', needsArticles: false },
    { name: 'Nuestra Visión',  href: '#nosotros', needsArticles: false },
    { name: 'Valores',         href: '#nosotros', needsArticles: false },
    { name: 'Gestión',         href: '/panel/articulos', needsArticles: true },
  ],
  contacto: [
    { name: 'info@elatech.io',     href: 'mailto:info@elatech.io' },
    { name: '+54 9 221 613-8198',  href: 'https://wa.me/5492216138198' },
    { name: 'La Plata, Argentina', href: '#' },
  ],
};

const socialLinks = [
  { icon: Linkedin,  href: '#', label: 'LinkedIn' },
  { icon: Github,    href: '#', label: 'GitHub' },
  { icon: Instagram, href: '#', label: 'Instagram' },
  { icon: Twitter,   href: '#', label: 'Twitter' },
];

export default function Footer({ showArticles }: { showArticles: boolean }) {
  const scrollToSection = (href: string) => {
    if (href.startsWith('#')) {
      document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const servicios = footerLinks.servicios.filter((link) => showArticles || !link.needsArticles);
  const empresa = footerLinks.empresa.filter((link) => showArticles || !link.needsArticles);

  return (
    <footer style={{ backgroundColor: '#0D1B38' }}>
      <div className="page-container pt-20 pb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 mb-14">
          {/* Brand */}
          <div className="lg:col-span-1">
            <a
              href="#"
              onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
              className="font-editorial text-2xl font-light uppercase tracking-[0.08em] text-white select-none inline-block mb-5"
            >
              elatech
            </a>
            <p className="text-body-small mb-7 leading-relaxed" style={{ color: 'rgba(255,255,255,0.5)' }}>
              Transformando empresas a través de la tecnología y la innovación.
              Soluciones digitales que impulsan el crecimiento de tu negocio.
            </p>
            <div className="flex gap-3">
              {socialLinks.map((social) => {
                const Icon = social.icon;
                return (
                  <a
                    key={social.label}
                    href={social.href}
                    aria-label={social.label}
                    className="w-10 h-10 rounded-xl flex items-center justify-center transition-colors"
                    style={{ backgroundColor: 'rgba(255,255,255,0.07)', color: 'rgba(255,255,255,0.45)' }}
                  >
                    <Icon className="w-5 h-5" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Servicios */}
          <div>
            <h4 className="text-label text-white mb-5">Servicios</h4>
            <ul className="space-y-3">
              {servicios.map((link) => (
                <li key={link.name}>
                  <button
                    onClick={() => scrollToSection(link.href)}
                    className="text-body-small transition-colors hover:text-white"
                    style={{ color: 'rgba(255,255,255,0.5)' }}
                  >
                    {link.name}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Empresa */}
          <div>
            <h4 className="text-label text-white mb-5">Empresa</h4>
            <ul className="space-y-3">
              {empresa.map((link) => (
                <li key={link.name}>
                  {link.href.startsWith('#') ? (
                    <button
                      onClick={() => scrollToSection(link.href)}
                      className="text-body-small transition-colors hover:text-white"
                      style={{ color: 'rgba(255,255,255,0.5)' }}
                    >
                      {link.name}
                    </button>
                  ) : (
                    <a
                      href={link.href}
                      className="text-body-small transition-colors hover:text-white"
                      style={{ color: 'rgba(255,255,255,0.5)' }}
                    >
                      {link.name}
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Contacto */}
          <div>
            <h4 className="text-label text-white mb-5">Contacto</h4>
            <ul className="space-y-3">
              {footerLinks.contacto.map((link) => (
                <li key={link.name}>
                  <a
                    href={link.href}
                    target={link.href.startsWith('http') ? '_blank' : undefined}
                    rel={link.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                    className="text-body-small transition-colors hover:text-white"
                    style={{ color: 'rgba(255,255,255,0.5)' }}
                  >
                    {link.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 border-t flex flex-col sm:flex-row items-center justify-between gap-4" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
          <p className="text-body-small" style={{ color: 'rgba(255,255,255,0.35)' }}>
            © {new Date().getFullYear()} ElaTech. Todos los derechos reservados.
          </p>
          <div className="flex gap-6">
            <button className="text-body-small transition-colors hover:text-white" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Política de Privacidad
            </button>
            <button className="text-body-small transition-colors hover:text-white" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Términos de Servicio
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}
