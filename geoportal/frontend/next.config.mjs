/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: '/geoportal',
  assetPrefix: '/geoportal',
  output: 'standalone',
  outputFileTracingRoot: '/opt/phi_gis_platform/geoportal/frontend',
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
  trailingSlash: false
};

export default nextConfig;
