/** @type {import('next').NextConfig} */
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
