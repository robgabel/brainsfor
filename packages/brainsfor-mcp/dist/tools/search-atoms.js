import { z } from "zod";
import { getBrainIndex } from "../loaders/brain-loader.js";
import { findBrain } from "../loaders/index-loader.js";
function scoreAtom(atom, terms) {
    let score = 0;
    const fields = [atom.content, atom.original_quote || "", atom.implication || ""];
    const combined = fields.join(" ").toLowerCase();
    for (const term of terms) {
        const lower = term.toLowerCase();
        // Exact match in content gets highest weight
        if (atom.content.toLowerCase().includes(lower))
            score += 3;
        // Match in original_quote
        if (atom.original_quote?.toLowerCase().includes(lower))
            score += 2;
        // Match in implication
        if (atom.implication?.toLowerCase().includes(lower))
            score += 1;
        // Match in topics
        if (atom.topics.some((t) => t.toLowerCase().includes(lower)))
            score += 1;
    }
    // Boost by confidence
    score *= atom.confidence;
    return score;
}
export function registerSearchAtoms(server, brainsDir) {
    server.registerTool("search_atoms", {
        title: "Search Brain Atoms by Text",
        description: "Full-text search across atom content, original quotes, and implications. Scores results by relevance and confidence. Use this to find atoms that topic-based query_atoms might miss.",
        inputSchema: z
            .object({
            brain_slug: z.string().describe("Brain identifier"),
            query: z.string().min(2).describe("Search query (words or phrases)"),
            limit: z
                .number()
                .int()
                .min(1)
                .max(50)
                .default(10)
                .describe("Maximum atoms to return"),
        })
            .strict(),
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: false,
        },
    }, async ({ brain_slug, query, limit }) => {
        const entry = findBrain(brainsDir, brain_slug);
        if (!entry) {
            return {
                content: [{ type: "text", text: `Brain "${brain_slug}" not found.` }],
                isError: true,
            };
        }
        try {
            const index = getBrainIndex(brainsDir, brain_slug);
            const terms = query
                .split(/\s+/)
                .filter((t) => t.length >= 2);
            const scored = [];
            for (const atom of index.atomsById.values()) {
                const score = scoreAtom(atom, terms);
                if (score > 0) {
                    scored.push({ atom, score });
                }
            }
            scored.sort((a, b) => b.score - a.score);
            const results = scored.slice(0, limit).map(({ atom, score }) => ({
                id: atom.id,
                content: atom.content,
                original_quote: atom.original_quote,
                implication: atom.implication,
                confidence_tier: atom.confidence_tier,
                cluster: atom.cluster,
                topics: atom.topics,
                source_ref: atom.source_ref,
                source_date: atom.source_date,
                relevance_score: Math.round(score * 100) / 100,
            }));
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({ brain: brain_slug, query, count: results.length, atoms: results }, null, 2),
                    },
                ],
            };
        }
        catch (e) {
            return {
                content: [{ type: "text", text: `Error searching atoms: ${e}` }],
                isError: true,
            };
        }
    });
}
