# QA report: PRINCIPLES.md BrainsFor layer, round 1

**Date:** 2026-11-06. **Reviewer:** independent agent, no research context. **Scope:** header (lines 1 to 12), Part 5 (35 to 44), "How the core shows up here", Parts 6 to 8, QA record. The vendored core (lines 16 to 362) is out of scope; `node --test scripts/test/principles-core-vendored.test.ts` passes 3/3.

Method: every `file:line` read in this checkout with three lines of context; every commit via `git show -s`; PR #34 and #58 via `gh api`; every `rb` atom via `brain_search`; `linkedin_voice_rules` via `linkedin_context`; every Part 8 number re-run on `origin/main` (295 commits, 2026-04-04 to 2026-07-22).

## 1. Receipt audit

Status key: VERIFIED (text and location match), VERIFIED-APPROX (right idea, wrong line or softened quote), UNSUPPORTED (not found), MISREAD (source exists but does not say what the doc claims).

### 35
| Receipt | Status | Note |
|---|---|---|
| `BRAND.md:17-19` | VERIFIED | lines 17 and 19 |
| `BRAND.md:370` | VERIFIED | |
| `docs/INTEGRATION-GUIDE.md:205` | VERIFIED | |
| commit `7c1125a` | VERIFIED | quote with ellipsis matches body |
| `website/middleware.ts:3-6` | VERIFIED | "MUST stay exempt" is line 6 |
| `docs/INFRA-AUDIT-2026-07-01.md:17`, `:23` | VERIFIED | |
| `IMPROVEMENTS.md:30` | VERIFIED-APPROX | source says "paywall-enforceable at the protocol level"; the doc drops the "paywall-" prefix inside the quotation |

### 36
| Receipt | Status | Note |
|---|---|---|
| `personas.md:258` | VERIFIED | |
| `business-plan.md:57` | VERIFIED | |
| `PRD-homepage-first-mile.md:14`, `:3`, `:60` | VERIFIED | |
| `website/CLAUDE.md:20` | VERIFIED | |
| `LAUNCH.md:98`, `:105` | VERIFIED | |

### 37
| Receipt | Status | Note |
|---|---|---|
| `LAUNCH.md:208`, `:205` | VERIFIED | |
| `CLAUDE.md` (publish-qa-scores) | VERIFIED | line 458 |
| `HANDOFF-brain-qa.md:90`, `:62` | VERIFIED | |
| `scripts/brain-qa.py:54-67` | VERIFIED | `PERSONA_PASS = 70` (54), `VOICE_GATE = 0.60` (55), `AUTH_VOICE_FLOOR = 80` (67) |
| `CLAUDE.md` (self-recognition) | VERIFIED | line 469 |
| `business-plan.md:693` | VERIFIED | |
| "the eight sub-gate brains" | VERIFIED | `LAUNCH.md:202` "Flip the 8 sub-gate brains" |

### 38
| Receipt | Status | Note |
|---|---|---|
| `CLAUDE.md` (epistemic atoms) | VERIFIED | line 199 |
| `skills/brain-foundation/SKILL.md:72-73` | VERIFIED | |
| `CLAUDE.md` "hedging a person's own biography reads as amnesia" | VERIFIED | line 207; the phrase also sits in SKILL.md:72 |
| `SPEC-synthesis-grounding.md:19`, `:35`, `:124` | VERIFIED | |
| `PLAN-brain-depth.md:96-98` | VERIFIED | |
| `CLAUDE.md` (2026-07-18 lessons) x.com/LinkedIn | VERIFIED | line 337 |

### 39
| Receipt | Status | Note |
|---|---|---|
| `scripts/diarize.py:5-7` | VERIFIED | lines 6 and 7 |
| `CLAUDE.md` (2026-06-20 lessons) speaker-blind | VERIFIED | line 280 |
| `scripts/enrich-voice.py:84`, `:82` | VERIFIED | |
| PR #58 body | VERIFIED | "executed with Rob's explicit authorization"; "Full reversible ledger committed"; merged 2026-07-06 |
| `scripts/auto_build_config.py:476-484` | VERIFIED | lines 476 and 484 |
| `HANDOFF-brain-qa.md:30` | VERIFIED | |
| `BRAND.md:365`, `:217` | VERIFIED | |
| `IMPROVEMENTS.md:102` | VERIFIED | |

### 40
| Receipt | Status | Note |
|---|---|---|
| `scripts/auto-build-brain.py:4-5` | VERIFIED-APPROX | the quoted sentence is lines 5 to 6, not 4 to 5 (line 4 is blank) |
| `scripts/build-brain.py:1046-1049` | VERIFIED | |
| commit `9d67692` | VERIFIED | |
| `scripts/auto-build-brain.py:2248-2252` | VERIFIED | lines 2249 to 2250 |
| `CLAUDE.md` (verify-facts HARD LESSON) | VERIFIED | line 204 |
| `scripts/classify-claims.py:9-12` | VERIFIED | |
| commit `84175bb` | VERIFIED | subject says "5 ... claims", body says "all four proposals approved"; the inconsistency is in the source, not the doc |
| `.github/workflows/build-brain.yml:41-44`, `:191` | VERIFIED | |
| commits `fa73048`, `4754093` | VERIFIED | |
| `scripts/verify-facts.py:179-187` | VERIFIED | see section 6 |

### 41
| Receipt | Status | Note |
|---|---|---|
| commit `1669e3b` | VERIFIED | both quotes present |
| `scripts/brain-qa.py:64-65` | VERIFIED | |
| `PLAN-brain-depth.md:99-103` | VERIFIED | |
| `scripts/auto_build_config.py:88-90` | VERIFIED | |
| commit `36862a6` | VERIFIED | |
| `PRD-sonnet-4-6-upgrade.md:114`, `:128` | VERIFIED | |
| `CLAUDE.md` (2026-07-18) whitelist; (2026-07-04) never strip | VERIFIED | lines 336, 276 |

### 42
| Receipt | Status | Note |
|---|---|---|
| `scripts/auto_build_config.py:41-62`, `:31-38` | VERIFIED | |
| `scripts/brain-qa.py:25-27` | VERIFIED | |
| `CLAUDE.md` (eval harness) | VERIFIED | line 432 |
| commit `e7ec4ac` | VERIFIED | |
| `docs/INFRA-AUDIT-2026-07-01.md:125` | VERIFIED | |
| `PRD-sonnet-4-6-upgrade.md:35` | VERIFIED | |
| Gloss "Every pipeline phase in the rules file carries a dollar figure" | MISREAD | `CLAUDE.md:228-239` lists Phases 0 to 5; none carries a dollar figure. Dollar figures in CLAUDE.md attach to the whole build (~$23), classify-claims ($0.17), the atom-floor note ($17), brain-qa ($0.46, $10), evals ($14). The sentence overstates. |

### 43
| Receipt | Status | Note |
|---|---|---|
| `personas.md:262`, `:260` | VERIFIED | |
| `BACKLOG.md:19-23` | VERIFIED | five rows, each ending "Rob knows him personally" |
| `business-plan.md:226`, `:185`, `:292`, `:199`, `:195` | VERIFIED | |
| `LAUNCH.md:179` | VERIFIED | |

### 44
| Receipt | Status | Note |
|---|---|---|
| `BRAND.md:38`, `:355`, `:357` | VERIFIED | |
| `website/CLAUDE.md:8`, `:30` | VERIFIED | |
| rb 2026-05-29 slack | VERIFIED | verbatim; source_type slack, date 2026-05-29, people [Rob Gabel]. It is a bot paraphrase ("Rob's voice guidelines for this post require"), not his words. |
| rb 2026-07-10 slack | VERIFIED as text, MISREAD as attribution | verbatim; source_type slack, date 2026-07-10. The atom carries no `people` field, and its sibling atom of the same date says the Onlyness Test "was proposed" as a Writers' Room gate. Nothing marks it as a Rob instruction. The gloss "two Rob instructions on record for the number-first and name-swap halves" is not supported for the name-swap half. |
| `skills/brain-foundation/SKILL.md:84` | VERIFIED | |

### How the core shows up here
| Item | Status | Note |
|---|---|---|
| 1: `auto_build_config.py:484`; `verify-facts.py:14` | VERIFIED | |
| 2: `website/app/page.tsx:111` "the beta band says" | MISREAD (location) | line 111 is inside the "Beat 5c: the other minds" section (page.tsx:89-114, the brain-pill row under "Browse all brains"). `<BetaBand />` renders in a separate section at line 86, and `BetaBand.tsx` has its own copy. Quote is verbatim; the attribution to the beta band is wrong. |
| 2: "every detail page a QA breakdown" | VERIFIED-APPROX | 22 of 26 index entries carry `qa`; the four without are hidden and have no detail page |
| 3: commit `1669e3b`; `INFRA-AUDIT:10` | VERIFIED | |
| 5: commits `1e27646`, `14291e5` | VERIFIED | |
| 6: `build-brain.py:1046` | VERIFIED | |
| 7: `CLAUDE.md` 2026-07-18 lessons | VERIFIED | |
| 9: `packages/brainsfor-mcp/src/scoring.ts` "THE one retrieval algorithm"; `INFRA-AUDIT:3`, `:53` | VERIFIED-APPROX | scoring.ts:1 verified. INFRA-AUDIT:3 quotes Rob's approval as "auth: park, dedicated Supabase stays free-tier, new model family, drop cross_connections"; the registry-copy deletion is Move 7 at line 9 and is not in the quoted approval. "with Rob's OK" rests on "Rob approved the plan" generally. |
| 10: `INFRA-AUDIT:13`; commit `c6307ed` | VERIFIED | |
| 11: `website/lib/site-config.ts`; `CLAUDE.md` Phase 7 | VERIFIED | site-config.ts:1-5; CLAUDE.md:538 unchecked |
| 13: `scripts/diarize.py`; `SPEC-synthesis-grounding.md:51` | VERIFIED | |
| 14: `scripts/persona-qa.py:9-22`; commit `1669e3b` | VERIFIED | |
| 15: `auto_build_config.py:88-90` | VERIFIED | |
| 18: commit `4ce7d44`; `CLAUDE.md` "Gotcha that bit us" | VERIFIED | |
| 28: commit `de11b83` | VERIFIED | "Shaped by a /board review (Jobs, Belsky, Graham, Gary Vee, Elon)" |
| 30: `BRAND.md:355` | VERIFIED | |
| 31: commit `67fb924`; `MIN_QUOTE_PROVENANCE = 50` | VERIFIED | `auto_build_config.py:76` |
| 34: `website/CLAUDE.md:30` | VERIFIED | |

### Part 6
| Tension | Receipts | Status |
|---|---|---|
| 1 | `INFRA-AUDIT:25`, `:55`; `LAUNCH.md:149`; `middleware.ts:29`; commit `0375975` 2026-07-22 | all VERIFIED |
| 2 | `auto-build-brain.py:4-5` (APPROX, lines 5-6); `verify-facts.py:179-187`; commit `3dfcdde`; commit `4868b12` "vetoed"; ledger `review` key "human-proxy review" | VERIFIED |
| 3 | 49/13/205; `9164a41`, `bb1287a`; `b79a281`, `31ec85b`, `5307f9e` | counts: see section 5 (merge/direct split differs); the two Claude merges did land LAUNCH.md (verified by `--stat`); the three live-flip hashes are single-parent direct commits by "Rob Gabel" with "status=live"/"live" in the subject. "ten brains" flipped live by direct commit: I could confirm five by subject grep; the ten is UNVERIFIED (would need index.json diffs). |
| 4 | hero-demos counts; `BRAND.md:145-147`, `:62`; `SKILL.md:124-141`; PR #34 | hero-demos.ts has 25 em dashes, 17 inside string literals (16 in answers, 1 in a chip label), 7 in comments: VERIFIED. "4 on the pricing page": VERIFIED. "1 in the beta band": MISREAD, same location error as above; `BetaBand.tsx` itself holds 3 em dashes that Part 8's 30 does not count. "nine contrast constructions in about 700 words": VERIFIED-APPROX (10 ", not" constructions across all 1,314 quoted words; the thinker answers alone are roughly 700). BRAND.md and SKILL.md lines VERIFIED. PR #34 merged by robgabel 2026-06-21: VERIFIED. |
| 5 | `publish-qa-scores.py:36-40`; commits `11b899d`, `7f7a7be` | VERIFIED-APPROX. Panels: 07-04 = 63 (published, as_of 07-04), 07-05 = 58 (`interim: true`), 07-08 = 62 (not flagged interim). The guard holds the pill over the 58; the 62 is held only because `publish-qa-scores.py` was not re-run after 07-08 (`7f7a7be` says "left at 63 per the interim-renovation guard" but did not flag its own eval). The doc attributes both to the guard. |
| 6 | `SKILL.md:64`, `:89`; `BRAND.md:76`, `:367`; `CLAUDE.md` self-recognition 50% | all VERIFIED |
| 7 | `linkedin_voice_rules`; `BetaBand.tsx:23-24`; `LAUNCH.md:185` | all VERIFIED (both voice-rule quotes verbatim) |
| 8 | rb 2026-04-25 slack; `route.ts:127` | VERIFIED (atom: slack, 2026-04-25, people [Rob Gabel]; a bot paraphrase) |
| 9 | `.gitignore:37`; `CLAUDE.md` 2026-07-04; `backfill-raw-sources.py` | VERIFIED |
| 10 | `CLAUDE.md:134` RPC vs `:121` keyword; 6 vs 9 criteria (`audit-brains.py:109-118`); `brain-qa.py:143-145`; "25 brains" (`CLAUDE.md:124`) vs 26; 49 commits; no test file | all VERIFIED |
| 11 | commit `2c9fa45`; `PLAN-brain-depth.md:72-75` | VERIFIED-APPROX: `2c9fa45` is a branch-scoped CI workflow that dispatches `confirm_cost=yes-23`, committed under Rob's identity with a Claude co-author; "sessions dispatching" is an inference |
| 12 | rb 2026-04-01 session; rb 2026-04-28 slack | 04-01 VERIFIED verbatim with ellipsis. 04-28 VERIFIED-APPROX: the atom reads "Rob is deferring a decision on whether BrainsForFree should consolidate skills similarly pending an architecture review"; the doc's "a BrainsFor skills decision deferred" compresses it. |

### Part 7
rb 2026-05-10 session (Tubular retrospective planned): VERIFIED. "99 LinkedIn originals": VERIFIED in `linkedin_voice_rules`. `CLAUDE.md` Remaining Questions carrying pricing and licensing: VERIFIED (lines 535-539).

### Header
Line 11: "both comments under his login are agent posts": the two `robgabel` comments (PR #45 2026-07-03, PR #26 2026-07-04) read as session-style status posts; plausible, not provable. "the standing human gate" listed among decisions "the record attributes to him by name": no receipt in the doc names Rob for that decision (commit `3dfcdde` says "Per the human-gate rule" with no attribution; `PLAN-brain-depth.md:96` says "Rob reviews", a plan). UNSUPPORTED as a Rob-attributed decision.

## 2. Tag audit

| # | Tag | Verdict |
|---|---|---|
| 35 | DOC | Justified. All receipts are Claude-drafted docs and a session commit. |
| 36 | DOC | Justified. |
| 37 | ROB (Option C), DOC (gate, metric) | ROB is justified under the task's rule (an explicit dated record: `LAUNCH.md:208` "CHOSEN (Rob, 2026-07-06)"). It is not justified under the doc's own header definition at line 9, which reads ROB as "his own words". Either widen line 9 to "or a dated record that he chose/approved/vetoed" or retag. See F5. |
| 38 | DOC | Justified. `PLAN-brain-depth.md:96` "Rob reviews" is a plan, correctly not used for ROB. |
| 39 | DOC, one ROB (Oprah purge) | The ROB rests on PR #58's body, "executed with Rob's explicit authorization", an agent's paraphrase, dated by the PR (2026-07-06). Passes the task's rule, barely; the PR body gives no date for the authorization itself. |
| 40 | DOC, ROB for one gated approval | Commit `84175bb` (2026-07-05) "(Rob-approved)", "all four proposals approved". Agent's record, dated. Passes the task's rule. |
| 41 | DOC | Justified. |
| 42 | DOC | Justified. |
| 43 | DOC | Justified. "Rob knows him personally" is a doc claim. |
| 44 | DOC, "with two Rob instructions on record" | DOC is right. The "two Rob instructions" gloss is overstated: rb 2026-05-29 is a bot paraphrase tagged to Rob (acceptable as "on record"); rb 2026-07-10 (Onlyness Test) has no person attached and its sibling atom says it was proposed, not instructed. See F4. |

No DOC that is actually INFERRED. One ROB-adjacent gloss (44) rests on an atom that does not attribute to Rob at all.

## 3. Duplicates and restatements

- **44 restates core 30 and overlaps 36.** "Every piece carries a number" is core 30 ("named, checkable specifics beat any adjective"); "the demo outranks the adjective" is 36's thesis. What is BrainsFor-only in 44 is the inversion of the plumbing ban (core 34) for a builder reader, and the name-swap test. Fold: cut the number clause and the demo clause from 44; keep "write for a builder who came to evaluate; the plumbing is the proof; name-swap test". The agent-as-reader clause in 35 belongs in 44 too, since 44 is the "who is the reader" principle.
- **41 restates core 3 and core 26 in part.** "Pilot where the delta is knowable and file the null result" is core 26's pass/fail line; "the cost estimate is itself a claim to be measured" (42) is core 3. The BrainsFor-only content of 41 is "when the gate and a better signal disagree, fix the gate, and give every gate its own kill criterion". Fold the pilot/null-result clause into core 26's example list and keep 41 at the instrument rule.
- **40's last sentence is a separate rule.** "Parallel sessions claim a brain before writing to its tables" is coordination hygiene, unrelated to fail-open/fail-closed. Either its own short principle or a line under core 24 (only I commission work) in the Part 6 tension 11 note.
- **43 is four beliefs in one heading:** subject selection (thinker is distribution), channel strategy (no marketplace), content economics (every atom is content, close to core 29), and pricing (unvalidated by the doc's own admission). The pricing clause has no decision behind it and should move to Part 7. The content clause is core 29 with BrainsFor nouns.
- **38 and 41 share "ungrounded is not false".** 38's last sentence ("fix by addition and labeling, never by deletion") and 41's first gloss ("scrubbing true figures to clear a numeric gate made brains worse") are the same lesson from two scripts. Keep it in 38 (what the product may say) and let 41 cite it.
- 37 and 39 are distinct (the model-as-subject veto versus the real subject's objection), and 38/39 are distinct (truth axis versus attribution axis). No fold needed.

## 4. Prose rules

Em dashes: `awk 'NR>363' PRINCIPLES.md | grep -n "—"` returns 20 hits on lines 374, 379, 387, 395 (2), 396, 398, 406, 416, 418, 426, 427, 428, 431, 441, 450, 458, 459, 460 (2), 479. Every one is inside a double-quoted source quotation (checked by counting unescaped quotes before each dash). Lines 1 to 13 (header) contain none. PASS.

Claude-isms: no "it's worth noting", "crucially", "importantly", "in other words", or hedge stacks in the builder's prose. No "not X but Y" constructions.

The contrast tic (core 34: "X, not Y at volume") is present in the builder's own prose outside quotations: 17 ", not" constructions in lines 364 to 552 (368, 370, 383, 393 twice, 403 three times, 424, 436, 464, 486, 504, 505, 513, 523, 524) plus 3 in the header (3, 7, 11). Examples: "Thresholds, not vibes", "Confidence is repetition, not truth", "a rubric misfit, not a brain defect", "a July habit on this repo, not its history", "Absent, not silent". Tension 4 names this exact tic as "plain drift" in the shipped copy; the layer that names it carries it at the same density. See F7.

## 5. Counts (Part 8), re-run on `origin/main`

| What | Doc | Mine | Verdict |
|---|---|---|---|
| Commits on main, 2026-04-04 to 2026-07-22 | 295 | 295 | match |
| First-parent commits | 267 | 267 | match |
| squash `(#N)` / merge commit / direct | 49 / 13 / 205 | 49 / 15 / 203 by parent count | mismatch. Two true merge commits (`74efc52`, Claude, "Make Jesse Pujji bio more impressive..."; `c284548`, Rob Gabel, "merge: auto-sync rob-ai CLAUDE.md brains table") have two parents but no "Merge " subject prefix; the doc classified by subject. |
| Direct by author | Rob 173, Claude 30, bot 2 | Rob 172 (82 "Rob Gabel" + 90 "robgabel"), Claude 29, bot 2 | same two commits |
| Rob-identity commits; with `Co-authored-by: Claude` | 248, 228 | 248; 228 by body grep (221 by `%(trailers:...)`, which misses seven non-trailer placements) | match on the doc's method |
| Commits authored "Claude" | 45 | 45 | match |
| Rob-identity subjects with em dash | 56 | 56 | match |
| GitHub comments under Rob's login; typed by him | 2, 0 | 2 (PR #45, PR #26); both read as session posts | match (the 0 is a judgment) |
| Pull requests; review comments | 65 (0) | 65; 0 | match |
| Python scripts in `scripts/` (archived) | 35 (6) | 35 (6) | match |
| Committed test files before this PR | 0 | 0 | match |
| Workflows; neither runs tests | 2 | 2 (`build-brain.yml`, `export-brain.yml`); no test step in either | match |
| Brains live/hidden; atoms; connections | 22/4; 21,815; 23,385 | 26 brains, 22/4; 21,815; 23,385 | match |
| Numeric constants in `auto_build_config.py` | 12 | 12 uppercase numeric assignments | match |
| Commits touching CLAUDE.md; length before this PR | 49; 535 | 49; 535 (549 in the working tree) | match |
| Em dashes in `hero-demos.ts`, `page.tsx`, pricing | 30 | 30 (25 + 1 + 4) | match |

Tension 3 then says "205 direct, of which 30 are authored Claude with no PR, including the merges that landed LAUNCH.md and PRD-8 (`9164a41`, `bb1287a`)". Under the doc's own Part 8 classification those two hashes are among the 13 merge commits (subjects start with "Merge"), so they cannot also be inside the 205. The sentence is internally inconsistent with Part 8. The underlying claim, that a Claude session merged to main without a PR, is true for both hashes.

## 6. Tension check

All 12 tensions have both sides receipted; see the Part 6 table in section 1 for status per receipt. Leans that misstate a side:

- Tension 2: accurate. `scripts/verify-facts.py:181-186` runs `sb.table(table).update({"verification": ..., "proof_ref": ..., "verified_at": ...})` for every verdict in `flagged`, which is every non-`unverified` verdict (lines 174-177). There is no review column, no `--apply` flag, and no per-verdict gate; the only switches are `--dry-run` (no API call, no writes at all, line 105) and `--limit`. The script also writes a triage copy to `evals/fact-verdicts-<date>.json` (lines 205-215), so the "manual revert" in `3dfcdde` had a file to work from; the doc could say so, but its claim stands as written.
- Tension 4: the "1 in the beta band" side is misplaced (section 1), and `BetaBand.tsx` carries 3 em dashes the count omits. The lean is unaffected.
- Tension 5: the lean treats the 62 as held by the guard; it is held by a publish that was never re-run. The lean ("a tracked exception with a time limit, or publish the latest") still fits.
- Tension 9: both sides receipted; the lean is fair.
- Tension 11: "sessions dispatching $23 builds" is inferred from a CI file under Rob's identity; the lean already says "ambiguous".

## 7. Misses (candidates, at most five)

1. **A judge panel needs a seat that rewards being interesting, or the gate selects for safe, boring brains.** `HANDOFF-brain-qa.md:88`: "Munger/Kara optimize for 'not fooled' (risk); Brené + an 'interesting/useful' rubric must pull the other way, or you select for safe, boring brains." Not in 37 or 41; not in the core (14 is about independence, not about which direction judges pull).
2. **A model's answer is never a source for another model; only its citations are.** `SPEC-synthesis-grounding.md:38-51`: "Grounding a principle on Perplexity's prose just launders one model's confabulation into another's ... use only Perplexity's citations, never its answer text." Core 13 (primary beats aggregator) is close but does not name the laundering failure, and 38 does not say where grounding may come from.
3. **The registry is the only seam; every surface derives from the pack and holds no state.** `docs/INFRA-AUDIT-2026-07-01.md:27`: "Pack Registry (the single interface: `brains/index.json` + `pack/` artifacts) → N thin surfaces ... that all derive from the registry and hold no state of their own"; `:83` "Make the Pack Registry the single seam." Core 9 and 11 cover define-once and platform; neither says the artifact is the interface and the surfaces are stateless.
4. **A beta user is a completed feedback loop, not a download.** `LAUNCH.md:13`: "10 beta users ... who install a brain, use it in a real session, and email back one thing their agent did better. That's it. Not revenue, not HN front page"; `:151` "That email = a completed beta slot." Core 26 asks for a pass/fail line; this names the BrainsFor unit of progress, and tension 1 depends on it.
5. **A model panel is a signal, never ground truth; a human spot-checks the chair's top flag before anything ships.** `HANDOFF-brain-qa.md:84`: "Reflexivity ... Tier-4 human calibration is mandatory, not optional"; `CLAUDE.md:464` "Treat the panel as a strong signal, not ground truth". 40 gates shipment and 37 trusts the panel's number; neither says what the human checks. This also answers Part 7's open item on whether a second model pass may count as the human.

Also noted but closer to existing principles: build phases are idempotent and progress is committed so a fresh checkout can resume (`CLAUDE.md:245`), which core 7 and 42 partly cover.

## 8. Verdict

`VERDICT: FINDINGS`

- **F1 (major, wrong count).** `PRINCIPLES.md:533-534` and `:504`. Part 8 reports 13 merge commits and 205 direct; by parent count it is 15 and 203 (`74efc52`, `c284548` are two-parent merges with non-"Merge" subjects). Direct-by-author becomes Rob 172, Claude 29, bot 2. Either relabel the row "subject starts with Merge" or correct the numbers.
- **F2 (major, internal inconsistency).** `PRINCIPLES.md:504`. Tension 3 counts `9164a41` and `bb1287a` inside the 205 direct commits while Part 8 counts them among the 13 merge commits. Say "two of the 13 merge commits are Claude merges with no PR, and they landed LAUNCH.md and PRD-8".
- **F3 (major, misread source).** `PRINCIPLES.md:479` and `:505`. The em dash quoted as "the beta band says" lives at `website/app/page.tsx:111`, inside the "Beat 5c: the other minds" brain-pill section, not in `BetaBand` (rendered at `page.tsx:86`). `BetaBand.tsx` carries 3 em dashes that the Part 8 count of 30 omits. Fix both sentences and either add BetaBand to the count or say the count is three files.
- **F4 (major, wrong attribution).** `PRINCIPLES.md:466`, `:470`. "two Rob instructions on record" for 44: rb 2026-07-10 (Onlyness Test) has no person attached and its sibling atom of the same date says the test "was proposed"; it is not a Rob instruction. Drop to "one bot-recorded Rob instruction (number-first) and one proposed test (name swap)".
- **F5 (minor, tag definition).** `PRINCIPLES.md:9` versus `:393`. The header defines ROB as "his own words"; 37's ROB rests on `LAUNCH.md:208`, an agent's dated record of a choice. Widen line 9 to include a dated record that he chose/approved/vetoed, which is the rule the layer actually uses (37, 39, 40).
- **F6 (minor, misread).** `PRINCIPLES.md:446`. "Every pipeline phase in the rules file carries a dollar figure": `CLAUDE.md:228-239` phases carry none. Say "the build, the classifier, the panel and the eval harness each carry a dollar figure".
- **F7 (minor, prose).** Lines 368-524: 17 ", not Y" contrast constructions in the builder's own prose (plus 3 in the header), the tic core 34 bans at volume and tension 4 calls drift. Rewrite roughly half as plain statements.
- **F8 (minor, unsupported attribution).** `PRINCIPLES.md:11`. "the standing human gate" is listed among decisions the record attributes to Rob by name; no receipt in the doc names him for it (`3dfcdde` says "Per the human-gate rule"; `PLAN-brain-depth.md:96` is a plan). Drop it from the list or cite the record.
- **F9 (minor, mechanism).** `PRINCIPLES.md:506`. The 62 (07-08 panel) is not held by the interim guard; that eval is unflagged and the pill is stale because `publish-qa-scores.py` was not re-run. Only the 58 is guard-held.
- **F10 (minor, line drift).** `PRINCIPLES.md:426`, `:503`: `scripts/auto-build-brain.py:4-5` should be `:5-6`. `PRINCIPLES.md:379`: the IMPROVEMENTS.md quote drops "paywall-" from "paywall-enforceable". `PRINCIPLES.md:504`: "ten brains were flipped live by direct commit" is unverified (five confirmed by subject).
- **F11 (minor, duplicates).** Fold per section 3: 44 loses its number and demo clauses to core 30 and 36; 41 loses its pilot/null-result clause to core 26; 40's session-claim sentence moves out; 43's pricing clause moves to Part 7.

No blockers: every cited file, line region, commit, PR, atom and config key exists, and no quote is attributed to Rob that the record contradicts.
