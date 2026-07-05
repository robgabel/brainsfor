// Build-time multi-tenant seam — the "Brains For ___" system as config.
//
// One codebase, N Vercel projects. Each sister surface is a separate Vercel
// project on THIS repo that sets NEXT_PUBLIC_SITE_ID (+ its domain). Tenancy
// is resolved at BUILD time, not request time, so every page stays statically
// generated (SSG) exactly as today — no host-based branching in the request
// path, no marginal infra per site (no DB, no scrapers; packs are static).
//
// Spin up a sister site:
//   1. Add an entry to SITES below (brand, copy, catalog subset).
//   2. New Vercel project → same repo, Root Directory `website`, same env vars,
//      plus NEXT_PUBLIC_SITE_ID=<id>. Attach the domain. Done.
//
// The flagship (brainsforagents.com) is the default — builds without
// NEXT_PUBLIC_SITE_ID behave exactly as before this seam existed.

export interface SiteConfig {
  id: string;
  /** Display brand, e.g. "brainsforagents" (nav logo, footer, titles). */
  name: string;
  /** Hero one-liner used in default metadata. */
  tagline: string;
  /** Default meta description. */
  description: string;
  /** Canonical https origin (metadataBase, sitemap, CORS, pack asset URLs). */
  origin: string;
  /** Additional allowed CORS origins (www variant etc). */
  extraOrigins: string[];
  /** Catalog subset by slug; null = every live brain in brains/index.json. */
  brainSlugs: string[] | null;
}

const SITES: Record<string, SiteConfig> = {
  agents: {
    id: "agents",
    name: "brainsforagents",
    tagline: "Load a genius into your AI",
    description:
      "Knowledge graphs of the world's best thinkers, packaged as 8 AI skills you actually use. Think better in seconds.",
    origin: "https://brainsforagents.com",
    extraOrigins: ["https://www.brainsforagents.com"],
    brainSlugs: null,
  },
  // Example sister surface (inactive until a Vercel project sets
  // NEXT_PUBLIC_SITE_ID=sale). Edit copy/catalog before launching it.
  sale: {
    id: "sale",
    name: "brainsforsale",
    tagline: "Load a genius into your AI",
    description:
      "Knowledge graphs of the world's best thinkers, packaged as 8 AI skills you actually use.",
    origin: "https://brainsforsale.com",
    extraOrigins: ["https://www.brainsforsale.com"],
    brainSlugs: null,
  },
};

const siteId = process.env.NEXT_PUBLIC_SITE_ID ?? "agents";
export const SITE: SiteConfig = SITES[siteId] ?? SITES.agents;
