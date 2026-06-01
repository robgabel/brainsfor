# Spec: Phase 3.5 — Synthesis Grounding & Sourcing

**Status:** proposed · **Owner:** Rob · **Date:** 2026-06-01
**Problem:** The synthesis layer (first_principles, contrarian_positions, does_not_believe,
would_not_say) confabulates for famous subjects. Semantic fact-check found elon-musk 2%
grounded, jensen-huang 2%, oprah 25%, gokul 39%, hank 27% — the model wrote real-but-unsourced
principles from pretraining instead of deriving them from the corpus. The atoms are grounded;
the *synthesis* (the most-visible layer) is not.

## Core principle

"Ungrounded" conflates two opposite failures. Never treat them the same:

| Type | What it is | Right response |
|------|------------|----------------|
| **A** | True to the person, just **not in our corpus** ("Physics is the only law") | **Source it** — go find the primary quote. Never delete. |
| **B** | **Confabulated / false** — a position they don't hold | Drop or correct |

The grounding number says a principle *isn't sourced*. It does **not** say it's *wrong*.
A and B need different machinery. The current "cite or drop" idea wrongly deletes Type A.

## The reframe: synthesis-driven retrieval

The model's pretraining knowledge of famous people is a **candidate generator**, not a liability.
The bug is that the pipeline proposes a principle and never goes to find the evidence. So:

```
synthesis proposes principle  →  retrieve candidate primary sources  →
fetch primary text  →  verify a VERBATIM quote supports it  →
  found     → mint a grounding atom (corpus GROWS), tag `sourced`
  not found → truth-check: real-but-unsourceable → `attributed` (label, keep)
                          actually false         → `dropped` (or human review)
```

Outcome: the brain gets **more true** under QA, not thinner. Newly-minted atoms also raise
voice% and grounding% for real.

## Does a Perplexity API help? Yes — for discovery only. Never as the grounding authority.

The grounding gate has two sub-problems with opposite tool fits:

1. **Discovery** — "where might [person] have said this?" → broad, semantic, returns candidate URLs.
2. **Verification** — "does the primary source contain a verbatim quote supporting it?" → narrow,
   exact, returns a real quote or nothing.

**Perplexity (Sonar) is strong at #1, dangerous at #2.** It is a *summarizer*: its answer text is
itself LLM-synthesized and can paraphrase or hallucinate. Grounding a principle on Perplexity's
prose just **launders one model's confabulation into another's** — we'd swap the synthesis model's
guess for Perplexity's guess and call it "sourced." That destroys the exact moat we're protecting.

**Rule: use only Perplexity's *citations* (the source URLs), never its answer text.** Then fetch the
primary source ourselves and run the existing verbatim-quote verifier. The grounding atom must be a
real quote that provably exists in primary material.

### Search-API options for the discovery step (ranked)

| Option | Fit | Notes |
|--------|-----|-------|
| **Exa / Metaphor** | ★ best | Semantic search that returns *primary URLs by meaning*, no summarization layer to launder. Built for "find content matching this claim." Cleanest integrity story. |
| **Perplexity Sonar** | ★ good (citations only) | Excellent claim-targeted retrieval + citations; cheap (~$0.005/query). MUST discard answer text, keep URLs only. |
| **Firecrawl search** | ok (already integrated) | We already use it in Phase 0. Keyword-ish; weaker at semantic claim-matching but zero new dependency. |
| **YouTube Data API** | ok (for video) | Good for finding the talk; still need transcript fetch + verify. |

**Recommendation:** Exa for discovery (or Perplexity-citations if we already have a key), then ALWAYS
fetch + verbatim-verify. Perplexity helps, but it is the *map*, not the *territory*.

## Phase 3.5 algorithm (per synthesis principle)

```
1. CORPUS CHECK (free, existing): semantic match vs the brain's atoms.
   grounded → attach atom_id, tag `grounded`. DONE.

2. DISCOVERY (Exa/Perplexity-citations): query "[person] <claim paraphrase> quote/interview".
   → up to N candidate primary-source URLs (prefer their own talks/essays/interviews;
     down-rank third-party summaries).

3. FETCH + VERIFY (existing Firecrawl scrape / YouTube transcript + verbatim verifier):
   pull primary text; search for a verbatim span that supports the principle.
   found    → mint grounding atom {content, original_quote, source_ref=URL}, attach,
              tag `sourced`. Add atom to the corpus.
   not found → step 4.

4. TRUTH CHECK (LLM judge, knowledge-based — SEPARATE from sourcing):
   "Is this principle genuinely held by [person]? true/false + reasoning."
   true  → tag `attributed` (keep, label honestly as widely-attributed-not-corpus-sourced).
   false → tag `dropped` (or queue for human review if confidence < threshold).
```

## Data model

Each synthesis principle gains:
```json
{
  "title": "...", "desc": "...",
  "provenance": "grounded | sourced | attributed | dropped",
  "evidence": { "atom_id": "...", "quote": "...", "source_ref": "https://..." }  // for grounded/sourced
}
```
Pack/explore.html render a small provenance badge so the human-facing UI is honest:
**Grounded** (in corpus) · **Sourced** (retrieved primary quote) · **Attributed** (widely documented,
not in our material). `dropped` never ships.

## Gate (fail-closed on integrity, not on completeness)

- **Hard block:** any principle still tagged `confabulated/false` and presented as grounded. (the bug today)
- **Soft flag, build continues, ship HIDDEN:** if `attributed + dropped` > 30% of principles → the
  corpus is too thin for this subject; surface "undersampled — add sources." (consistent with voice floor)
- Report per-build: grounded / sourced / attributed / dropped counts. The honest grounding number is
  `(grounded + sourced) / total`.

## Cost (per brain)

- Discovery: ~12 ungrounded principles × 1 query ≈ $0.05–0.10 (Exa or Sonar).
- Fetch: Firecrawl/transcript — already in pipeline.
- Verify: existing verifier (free) + 1 truth-check LLM call per still-ungrounded principle (~$0.02).
- **~$0.15/brain.** Trivial vs. the credibility it buys.

## Why this over "cite or drop"

Deletion fixes confabulation by *subtraction* — and silently discards real knowledge when our 30
clips undersample a subject with thousands of hours of public material. This fixes it by *addition*
(retrieve the real quote) and *honesty* (label what we couldn't source). A brain should get richer
and more credible under QA. Dropping "Physics is the only law" because our sample missed it would
make the Elon brain emptier AND less true — optimizing the metric against the target.

## Immediate follow-ups (separate from the systemic gate)

- Re-source the 5 confabulated brains (elon, jensen, oprah, gokul, hank) once Phase 3.5 exists.
- Backfill: run Phase 3.5 over the whole catalog; expect grounding to rise materially via `sourced`,
  with a clear `attributed` tail that's honest rather than faked.
