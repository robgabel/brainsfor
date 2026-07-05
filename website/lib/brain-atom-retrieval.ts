// Question-aware atom retrieval for the /board (and future /skill) demos.
//
// Why: loading the entire static brain-context.md per request causes mode
// collapse — every brain anchors on its #1 first principle because that's
// what sits at position [0] of the system prompt. Pulling the ~15 atoms most
// relevant to the user's question shifts what the model attends to from "the
// canonical thesis" to "atoms that match THIS question."
//
// Retrieval source: the brain's shipped pack JSON via lib/brain-atoms-db
// (static CDN asset, cached per instance — no DB), scored by lexical overlap
// (content + verbatim quote + implication + topics + cluster) against the
// question.
//
// Failure mode is graceful: if the pack fetch fails, the caller gets an empty
// block and the route falls back to the brain synthesis context alone (still
// benefits from Layer 1 prompt surgery).

import { scoreAtomsForQuery } from "@brainsfor/mcp/scoring";
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
  source_date: string | null;
  similarity: number; // lexical relevance score in [0,1] (kept name for caller compat)
}

export async function retrieveRelevantAtoms(
  slug: string,
  query: string,
  k: number = 15,
): Promise<RetrievedAtom[]> {
  const atoms = await fetchBrainAtoms(slug);
  if (atoms.length === 0) return [];

  // Canonical shared scorer — the SAME algorithm the @brainsfor/mcp
  // search_atoms tool runs (packages/brainsfor-mcp/src/scoring.ts). One
  // implementation, every surface; the two copies had already drifted once.
  return scoreAtomsForQuery(atoms, query, k).map(({ atom, similarity }) => ({
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
      source_date: atom.source_date ?? null,
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
    // Date matters for /evolve (era timelines) — include when the pack has it.
    const date = a.source_date ? `, date=${a.source_date.slice(0, 10)}` : "";
    let block = `[A${i + 1}] (cluster=${cluster}${date}, relevance=${sim})${tag}\n  "${quote}"`;
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
