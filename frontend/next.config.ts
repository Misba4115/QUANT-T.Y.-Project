import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Development is intentionally reachable through either loopback spelling.
  // Next 16 otherwise blocks its own chunks when the browser uses 127.0.0.1
  // while the dev server advertises localhost.
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  turbopack: {
    root: process.cwd(),
  },
  async rewrites() {
    const backendOrigin = (process.env.API_PROXY_TARGET || "http://127.0.0.1:8000").replace(/\/$/, "");
    return [
      {
        source: "/api/:path*",
        destination: `${backendOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
