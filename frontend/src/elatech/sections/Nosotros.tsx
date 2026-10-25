import { useEffect, useRef, useState } from 'react';
import { Target, Eye, Lightbulb, Heart, Award, Rocket } from 'lucide-react';

const valores = [
  {
    icon: Lightbulb,
    title: 'Innovación',
    description: 'Buscamos constantemente nuevas formas de resolver problemas con tecnología.',
  },
  {
    icon: Heart,
    title: 'Compromiso',
    description: 'Nos involucramos profundamente en cada proyecto como si fuera nuestro.',
  },
  {
    icon: Award,
    title: 'Calidad',
    description: 'Excelencia en cada entrega, superando las expectativas de nuestros clientes.',
  },
  {
    icon: Rocket,
    title: 'Agilidad',
    description: 'Respuesta rápida y adaptación continua a los cambios del mercado.',
  },
];

export default function Nosotros() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setIsVisible(true); },
      { threshold: 0.2 }
    );
    if (sectionRef.current) observer.observe(sectionRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <section
      id="nosotros"
      ref={sectionRef}
      className="py-28 lg:py-36 px-4 sm:px-6 lg:px-8 bg-white"
    >
      <div className="page-container">
        {/* Header */}
        <div className="text-center mb-20">
          <span className="text-label block mb-5" style={{ color: '#2793b4' }}>
            Conócenos
          </span>
          <h2 className="text-h2 text-gray-900">
            Quienes <span style={{ fontStyle: 'italic', color: '#2793b4' }}>Somos</span>
          </h2>
        </div>

        {/* Descripción + Misión & Visión */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-20">
          <div
            className={`transition-all duration-700 ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-8'}`}
          >
            <div className="rounded-3xl p-10 bg-white shadow-sm border border-gray-100">
              <p className="text-body text-gray-700 leading-relaxed mb-6">
                En <span className="font-semibold" style={{ color: '#2793b4' }}>elatech.io</span> somos una empresa
                especializada en el desarrollo, diseño, programación y mantenimiento de soluciones
                tecnológicas adaptadas a las necesidades de cada cliente.
              </p>
              <p className="text-body-small text-gray-600 leading-relaxed mb-5">
                Nuestro objetivo es ayudar a las organizaciones a evolucionar hacia un entorno más
                digital, automatizado y eficiente, optimizando procesos y fortaleciendo la comunicación
                interna y externa.
              </p>
              <p className="text-body-small text-gray-600 leading-relaxed">
                Contamos con un equipo interdisciplinario que combina innovación, conocimiento y
                atención personalizada para ofrecer resultados concretos y sostenibles.
              </p>
            </div>
          </div>

          <div
            className={`space-y-6 transition-all duration-700 delay-200 ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8'}`}
          >
            {/* Misión */}
            <div className="rounded-3xl p-8 bg-white shadow-sm border-l-4" style={{ borderLeftColor: '#2793b4' }}>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ backgroundColor: '#EEF8FC' }}>
                  <Target className="w-5 h-5" style={{ color: '#2793b4' }} />
                </div>
                <h3 className="text-h3 text-gray-900">Misión</h3>
              </div>
              <p className="text-body-small text-gray-600 leading-relaxed">
                Nuestro proceso de relevamiento identifica oportunidades de mejora, evalúa tu
                infraestructura tecnológica actual y determina el mejor camino para tu
                transformación digital.
              </p>
            </div>

            {/* Visión */}
            <div className="rounded-3xl p-8 bg-white shadow-sm border-l-4" style={{ borderLeftColor: '#C5A55A' }}>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ backgroundColor: '#fdf8ef' }}>
                  <Eye className="w-5 h-5" style={{ color: '#C5A55A' }} />
                </div>
                <h3 className="text-h3 text-gray-900">Visión</h3>
              </div>
              <p className="text-body-small text-gray-600 leading-relaxed">
                Ser una empresa referente en innovación tecnológica a nivel nacional, reconocida
                por su compromiso, calidad de servicio y capacidad para ofrecer soluciones digitales
                que transformen positivamente la manera de trabajar y comunicar.
              </p>
            </div>
          </div>
        </div>

        {/* Valores */}
        <div>
          <h3 className="text-h3 text-gray-900 text-center mb-12">
            Nuestros <span style={{ fontStyle: 'italic', color: '#2793b4' }}>Valores</span>
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {valores.map((valor, index) => {
              const Icon = valor.icon;
              return (
                <div
                  key={valor.title}
                  className={`rounded-3xl p-8 text-center bg-white shadow-sm border border-gray-100 transition-all duration-500 hover:-translate-y-1 ${
                    isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
                  }`}
                  style={{ transitionDelay: `${400 + index * 100}ms` }}
                >
                  <div
                    className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-5"
                    style={{ backgroundColor: '#EEF8FC', color: '#2793b4' }}
                  >
                    <Icon className="w-7 h-7" />
                  </div>
                  <h4 className="text-h3 text-gray-900 mb-2">{valor.title}</h4>
                  <p className="text-body-small text-gray-500">{valor.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
