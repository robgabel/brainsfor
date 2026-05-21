// Question-aware atom retrieval for the /board (and future /skill) demos.
//
// Why: loading the entire static brain-context.md per request causes mode
// collapse — every brain anchors on its #1 first principle because that's
// what sits at position [0] of the system prompt. Pulling the 15 atoms most
// semantically relevant to the user's question shifts what the model attends
// to from "the canonical thesis" to "atoms that match THIS question."
//
// Failure mode is graceful: if OpenAI is unavailable, Supabase is unreachable,
// or the RPC errors, the caller gets back an empty block and the route falls
// back to the static brain-context.md alone (still benefits from Layer 1
// prompt surgery).

import { createClient } from "@supabase/supabase-js";

const EMBEDDING_MODEL = "text-embedding-3-large";
const EMBEDDING_DIMS = 1536; // matches what's stored in <slug>_atoms.embedding

interface RetrievedAtom {
  id: string;
  content: string;
  original_quote: string | null;
  implication: string | null;
  confidence_tier: string | null;
  cluster: string | null;
  topics: string[] | null;
  similarity: number;
}

let cachedSupabase: ReturnType<typeof createClient> | null = null;
function getSupabase() {
  if (cachedSupabase) return cachedSupabase;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return null;
  cachedSupabase = createClient(url, key, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
  return cachedSupabase;
}

async function embedQuery(text: string): Promise<number[] | null> {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.warn(
      "[brain-atom-retrieval] OPENAI_API_KEY not set — skipping retrieval, falling back to static context",
    );
    return null;
  }

  try {
    const resp = await fetch("https://api.openai.com/v1/embeddings", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${key}`,
      },
      body: JSON.stringify({
        model: EMBEDDING_MODEL,
        input: text,
        dimensions: EMBEDDING_DIMS,
      }),
      // Short timeout — board calls are user-facing and fan out 5x in parallel.
      // If OpenAI is slow we'd rather degrade to Layer 1 than block the stream.
      signal: AbortSignal.timeout(4000),
    });
    if (!resp.ok) {
      console.error(
        `[brain-atom-retrieval] OpenAI embedding ${resp.status}: ${await resp.text()}`,
      );
      return null;
    }
    const data = await resp.json();
    return data.data?.[0]?.embedding ?? null;
  } catch (err) {
    console.error(
      `[brain-atom-retrieval] embedQuery failed: ${(err as Error).message}`,
    );
    return null;
  }
}

export async function retrieveRelevantAtoms(
  slug: string,
  query: string,
  k: number = 15,
): Promise<RetrievedAtom[]> {
  const supabase = getSupabase();
  if (!supabase) return [];

  const embedding = await embedQuery(query);
  if (!embedding) return [];

  try {
    // Cast through unknown because we don't ship generated Supabase types —
    // the RPC signature is verified at runtime by the function definition.
    const { data, error } = await (
      supabase.rpc as unknown as (
        fn: string,
        args: Record<string, unknown>,
      ) => Promise<{ data: RetrievedAtom[] | null; error: { message: string } | null }>
    )("search_brain_atoms", {
      p_slug: slug,
      p_embedding: JSON.stringify(embedding),
      p_k: k,
      p_min_similarity: 0.0,
    });
    if (error) {
      console.error(
        `[brain-atom-retrieval] RPC error for ${slug}: ${error.message}`,
      );
      return [];
    }
    return (data as RetrievedAtom[]) ?? [];
  } catch (err) {
    console.error(
      `[brain-atom-retrieval] supabase.rpc threw for ${slug}: ${(err as Error).message}`,
    );
    return [];
  }
}

// Format retrieved atoms into a system-prompt block. The block is labeled
// loudly so the model can find it amid the larger brain context, and the
// atoms include the verbatim quote (when present) because BOARD_FORMAT
// instructs the model to cite "GROUNDED ON: <verbatim atom quote>".
export function formatAtomsBlock(atoms: RetrievedAtom[]): string {
  if (atoms.length === 0) {
    return "RELEVANT ATOMS FOR THIS QUESTION:\n(retrieval unavailable — reason from the full brain context below, but still avoid your headline mental model)";
  }

  const lines = atoms.map((a, i) => {
    const quote = a.original_quote?.trim() || a.content.trim();
    const impl = a.implication?.trim();
    const cluster = a.cluster ?? "general";
    const sim = a.similarity.toFixed(2);
    let block = `[A${i + 1}] (cluster=${cluster}, sim=${sim})\n  "${quote}"`;
    if (impl) block += `\n  Implication: ${impl}`;
    return block;
  });

  return [
    "RELEVANT ATOMS FOR THIS QUESTION (top matches by semantic similarity — prefer these over your headline thesis):",
    lines.join("\n\n"),
    "(End of relevant atoms. The full brain context follows below for voice and context, but the atoms above are the most question-relevant.)",
  ].join("\n\n");
}
