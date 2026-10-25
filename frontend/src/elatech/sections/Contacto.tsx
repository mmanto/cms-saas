import { useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import {
  Mail,
  Phone,
  MapPin,
  Send,
  MessageCircle,
  Clock,
  CheckCircle2,
} from 'lucide-react';

const inputClass =
  'w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-body-small text-gray-900 outline-none';

export default function Contacto() {
  const [formData, setFormData] = useState({
    nombre: '',
    email: '',
    empresa: '',
    telefono: '',
    mensaje: '',
  });
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitted(true);
    setTimeout(() => {
      setIsSubmitted(false);
      setFormData({ nombre: '', email: '', empresa: '', telefono: '', mensaje: '' });
    }, 3000);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const contactInfo = [
    { icon: Mail,    label: 'Email',     value: 'info@elatech.io',        href: 'mailto:info@elatech.io' },
    { icon: Phone,   label: 'Teléfono',  value: '+54 9 221 613-8198',      href: 'https://wa.me/5492216138198?text=Hola,%20escribo%20para%20consultar%20por%20sus%20servicios' },
    { icon: MapPin,  label: 'Ubicación', value: 'La Plata, Argentina',     href: '#' },
    { icon: Clock,   label: 'Horario',   value: 'Lun - Vie: 9:00 - 18:00', href: '#' },
  ];

  return (
    <section
      id="contacto"
      className="py-28 lg:py-36 px-4 sm:px-6 lg:px-8 bg-white"
    >
      <div className="page-container">
        {/* Header */}
        <div className="text-center mb-20">
          <span className="text-label block mb-5" style={{ color: '#2793b4' }}>
            Estamos para ayudarte
          </span>
          <h2 className="text-h2 text-gray-900">
            Contacta<span style={{ fontStyle: 'italic', color: '#2793b4' }}>nos</span>
          </h2>
          <p className="text-body text-gray-500 max-w-2xl mx-auto mt-6">
            ¿Tenés un proyecto en mente? Escribinos y te ayudamos a hacerlo realidad.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Info */}
          <div className="lg:col-span-2 space-y-4">
            {contactInfo.map((item) => {
              const Icon = item.icon;
              return (
                <a
                  key={item.label}
                  href={item.href}
                  target={item.href.startsWith('http') ? '_blank' : undefined}
                  rel={item.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                  className="flex items-center gap-4 rounded-3xl p-6 bg-white border border-gray-100 shadow-sm hover:shadow-md transition-shadow group"
                >
                  <div
                    className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0"
                    style={{ backgroundColor: '#EEF8FC', color: '#2793b4' }}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-label text-gray-400">{item.label}</span>
                    <p className="text-body-small text-gray-900 font-medium mt-0.5">{item.value}</p>
                  </div>
                </a>
              );
            })}

            {/* WhatsApp */}
            <a
              href="https://wa.me/5492216138198?text=Hola,%20escribo%20para%20consultar%20por%20sus%20servicios"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-4 rounded-3xl p-6 mt-4 shadow-sm hover:shadow-md transition-shadow"
              style={{ backgroundColor: '#DCFCE7', border: '1px solid #bbf7d0' }}
            >
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#86efac' }}>
                <MessageCircle className="w-6 h-6 text-green-800" />
              </div>
              <div>
                <span className="text-label text-green-700">WhatsApp</span>
                <p className="text-body-small text-gray-900 font-medium mt-0.5">Chateá con nosotros</p>
              </div>
            </a>
          </div>

          {/* Formulario */}
          <div className="lg:col-span-3">
            <form
              onSubmit={handleSubmit}
              className="rounded-3xl p-10 bg-white border border-gray-100 shadow-sm"
            >
              {isSubmitted ? (
                <div className="flex flex-col items-center justify-center py-14 text-center">
                  <div className="w-16 h-16 rounded-full flex items-center justify-center mb-5" style={{ backgroundColor: '#DCFCE7' }}>
                    <CheckCircle2 className="w-8 h-8 text-green-600" />
                  </div>
                  <h3 className="text-h3 text-gray-900 mb-2">¡Mensaje enviado!</h3>
                  <p className="text-body-small text-gray-500">Nos pondremos en contacto contigo pronto.</p>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                    <div className="space-y-2">
                      <label htmlFor="nombre" className="text-body-small text-gray-600">Nombre *</label>
                      <input id="nombre" name="nombre" value={formData.nombre} onChange={handleChange}
                        placeholder="Tu nombre" required
                        className={inputClass} />
                    </div>
                    <div className="space-y-2">
                      <label htmlFor="email" className="text-body-small text-gray-600">Email *</label>
                      <input id="email" name="email" type="email" value={formData.email} onChange={handleChange}
                        placeholder="tu@email.com" required
                        className={inputClass} />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                    <div className="space-y-2">
                      <label htmlFor="empresa" className="text-body-small text-gray-600">Empresa</label>
                      <input id="empresa" name="empresa" value={formData.empresa} onChange={handleChange}
                        placeholder="Nombre de tu empresa"
                        className={inputClass} />
                    </div>
                    <div className="space-y-2">
                      <label htmlFor="telefono" className="text-body-small text-gray-600">Teléfono</label>
                      <input id="telefono" name="telefono" value={formData.telefono} onChange={handleChange}
                        placeholder="+54 9 ..."
                        className={inputClass} />
                    </div>
                  </div>

                  <div className="space-y-2 mb-7">
                    <label htmlFor="mensaje" className="text-body-small text-gray-600">Mensaje *</label>
                    <textarea id="mensaje" name="mensaje" value={formData.mensaje} onChange={handleChange}
                      placeholder="Contanos sobre tu proyecto..."
                      required rows={4}
                      className={`${inputClass} resize-none`} />
                  </div>

                  <button
                    type="submit"
                    className="text-cta w-full inline-flex items-center justify-center gap-2 rounded-xl py-4 text-white transition-opacity hover:opacity-90"
                    style={{ backgroundColor: '#2793b4' }}
                  >
                    Enviar Mensaje
                    <Send className="w-4 h-4" />
                  </button>
                </>
              )}
            </form>
          </div>
        </div>
      </div>
    </section>
  );
}
