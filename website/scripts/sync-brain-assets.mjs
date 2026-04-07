#!/usr/bin/env node
/**
 * Syncs brain pack assets (explore.html, brain-atoms.json) into website/public/
 * so they're served as static files. Run automatically via `npm run prebuild`.
 */
import fs from "fs";
import path from "path";

const BRAINS_DIR = path.join(process.cwd(), "..", "brains");
const PUBLIC_DIR = path.join(process.cwd(), "public", "brains");

const index = JSON.parse(fs.readFileSync(path.join(BRAINS_DIR, "index.json"), "utf-8"));

const ASSETS = ["explore.html", "brain-atoms.json"];

let synced = 0;

for (const brain of index.brains) {
  const packDir = path.join(BRAINS_DIR, brain.slug, "pack");
  const destDir = path.join(PUBLIC_DIR, brain.slug);

  for (const file of ASSETS) {
    const src = path.join(packDir, file);
    if (!fs.existsSync(src)) continue;

    fs.mkdirSync(destDir, { recursive: true });
    fs.copyFileSync(src, path.join(destDir, file));
    synced++;
  }
}

console.log(`Synced ${synced} brain assets for ${index.brains.length} brains.`);
