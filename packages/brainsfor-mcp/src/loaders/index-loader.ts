import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import type { BrainsIndex, IndexEntry } from "../types.js";

let cachedIndex: BrainsIndex | null = null;
let cachedBrainsDir: string | null = null;

export function resolveBrainsDir(): string {
  const home = process.env.BRAINSFOR_HOME || join(process.env.HOME || "~", ".brainsfor");
  const brainsDir = join(home, "brains");

  // Also check common dev locations
  const candidates = [
    brainsDir,
    join(process.env.HOME || "~", "rob-ai", "brainsfor", "brains"),
  ];

  for (const dir of candidates) {
    if (existsSync(join(dir, "index.json"))) {
      return dir;
    }
  }

  return brainsDir;
}

export function loadBrainsIndex(brainsDir: string): BrainsIndex {
  if (cachedIndex && cachedBrainsDir === brainsDir) return cachedIndex;

  const indexPath = join(brainsDir, "index.json");
  if (!existsSync(indexPath)) {
    return { brains: [] };
  }

  const raw = readFileSync(indexPath, "utf-8");
  cachedIndex = JSON.parse(raw);
  cachedBrainsDir = brainsDir;
  return cachedIndex!;
}

export function getLiveBrains(brainsDir: string): IndexEntry[] {
  const index = loadBrainsIndex(brainsDir);
  return index.brains.filter((b) => b.status === "live");
}

export function findBrain(brainsDir: string, slug: string): IndexEntry | undefined {
  const index = loadBrainsIndex(brainsDir);
  return index.brains.find((b) => b.slug === slug);
}
