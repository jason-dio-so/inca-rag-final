/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
    DEV_MOCK_MODE: process.env.DEV_MOCK_MODE || '0',
  },
}

module.exports = nextConfig
