# HANDOFF — Hard Lessons + Receipts mining → Annie-chaired Judge Panel

**Status:** design locked, Jesse pilot shipped. This doc is the build plan for making it *systemic*.
**Author context:** continues the session that built the Jesse Pujji brain, diarization, and the "How They Think v2" Explorer.
**One-line goal:** every brain should (a) carry honest, sourced **Hard Lessons**, and (b) be QA'd *from its human's perspective* by a panel of brains, chaired by Annie Duke — before it goes `live`.

---

## 0. What already exists (DO NOT rebuild)

- **`scripts/diarize.py`** — speaker diarization waterfall (named → llm → stt → none). Interview/podcast atoms are attributed to the subject only. Wired into both extraction paths.
- **Hard Lessons schema + UI — SHIPPED & fleet-rolled.** `synthesis.hard_lessons` renders in `explore.html` ("How They Think" → Hard Lessons group). Per-entry shape:
  ```json
  {
    "title": "the mistake, first person",
    "cost":  "what it actually cost (the rubric: must name a real cost)",
    "change":"what changed as a result",
    "receipts": [ { "quote": "backing atom/quote", "source": "human-readable source label", "url": "optional" } ]
  }
  ```
  `export-brain.py` passes the whole `synthesis` object through (no whitelist) — **no export change needed** to add fields.
- **Receipts UI — SHIPPED** (expandable "Receipts (n)" under each hard lesson). Scoped to Hard Lessons by decision; NOT yet on other synthesis sections.
- **Jesse Pujji = the reference example.** `brains/jesse-pujji/brain.json` has 3 hand-mined hard lessons + receipts. Use it as the golden output shape.
- **`scripts/audit-quote-leakage.py`** — flags interviewer text leaking into `original_quote` (HOST/QUESTION). Zero-cost.
- **`scripts/eval-brains.py` + `scripts/eval_rubric.py`** — existing behavioral eval harness (20 prompts, voice/factuality/relevance/constraint judge). The panel is the *next tier* on top of this.
- **Existing `/board`** — `website/app/api/board/route.ts` + local `~/rob-ai/skills/board/`. Independent sub-agents, one per brain, no cross-contamination, synthesis-chair pass. **This is the substrate to reuse for the judge panel.**
- **Atoms now served statically** (`website/lib/brain-atoms-db.ts` reads the shipped pack JSON, not Supabase) — so no per-brain prod-DB migration is needed for anything the website/QA reads.

### Decisions already made
- **Hard Lessons rubric:** every entry must name a *real cost*, or it gets cut. "I worked too hard" is not a hard lesson. Sanitized/empty sections are a **QA signal**, not a fill-with-filler problem.
- **Receipts scope:** Hard Lessons only for now (revisit generalizing to all synthesis claims later).
- **Explorer:** designed-dark, locked to DESIGN.md type system (Space Grotesk display / Inter body). Don't re-litigate.
- **Judge panel roster:** **Annie Duke (chair)**, **Kara Swisher**, **Charlie Munger**, **Brené Brown**. No brain judges its own brain (or close peers). Human calibration anchor required.

---

## 1. Workstream A — Hard Lessons + Receipts mining (pipeline)

**Goal:** auto-generate `synthesis.hard_lessons` (with receipts) during the build, instead of hand-mining.

**Where it goes:** Phase 3 (Synthesis). Add a sub-step after the synthesis section is generated — either in `build-brain.py` (synthesis stage) or as a dedicated pass invoked from `auto-build-brain.py` Phase 3, alongside the existing `ground-synthesis.py` call.

**Prompt (add to `scripts/auto_build_config.py`, canonical home for prompts):** a `HARD_LESSONS_PROMPT` that:
1. Takes the diarized atom corpus (subject-only quotes) + the synthesis.
2. Extracts **only grounded** hard lessons — a mistake the subject actually made, the cost paid, what changed.
3. For each, attaches **receipts**: the backing atom(s) — store `quote` + `source` (map from `source_ref` to a human label) and, ideally, `atom_id` for traceability.
4. **Enforces the cost-rubric:** if an entry can't name a real, corpus-grounded cost, drop it. Returning `[]` is correct for a thin/sanitized corpus.
5. Writes `synthesis.hard_lessons` into `brain.json`.

**Also update the LLM file:** `brain-context.md` is generated from `synthesis.md` (markdown), not the structured keys — so Hard Lessons currently won't reach the LLM context. Add a "Hard Lessons" section to the synthesis markdown generator so `/advise`, `/coach`, etc. can use them.

**Guardrail:** route only diarized interview/essay atoms; never invent a cost. This is the anti-sanitization mechanism — its honesty is the whole point.

**Acceptance:** re-running on Jesse reproduces ~the 3 hand-mined lessons (held Ampush too long vs $60–75M; optimized against failure; non-linear $30M climb) with receipts pointing at the real sources.

---

## 2. Workstream B — Annie-chaired Judge Panel (persona QA)

**Goal:** judge a brain *from its human's perspective* — would the person recognize themselves; is every hard claim true; is the mess included; does it ever break the person's constitution.

**Tiered QA regime (thresholds, not vibes):**
| Tier | Tool | Checks | Status |
|---|---|---|---|
| 1 Structural | `audit-brains.py` | files, counts, orphans | exists |
| 2 Behavioral | `eval-brains.py` | answers like them (20 prompts) | exists |
| 3 **Persona QA** | **`scripts/persona-qa.py` (NEW)** | recognizability, hard-fact fidelity, coverage-of-the-inconvenient, anti-slop, constitution adherence | **build this** |
| 4 Human calibration | manual sample | anchor the LLM judges to ground truth | process |

**The panel (reuse `/board` independent-subagent pattern):**
| Judge | Brain principle | Dimension | Asks |
|---|---|---|---|
| **Kara Swisher** | power w/o accountability | Authenticity / recognizability | "Is this the real person, or performing? Where's it dodging?" |
| **Charlie Munger** | avoid standard stupidities; invert | Rigor / anti-slop | "Real insight or platitudes with a name on them?" |
| **Brené Brown** | vulnerability is the measure of courage | Coverage of the human/mess | "Is the *whole* person here — the failures, not just wins?" |
| **Annie Duke (CHAIR)** | resulting is the enemy of learning | Calibration / judge-of-judges | "Good *judgment* or just good-sounding? How confident should we be?" |

- **Constitution to grade against** = `first_principles` + `does_not_believe` + `would_not_say` (+ `hard_lessons`). Constitutional-AI applied to personas.
- **Numeric-claims verifier** (`scripts/verify-claims.py`, NEW): flag every hard figure (revenue/users/raise/exit/date) and check the corpus for a larger/newer one. This is what would have caught the Ampush **$10M → $30M** defect automatically. Feed its output into the panel's fidelity score.
- **Outputs:** `brains/<slug>/evals/persona-review-<date>.md` + a scorecard; ranked fixes.
- **`/brain-qa` orchestrator skill:** runs Tiers 1–3 + numeric verifier, emits one scorecard, ranks all brains by **interesting + useful + faithful**.

**Inconvenient risks to design for (don't skip):**
1. **Reflexivity** — the persona-judge is a model approximating the human, judging a model of the human. Tier-4 human calibration is mandatory, not optional.
2. **Correlated errors** — judges roleplayed by the same base model share a prior; independence is partial. Mitigate with the `/board` independent-subagent design + diverse rubrics + human spot-checks.
3. **Judge fidelity** — a judge built from slop produces slop verdicts. Validate the four judge brains against their humans *before* trusting them.
4. **Recusal** — no brain judges its own pack or close peers.
5. **Two tracks** — Munger/Kara optimize for "not fooled" (risk); Brené + an "interesting/useful" rubric must pull the other way, or you select for safe, boring brains.

**Ship-gate (RSP for brains):** `hidden → live` only when Persona-QA ≥ threshold, **zero unverified hard numbers**, voice ≥ ~60%. Publish the score on the brain page → race-to-the-top on fidelity.

---

## 3. Recommended sequence
1. **Workstream A** (hard_lessons + receipts mining) — gives every brain the data the panel will judge.
2. **`verify-claims.py`** (numeric verifier) — cheap, high-value, catches the $10M-class defects.
3. **`persona-qa.py`** + the 4-judge panel (Annie chair) on the `/board` substrate.
4. **`/brain-qa`** orchestrator + ship-gate thresholds + public score.
5. **Backfill:** re-mine failure-heavy sources for interview-heavy brains (per `audit-quote-leakage.py` + thin hard_lessons), then re-run the fleet QA.

## 4. Pilot target
Run the whole chain on **Jesse first** (his Hard Lessons + receipts already exist as the reference), then fan out. His thin-but-honest Hard Lessons section is the canonical "the corpus is sanitized → go mine the real failures" finding the panel should surface.
