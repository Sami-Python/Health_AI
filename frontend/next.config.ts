import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export for Cloudflare Pages
  output: "export",

  // Cloudflare Pages compatible settings
  images: {
    unoptimized: true, // Cloudflare doesn't support Next.js image optimization
  },

  // Trailing slash for static hosting
  trailingSlash: true,
};

export default nextConfig;
