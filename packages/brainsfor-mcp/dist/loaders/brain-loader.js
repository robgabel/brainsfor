import { readFileSync } from "node:fs";
import { join } from "node:path";
const brainCache = new Map();
const indexCache = new Map();
/**
 * Reject slugs that could traverse out of the brains directory.
 * Mirrors the validation pattern in website/lib/brain-context.ts.
 */
function validateSlug(slug) {
    if (!slug || /[./\\]/.test(slug)) {
        throw new Error(`Invalid slug: ${slug}`);
    }
}
export function loadBrainData(brainsDir, slug) {
    validateSlug(slug);
    const cached = brainCache.get(slug);
    if (cached)
        return cached;
    const atomsPath = join(brainsDir, slug, "pack", "brain-atoms.json");
    const raw = readFileSync(atomsPath, "utf-8");
    const data = JSON.parse(raw);
    brainCache.set(slug, data);
    return data;
}
export function getBrainIndex(brainsDir, slug) {
    validateSlug(slug);
    const cached = indexCache.get(slug);
    if (cached)
        return cached;
    const data = loadBrainData(brainsDir, slug);
    const atomsById = new Map();
    const atomsByTopic = new Map();
    const atomsByCluster = new Map();
    for (const atom of data.atoms) {
        atomsById.set(atom.id, atom);
        // Index by cluster
        const clusterList = atomsByCluster.get(atom.cluster);
        if (clusterList) {
            clusterList.push(atom);
        }
        else {
            atomsByCluster.set(atom.cluster, [atom]);
        }
        // Index by topic
        for (const topic of atom.topics) {
            const topicLower = topic.toLowerCase();
            const topicList = atomsByTopic.get(topicLower);
            if (topicList) {
                topicList.push(atom);
            }
            else {
                atomsByTopic.set(topicLower, [atom]);
            }
        }
    }
    const index = { atomsById, atomsByTopic, atomsByCluster };
    indexCache.set(slug, index);
    return index;
}
export function clearCache() {
    brainCache.clear();
    indexCache.clear();
}
