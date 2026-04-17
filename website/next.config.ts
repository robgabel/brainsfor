import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Global security headers. CORS for /api/skill is handled inside the
  // route handler so we can do exact-origin matching without wrestling
  // path-to-regexp over colons in scheme.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
