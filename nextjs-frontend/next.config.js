/** @type {import(''next'').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb',
    },
    cpus: 1,
    workerThreads: false,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8010/api/v1/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
