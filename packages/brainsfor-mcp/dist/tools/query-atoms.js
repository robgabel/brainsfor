import { z } from "zod";
import { getBrainIndex } from "../loaders/brain-loader.js";
import { findBrain } from "../loaders/index-loader.js";
function formatAtom(atom) {
    return {
        id: atom.id,
        content: atom.content,
        original_quote: atom.original_quote,
        implication: atom.implication,
        confidence_tier: atom.confidence_tier,
        confidence: atom.confidence,
        cluster: atom.cluster,
        topics: atom.topics,
        source_ref: atom.source_ref,
        source_date: atom.source_date,
    };
}
export function registerQueryAtoms(server, brainsDir) {
    server.registerTool("query_atoms", {
        title: "Query Brain Atoms by Topic",
        description: "Retrieve atoms from a brain pack filtered by topic tags, cluster, or confidence. Uses pre-built topic index for fast O(1) lookup. Returns atoms with content, original quotes, implications, and confidence tiers.",
        inputSchema: z
            .object({
            brain_slug: z.string().describe("Brain identifier"),
            topics: z
                .array(z.string())
                .optional()
                .describe("Topic tags to filter by (case-insensitive, matched against atom topic arrays)"),
            cluster: z.string().optional().describe("Cluster name to filter by"),
            confidence_min: z
                .number()
                .min(0)
                .max(1)
                .optional()
                .describe("Minimum confidence score (0-1)"),
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
    }, async ({ brain_slug, topics, cluster, confidence_min, limit }) => {
        const entry = findBrain(brainsDir, brain_slug);
        if (!entry) {
            return {
                content: [{ type: "text", text: `Brain "${brain_slug}" not found.` }],
                isError: true,
            };
        }
        try {
            const index = getBrainIndex(brainsDir, brain_slug);
            let candidates = [];
            // Collect atoms matching topics (union)
            if (topics && topics.length > 0) {
                const seen = new Set();
                for (const topic of topics) {
                    const matches = index.atomsByTopic.get(topic.toLowerCase()) || [];
                    for (const atom of matches) {
                        if (!seen.has(atom.id)) {
                            seen.add(atom.id);
                            candidates.push(atom);
                        }
                    }
                }
            }
            // Filter by cluster
            if (cluster) {
                if (candidates.length === 0 && (!topics || topics.length === 0)) {
                    candidates = index.atomsByCluster.get(cluster) || [];
                }
                else {
                    candidates = candidates.filter((a) => a.cluster === cluster);
                }
            }
            // If no filters, return top atoms by confidence
            if (candidates.length === 0 && !topics?.length && !cluster) {
                candidates = Array.from(index.atomsById.values());
            }
            // Filter by confidence
            if (confidence_min !== undefined) {
                candidates = candidates.filter((a) => a.confidence >= confidence_min);
            }
            // Sort by confidence descending, take limit
            candidates.sort((a, b) => b.confidence - a.confidence);
            const results = candidates.slice(0, limit).map(formatAtom);
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({ brain: brain_slug, count: results.length, atoms: results }, null, 2),
                    },
                ],
            };
        }
        catch (e) {
            return {
                content: [{ type: "text", text: `Error querying atoms: ${e}` }],
                isError: true,
            };
        }
    });
}
