import { z } from "zod";
import { getBrainIndex, loadBrainData } from "../loaders/brain-loader.js";
import { findBrain } from "../loaders/index-loader.js";
export function registerGetConnections(server, brainsDir) {
    server.registerTool("get_connections", {
        title: "Get Atom Connections",
        description: "Get typed connections for a specific atom: what supports it, contradicts it, extends it, or relates to it. Optionally traverse depth=2 for second-order connections. Use this to trace reasoning chains through the knowledge graph.",
        inputSchema: z
            .object({
            brain_slug: z.string().describe("Brain identifier"),
            atom_id: z.string().describe("UUID of the atom to get connections for"),
            relationship: z
                .enum(["supports", "contradicts", "extends", "related", "inspired_by"])
                .optional()
                .describe("Filter to a specific relationship type"),
            depth: z
                .number()
                .int()
                .min(1)
                .max(2)
                .default(1)
                .describe("Traversal depth (1 = direct connections, 2 = include connections of connections)"),
        })
            .strict(),
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: false,
        },
    }, async ({ brain_slug, atom_id, relationship, depth }) => {
        const entry = findBrain(brainsDir, brain_slug);
        if (!entry) {
            return {
                content: [{ type: "text", text: `Brain "${brain_slug}" not found.` }],
                isError: true,
            };
        }
        try {
            const index = getBrainIndex(brainsDir, brain_slug);
            const data = loadBrainData(brainsDir, brain_slug);
            const sourceAtom = index.atomsById.get(atom_id);
            if (!sourceAtom) {
                return {
                    content: [{ type: "text", text: `Atom "${atom_id}" not found in brain "${brain_slug}".` }],
                    isError: true,
                };
            }
            // Find connections from both the atom's inline connections and top-level connections
            const connectionSet = new Map();
            // Inline connections on the atom
            for (const conn of sourceAtom.connections) {
                if (!relationship || conn.relationship === relationship) {
                    connectionSet.set(conn.target_id, {
                        atom_id: conn.target_id,
                        relationship: conn.relationship,
                        confidence: conn.confidence,
                        direction: "outgoing",
                    });
                }
            }
            // Top-level connections (bidirectional lookup)
            for (const conn of data.connections) {
                if (conn.atom_id_1 === atom_id || conn.atom_id_2 === atom_id) {
                    if (!relationship || conn.relationship === relationship) {
                        const targetId = conn.atom_id_1 === atom_id ? conn.atom_id_2 : conn.atom_id_1;
                        const direction = conn.atom_id_1 === atom_id ? "outgoing" : "incoming";
                        if (!connectionSet.has(targetId)) {
                            connectionSet.set(targetId, {
                                atom_id: targetId,
                                relationship: conn.relationship,
                                confidence: conn.confidence,
                                direction,
                            });
                        }
                    }
                }
            }
            // Resolve connected atoms
            const connections = [];
            for (const conn of connectionSet.values()) {
                const target = index.atomsById.get(conn.atom_id);
                if (target) {
                    connections.push({
                        ...conn,
                        content: target.content,
                        original_quote: target.original_quote,
                        confidence_tier: target.confidence_tier,
                        cluster: target.cluster,
                    });
                }
            }
            // Depth 2: get connections of connections
            let secondOrder = [];
            if (depth === 2) {
                const firstOrderIds = new Set(connections.map((c) => c.atom_id));
                firstOrderIds.add(atom_id);
                for (const firstConn of connections) {
                    const firstAtom = index.atomsById.get(firstConn.atom_id);
                    if (!firstAtom)
                        continue;
                    for (const subConn of firstAtom.connections) {
                        if (firstOrderIds.has(subConn.target_id))
                            continue;
                        if (relationship && subConn.relationship !== relationship)
                            continue;
                        const target = index.atomsById.get(subConn.target_id);
                        if (target) {
                            secondOrder.push({
                                atom_id: subConn.target_id,
                                relationship: subConn.relationship,
                                confidence: subConn.confidence,
                                direction: "second_order",
                                content: target.content,
                                original_quote: target.original_quote,
                                confidence_tier: target.confidence_tier,
                                cluster: target.cluster,
                            });
                            firstOrderIds.add(subConn.target_id);
                        }
                    }
                }
            }
            const result = {
                brain: brain_slug,
                source_atom: {
                    id: sourceAtom.id,
                    content: sourceAtom.content,
                    cluster: sourceAtom.cluster,
                },
                connections,
                ...(secondOrder.length > 0 ? { second_order: secondOrder } : {}),
            };
            return {
                content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
            };
        }
        catch (e) {
            return {
                content: [{ type: "text", text: `Error getting connections: ${e}` }],
                isError: true,
            };
        }
    });
}
