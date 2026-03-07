/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8123/api/:path*', // Ring MCP API
      },
    ]
  },
}

module.exports = nextConfig