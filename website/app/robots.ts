import type { MetadataRoute } from "next";

// Crawl policy for the public site. The agent surface (/AGENTS.md, /llms.txt,
// /brains/* static packs) is intentionally crawlable — being discoverable by
// answer engines and AI crawlers is the point. Only the logged-in and
// API surfaces are excluded.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/", "/dashboard", "/auth/", "/login"],
    },
    sitemap: "https://brainsforagents.com/sitemap.xml",
  };
}
