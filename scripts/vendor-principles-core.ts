// Vendors the core principles (rob-ai/system/PRINCIPLES.md, Parts 1 to 4) into
// this repo's PRINCIPLES.md between two marker comments, and records the
// sha256 of the vendored text in the begin marker. The hash does not catch a
// change at the source (it cannot, across repos); it catches an edit made to
// the copy instead of the source. scripts/test/principles-core-vendored.test.ts
// recomputes it. Run from the repo root:
//
//   node scripts/vendor-principles-core.ts --source ../rob-ai/system/PRINCIPLES.md
//
// (Node 22.18+ strips types natively; no tsx needed in this repo.)
//
// Edit the core in rob-ai, merge it there, then re-run this and commit the
// result here. Never edit the text between the markers by hand.

import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const BEGIN_RE =
  /^<!-- principles-core:begin source=(\S+) sha256=([0-9a-f]{64}) -->$/m;
export const END = "<!-- principles-core:end -->";
export const SOURCE_LABEL = "rob-ai/system/PRINCIPLES.md";

/** Parts 1 to 4 of the core file: from its first `---` rule to the project-layer note. */
export function coreBody(core: string): string {
  const start = core.indexOf("\n---\n");
  const end = core.indexOf("\n## What a new project adds");
  if (start < 0 || end < 0 || end <= start) {
    throw new Error("core file: expected a leading --- rule and a '## What a new project adds' heading");
  }
  return core.slice(start + "\n---\n".length, end).trim();
}

export function sha256(text: string): string {
  return createHash("sha256").update(text, "utf8").digest("hex");
}

export function splice(target: string, body: string): string {
  const begin = `<!-- principles-core:begin source=${SOURCE_LABEL} sha256=${sha256(body)} -->`;
  const block = `${begin}\n${body}\n${END}`;
  const beginAt = target.search(BEGIN_RE);
  const endAt = target.indexOf(END);
  if (beginAt < 0 || endAt < 0 || endAt < beginAt) {
    throw new Error("target: expected an existing principles-core marker block to replace");
  }
  return target.slice(0, beginAt) + block + target.slice(endAt + END.length);
}

function main() {
  const args = process.argv.slice(2);
  const i = args.indexOf("--source");
  if (i < 0 || !args[i + 1]) {
    console.error("usage: vendor-principles-core.ts --source <path to rob-ai/system/PRINCIPLES.md>");
    process.exit(2);
  }
  const root = join(dirname(fileURLToPath(import.meta.url)), "..");
  const source = resolve(args[i + 1]);
  const targetPath = join(root, "PRINCIPLES.md");
  const body = coreBody(readFileSync(source, "utf8"));
  const out = splice(readFileSync(targetPath, "utf8"), body);
  writeFileSync(targetPath, out);
  console.log(`vendored ${body.length} bytes from ${source}; sha256=${sha256(body)}`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
