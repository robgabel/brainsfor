// Canonical lexical atom scorer — THE one retrieval algorithm.
//
// Shared by every BrainsFor runtime surface:
//   - this MCP server's search_atoms tool
//   - the website's /api/skill + /api/board retrieval
//     (website/lib/brain-atom-retrieval.ts imports it via the
//      `@brainsfor/mcp` file: dependency)
//
// History: the website and the MCP each grew their own keyword scorer and
// they drifted (different weights, different tokenization). This module is
// the merge — it keeps the website's algorithm because that one was tuned
// during the mode-collapse fix (topic/cluster tags are curated, so they
// outweigh body-text matches; scores normalize to [0,1]; confidence only
// breaks ties). Dependency-free on purpose: no API keys, no network, works
// identically in a stdio MCP process and a Vercel function.

/** Minimal structural shape — both the MCP's Atom and the website's DbAtom satisfy it. */
export interface ScorableAtom {
  content?: string | null;
  original_quote?: string | null;
  implication?: string | null;
  cluster?: string | null;
  topics?: string[] | null;
  confidence?: number | null;
}

export interface ScoredAtom<T extends ScorableAtom> {
  atom: T;
  /** Lexical relevance in [0,1] — 1.0 means every query token hit a curated topic tag. */
  similarity: number;
}

const STOPWORDS = new Set([
  "the", "a", "an", "and", "or", "but", "if", "is", "are", "was", "were", "be",
  "been", "being", "to", "of", "in", "on", "at", "by", "for", "with", "as",
  "from", "into", "that", "this", "these", "those", "it", "its", "i", "you",
  "your", "we", "our", "they", "their", "he", "she", "his", "her", "have", "has",
  "had", "do", "does", "did", "will", "would", "could", "should", "may", "might",
  "can", "shall", "not", "no", "so", "than", "then", "there", "here", "what",
  "which", "who", "when", "where", "how", "why", "all", "any", "some", "more",
  "most", "such", "about", "also", "just", "only", "very", "really", "too",
  "much", "even", "still", "my", "me", "am", "im",
]);

export function tokenize(text: string): string[] {
  return (text.toLowerCase().match(/[a-z][a-z'-]+/g) ?? []).filter(
    (t) => t.length > 2 && !STOPWORDS.has(t),
  );
}

/**
 * Score atoms against a query and return the top-k, most relevant first.
 * Weights: curated topic tags 3x, cluster 2x, body text (content + verbatim
 * quote + implication) 1x. Similarity normalizes by the best achievable
 * score; atom confidence is a tie-break only (never outranks relevance).
 */
export function scoreAtomsForQuery<T extends ScorableAtom>(
  atoms: T[],
  query: string,
  k: number,
): ScoredAtom<T>[] {
  const qTokens = tokenize(query);
  if (qTokens.length === 0) return [];
  const qSet = new Set(qTokens);

  const scored = atoms.map((a) => {
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
    const similarity = score / (qSet.size * 3);
    const confBoost = (a.confidence ?? 0.8) * 0.001;
    return { atom: a, rank: similarity + confBoost, similarity };
  });

  return scored
    .filter((s) => s.rank > 0)
    .sort((a, b) => b.rank - a.rank)
    .slice(0, k)
    .map(({ atom, similarity }) => ({ atom, similarity: Math.min(1, similarity) }));
}
