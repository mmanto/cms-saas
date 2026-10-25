import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Necesario para el Dockerfile de produccion: genera .next/standalone.
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,
  experimental: {
    // El formulario del articulo sube la imagen por una Server Action; el tope
    // de la API es 5 MB, mas el overhead del multipart.
    serverActions: { bodySizeLimit: '6mb' },
  },
};

export default nextConfig;
