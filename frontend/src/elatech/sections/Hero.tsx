export default function Hero({ showArticles }: { showArticles: boolean }) {
  const scrollToSection = (href: string) => {
    const element = document.querySelector(href);
    if (element) element.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="relative min-h-screen flex flex-col justify-center px-4 sm:px-6 lg:px-8 overflow-hidden">
      {/* Fondo navy */}
      <div className="absolute inset-0" style={{ backgroundColor: '#2A3B4D' }} />

      {/* Overlay degradado */}
      <div className="absolute inset-0" style={{
        background: 'linear-gradient(180deg, rgba(42,59,77,0.5) 0%, rgba(42,59,77,0.2) 40%, rgba(42,59,77,0.7) 100%)',
      }} />

      {/* Grid de puntos */}
      <div className="absolute inset-0" style={{
        backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px)',
        backgroundSize: '30px 30px',
      }} />

      {/* Manchas de luz */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: 'radial-gradient(ellipse at 18% 65%, rgba(39,147,180,0.12) 0%, transparent 52%), radial-gradient(ellipse at 82% 18%, rgba(197,165,90,0.07) 0%, transparent 45%)',
      }} />

      <div className="relative page-container w-full py-28 text-center">

        {/* Texto */}
        <span className="text-label block mb-7" style={{ color: '#C5A55A' }}>
          Consultoría &amp; Capacitación Tecnológica
        </span>
        <h1 className="text-h1 text-white mb-7 mx-auto" style={{ maxWidth: '800px' }}>
          Transformamos tu negocio con{' '}
          <span style={{ color: '#2793b4', fontStyle: 'italic' }}>tecnología</span>
        </h1>
        <p className="text-body mx-auto mb-10" style={{ color: 'rgba(255,255,255,0.62)', maxWidth: '560px' }}>
          Bienvenidos a elatech.io — soluciones tecnológicas innovadoras que acompañan a
          las organizaciones en su proceso de transformación digital.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-20">
          <button
            onClick={() => scrollToSection('#servicios')}
            className="text-cta inline-flex items-center justify-center rounded-lg transition-all duration-200 px-7 py-4 text-white"
            style={{ backgroundColor: '#2793b4' }}
          >
            Explorar Servicios
          </button>
          <button
            onClick={() => scrollToSection('#contacto')}
            className="text-cta inline-flex items-center justify-center rounded-lg transition-all duration-200 px-7 py-4 border text-white hover:bg-white/10"
            style={{ borderColor: 'rgba(255,255,255,0.22)' }}
          >
            Contactar
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 max-w-2xl mx-auto">
          {showArticles ? (
            <button
              onClick={() => scrollToSection('#proyectos')}
              className="rounded-3xl p-8 text-center hover:bg-white/10 transition-colors"
              style={{ backgroundColor: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.1)' }}
            >
              <div className="text-h3 text-white mb-1">Proyectos</div>
            </button>
          ) : null}
          <button
            onClick={() => scrollToSection('#nosotros')}
            className="rounded-3xl p-8 text-center hover:bg-white/10 transition-colors"
            style={{ backgroundColor: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.1)' }}
          >
            <div className="text-h3 text-white mb-1">Nosotros</div>
          </button>
          {showArticles ? (
            <button
              onClick={() => scrollToSection('#capacitaciones')}
              className="rounded-3xl p-8 text-center hover:bg-white/10 transition-colors"
              style={{ backgroundColor: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.1)' }}
            >
              <div className="text-h3 text-white mb-1">Capacitaciones</div>
            </button>
          ) : null}
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1 pointer-events-none" style={{ opacity: 0.35 }}>
        <span className="text-label text-white">scroll</span>
        <svg className="w-4 h-4 text-white animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </section>
  );
}
