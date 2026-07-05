import type { MetadataRoute } from "next";
import { getLiveBrains } from "@/lib/brains";
import { SITE } from "@/lib/site-config";

const BASE = SITE.origin;

export default function sitemap(): MetadataRoute.Sitemap {
  const pages: MetadataRoute.Sitemap = [
    { url: BASE, changeFrequency: "weekly", priority: 1 },
    { url: `${BASE}/brains`, changeFrequency: "weekly", priority: 0.9 },
    { url: `${BASE}/skills`, changeFrequency: "monthly", priority: 0.8 },
    { url: `${BASE}/pricing`, changeFrequency: "monthly", priority: 0.5 },
    { url: `${BASE}/privacy`, changeFrequency: "yearly", priority: 0.2 },
    { url: `${BASE}/terms`, changeFrequency: "yearly", priority: 0.2 },
    // The agent-facing doc is a first-class page for AI crawlers.
    { url: `${BASE}/AGENTS.md`, changeFrequency: "monthly", priority: 0.8 },
  ];

  const brainPages: MetadataRoute.Sitemap = getLiveBrains().map((brain) => ({
    url: `${BASE}/brains/${brain.slug}`,
    changeFrequency: "weekly",
    priority: 0.8,
  }));

  return [...pages, ...brainPages];
}
