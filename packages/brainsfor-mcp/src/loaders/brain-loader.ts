import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Atom, BrainData, BrainIndex } from "../types.js";

const brainCache = new Map<string, BrainData>();
const indexCache = new Map<string, BrainIndex>();

/**
 * Reject slugs that could traverse out of the brains directory.
 * Mirrors the validation pattern in website/lib/brain-context.ts.
 */
function validateSlug(slug: string): void {
  if (!slug || /[./\\]/.test(slug)) {
    throw new Error(`Invalid slug: ${slug}`);
  }
}

export function loadBrainData(brainsDir: string, slug: string): BrainData {
  validateSlug(slug);

  const cached = brainCache.get(slug);
  if (cached) return cached;

  const atomsPath = join(brainsDir, slug, "pack", "brain-atoms.json");
  const raw = readFileSync(atomsPath, "utf-8");
  const data: BrainData = JSON.parse(raw);

  brainCache.set(slug, data);
  return data;
}

export function getBrainIndex(brainsDir: string, slug: string): BrainIndex {
  validateSlug(slug);

  const cached = indexCache.get(slug);
  if (cached) return cached;

  const data = loadBrainData(brainsDir, slug);

  const atomsById = new Map<string, Atom>();
  const atomsByTopic = new Map<string, Atom[]>();
  const atomsByCluster = new Map<string, Atom[]>();

  for (const atom of data.atoms) {
    atomsById.set(atom.id, atom);

    // Index by cluster
    const clusterList = atomsByCluster.get(atom.cluster);
    if (clusterList) {
      clusterList.push(atom);
    } else {
      atomsByCluster.set(atom.cluster, [atom]);
    }

    // Index by topic
    for (const topic of atom.topics) {
      const topicLower = topic.toLowerCase();
      const topicList = atomsByTopic.get(topicLower);
      if (topicList) {
        topicList.push(atom);
      } else {
        atomsByTopic.set(topicLower, [atom]);
      }
    }
  }

  const index: BrainIndex = { atomsById, atomsByTopic, atomsByCluster };
  indexCache.set(slug, index);
  return index;
}

export function clearCache(): void {
  brainCache.clear();
  indexCache.clear();
}
