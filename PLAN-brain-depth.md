# Brain Depth Plan — Elon showcase fix + fleet improvement (2026-07-04)

Grounded in the canonical scorecard (`brains/eval-runs/persona-qa-fleet-2026-07-04.md`: avg 71.6,
6/22 ship-gate) and the per-brain Opus panel reviews. Owner: Rob. Status: Part 1 ready to execute.

---

## Part 1 — Elon Musk (showcase brain, landing page): 63 → target 75+

**Diagnosis (from persona-review-2026-07-04):** auth 76 / rigor 72 / **coverage 34** / calib 68, voice 0.47.
Kara's verdict: *"a genuinely good process brain wearing a reputation-management skin."* The judges'
specific complaints, each of which maps to a concrete fix below:
- Every hard lesson "resolves into vindication" — cost-free, shame-free, change-free.
- The political operator, impulsive poster, and vindictive litigant are missing entirely.
- No relational cost anywhere (divorce = one bullet point, instantly overwritten).
- No self-inversion: "urgency is a choice" with zero counterweight for chronically blown timelines.
- Marketing claims reprinted as engineering truths ("X restored free speech", "hallucination-free
  Grok", "AI5 40x") — **an epistemic-classification failure, now fixable with claim_type/verification**.

### A0. Source cleanup FIRST (found 2026-07-04)
`source/sources.json` contains Phase-0 discovery pollution — e.g. source [20/20] is
"Fundamentals of Computer | computer science class 9 sindh board" (a Pakistani school lesson).
Audit all 35 entries, delete junk, before adding anything. Also: transcript fetches were
throttled after heavy same-day use — space `ingest-youtube.py` runs or expect blank ERRORs.

### A. Source expansion — the mess, in his own words (~$6, diarized ingest)
The corpus is 35 sources (20 videos, 10 profiles, 4 essays, 1 interview) — the highlight reel.
Add the crisis/conflict corpus where Musk himself narrates cost. Candidates (all long-form, his voice,
diarization-safe):
1. **2018 "worst year"** — NYT interview coverage + Rogan #1169 aftermath; 60 Minutes (2012, 2014).
2. **TED 2022 (Chris Anderson)** — the FSD miss admission ("I'm the boy who cried FSD"), Twitter-deal
   ambivalence.
3. **Code Conference interviews (Kara Swisher era)** — the political operator on record.
4. **DealBook 2023** — the advertiser outburst; BBC 2023; Don Lemon 2024 — the impulsive poster,
   unedited.
5. **SpaceX near-death** — Starbase walkthrough interviews, 2008 Christmas-eve narrations beyond the
   one already present.
6. **Isaacson-tour interviews (2023)** — on firings, demons, relational cost (his responses, not the
   biographer's prose).
Run: add to `source/sources.json` → `ingest-youtube.py --from-sources` (local, not CI) →
`extract` via the diarized path so interviewer words never enter his mouth.

### B. Hard-lessons re-mine with an anti-vindication rubric (~$1)
Re-run `mine-hard-lessons.py` on the enlarged corpus with the rubric hardened: a lesson MUST name a
real cost (money, relationship, reputation, time) and what he gave up — "I reinforced my default"
does not qualify. Target: 6-8 lessons where at least half end in loss, not vindication.

### C. Self-inversion atoms — the blown-timeline record (epistemic layer, ~$0)
Author fact-atoms (claim_type='fact', verification='verified', proof_ref=dated public statements) for
the timeline record: FSD "next year" (2014→), Mars cargo 2022 → slipped, robotaxi dates, Roadster 2.
Not gotchas — the counterweight the Munger judge demanded so the brain can invert on its own
overconfidence. Human-authored, ~10 atoms, loaded via the standard table.

### D. Epistemic reclassification of the marketing claims (human-gated, ~$0)
The three claims the panel flagged + the 9 unreviewed proposals in
`evals/fact-verdicts-2026-06-27.json`: classify "X restored free speech" etc. as `fact`+`contested`
with proof_ref, per the faithful-but-flagged rule. Rob reviews each verdict (the verify-facts gate);
nothing auto-publishes.

### E. Voice 0.47 → 0.60+ (~$1)
Fetch Elon transcripts locally, run `enrich-voice.py` (now verbatim-only) — his real syntax (the
pauses, the "sure", the profanity) is in the 20 videos already listed; it was just never extracted.

### F. Re-panel (~$0.40)
`persona-qa.py --brain elon-musk`. Success = coverage 34→60+, composite 63→75+, would-sign holds.
Total: **~$10, one session.** The showcase brain stops being a press kit.

---

## Part 2 — Fleet plan (tiered by actual blocker, not by score)

### Tier 0 — voice-blocked, IN FLIGHT (gary-vee 80, sara-blakely 79, oprah 76, jesse-pujji 74)
Pass persona ≥70 already; blocked ONLY by voice < 0.60. Voice pass running now (verbatim-only
extraction + corpus-verified apply). Then re-panel the four. **Expected: 6/22 → 10/22 ship.** (~$5)

### Tier 1 — coverage-blocked (the Elon playbook, generalized)
yann-lecun (cov 48), jensen-huang (45), scott-belsky (44), elon-musk (40), bill-harris (38),
jeremy-utley (62), jesse-pujji (62), melinda (58). Same three moves per brain: **(a)** add 3-5
crisis/failure/conflict sources in the subject's own words, **(b)** re-mine hard lessons under the
anti-vindication rubric, **(c)** re-panel. ~$8-12/brain. Order by product value: elon (Part 1) →
belsky (original flagship) → jensen → yann → the rest. Skip bill-harris until its caption-failure
issue is fixed (20 videos, 38 atoms — likely rescuable the jesse way, locally, free).

### Tier 2 — the floor (structural problems, not polish)
- **peter-zeihan (52):** two distinct problems. (1) Coverage 36 — needs the Tier-1 treatment.
  (2) His product IS contested claims — 22 sat in the verify triage. The fix is epistemic honesty,
  not deletion: Rob reviews `evals/fact-verdicts-2026-06-27.json`, promotes genuine `contested`
  verdicts with proof_refs, and the faithful-but-flagged rule voices them AS his claims. A Zeihan
  brain that flags its own contested predictions is more valuable than one that hides them.
- **sun-tzu (47):** likely a RUBRIC misfit, not a brain defect — an ancient aphorist has no personal
  "mess" for the Brené judge to find (coverage 38 measures a thing the corpus cannot contain).
  Fix the instrument: add a corpus-shape modifier to `persona-qa.py` (score coverage against what
  the corpus CAN contain) before spending a dollar "improving" the brain. Validate against
  charlie-munger (also aphorism-heavy, scores 82) as the control.

### Cross-cutting passes (cheap, scriptable, fleet-wide)
1. **Transcript fetch-all + re-audit (free, do FIRST).** The jesse lesson: provenance scores are
   understated wherever transcripts aren't local. Run `ingest-youtube.py --from-sources` across all
   26, re-run `audit-brains.py`. Several "fabricated quote" warnings will evaporate; what remains is
   the REAL fabrication list.
2. **Temporal density backfill** — annie-duke, melinda, belsky at 0% dated atoms; /evolve (the
   site's proof-point skill) can't run on them. Backfill `source_date` from sources.json dates.
3. **Epistemic verification, brain-by-brain, human-gated** — the standing triage files await review
   (zeihan first: his contested claims are his product). Never auto-publish a false/contested flag.
4. **Diarization re-check** — the shipped 25 predate diarize.py; interview-heavy brains (kara,
   oprah, the greens, attia) risk interviewer words in the subject's mouth. Spot-check via the
   local-transcript matcher; rebuild extraction only where leakage is confirmed.

### Sequencing
1. Tier 0 finish + re-panel (today) → 2. Cross-cut #1 transcript fetch-all (today, free) →
3. Elon Part 1 (next session, ~$10) → 4. Zeihan epistemic triage w/ Rob (30 min of his eyes) →
5. Tier 1 one brain at a time, re-panel each → 6. sun-tzu rubric fix → 7. temporal backfill.

## Remaining Questions
- [ ] Does the persona-qa coverage dimension need a corpus-shape modifier before Tier 1 spends
      money chasing a score some corpora can't reach? (sun-tzu test case)
- [ ] Elon C (blown-timeline atoms): does Rob want these in the public showcase brain, given the
      landing page is the first thing a visitor sees? (My position: yes — a brain that can name its
      own misses is the product's honesty claim made visible.)
- [ ] bill-harris: rescue captions locally, or rebuild from richer text sources?
- [ ] Voice threshold 0.60: is the persona-qa voice score sensitive to enrichment coverage alone,
      or does it need re-paneling to move? (Verify on the first Tier-0 re-panel.)
