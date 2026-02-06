import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Cloudflare Pages compatible settings
  images: {
    unoptimized: true, // Cloudflare doesn't support Next.js image optimization
  },
  // Ensure trailing slashes for static hosting compatibility
  trailingSlash: false,
};

export default nextConfig;
