import Link from 'next/link';

import { requestClub, siteForClub } from '@/lib/sites';

/**
 * 404: el del sitio del club, o uno minimo de la plataforma. Next usa este
 * archivo para toda la app, asi que la rama de la plataforma tambien cubre los
 * 404 del backoffice (por ejemplo, `/admin` en el host de un club).
 *
 * No lleva `export const dynamic`: el layout raiz ya es `force-dynamic` y el
 * build reporta `/_not-found` como dinamica.
 */
export default async function NotFound() {
  const site = siteForClub(await requestClub());
  if (site) return site.notFound;

  return (
    <main style={{ maxWidth: 720, margin: '0 auto', padding: '4rem 1.5rem' }}>
      <h1 style={{ fontSize: '1.6rem', marginBottom: '0.5rem' }}>No encontramos esa pagina</h1>
      <p style={{ color: '#9aa4bf' }}>
        <Link href="/" style={{ color: 'var(--brand)' }}>
          Volver al inicio
        </Link>
      </p>
    </main>
  );
}
