import { useEffect, useRef, useState } from 'react';
import {
  ClipboardList,
  Search,
  BarChart3,
  FileText,
  Lightbulb,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react';

const pasos = [
  {
    icon: ClipboardList,
    title: 'Recolección de Información',
    description: 'Reunimos datos sobre tu infraestructura actual, procesos y necesidades específicas.',
  },
  {
    icon: Search,
    title: 'Análisis Detallado',
    description: 'Evaluamos cada aspecto de tu entorno tecnológico para identificar fortalezas y áreas de mejora.',
  },
  {
    icon: BarChart3,
    title: 'Evaluación de Tecnologías',
    description: 'Comparamos las soluciones disponibles con tus requerimientos y presupuesto.',
  },
  {
    icon: FileText,
    title: 'Documentación',
    description: 'Elaboramos un informe completo con hallazgos, recomendaciones y roadmap de implementación.',
  },
  {
    icon: Lightbulb,
    title: 'Propuesta de Valor',
    description: 'Presentamos soluciones personalizadas que maximicen el retorno de inversión.',
  },
];

const beneficios = [
  'Identificación de cuellos de botella tecnológicos',
  'Reducción de costos operativos',
  'Mejora en la seguridad de la información',
  'Optimización de procesos de negocio',
  'Planificación tecnológica a largo plazo',
  'Toma de decisiones basada en datos',
];

export default function Relevamiento() {
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

  const scrollToContact = () => {
    document.querySelector('#contacto')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section
      id="relevamiento"
      ref={sectionRef}
      className="py-28 lg:py-36 px-4 sm:px-6 lg:px-8"
      style={{ backgroundColor: '#f3f4f6' }}
    >
      <div className="page-container">
        {/* Header */}
        <div className="text-center mb-20">
          <span className="text-label block mb-5" style={{ color: '#2793b4' }}>
            Proceso Estratégico
          </span>
          <h2 className="text-h2 text-gray-900">
            Relevamiento <span style={{ fontStyle: 'italic', color: '#2793b4' }}>Tecnológico</span>
          </h2>
          <p className="text-body text-gray-500 max-w-3xl mx-auto mt-6">
            En ElaTech entendemos que cada empresa tiene necesidades únicas. Por eso, antes de
            proponer cualquier solución, realizamos un análisis detallado del estado actual de
            tu organización.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
          {/* Proceso */}
          <div
            className={`transition-all duration-700 ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-8'}`}
          >
            <h3 className="text-h3 text-gray-900 mb-8">Nuestro Proceso</h3>
            <div className="space-y-4">
              {pasos.map((paso, index) => {
                const Icon = paso.icon;
                return (
                  <div key={paso.title} className="flex gap-4 group">
                    <div className="flex flex-col items-center">
                      <div
                        className="w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 transition-colors"
                        style={{ backgroundColor: '#EEF8FC', color: '#2793b4' }}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      {index < pasos.length - 1 && (
                        <div className="w-0.5 h-full mt-2" style={{ backgroundColor: '#d1dce8' }} />
                      )}
                    </div>
                    <div className="pb-6 flex-1">
                      <span className="text-label mb-1 block" style={{ color: '#2793b4' }}>
                        Paso {index + 1}
                      </span>
                      <h4 className="text-h3 text-gray-900 mb-1 group-hover:opacity-70 transition-opacity">
                        {paso.title}
                      </h4>
                      <p className="text-body-small text-gray-500">{paso.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Beneficios + CTA */}
          <div
            className={`space-y-6 transition-all duration-700 delay-200 ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8'}`}
          >
            <div className="rounded-3xl p-10 bg-white shadow-sm" style={{ border: '1px solid #d1dce8' }}>
              <h3 className="text-h3 text-gray-900 mb-5">¿Por qué es importante?</h3>
              <p className="text-body-small text-gray-600 leading-relaxed mb-7">
                La actualización tecnológica no es solo sobre herramientas nuevas, es sobre
                encontrar las soluciones adecuadas que impulsen el crecimiento de tu negocio
                de manera sostenible y eficiente.
              </p>
              <div className="space-y-4">
                {beneficios.map((beneficio) => (
                  <div key={beneficio} className="flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 flex-shrink-0" style={{ color: '#2793b4' }} />
                    <span className="text-body-small text-gray-600">{beneficio}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* CTA */}
            <div
              className="rounded-3xl p-10 text-center bg-white"
              style={{ border: '1px solid #d1dce8' }}
            >
              <h4 className="text-h3 text-gray-900 mb-3">
                ¿Listo para transformar tu empresa?
              </h4>
              <p className="text-body-small text-gray-500 mb-7">
                Agenda un relevamiento tecnológico gratuito y descubrí el potencial de tu organización.
              </p>
              <button
                onClick={scrollToContact}
                className="text-cta inline-flex items-center gap-2 rounded-lg px-7 py-4 text-white transition-opacity hover:opacity-90"
                style={{ backgroundColor: '#2793b4' }}
              >
                Solicitar Relevamiento
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
