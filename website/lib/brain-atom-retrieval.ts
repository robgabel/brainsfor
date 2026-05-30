// Question-aware atom retrieval for the /board (and future /skill) demos.
//
// Why: loading the entire static brain-context.md per request causes mode
// collapse — every brain anchors on its #1 first principle because that's
// what sits at position [0] of the system prompt. Pulling the ~15 atoms most
// relevant to the user's question shifts what the model attends to from "the
// canonical thesis" to "atoms that match THIS question."
//
// Retrieval source: the SHIPPED pack JSON at public/brains/<slug>/brain-atoms.json,
// scored by lexical overlap (content + verbatim quote + implication + topics +
// cluster) against the question. This deliberately does NOT use Supabase vector
// search: only 1 of 22 brains ever had embeddings populated, so the vector RPC
// silently returned empty for everyone else and Layer 2 was a no-op fleet-wide.
// Reading the pack works for every brain with zero infra and no embeddings.
//
// Failure mode is graceful: if the pack can't be read, the caller gets an empty
// block and the route falls back to the static brain-context.md alone (still
// benefits from Layer 1 prompt surgery).

import { readFile } from "fs/promises";
import path from "path";

interface RetrievedAtom {
  id: string;
  content: string;
  original_quote: string | null;
  implication: string | null;
  confidence_tier: string | null;
  cluster: string | null;
  topics: string[] | null;
  similarity: number; // lexical relevance score in [0,1] (kept name for caller compat)
}

interface PackAtom {
  id: string;
  content?: string;
  original_quote?: string | null;
  implication?: string | null;
  confidence_tier?: string | null;
  confidence?: number | null;
  cluster?: string | null;
  topics?: string[] | null;
}

// Slug allowlist — we read a path derived from this, so guard against traversal.
const SLUG_RE = /^[a-z][a-z0-9_-]{1,60}$/;

const STOPWORDS = new Set([
  "the", "a", "an", "and", "or", "but", "if", "is", "are", "was", "were", "be",
  "been", "being", "to", "of", "in", "on", "at", "by", "for", "with", "as",
  "from", "into", "that", "this", "these", "those", "it", "its", "i", "you",
  "your", "we", "our", "they", "their", "he", "she", "his", "her", "have", "has",
  "had", "do", "does", "did", "will", "would", "could", "should", "may", "might",
  "can", "shall", "not", "no", "so", "than", "then", "there", "here", "what",
  "which", "who", "when", "where", "how", "why", "all", "any", "some", "more",
  "most", "such", "about", "also", "just", "only", "very", "really", "too",
  "much", "even", "still", "should", "my", "me", "am", "im",
]);

function tokenize(text: string): string[] {
  return (text.toLowerCase().match(/[a-z][a-z'-]+/g) ?? []).filter(
    (t) => t.length > 2 && !STOPWORDS.has(t),
  );
}

// Per-slug pack cache (atoms only). Populated on first request, then reused for
// the lifetime of the serverless instance.
const packCache = new Map<string, PackAtom[]>();

async function loadPackAtoms(slug: string): Promise<PackAtom[]> {
  if (packCache.has(slug)) return packCache.get(slug)!;
  try {
    const file = path.join(
      process.cwd(),
      "public",
      "brains",
      slug,
      "brain-atoms.json",
    );
    const raw = await readFile(file, "utf8");
    const parsed = JSON.parse(raw);
    const atoms: PackAtom[] = Array.isArray(parsed?.atoms) ? parsed.atoms : [];
    packCache.set(slug, atoms);
    return atoms;
  } catch (err) {
    console.error(
      `[brain-atom-retrieval] could not load pack for ${slug}: ${(err as Error).message}`,
    );
    packCache.set(slug, []); // cache the miss so we don't retry fs every request
    return [];
  }
}

export async function retrieveRelevantAtoms(
  slug: string,
  query: string,
  k: number = 15,
): Promise<RetrievedAtom[]> {
  if (!SLUG_RE.test(slug)) return [];
  const atoms = await loadPackAtoms(slug);
  if (atoms.length === 0) return [];

  const qTokens = tokenize(query);
  if (qTokens.length === 0) return [];
  const qSet = new Set(qTokens);

  const scored = atoms.map((a) => {
    // Topic / cluster matches are the strongest signal (curated tags), then the
    // verbatim quote and content, then the implication.
    const topicTokens = new Set(
      (a.topics ?? []).flatMap((t) => tokenize(String(t))),
    );
    const clusterTokens = new Set(tokenize(a.cluster ?? ""));
    const bodyTokens = new Set([
      ...tokenize(a.content ?? ""),
      ...tokenize(a.original_quote ?? ""),
      ...tokenize(a.implication ?? ""),
    ]);

    let score = 0;
    for (const t of qSet) {
      if (topicTokens.has(t)) score += 3;
      else if (clusterTokens.has(t)) score += 2;
      else if (bodyTokens.has(t)) score += 1;
    }
    // Normalize to [0,1] by the best achievable (every query token a topic hit).
    const similarity = score / (qSet.size * 3);
    // Light tie-break toward higher-confidence atoms.
    const confBoost = (a.confidence ?? 0.8) * 0.001;
    return { atom: a, score: similarity + confBoost, similarity };
  });

  return scored
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, k)
    .map(({ atom, similarity }) => ({
      id: atom.id,
      content: atom.content ?? "",
      original_quote: atom.original_quote ?? null,
      implication: atom.implication ?? null,
      confidence_tier: atom.confidence_tier ?? null,
      cluster: atom.cluster ?? null,
      topics: atom.topics ?? null,
      similarity: Math.min(1, similarity),
    }));
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
    let block = `[A${i + 1}] (cluster=${cluster}, relevance=${sim})\n  "${quote}"`;
    if (impl) block += `\n  Implication: ${impl}`;
    return block;
  });

  return [
    "RELEVANT ATOMS FOR THIS QUESTION (top matches for THIS question — prefer these over your headline thesis):",
    lines.join("\n\n"),
    "(End of relevant atoms. The full brain context follows below for voice and context, but the atoms above are the most question-relevant.)",
  ].join("\n\n");
}
