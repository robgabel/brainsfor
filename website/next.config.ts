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
          { key: "X-Robots-Tag", value: "noindex, nofollow" },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
      // Force Markdown content-type for the agent doc — Vercel defaults to
      // text/markdown but be explicit so non-browser clients (curl, agent
      // fetchers) don't get surprised.
      {
        source: "/AGENTS.md",
        headers: [
          { key: "Content-Type", value: "text/markdown; charset=utf-8" },
        ],
      },
      {
        source: "/llms.txt",
        headers: [
          { key: "Content-Type", value: "text/markdown; charset=utf-8" },
        ],
      },
    ];
  },
  // Mirror /AGENTS.md at /llms.txt so we maintain one source file. The
  // emerging llms.txt convention expects this exact path.
  async rewrites() {
    return [{ source: "/llms.txt", destination: "/AGENTS.md" }];
  },
  // The /api/skill and /api/board routes read brain-atoms.json via dynamic fs
  // paths (path.join(BRAINS_DIR, slug, ...)). Next can't statically resolve the
  // slug, so it traces the ENTIRE brains/ tree (1979 source files + the 31MB
  // redundant brain-atoms.js + zips + context.md) into those function bundles,
  // blowing past Vercel's serverless function size limit ("Deploying outputs"
  // failure). Exclude everything the routes DON'T read at runtime; keep only
  // brain-atoms.json (the file they actually load).
  outputFileTracingExcludes: {
    "*": [
      "**/brains/*/research/**",
      "**/brains/*/source/**",
      "**/brains/*/data/**",
      "**/brains/*/evals/**",
      "**/brains/*/build-progress.json",
      "**/brains/*/synthesis.md",
      "**/brains/*/pack/brain-atoms.js",
      "**/brains/*/pack/brain-context.md",
      "**/brains/*/pack/skills/**",
      "**/brains/*/pack/*.zip",
      "**/brains/*/cross-connections-backup.json",
      "**/public/brains/*/brain-atoms.js",
      "**/public/brains/*/brain-context.md",
      "**/public/brains/*/*.zip",
    ],
  },
};

export default nextConfig;
