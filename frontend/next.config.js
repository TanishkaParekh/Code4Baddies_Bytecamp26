/** @type {import('next').NextConfig} */
const nextConfig = {
  // Proxy /api/* → backend during local dev so CORS is never an issue
  // In production, NEXT_PUBLIC_API_URL points directly to Railway
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
