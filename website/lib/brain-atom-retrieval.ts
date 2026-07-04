// Question-aware atom retrieval for the /board (and future /skill) demos.
//
// Why: loading the entire static brain-context.md per request causes mode
// collapse — every brain anchors on its #1 first principle because that's
// what sits at position [0] of the system prompt. Pulling the ~15 atoms most
// relevant to the user's question shifts what the model attends to from "the
// canonical thesis" to "atoms that match THIS question."
//
// Retrieval source: the brain's <slug>_atoms table in Supabase (via lib/brain-atoms-db),
// scored by lexical overlap (content + verbatim quote + implication + topics +
// cluster) against the question. Previously this read the multi-MB pack JSON off
// the filesystem, which made Next trace the whole brains/ tree into the function
// bundle and broke deploys. Supabase keeps the bundle flat.
//
// Failure mode is graceful: if Supabase is unreachable, the caller gets an empty
// block and the route falls back to the static brain-context.md alone (still
// benefits from Layer 1 prompt surgery).

import { fetchBrainAtoms } from "./brain-atoms-db";

interface RetrievedAtom {
  id: string;
  content: string;
  original_quote: string | null;
  implication: string | null;
  confidence_tier: string | null;
  claim_type: "fact" | "opinion" | "prediction";
  verification: "unverified" | "verified" | "false" | "contested";
  proof_ref: string | null;
  cluster: string | null;
  topics: string[] | null;
  similarity: number; // lexical relevance score in [0,1] (kept name for caller compat)
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
  "much", "even", "still", "should", "my", "me", "am", "im",
]);

function tokenize(text: string): string[] {
  return (text.toLowerCase().match(/[a-z][a-z'-]+/g) ?? []).filter(
    (t) => t.length > 2 && !STOPWORDS.has(t),
  );
}

export async function retrieveRelevantAtoms(
  slug: string,
  query: string,
  k: number = 15,
): Promise<RetrievedAtom[]> {
  const atoms = await fetchBrainAtoms(slug);
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
      claim_type: atom.claim_type ?? "opinion",
      verification: atom.verification ?? "unverified",
      proof_ref: atom.proof_ref ?? null,
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
    // Epistemic tag — only annotate when it changes how the claim may be voiced.
    const ct = a.claim_type ?? "opinion";
    const vf = a.verification ?? "unverified";
    let tag = "";
    if (ct === "fact" && vf === "verified") tag = " [VERIFIED FACT]";
    else if (ct === "fact" && (vf === "false" || vf === "contested"))
      tag = ` [${vf.toUpperCase()} — sincere belief but NOT established fact; flag it]`;
    else if (ct === "prediction") tag = " [PREDICTION — frame as forecast]";
    let block = `[A${i + 1}] (cluster=${cluster}, relevance=${sim})${tag}\n  "${quote}"`;
    if (impl) block += `\n  Implication: ${impl}`;
    if ((vf === "false" || vf === "contested") && a.proof_ref)
      block += `\n  Verdict basis: ${a.proof_ref}`;
    return block;
  });

  return [
    "RELEVANT ATOMS FOR THIS QUESTION (top matches for THIS question — prefer these over your headline thesis):",
    lines.join("\n\n"),
    "EPISTEMIC RULE: An atom tagged [FALSE …] or [CONTESTED …] is a claim you sincerely hold but that is NOT established fact — you may voice it in your own words, but you MUST flag that it's refuted/contested; never state it as true. A [VERIFIED FACT] may be stated plainly. Everything else: state plainly, but invent no specifics (no numbers or dates not in the atom).",
    "(End of relevant atoms. The full brain context follows below for voice and context, but the atoms above are the most question-relevant.)",
  ].join("\n\n");
}
