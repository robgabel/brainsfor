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
export declare function tokenize(text: string): string[];
/**
 * Score atoms against a query and return the top-k, most relevant first.
 * Weights: curated topic tags 3x, cluster 2x, body text (content + verbatim
 * quote + implication) 1x. Similarity normalizes by the best achievable
 * score; atom confidence is a tie-break only (never outranks relevance).
 */
export declare function scoreAtomsForQuery<T extends ScorableAtom>(atoms: T[], query: string, k: number): ScoredAtom<T>[];
