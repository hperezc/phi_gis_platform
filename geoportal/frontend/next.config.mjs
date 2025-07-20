/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    outputFileTracingRoot: undefined,
  },
  env: {
    NEXT_PUBLIC_API_URL: 'https://aplicativosgrd.crantioquia.org.co/api'
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://aplicativosgrd.crantioquia.org.co/api/:path*'
      }
    ];
  },
  // Agregar configuración para servir archivos estáticos
  assetPrefix: process.env.NODE_ENV === 'production' ? 'https://aplicativosgrd.crantioquia.org.co' : '',
  basePath: '',
  trailingSlash: false
};

export default nextConfig;
