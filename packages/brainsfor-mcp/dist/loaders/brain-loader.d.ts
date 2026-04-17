import type { BrainData, BrainIndex } from "../types.js";
export declare function loadBrainData(brainsDir: string, slug: string): BrainData;
export declare function getBrainIndex(brainsDir: string, slug: string): BrainIndex;
export declare function clearCache(): void;
