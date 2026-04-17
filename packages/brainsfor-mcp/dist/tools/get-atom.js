import { z } from "zod";
import { getBrainIndex } from "../loaders/brain-loader.js";
import { findBrain } from "../loaders/index-loader.js";
export function registerGetAtom(server, brainsDir) {
    server.registerTool("get_atom", {
        title: "Get Single Atom",
        description: "Get the full details of a specific atom by ID, including all fields: content, original quote, implication, confidence, topics, connections, and source reference.",
        inputSchema: z
            .object({
            brain_slug: z.string().describe("Brain identifier"),
            atom_id: z.string().describe("UUID of the atom"),
        })
            .strict(),
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: false,
        },
    }, async ({ brain_slug, atom_id }) => {
        const entry = findBrain(brainsDir, brain_slug);
        if (!entry) {
            return {
                content: [{ type: "text", text: `Brain "${brain_slug}" not found.` }],
                isError: true,
            };
        }
        try {
            const index = getBrainIndex(brainsDir, brain_slug);
            const atom = index.atomsById.get(atom_id);
            if (!atom) {
                return {
                    content: [{ type: "text", text: `Atom "${atom_id}" not found in brain "${brain_slug}".` }],
                    isError: true,
                };
            }
            return {
                content: [{ type: "text", text: JSON.stringify({ brain: brain_slug, atom }, null, 2) }],
            };
        }
        catch (e) {
            return {
                content: [{ type: "text", text: `Error getting atom: ${e}` }],
                isError: true,
            };
        }
    });
}
