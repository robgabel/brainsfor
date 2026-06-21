// Single source of brain-atom data for serverless routes (/api/skill citations,
// /api/board retrieval): fetch the brain's shipped static pack JSON
// (public/brains/<slug>/brain-atoms.json) over HTTP from the site's own CDN.
//
// History / why this shape:
//  1. Originally fs.readFile()'d the pack via a dynamic path — Next traced the
//     ENTIRE brains/ tree into the function bundle, blowing Vercel's size limit.
//  2. Moved to Supabase to keep the bundle flat. But serving multi-MB atom sets
//     from Supabase on every skill/board call burns egress and, on the free tier,
//     pauses the project — taking the demos down site-wide and forcing a manual
//     per-brain migrate into the prod DB.
//  3. Now: fetch the static CDN asset. No fs trace (bundle stays flat), no DB
//     dependency (no egress, no pausing, no per-brain prod migration), and the
//     data is byte-identical to what the brain pack ships. Cached per serverless
//     instance — atoms are immutable between deploys.
//
// The pack JSON's atoms already carry every DbAtom field, so this is a 1:1 read.

const SLUG_RE = /^[a-z][a-z0-9-]{1,60}$/;

export interface DbAtom {
  id: string;
  content: string | null;
  original_quote: string | null;
  implication: string | null;
  confidence_tier: string | null;
  confidence: number | null;
  cluster: string | null;
  topics: string[] | null;
  source_ref: string | null;
  source_url: string | null;
  source_date: string | null;
}

/** Public origin that serves /brains/<slug>/brain-atoms.json from the CDN.
 *  Override per environment with NEXT_PUBLIC_SITE_URL; defaults to prod. */
function siteOrigin(): string {
  const explicit = process.env.NEXT_PUBLIC_SITE_URL;
  if (explicit) return explicit.replace(/\/+$/, "");
  return "https://brainsforfree.com";
}

const atomCache = new Map<string, DbAtom[]>();

/** All atoms for a brain, read from its shipped pack JSON on the CDN. Cached per
 *  instance. Returns [] on any failure (callers degrade gracefully). */
export async function fetchBrainAtoms(slug: string): Promise<DbAtom[]> {
  if (!SLUG_RE.test(slug)) return [];
  const hit = atomCache.get(slug);
  if (hit) return hit;

  const url = `${siteOrigin()}/brains/${slug}/brain-atoms.json`;
  try {
    // no-store: the per-instance atomCache below handles reuse; this avoids
    // Next's fetch data-cache size cap on large (>2MB) packs.
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) {
      console.error(`[brain-atoms-db] ${url}: HTTP ${res.status}`);
      return [];
    }
    const data: unknown = await res.json();
    const raw = (data as { atoms?: unknown })?.atoms;
    if (!Array.isArray(raw)) {
      console.error(`[brain-atoms-db] ${url}: no atoms array`);
      return [];
    }
    const atoms: DbAtom[] = raw.map((a: Record<string, unknown>) => ({
      id: String(a.id ?? ""),
      content: (a.content as string) ?? null,
      original_quote: (a.original_quote as string) ?? null,
      implication: (a.implication as string) ?? null,
      confidence_tier: (a.confidence_tier as string) ?? null,
      confidence: typeof a.confidence === "number" ? a.confidence : null,
      cluster: (a.cluster as string) ?? null,
      topics: Array.isArray(a.topics) ? (a.topics as string[]) : null,
      source_ref: (a.source_ref as string) ?? null,
      source_url: (a.source_url as string) ?? null,
      source_date: (a.source_date as string) ?? null,
    }));
    atomCache.set(slug, atoms);
    return atoms;
  } catch (e) {
    console.error(`[brain-atoms-db] fetch failed for ${slug}:`, e);
    return [];
  }
}
