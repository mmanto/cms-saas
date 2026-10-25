import { useEffect, useRef, useState } from 'react';
import {
  Code2,
  GraduationCap,
  Search,
  FolderKanban,
  Brain,
  Microscope,
} from 'lucide-react';

const servicios = [
  {
    icon: Code2,
    title: 'Desarrollo de Software',
    description: 'Creamos soluciones a medida como producto o servicio. Aplicaciones web, móviles y sistemas empresariales con las últimas tecnologías.',
  },
  {
    icon: GraduationCap,
    title: 'Capacitaciones',
    description: 'Programas de formación en tecnologías actuales. Actualizamos a tu equipo en las herramientas y prácticas más demandadas del mercado.',
  },
  {
    icon: Search,
    title: 'Relevamiento Tecnológico',
    description: 'Análisis exhaustivo del estado actual de tu infraestructura. Identificamos oportunidades de mejora y modernización.',
  },
  {
    icon: FolderKanban,
    title: 'Gestión de Proyectos IT',
    description: 'Tomamos, dirigimos y gestionamos tu proyecto mediante metodologías ágiles. Entregas efectivas alineadas con tus objetivos de negocio.',
  },
  {
    icon: Brain,
    title: 'Asesoramiento en IA',
    description: 'Consultoría especializada en inteligencia artificial. Identificamos oportunidades e implementamos IA para optimizar tus procesos.',
  },
  {
    icon: Microscope,
    title: 'Investigación de Tecnologías',
    description: 'Análisis, descubrimiento y evaluación de posibilidades de implementación de tecnologías emergentes para tu organización.',
  },
];

export default function Servicios() {
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
    const cards = sectionRef.current?.querySelectorAll('.service-card');
    cards?.forEach((card) => observer.observe(card));
    return () => observer.disconnect();
  }, []);

  return (
    <section
      id="servicios"
      ref={sectionRef}
      className="py-28 lg:py-36 px-4 sm:px-6 lg:px-8 bg-white"
    >
      <div className="page-container">
        {/* Header */}
        <div className="text-center mb-20">
          <span className="text-label block mb-5" style={{ color: '#2793b4' }}>
            Nuestras Soluciones
          </span>
          <h2 className="text-h2 text-gray-900">
            Nuestros <span style={{ fontStyle: 'italic', color: '#2793b4' }}>Servicios</span>
          </h2>
          <p className="text-body text-gray-500 max-w-2xl mx-auto mt-6">
            Desarrollamos herramientas que impulsan la eficiencia, la comunicación
            y la competitividad de nuestros clientes.
          </p>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {servicios.map((servicio, index) => {
            const Icon = servicio.icon;
            const isVisible = visibleCards.has(index);
            return (
              <div
                key={servicio.title}
                data-index={index}
                className={`service-card rounded-3xl p-10 border border-gray-100 hover:shadow-md transition-all duration-500 hover:-translate-y-1 ${
                  isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
                }`}
                style={{ transitionDelay: `${index * 80}ms` }}
              >
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6"
                  style={{ backgroundColor: '#EEF8FC', color: '#2793b4' }}
                >
                  <Icon className="w-7 h-7" />
                </div>
                <h3 className="text-h3 text-gray-900 mb-3">{servicio.title}</h3>
                <p className="text-body-small text-gray-500">{servicio.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
