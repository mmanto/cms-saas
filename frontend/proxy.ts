import { NextResponse, type NextRequest } from 'next/server';

import { PANEL_HEADER } from '@/lib/tenant';

/**
 * Marca las rutas del panel del club antes de renderizar.
 *
 * El panel es su propio backoffice (mismo design system que `/admin`): no debe
 * heredar el chrome ni los resets CSS del sitio del club. El layout raiz lee
 * esta marca y omite `site.Shell`; el proxy es la unica capa que conoce la ruta
 * en el servidor.
 */
export function proxy(request: NextRequest) {
  const headers = new Headers(request.headers);
  headers.set(PANEL_HEADER, '1');
  return NextResponse.next({ request: { headers } });
}

export const config = {
  matcher: '/panel/:path*',
};
