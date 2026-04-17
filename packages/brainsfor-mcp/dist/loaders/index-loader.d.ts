import type { BrainsIndex, IndexEntry } from "../types.js";
export declare function resolveBrainsDir(): string;
export declare function loadBrainsIndex(brainsDir: string): BrainsIndex;
export declare function getLiveBrains(brainsDir: string): IndexEntry[];
export declare function findBrain(brainsDir: string, slug: string): IndexEntry | undefined;
