import fs from "fs";
import path from "path";

export interface Brain {
  slug: string;
  name: string;
  source: string;
  tagline: string;
  bio: string;
  atomCount: number;
  connectionCount: number;
  editionCount: number;
  clusterCount: number;
  status: "live" | "scaffolded" | "requested";
  price: number; // in dollars
  topics: string[];
  packPath: string;
  badge?: string;
}

interface IndexEntry {
  slug: string;
  name: string;
  source: string;
  atom_count: number;
  connection_count: number;
  status: string;
  pack_path: string;
}

interface BrainConfig {
  brain_name: string;
  brain_source_description: string;
  brain_tagline?: string;
  badge?: string;
  edition_count?: number;
  clusters?: Record<string, unknown>;
  website?: {
    tagline?: string;
    bio?: string;
    topics?: string[];
    price?: number;
  };
}

// Try parent dir first (local dev), fall back to public/brains (Vercel)
const BRAINS_DIR = fs.existsSync(path.join(process.cwd(), "..", "brains", "index.json"))
  ? path.join(process.cwd(), "..", "brains")
  : path.join(process.cwd(), "public", "brains");

function loadBrains(): Brain[] {
  const indexPath = path.join(BRAINS_DIR, "index.json");
  const index: { brains: IndexEntry[] } = JSON.parse(
    fs.readFileSync(indexPath, "utf-8"),
  );

  return index.brains.filter((entry) => entry.status !== "hidden").map((entry) => {
    const configPath = fs.existsSync(path.join(BRAINS_DIR, entry.slug, "brain.json"))
      ? path.join(BRAINS_DIR, entry.slug, "brain.json")
      : path.join(process.cwd(), "public", "brains", entry.slug, "brain.json");
    const config: BrainConfig = JSON.parse(
      fs.readFileSync(configPath, "utf-8"),
    );

    const statusMap: Record<string, Brain["status"]> = {
      live: "live",
      ingesting: "scaffolded",
      scaffolded: "scaffolded",
      requested: "requested",
    };

    return {
      slug: entry.slug,
      name: config.brain_name,
      source: config.brain_source_description,
      tagline: config.website?.tagline ?? config.brain_tagline ?? "",
      bio: config.website?.bio ?? "",
      atomCount: entry.atom_count,
      connectionCount: entry.connection_count,
      editionCount: config.edition_count ?? 0,
      clusterCount: Object.keys(config.clusters ?? {}).length,
      status: statusMap[entry.status] ?? "scaffolded",
      price: config.website?.price ?? 29,
      topics: config.website?.topics ?? [],
      packPath: entry.pack_path,
      // Badges (V1/V2/NEW/Draft) are intentionally suppressed site-wide.
      // The data still lives in brain.json — we just don't render it.
      badge: undefined,
    };
  });
}

export const BRAINS: Brain[] = loadBrains().sort((a, b) => {
  const lastA = a.name.split(" ").pop()?.toLowerCase() ?? "";
  const lastB = b.name.split(" ").pop()?.toLowerCase() ?? "";
  return lastA.localeCompare(lastB);
});

export function getBrain(slug: string): Brain | undefined {
  return BRAINS.find((b) => b.slug === slug);
}

export function getLiveBrains(): Brain[] {
  return BRAINS.filter((b) => b.status === "live");
}

// Order matters: leads with the skills that are structurally impossible to fake
// with a single prompted LLM call (evolve = temporal, connect = typed-graph,
// surprise = curated-atom retrieval). /advise is most prompt-replicable so it
// goes last. `uniqueToBrains` controls the "Only with a brain" badge on /skills.
export const SKILLS = [
  { name: "evolve", title: "Evolve", desc: "Watch a thinker change their mind across time \u2014 dated quotes, in order.", icon: "\u{1F4C8}", workflow: "Learning", uniqueToBrains: true },
  { name: "connect", title: "Connect", desc: "Find a typed bridge between two ideas in the graph.", icon: "\u{1F517}", workflow: "Creative", uniqueToBrains: true },
  { name: "surprise", title: "Surprise", desc: "Curated atom you didn\u2019t go looking for.", icon: "\u2728", workflow: "Creative", uniqueToBrains: true },
  { name: "predict", title: "Predict", desc: "Cascade second and third-order effects from their worldview.", icon: "\u{1F52E}", workflow: "Forecast", uniqueToBrains: false },
  { name: "coach", title: "Coach", desc: "Sequential Socratic questions in their voice.", icon: "\u{1FA9E}", workflow: "Decision", uniqueToBrains: false },
  { name: "debate", title: "Debate", desc: "Stress-test a position from their actual stance.", icon: "\u2694\uFE0F", workflow: "Decision", uniqueToBrains: false },
  { name: "teach", title: "Teach", desc: "Concepts through their lens, in their frameworks.", icon: "\u{1F4D6}", workflow: "Learning", uniqueToBrains: false },
  { name: "advise", title: "Advise", desc: "Counsel grounded in the brain\u2019s atoms.", icon: "\u{1F9ED}", workflow: "Decision", uniqueToBrains: false },
];

export const TIERS = [
  {
    name: "Standard",
    price: 29,
    period: "per brain",
    features: [
      "Full skill pack (8 AI skills)",
      "Knowledge atoms (JSON)",
      "Brain context file (MD)",
      "Visual brain explorer (HTML)",
      "Mental model map",
      "All topic lenses",
    ],
    cta: "Get this brain — free",
    highlighted: true,
  },
  {
    name: "Pro",
    price: 79,
    period: "per brain",
    features: [
      "Everything in Standard",
      "Pre-computed embeddings (1536-dim)",
      "API access for semantic search",
      "Auto-updates on new content",
      "Priority support",
    ],
    cta: "Go Pro",
    highlighted: false,
  },
  {
    name: "API",
    price: 199,
    period: "per month",
    features: [
      "Programmatic access to all brains",
      "Semantic search endpoint",
      "Graph traversal API",
      "Usage analytics",
      "Webhook notifications",
    ],
    cta: "Get API access",
    highlighted: false,
  },
];
