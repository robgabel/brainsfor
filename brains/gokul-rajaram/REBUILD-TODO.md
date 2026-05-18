# Gokul Rajaram — Rebuild TODO

Captured 2026-05-18 after the new QA checks (`check_quote_provenance`, `check_synthesis_grounding`, `fact-check-brain.py`) revealed the synthesis layer is mostly LLM extrapolation, not Gokul's actual words.

## Current QA verdict

| Metric | Value | Target | Status |
|---|---|---|---|
| Structural audit | 80/100 (B) | 90+ | Down from 92 after new checks added |
| Quote provenance | 86% verified | 50%+ | ✅ Strong — most atom quotes trace to transcripts |
| Synthesis grounding (lexical) | 0% | 70%+ | ❌ No principle key phrases appear in source |
| Fact-check (semantic, Sonnet) | 13.5% (3 grounded / 22 ungrounded) | 70%+ | ❌ Only 3 of 26 principles supported by source |
| Voice coverage | 42% | 50%+ | ⚠️ Below target, supplemental atoms lack quotes |
| Adversarial eval | not yet re-run with 8 prompts | pass | ⏳ Pending |

## Root cause

Two interacting problems:

1. **20VC 8 Moats interview failed to ingest** (Phase 2.1 JSON parse error). This was THE primary source for AI-defensibility / data half-life / 8 moats content. Without it, the synthesis fabricated those positions from Opus's training data.

2. **Phase 3 synthesis is atom-based, not transcript-based.** Even with the 6 successful transcripts, the synthesis layer reads aggregated atoms (which were Haiku-extracted summaries) rather than the raw 265K-char transcript corpus. This compresses out the rhetorical structure, qualifications, and negative-space evidence (`would_not_say`).

## Rebuild plan

### Step 1 — Recover the 20VC 8 Moats interview

The Phase 2.1 ingestion errored on this video with `Expecting property name enclosed in double quotes`. Likely a malformed quote in the LLM's atom-extraction JSON output.

- [ ] Re-fetch transcript: `python3 scripts/ingest-youtube.py --brain gokul-rajaram --download --video 6ctOnY1WmBw`
- [ ] Re-run atom extraction on just that video — investigate the JSON parse failure mode; may need to switch from Haiku to Sonnet for atom extraction on long transcripts, or add a JSON-repair pass
- [ ] Verify the resulting atoms include explicit "data half-life", "8 moats", "ERPs vs Zendesk/Slack" content traceable to verbatim quotes

### Step 2 — Persist text-source raw scrapes

Phase 2.2 currently throws away the raw text after atom extraction. This breaks provenance for ~50% of atoms.

- [ ] Modify `scripts/auto-build-brain.py` `scrape_text_sources()` to save raw Firecrawl markdown alongside extracted atoms (e.g., `brains/{slug}/source/text/{filename}.md`)
- [ ] Update `load_source_corpus()` in `audit-brains.py` and `fact-check-brain.py` to include these raw text files in the corpus
- [ ] Re-scrape Gokul's text sources to get the raw markdown corpus
- [ ] Re-run audit + fact-check — expect provenance to improve significantly

### Step 3 — Rebuild synthesis from transcripts (not atoms)

This is the high-impact change. Synthesis should read **raw source corpus**, not the atomized intermediate.

- [ ] Add a new `--synthesis-from-transcripts` flag to `scripts/auto-build-brain.py` Phase 3 (or write a new `scripts/synthesize-from-source.py`)
- [ ] The Phase 3 prompt should:
  1. Receive the full transcript corpus + raw text scrapes (not atoms)
  2. Be instructed: "Extract first_principles ONLY if you can identify ≥3 distinct passages in the corpus that express the same underlying belief"
  3. Be instructed: "For `would_not_say`, identify moments where the speaker rejected an interviewer's premise, sidestepped a question, or explicitly said 'I disagree' — cite the rejection moment verbatim"
  4. Output structured JSON where each principle has a `source_evidence` array with verbatim quotes + timestamps
- [ ] Run `scripts/fact-check-brain.py` on the new synthesis — target ≥70% grounding
- [ ] Drop any principle that can't be grounded ≥2 times

### Step 4 — Cluster realignment (already done, but verify)

The cluster realignment (decision_making, ads_monetization, founder_mode, ai_defensibility) is correct. After the new synthesis lands, verify clusters still match the actual themes that emerge from grounded principles. May need minor adjustments — e.g., if "ai_defensibility" principles all collapse into the 8-moats interview content, the cluster name could be more specific.

- [ ] After Step 3, re-run `python3 scripts/audit-brains.py --brain gokul-rajaram`
- [ ] Check cluster voice% by cluster — if any new cluster has 0% voice, it's a sign the synthesis didn't surface real content for it
- [ ] Drop or rename clusters that can't be grounded

### Step 5 — Voice enrichment with better URL mapping

The `enrich-voice.py` run got 3/200 success because `source_ref` is mostly title strings, not URLs.

- [ ] Either fix `source_ref` during atom extraction to be the URL (better), or expand `sources.json` to have title→URL mappings for ALL sources including paraphrase titles
- [ ] Re-run `python3 scripts/enrich-voice.py --brain gokul-rajaram --limit 200`
- [ ] Apply the review file: `python3 scripts/enrich-voice.py --brain gokul-rajaram --apply <review>.json`
- [ ] Target voice coverage 50%+

### Step 6 — Behavioral eval at full prompt scale

With the new 8-adversarial prompt format:

- [ ] Delete old prompts.json: `rm brains/gokul-rajaram/evals/prompts.json`
- [ ] Re-seed: `python3 scripts/eval-brains.py --brain gokul-rajaram --seed-prompts --force`
- [ ] Verify 24 total prompts (8 general / 8 voice / 8 adversarial), each adversarial targets a distinct would_not_say
- [ ] Run full eval: `python3 scripts/eval-brains.py --brain gokul-rajaram` (~10 min, ~$1)
- [ ] Check adversarial violations count — should be 0; if higher, the brain has principles that are too easy to contradict
- [ ] Verify voice fidelity ≥4.5 dimension average

### Step 7 — Ship + verify

- [ ] Re-export pack from updated atoms + new synthesis
- [ ] Run full QA gauntlet:
  - `python3 scripts/audit-brains.py --brain gokul-rajaram --with-behavioral` (structural ≥90, behavioral ≥85)
  - `python3 scripts/fact-check-brain.py --brain gokul-rajaram` (grounding ≥70%)
- [ ] Commit + push (Vercel auto-deploys to brainsforfree.com)
- [ ] Hand-verify 5 random principles in `explore.html` against transcripts

## Acceptance criteria

The Gokul brain is acceptable to ship when:

- Structural audit ≥90/100
- Quote provenance ≥70%
- Synthesis grounding ≥70% (lexical) AND ≥70% (fact-check semantic)
- Voice coverage ≥50%
- Behavioral eval ≥85/100 with 0 adversarial violations
- 100% of `would_not_say` items have a corresponding rejection moment cited from source

## Estimated effort

| Step | Time | Cost |
|---|---|---|
| 1. Recover 20VC | 30 min | ~$0.50 |
| 2. Persist text scrapes (pipeline change) | 2-3 hr coding + re-scrape | ~$1 |
| 3. Transcript-based synthesis | 1-2 hr coding + 1 hr run | ~$3-5 |
| 4. Cluster verify | 15 min | $0 |
| 5. Voice enrichment fix | 30 min coding + re-run | ~$1 |
| 6. Behavioral eval | 15 min | ~$1 |
| 7. Ship | 15 min | $0 |
| **Total** | **~6-8 hr eng + 2 hr compute** | **~$7-9** |

## Out of scope for this rebuild

- Adding new YouTube sources (Lenny's, Acquired episodes if Gokul appears on them)
- Building a `/brain gokul-rajaram` skill UX layer
- The "score 100/100 in behavioral eval" claim — re-running smoke test won't increase confidence; the structural issues need fixing first

## Risk

The biggest risk is that even with all 7 steps, the Gokul source corpus may be insufficient for a defensible 250+ atom brain. The 6 successful transcripts + ~10 text scrapes produced ~220 real-source atoms. If we cannot get to 70%+ grounding without padding from Phase 2.3 cluster fill, the right move may be to:

1. Find more real sources (more YouTube, more text), OR
2. Accept a smaller brain (~250 atoms, all real-source) and skip Phase 2.3 entirely

The current 554-atom brain is padded to volume targets, and that padding is what fails the fact-check. A 250-atom brain at 90% grounding is materially better than a 554-atom brain at 13.5%.
