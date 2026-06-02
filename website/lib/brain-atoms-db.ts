// Single source of brain-atom data for serverless routes: query Supabase instead
// of reading the multi-MB public/brains/<slug>/brain-atoms.json off the filesystem.
//
// Why this exists: /api/skill and /api/board used to fs.readFile() the pack JSON
// via a dynamic path (path.join(dir, slug, ...)). Next can't statically resolve the
// slug, so it traced the ENTIRE brains/ tree into those function bundles, blowing
// past Vercel's serverless function size limit ("Deploying outputs" failure) and
// freezing the live site on a stale build. Reading from Supabase keeps the bundle
// flat no matter how big or numerous the brains get.
//
// Uses the anon key — the *_atoms tables have an "Allow public read" RLS policy, so
// no service key is exposed to the edge. Slug is validated before it touches a table
// name. Atoms are cached per serverless instance (the data is immutable between deploys).

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

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

const SLUG_RE = /^[a-z][a-z0-9-]{1,60}$/;
const COLS =
  "id,content,original_quote,implication,confidence_tier,confidence,cluster,topics,source_ref,source_url,source_date";

let cachedClient: SupabaseClient | null = null;
function getClient(): SupabaseClient | null {
  if (cachedClient) return cachedClient;
  // NEXT_PUBLIC_* are inlined at build; the non-prefixed names are read from the
  // function's runtime env. Accept either so a missing/renamed build-time var can't
  // silently null the client. Anon key is sufficient (tables are public-read RLS).
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
  const key =
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY;
  if (!url || !key) {
    console.error("[brain-atoms-db] missing Supabase URL / anon key (checked NEXT_PUBLIC_* and bare names)");
    return null;
  }
  cachedClient = createClient(url, key, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
  return cachedClient;
}

const atomCache = new Map<string, DbAtom[]>();

/** All atoms for a brain, from its <slug>_atoms table. Paginated past PostgREST's
 *  1000-row cap, cached per instance. Returns [] on any failure (callers degrade). */
export async function fetchBrainAtoms(slug: string): Promise<DbAtom[]> {
  if (!SLUG_RE.test(slug)) return [];
  const hit = atomCache.get(slug);
  if (hit) return hit;

  const supabase = getClient();
  if (!supabase) return [];
  const table = `${slug.replace(/-/g, "_")}_atoms`;

  const all: DbAtom[] = [];
  for (let from = 0; from < 20000; from += 1000) {
    const { data, error } = await supabase
      .from(table)
      .select(COLS)
      .range(from, from + 999);
    if (error) {
      console.error(`[brain-atoms-db] ${table}: ${error.message}`);
      break;
    }
    const rows = (data ?? []) as unknown as DbAtom[];
    all.push(...rows);
    if (rows.length < 1000) break;
  }
  atomCache.set(slug, all);
  return all;
}
