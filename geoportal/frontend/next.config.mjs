/** @type {import('next').NextConfig} */
// PHI GIS Platform - Cruz Roja Colombiana Seccional Antioquia
const nextConfig = {
  basePath: '/geoportal',
  assetPrefix: '/geoportal',
  trailingSlash: false,
  output: 'standalone',
  images: {
    unoptimized: true
  }
};

export default nextConfig;
