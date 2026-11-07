// PRINCIPLES.md vendors the core principles from rob-ai/system/PRINCIPLES.md
// between two marker comments. The begin marker records the sha256 of the
// vendored text. This test recomputes it, so an edit made to the copy here
// (instead of at the source, then re-vendored with
// scripts/vendor-principles-core.ts) fails loudly. Core principle 9: define a
// rule once; a second copy drifts.
//
// Run from the repo root: `node --test scripts/test/principles-core-vendored.test.ts`

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { BEGIN_RE, END, sha256 } from "../vendor-principles-core.ts";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const PRINCIPLES = readFileSync(join(ROOT, "PRINCIPLES.md"), "utf8");

function vendoredBlock(): { recorded: string; body: string } {
  const m = PRINCIPLES.match(BEGIN_RE);
  assert.ok(m, "PRINCIPLES.md has a principles-core:begin marker");
  const beginAt = PRINCIPLES.indexOf(m[0]);
  const endAt = PRINCIPLES.indexOf(END);
  assert.ok(endAt > beginAt, "PRINCIPLES.md has a principles-core:end marker after begin");
  const body = PRINCIPLES.slice(beginAt + m[0].length, endAt).replace(/^\n/, "").replace(/\n$/, "");
  return { recorded: m[2], body };
}

test("the vendored core matches the hash recorded in its marker (edit the source, then re-vendor)", () => {
  const { recorded, body } = vendoredBlock();
  assert.ok(body.length > 10_000, "vendored core is not empty");
  assert.equal(sha256(body), recorded, "vendored core text was edited in place; edit rob-ai/system/PRINCIPLES.md and re-run scripts/vendor-principles-core.ts");
});

test("the vendored core holds Parts 1 to 4 and the project layer follows it", () => {
  const { body } = vendoredBlock();
  for (const part of ["## Part 1.", "## Part 2.", "## Part 3.", "## Part 4."]) {
    assert.ok(body.includes(part), `vendored core includes ${part}`);
  }
  const after = PRINCIPLES.slice(PRINCIPLES.indexOf(END));
  assert.ok(/^## Part 5\./m.test(after), "the BrainsFor layer (Part 5) follows the vendored core");
});

test("principle numbers are unique across the core and the layer", () => {
  const nums = [...PRINCIPLES.matchAll(/^### (\d+)\. /gm)].map((m) => Number(m[1]));
  assert.ok(nums.length >= 35, "at least 35 numbered principles");
  assert.deepEqual(nums, nums.map((_, i) => i + 1), "numbered 1..N without gaps or repeats");
});
