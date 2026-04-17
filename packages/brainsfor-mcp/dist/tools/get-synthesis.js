import { z } from "zod";
import { loadBrainData } from "../loaders/brain-loader.js";
import { findBrain } from "../loaders/index-loader.js";
export function registerGetSynthesis(server, brainsDir) {
    server.registerTool("get_synthesis", {
        title: "Get Brain Synthesis",
        description: "Get a thinker's intellectual operating system: first principles, thinking patterns, contrarian positions, what they don't believe, and what they'd never say. This is the foundation for reasoning like this thinker. Always call this first before querying atoms.",
        inputSchema: z
            .object({
            brain_slug: z.string().describe("Brain identifier (e.g., 'scott-belsky', 'charlie-munger')"),
        })
            .strict(),
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: false,
        },
    }, async ({ brain_slug }) => {
        const entry = findBrain(brainsDir, brain_slug);
        if (!entry) {
            return {
                content: [{ type: "text", text: `Brain "${brain_slug}" not found. Use list_brains to see installed brains.` }],
                isError: true,
            };
        }
        try {
            const data = loadBrainData(brainsDir, brain_slug);
            const { synthesis, brain } = data;
            const result = {
                brain_name: brain.name,
                brain_slug: brain.slug,
                atom_count: brain.atom_count,
                connection_count: brain.connection_count,
                bio: brain.bio,
                first_principles: synthesis.first_principles,
                thinking_patterns: synthesis.thinking_patterns,
                contrarian_positions: synthesis.contrarian_positions,
                does_not_believe: synthesis.does_not_believe,
                would_not_say: synthesis.would_not_say,
                biography: synthesis.biography,
            };
            return {
                content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
            };
        }
        catch (e) {
            return {
                content: [{ type: "text", text: `Error loading brain "${brain_slug}": ${e}` }],
                isError: true,
            };
        }
    });
}
