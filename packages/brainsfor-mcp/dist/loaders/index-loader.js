import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
let cachedIndex = null;
let cachedBrainsDir = null;
export function resolveBrainsDir() {
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
export function loadBrainsIndex(brainsDir) {
    if (cachedIndex && cachedBrainsDir === brainsDir)
        return cachedIndex;
    const indexPath = join(brainsDir, "index.json");
    if (!existsSync(indexPath)) {
        return { brains: [] };
    }
    const raw = readFileSync(indexPath, "utf-8");
    cachedIndex = JSON.parse(raw);
    cachedBrainsDir = brainsDir;
    return cachedIndex;
}
export function getLiveBrains(brainsDir) {
    const index = loadBrainsIndex(brainsDir);
    return index.brains.filter((b) => b.status === "live");
}
export function findBrain(brainsDir, slug) {
    const index = loadBrainsIndex(brainsDir);
    return index.brains.find((b) => b.slug === slug);
}
