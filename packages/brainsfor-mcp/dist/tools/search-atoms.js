import { z } from "zod";
import { getBrainIndex } from "../loaders/brain-loader.js";
import { findBrain } from "../loaders/index-loader.js";
import { scoreAtomsForQuery } from "../scoring.js";
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
            // Canonical shared scorer (src/scoring.ts) — same algorithm the
            // website's /api/skill and /api/board retrieval uses.
            const scored = scoreAtomsForQuery([...index.atomsById.values()], query, limit);
            const results = scored.map(({ atom, similarity }) => ({
                id: atom.id,
                content: atom.content,
                original_quote: atom.original_quote,
                implication: atom.implication,
                confidence_tier: atom.confidence_tier,
                cluster: atom.cluster,
                topics: atom.topics,
                source_ref: atom.source_ref,
                source_date: atom.source_date,
                claim_type: atom.claim_type ?? "opinion",
                verification: atom.verification ?? "unverified",
                proof_ref: atom.proof_ref ?? null,
                verified_at: atom.verified_at ?? null,
                relevance_score: Math.round(similarity * 100) / 100,
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
