# QA Report: FIRST-PRINCIPLES.md (clean-room audit)

**Reviewer:** independent QA agent, no part in drafting the document.
**Date:** 2026-11-06
**Scope:** `docs/synthetic-rob/FIRST-PRINCIPLES.md` (v1 draft, 401 lines).
**Method:** every `file:line` receipt was checked by reading the cited file; every `commit <hash>` by `git show`; every `rb <date> <type>` by `mcp__rob-brain__brain_search` (date and source_type compared to the citation); LinkedIn receipts against `linkedin_context` keys `linkedin_voice_rules` (updated 2026-10-30), `linkedin_creative_playbook` and `linkedin_pillars_personas` (both updated 2026-11-05). `prefs` receipts could not be checked and are marked UNVERIFIABLE-BY-ME throughout.

## Headline

The document is well-sourced. Of roughly 150 receipts, 4 are UNSUPPORTED (all four are rob-brain session atoms dated 2026-09-29 and 2026-10-12 that I could not find), 7 are VERIFIED-APPROX, 1 is MISREAD, and the rest are VERIFIED. The bigger problem is not the receipts. It is the confidence tiers. Eleven principles are rated HIGH on evidence that, under the document's own tier definition, is MED: Claude-drafted artifacts Rob merged, plus bot self-reviews that describe what the bot should do to Rob. The second big problem is that several "building" principles describe a correction Rob made once in July 2026, not a standing habit, and the repo record since then shows the opposite behavior. Details below.

---

## 1. Receipt audit

Grades: VERIFIED (text and location match), VERIFIED-APPROX (right idea, wrong line or softened quote), UNSUPPORTED (not found), MISREAD (source exists, does not say what the doc claims), UNVERIFIABLE-BY-ME (prefs).

### Part A

**A1.** prefs: UNVERIFIABLE-BY-ME. rb 2026-05-08 session: VERIFIED, exact text, source_type session, date matches. `PRD-homepage-first-mile.md:3`: VERIFIED ("Status: EXECUTED 2026-07-03 (same day"), and commit `8af00e8` is dated 2026-07-03. `business-plan.md:629`: VERIFIED. `business-plan.md:195`: VERIFIED.

**A2.** `PRD-homepage-first-mile.md:14`: VERIFIED. `business-plan.md:57`: VERIFIED. `personas.md:258`: VERIFIED. `BRAND.md:66`: VERIFIED. `website/CLAUDE.md` principle 5: VERIFIED (line 22). `LAUNCH.md:17`: VERIFIED.

**A3.** `LAUNCH.md:13`: VERIFIED. `LAUNCH.md:46`: VERIFIED. `business-plan.md:331`: VERIFIED. `docs/INFRA-AUDIT-2026-07-01.md:55`: VERIFIED. rb 2026-04-20 session: VERIFIED exact. rb 2026-04-21 slack: VERIFIED (several near-duplicate atoms; the exact five-step phrase exists). LinkedIn voice rules LOOP spine phrases: VERIFIED.

**A4.** `INFRA-AUDIT:3`: VERIFIED (quoted fragment matches). `:23`: VERIFIED. `:53`: VERIFIED. `:105`: VERIFIED. commit `e7ec4ac`: VERIFIED ("brains/index.json is the registry, docs point at it" is in the body). commit `32ea8a7`: VERIFIED. `BACKLOG.md:3`: VERIFIED ("single source of truth"). `business-plan.md:209`: VERIFIED. `LAUNCH.md:3`: VERIFIED-APPROX. The line says "This is the ONLY launch/marketing plan... If another doc contradicts this one, this one wins." It does not use the phrase "single source of truth"; the doc's quote marks imply it does. linkedin-post skill description "Supabase is source of truth": VERIFIED (skill listing).

**A5.** `INFRA-AUDIT:15`: VERIFIED. `:47-59` "seven requirements questioned (R1-R7), five declared invalid": VERIFIED-APPROX. Four are literally "requirement invalid" (R1, R2, R4, R6). R3 is "premature", R5 is "freeze", R7 is "the docs lie". Say four, or say "five rejected". rb 2026-09-29 session "Retire the input, rewrite the job...": UNSUPPORTED. Six searches (phrase, keyword, session-filtered) returned nothing with that date or wording. rb 2026-09-21 session: VERIFIED exact. rb 2026-10-12 session "a review job with no input is pure ritual cost": UNSUPPORTED. Nearest match is rb 2026-09-21 session ("A human-in-the-loop grading column that nobody fills is a dead feature masquerading as a feedback loop") and rb 2026-09-21 session ("An automated review job can stop producing output without anyone noticing").

**A6.** prefs: UNVERIFIABLE-BY-ME. rb 2026-03-12 slack: VERIFIED exact ("Rob established a new standard: bot must only provide..."). Voice rules "NEVER fabricate stories, statistics, or quotes. NEVER invent fake dialogue.": VERIFIED. `scripts/auto_build_config.py:76`: VERIFIED. `IMPROVEMENTS.md:70`: VERIFIED. `CLAUDE.md:212`: VERIFIED. `SPEC-synthesis-grounding.md:47-49`: VERIFIED. `BRAND.md:358`: VERIFIED. `skills/brain-foundation/SKILL.md:67`: VERIFIED.

**A7.** `CLAUDE.md:213`: VERIFIED. commit `3dfcdde`: VERIFIED. commit `4868b12`: VERIFIED. commit `84175bb`: VERIFIED ("(Rob-approved)" is in the subject line). `PLAN-brain-depth.md:113`: VERIFIED. `scripts/build-brain.py:1078`: VERIFIED. `PRD-homepage-first-mile.md:74`: VERIFIED.

**A8.** `SPEC-synthesis-grounding.md:103`: VERIFIED. `CLAUDE.md` transcript guardrail: VERIFIED (line 241). `auto_build_config.py:80`: VERIFIED. `website/app/api/skill/route.ts:60`: VERIFIED. commit `e7ec4ac` rate limiter: VERIFIED. commit `11b899d`: VERIFIED. See section 3 for why this receipt cuts against A9.

**A9.** `LAUNCH.md:208`: VERIFIED. `CLAUDE.md` publish-qa-scores policy: VERIFIED (line 459). `BRAND.md:369`: VERIFIED. `business-plan.md:693`: VERIFIED. `PLAN-brain-depth.md:127-128`: VERIFIED. `BRAND.md:38`: VERIFIED.

**A10.** prefs: UNVERIFIABLE-BY-ME. `CLAUDE.md:337`: VERIFIED. `HANDOFF-brain-qa.md:83-88`: VERIFIED. commit `1669e3b`: VERIFIED. `CLAUDE.md` eval re-judge: VERIFIED.

**A11.** `HANDOFF-brain-qa.md:62`: VERIFIED. `CLAUDE.md` ship-gate: VERIFIED (line 458). Pillars "Threshold: post 40+...": VERIFIED. rb 2026-04-28 session: VERIFIED exact. `business-plan.md:671`: VERIFIED.

**A12.** commit `1669e3b` both quotes: VERIFIED. `SPEC:124`: VERIFIED. `PLAN-brain-depth.md:99-103`: VERIFIED. Voice rules 2026-09-19 CHECK constraint and "'not captured' and 'seen by nobody'": VERIFIED. `CLAUDE.md` "Never strip quotes...": VERIFIED (line 276).

**A13.** prefs: UNVERIFIABLE-BY-ME. rb 2026-05-25 session: VERIFIED exact. rb 2026-04-28 session: VERIFIED exact. rb 2026-10-12 session "forced-decision date (do, defer with date, or drop)": UNSUPPORTED. Nearest is rb 2026-03-31 slack ("Past Go/No-Go date... Decision: park, not kill") and rb 2026-09-21 session ("Recommendation systems need a default action on Nth repeat, not a louder flag"). rb 2026-09-29 session "One blocker should produce one alert... trains the reader to skim past action": UNSUPPORTED. Nearest is rb 2026-07-29 session ("Consolidating 4-6 daily scraper alerts into a single root-cause escalation eliminates noise").

**A14.** `INFRA-AUDIT:117-125`: VERIFIED. commit `e7ec4ac` "10-20x runtime COGS cut": VERIFIED (subject line). `CLAUDE.md` "cached by default (cost guard)": VERIFIED (line 458). `CLAUDE.md` "~1.67× cost": VERIFIED (line 457). `PRD-sonnet-4-6-upgrade.md:35`: VERIFIED.

**A15.** `business-plan.md:69`: VERIFIED. `:185`: VERIFIED. `BRAND.md:370`: VERIFIED. rb 2026-03-01 linkedin: VERIFIED as an atom, but note the atom text is a third-person bot paraphrase ("Rob believes in the Claude ecosystem..."), not Rob's sentence. `CLAUDE.md` MCP design: VERIFIED.

**A16.** `HANDOFF-brain-qa.md:30`: VERIFIED. `PLAN-brain-depth.md:11`: VERIFIED. commit (#62) = `7f7a7be`: VERIFIED ("anti-vindication rubric" and "the id the panel said was laundered out" are both in the body). Voice rules "Tell on yourself...": VERIFIED.

**A17.** `LAUNCH.md:98`: VERIFIED. `:105`: VERIFIED. commit `de11b83`: VERIFIED. commit `e7ec4ac` pricing: VERIFIED. `INFRA-AUDIT:59`: VERIFIED.

### Part B

**B1.** prefs: UNVERIFIABLE-BY-ME. Voice rules both quotes: VERIFIED. Playbook "every one opens on a number...": VERIFIED. rb 2026-05-29 slack: VERIFIED exact. `BRAND.md:69-70`: VERIFIED. `BRAND.md:357`: VERIFIED.

**B2.** prefs: UNVERIFIABLE-BY-ME. Voice rules "Hook in the first line. Earn the click.": VERIFIED. `BRAND.md:160-165`: VERIFIED. `BRAND.md:33`: VERIFIED.

**B3.** prefs: UNVERIFIABLE-BY-ME. Voice rules: VERIFIED. `BRAND.md:83`: VERIFIED. `BRAND.md:356`: VERIFIED.

**B4.** prefs: UNVERIFIABLE-BY-ME. Voice rules Anti-Rob items: VERIFIED. "If a draft is generic, kill it..." and "Could anyone else have written this?": VERIFIED. `BRAND.md:114-135`: VERIFIED. `skills/brain-foundation/SKILL.md:84`: VERIFIED.

**B5.** prefs: UNVERIFIABLE-BY-ME. Voice rules both: VERIFIED. Playbook contrarian 12,227 and "2.5x the account average on reach": VERIFIED. rb 2026-04-11 slack: VERIFIED exact.

**B6.** Voice rules, all four quotes: VERIFIED. rb 2026-04-20 slack: VERIFIED. rb 2026-04-16 session: VERIFIED exact.

**B7.** Voice rules CTA data block: VERIFIED verbatim. Engagement-bait: VERIFIED. `BRAND.md:164`: VERIFIED. One MISREAD by omission: the same voice rules say "End with a clear takeaway or an honest question (NOT a 'what do you think?' CTA)". An honest question is an allowed close. B7's "No CTA, no engagement bait, no closing offer" and Part D's would_not_say "'What do you think?' as a closer" are fine, but B7's title "The takeaway is the close" drops the sanctioned honest-question close.

**B8.** rb 2026-05-10 session: VERIFIED exact. Voice rules both: VERIFIED. Playbook "Length is not a cost...": VERIFIED. `PRD-homepage-first-mile.md:25`: VERIFIED ("≤800 visible words"; the executed page came in at ~356 per line 3).

**B9.** rb 2026-03-29 linkedin: VERIFIED. The atom mixes a verbatim-looking opener with a bot summary ("Rob built a system using Claude Cowork + Supabase that ingested 76 posts..."), so "Rob's own post" is right for the source but the text as cited is partly paraphrase. rb 2026-04-16 session: VERIFIED. linkedin-post skill 5-phase line: VERIFIED (skill listing).

**B10.** rb 2026-04-25 slack, both atoms: VERIFIED exact. prefs: UNVERIFIABLE-BY-ME. Voice rules "Performative humility": VERIFIED.

**B11.** prefs: UNVERIFIABLE-BY-ME. `BRAND.md:38`: VERIFIED. `website/CLAUDE.md` "They arrived to evaluate...": VERIFIED (line 8). Voice rules "Preacher mode": VERIFIED.

**B12.** prefs (both): UNVERIFIABLE-BY-ME. Voice rules "Playful is seasoning...": VERIFIED; playful 1,244 imp and "a quarter of baseline": VERIFIED (playbook tone table). `BRAND.md:46`: VERIFIED.

### Part C

**C1.** `INFRA-AUDIT:25`: VERIFIED. `LAUNCH.md:149`: VERIFIED.
**C2.** rb 2026-05-11 session: VERIFIED exact. Voice rules 2026-10-30 "stories 13 (3 approved, 10 draft, 0 deployed)" and "never been deployed, five months running": VERIFIED. "broken for 26 days by a silent scraper failure. That is a LOOP post waiting to happen": VERIFIED. Pillars "0.68/week": VERIFIED.
**C3.** rb 2026-04-01 session: VERIFIED exact. rb 2026-05-08: VERIFIED.
**C4.** commits `b9eb7f4`, `74efc52`: VERIFIED, with a caveat. Both are authored "Claude" (not Rob) with a Claude-Session trailer. The body of `b9eb7f4` says "The originally-suggested $30M figure is flagged HIGH-severity ungrounded", so someone suggested $30M, but the record does not say it was Rob. commit `1669e3b` "restated in corpus units...": VERIFIED. "two weeks later": `b9eb7f4` is 2026-06-22, `1669e3b` is 2026-07-03. Eleven days. VERIFIED-APPROX.
**C5.** `IMPROVEMENTS.md:102`: VERIFIED, still unchecked. `business-plan.md:627`: VERIFIED.

### Part D hard_lessons receipts

1. "The infrastructure is optimized for supply..." `INFRA-AUDIT:25`: VERIFIED.
2. "Rob has not graded any reviewed thread to date..." rb 2026-05-11 session: VERIFIED exact.
3. "Scrubbing those to clear the gate was making brains WORSE" commit `1669e3b`: VERIFIED.

### Preamble provenance claim

"Of 66 commits on this repo, 54 are authored as Rob Gabel": VERIFIED (`git log`: 54 Rob Gabel, 12 Claude, 66 total at the time the doc was written; now 67 with the doc's own commit `e487835`). "nearly all bodies carry Co-Authored-By: Claude": VERIFIED. 49 of 55 Rob-authored commits carry a Co-Authored-By trailer; the 6 without are 5 merge commits plus the doc's own commit. Extra evidence the doc did not use: 27 of the 54 Rob-authored commit subjects contain an em-dash, which the doc says Rob never uses. The commit messages are Claude's prose under Rob's git identity. The 12 "Claude"-authored commits are the LAUNCH.md and PRD-1..8 launch-prep work (`9328b59`, `0aa0acf`, `891c655`, `db7354d`) and the two Jesse bio commits. So LAUNCH.md and PRD-8 are Claude-authored in git as well as in prose.

---

## 2. Provenance audit (HIGH tier check)

The tier table says HIGH requires Rob's own words or an explicit approved/chose/vetoed record. Checking each HIGH:

| Principle | Rob's-own-words or explicit decision receipt? | Verdict |
|---|---|---|
| A1 | prefs only (unverifiable). rb 05-08 is the bot reviewing itself. PRD and business-plan are Claude-drafted. | Downgrade to MED. Behavior contradicts (section 3). |
| A2 | None. PRD is "Authored: Belsky-brain session" (`PRD-homepage-first-mile.md:7`). personas.md:3 says "Source: brainstorm session with Rob", which is the closest thing. BRAND, website/CLAUDE.md, LAUNCH all Claude-drafted. | Downgrade to MED. Rob executed it by merging #46, which is exactly the MED definition. |
| A3 | LAUNCH.md is Claude-authored in git. rb atoms are bot paraphrases. The LOOP pillar is Rob's public franchise, which is the strongest piece. | MED-HIGH. |
| A4 | `INFRA-AUDIT:3` quotes Rob approving ("auth: park, dedicated Supabase stays free-tier, new model family, drop cross_connections"). That quote is about four specific cuts, not about "one source of truth" as a principle. Deletions were merged by Rob. | MED-HIGH. The "(Rob approved the audit)" label is accurate but the approval is narrower than the principle. |
| A6 | rb 2026-03-12 slack: "Rob established a new standard". Explicit. | HIGH holds. |
| A7 | commit `84175bb` "(Rob-approved)" in a Rob-identity commit; `4868b12` "Vetoed on review". | HIGH holds. |
| A9 | `LAUNCH.md:208` "CHOSEN (Rob, 2026-07-06)". Explicit attribution, though written by Claude in commit `db7354d`. | HIGH holds, with the caveat that the record of the decision is Claude's. |
| A10 | prefs + Claude docs. rb 2026-04-21 slack "#investment-research channel evals prioritize thesis structure and bull/bear case evaluation" supports but is a bot summary. | MED-HIGH. |
| A11 | "Rob's Edge" is a Rob-named construct (rb 2026-03-28 slack uses it with a 5/5 and a separate 2/5 defensibility score). The 50-point rubric is in Rob's own 2026-03-29 post. | HIGH holds, barely. |
| A13 | prefs + three bot self-reviews telling the bot to force decisions on Rob. These show Rob does not decide unprompted, not that Rob forces decisions. | Downgrade to MED and reframe (see section 3). |
| A16 | HANDOFF "Decisions already made" is Claude-drafted. Voice rules are Claude-rebuilt from data. Commit is Rob-identity. | MED-HIGH. |
| B1-B11 | Voice rules are "auto-rebuilt... from live Supabase" (Claude-written, data-derived from Rob's 99 posts). The slack atoms (05-29 "Rob's voice guidelines for this post require: no em-dashes...", 04-25 "Rob advocates for removing sycophantic hedging", 04-11 "Rob's voice patterns...") are bot records of Rob's instructions. B9 cites Rob's own post. | HIGH is defensible for B1, B4, B5, B6, B9, B10 (Rob instruction on record). B2, B3, B7, B8, B11 rest on prefs + data-derived rules: MED-HIGH unless prefs confirms. |
| C1, C2, C3 | Self-flagged by bot reviews and Claude audits, not by Rob. "self-flagged" means the system flagged it, not Rob. | Keep HIGH as factual record; relabel "system-flagged". |

Net: 11 of the 20 HIGH ratings should drop to MED or MED-HIGH under the document's own rules. The doc's strongest claims (A6, A7, A9, A11, B1, B4, B5, B6, B9, B10) survive.

---

## 3. Contradiction hunt

I searched for the opposite of 10 principles. Findings, strongest first.

**A1 / A3 / C1 (ship, real usage first).** The repo has been dormant since 2026-07-22 (`git log`: `0375975` 2026-07-22, then nothing until the doc commit on 2026-11-06). `SITE_PASSWORD` is still the gate (`website/middleware.ts:29`). The go-public P0 items are still unchecked (`LAUNCH.md:28-30`). The beta tracking table is empty (`LAUNCH.md:168-171`). The ask in `LAUNCH.md:149` ("nobody has been asked") was written 2026-07-04 and is still true four months later. Meanwhile rob-brain shows the pattern on a smaller product: `rb 2026-05-29 slack` "Rob built Highway 4 Events software for himself and launched it last Friday, achieving 100 visitors and 65 email subscribers in the first week." So Rob can ship in a week when the product is for himself. BrainsFor, which needs other people, has not been opened in seven months. A1 is a stated preference that the record contradicts on this project. The doc should say that plainly in A1, not only in C1.

**A5 (automate last).** The repo shows the reverse order for three months. `doc-refresh-log.md:3-27` and the eleven earlier runs (lines 31-633) are a nightly automation that patched counts into three prose docs. Run 9 (`doc-refresh-log.md:110`) and run 11 (`:70`) both flagged "zero drift... consider weekly cadence" and it kept running nightly. A pre-commit hook, a sync script and a memory file were added to defend it (`INFRA-AUDIT:53`). The `enrich-connections` pg_cron job still runs nightly (`CLAUDE.md:131`). `rb 2026-04-20 slack`: "Rob is designing a travel alerts system using daily cron jobs." The five-step pass is a July 2026 correction applied once, by Claude, approved by Rob. "Automate last" is what he learned, not what he does by default. Rate A5 MED and say it is a learned correction.

**A9 (publish all scores raw, including the low ones).** commit `11b899d` (cited under A8 as a virtue) holds the public elon-musk pill at 63 while the newest panel scored it 58. commit `7f7a7be` repeats it: "public QA pill left at 63 per the interim-renovation guard (do not publish a mid-reno dip)" after a re-panel of 62. That is a judgment call about what counts as a real score, but it is literally choosing not to publish a lower number for the landing-page brain. The doc should carry this as the tension inside A9, not file it under A8 as fail-soft.

**A6 (never fabricate) and the live catalog.** The principle is a learned rule, and the learning was expensive. yann-lecun shipped live with 140 of 197 quotes LLM-fabricated (`IMPROVEMENTS.md:70`). Synthesis was 2% grounded for elon-musk and jensen-huang (`SPEC-synthesis-grounding.md:5-6`). Deep-research atoms carried LLM-guessed source_refs across the fleet (`CLAUDE.md` 2026-07-03 lessons). All of those brains were public on brainsforagents.com while that was true. The three-layer defense landed 2026-05-25 (PR #23). A6 should state the date it became true in the pipeline and that it was discovered by audit, not designed in.

**B4 (banned words) vs. the brand's own docs.** `BRAND.md:118` and `:366` ban "AI clone". `BRAND.md:155` offers "Who should we clone next?" as a headline pattern. `business-plan.md:260`: "I cloned Scott Belsky's brain and I'm selling it for $29." `business-plan.md:280`: "Every person whose brain you clone..." The banned list is not enforced in the docs Rob merged. Also, 18 em-dashes in `website/lib/hero-demos.ts` and 4 in `website/app/pricing/page.tsx` ship on the public site today. The "no em-dash" rule is a rule for Rob's LinkedIn voice; it is not applied to product copy he approves.

**B7 (no CTA).** The marketing docs plan CTAs everywhere: `LAUNCH.md:185` "All of it ends with the beta CTA", `business-plan.md:292` "every piece sells the product with a CTA", `BRAND.md:176-204` five persona CTAs, `BRAND.md:341` atom-drop CTA. The no-CTA rule is measured on Rob's personal-brand posts (n=97) and is correct there. The doc should scope B7 to personal-voice posts. Part D's does_not_believe "That a CTA helps" is overbroad as written.

**A13 (force the decision).** All three rob-brain receipts are the bot critiquing itself for not forcing Rob. The record of Rob's own deciding is mixed: `rb 2026-04-28 slack` "Rob is deferring a decision on whether BrainsForFree should consolidate skills pending an architecture review"; `rb 2026-05-11 session` "at least 8 items past Go/No-Go"; `rb 2026-09-21 session` four channels got identical kill recommendations across four monthly triages and none were archived; `rb 2026-03-31 slack` "Past Go/No-Go date... Decision: park, not kill." On the other side, `LAUNCH.md:205-208` shows a real decision made in two days. The honest framing: Rob wants a default proposed because he knows he defers. A synthetic Rob should propose defaults AND know that the human version lets Go/No-Go dates lapse.

**A15 (never lock to one platform).** The entire stack is Claude-shaped: skills are `SKILL.md` files, the registry doc is `CLAUDE.md`, `.mcp.json` hardcodes `/Users/robgabel/...` and `/opt/homebrew/bin/node`, and the only install path the beta serves is "Claude/Cursor session" (`LAUNCH.md:15`). `rb 2026-03-01 linkedin`: "keeps coming back to Claude." Portability is a brand claim (`BRAND.md:106`), not a tested property. The doc already quotes that atom under A15 as support; it reads better as the tension.

**A14 (cost is a design input).** For about three months every `/api/skill` call sent 150-220K tokens uncached at ~$0.45-0.66 per call (`INFRA-AUDIT:49`, `:119`). The behavioral eval was specced at ~$1 and cost ~$14 (`CLAUDE.md`, eval harness "Cost reality"). ~$600 of brain builds (26 × ~$23) preceded the first user. Cost discipline is real after 2026-07-03 and absent before it. MED is the right rating; the doc has it at MED. Fine, but say when it started.

**A16 (sanitized is a defect) vs. Part D.** The doc applies the rubric to Rob and finds the corpus thin on his own costs. Correct. But HANDOFF-brain-qa.md says the cure for a sanitized corpus is to go mine failure-heavy sources (`HANDOFF-brain-qa.md:99`, `:102`), and the doc did not: no search for Rob's Tubular exit, LowerMyBills, A.T. Kearney, or the Spotter role was attempted (voice rules "Identity" block lists all of these). The three hard lessons are all about BrainsFor and PAOS, products that are months old.

**A4 (one source of truth).** No contradiction found after July. Before July, four docs restated the registry (`INFRA-AUDIT:39`). Clean now.

---

## 4. Missing principles

Read for this section: BRAND.md, LAUNCH.md, INFRA-AUDIT, HANDOFF-brain-qa.md, naming-exploration.md (head), personas.md (head), the three LinkedIn context keys, and 22 rob-brain queries on hiring, delegation, memory, naming, pricing, investing, time, tools, bureaucracy, distribution and first-customer tests. Hiring/teams and time management returned nothing usable (only newsletter atoms from Belsky and session summaries about content cadence). Proposals, with the doc's own tiers:

**M1. Every bet gets a Go/No-Go date and a kill criterion. MED-HIGH.** `rb 2026-04-18 slack`: "go/no-go decision target of 2026-05-02." `rb 2026-04-24 slack`: "MarkItDown integration has a Go/No-Go decision date of 2026-05-07." `rb 2026-03-31 slack`: "Past Go/No-Go date (Mar 30)... Decision: park, not kill." `IMPROVEMENTS.md:31`: "Kill criterion: <10 Pro subscribers within 90 days of launch → pivot." `rb 2026-03-28 slack`: an opportunity scored on Edge 5/5, timing 4/5, defensibility 2/5 "(concern)". This is distinct from A11 (score it) because it adds a clock and a pre-committed exit. The matching tension: `rb 2026-05-11 session` lists eight items past their date.

**M2. Auto-execute when the preconditions are met; confirm, don't ask. MED.** `rb 2026-04-13 session`: "When the bot identifies a high-confidence next action with all preconditions met... the default should be auto-execute with confirmation, not surface-and-wait." `rb 2026-06-08 session`: convert captures into "a smallest-viable-next-action with a definition of done." `rb 2026-05-08 session` on remediation: "proposals must convert to paos_improvements rows that block on action, not stay in markdown." This is the delegation-to-agents principle the doc lacks. A13 covers "propose"; this covers "then do it."

**M3. Silence must never look like health. Missing and zero are different values. MED-HIGH.** The doc buries this inside A12. It deserves its own entry because it recurs across systems: voice rules 2026-09-19 (DB CHECK so a zero write throws), `rb 2026-09-21 session` ("the absence of a report looks identical to a quiet week... a 14-week gap... while a separately-named health-check job kept posting"), `rb 2026-09-21 session` ("Self-scoring without external calibration drifts, and the drift is invisible because the scores keep getting written"), `rb 2026-08-26 session` (two triage cycles "marked... as 'processed' despite zero fixes, creating false closure"), and the playbook root-cause note ("Three nightly syncs reported 'corpus average unchanged,' which read as stable but actually meant blind").

**M4. Build the engine once; spawn surfaces as config. MED.** `INFRA-AUDIT:17` "the engine + local-sites strategy proven by hwy4-events → thisweekineugene". `:85` "exactly the hwy4 'frozen, tested core' pattern." `:87` "Sister sites as config, not deployments... A `sites.ts` map keyed by host." `:41` marginal cost of a sister site "~$0 (config entry + DNS)". This is an architecture belief that A4 does not capture and that shows up in two products.

**M5. Steal the pattern before you adopt the tool. Compare, then pick one. MED.** `rb 2026-04-15 slack`: "Rob evaluated 6-7 alternative Google Flights MCP server options and selected 'fli'." `rb 2026-04-28 slack`: "monitoring Impeccable 3's Live Mode implementation as a potential adoption pattern." `rb 2026-05-08 slack`: plans to graft BrainsFor brains into gstack roles rather than adopt gstack whole. `business-plan.md:106` and `CLAUDE.md` Skill Architecture v5: the foundation-skill pattern lifted from Impeccable. The decision frame "adopt / steal pattern / ignore" in `rb 2026-04-28 session` is the vocabulary. The tension: `rb 2026-05-08 session` says he explores instead of prototyping.

**M6. The receipt is the fix. Don't write the lesson until the system is repaired. MED.** Voice rules, LOOP irony note: "Do not write it until the scraper is actually fixed; the receipt is the fix." This is a writing rule that B6 does not contain and that governs when a personal story is allowed. Note the human cost: the scraper is still blocked on Rob as of 2026-11-05 (playbook header), so the post has been unwritable for two months.

**M7. Never reshare. Rewrite the take as an original. HIGH (data rule).** Playbook: "Reshares: 18 posts, 1,141 avg imp (23% of original reach)... Do not reshare." Voice rules corrected the penalty from 90% to 77% on 2026-09-19 and kept the rule. Small, but it is a hard format rule the doc omits, and it is the kind of thing a synthetic Rob would get wrong.

**M8. Lists without a CTA are the best structure. HIGH (data rule).** Voice rules: "LISTS WITHOUT CTAs are the single best format combo... 8,216 imp / 1.77% ER... a +76% reach lift." Also "Never land at 250." B8 has the length rule but not the list rule.

**M9. First person, in his own name, is the product's edge and its liability. LOW.** `BRAND.md:76` "We say 'Belsky would argue...' not 'Belsky says...' because we're synthesizing, not quoting." `BRAND.md:367` "Never promise the brain 'thinks like' the person." Against that: `skills/brain-foundation/SKILL.md:64` "You ARE the selected thinker. Respond in first person... Never speak about the thinker in third person." The brand guide and the product disagree about impersonation. This belongs in Part C as C6, and it matters for a synthetic Rob more than for any other brain, since Rob is the one person who could consent.

**M10. Business first; personal life is the third leg. MED.** Voice rules LOOP section: "Do NOT turn LOOP into self-help. The thesis is about business + org design FIRST, personal life as the third leg." Personas: "The Builder... Wants: real artifacts, honest costs, what broke." Nothing in Part B says what subjects Rob writes about or refuses to moralize on.

Not found despite searching: anything on hiring, headcount, managing people, or how he allocates his own time. The doc's Part E should list these as absent rather than silent.

---

## 5. Synthetic-Rob seed review (Part D)

**first_principles.** All ten map to verified A-principles. Two phrasing problems. "Disagreement is the product" (Independence beats consensus) has no receipt; the closest is `business-plan.md:288` "the argument about who's right IS the engagement", which is about marketing, not QA. "Silence beats a confident guess" is grounded (`CLAUDE.md:212`). "A 30-minute prototype beats a week of exploring" is grounded (rb 2026-05-08) but, per section 3, is aspirational on this project; a seed that states it as a first principle without the C1 tension will produce a synthetic Rob that is more decisive than the human.

**thinking_patterns.** "IdeaFlow" has no receipt in the doc. It rests on prefs ("Don't prematurely converge", cited in C3) which I cannot verify, plus the existence of the jeremy-utley brain. Partial support: `naming-exploration.md:3` "Target: 300+ candidates, then narrow." Mark as inference. "Both sides": grounded via voice rules and rb 2026-04-21 slack. "Five-step delete pass": grounded, but one-time (section 3, A5). "Receipts": grounded. "Edge score": grounded (rb 2026-04-28, 2026-03-28).

**does_not_believe.** "That more infrastructure is progress": grounded in `INFRA-AUDIT:23-25` but it is Claude's verdict that Rob approved, and his behavior before July was the opposite. "That a confident answer beats an honest 'unverified'": grounded (rb 2026-03-12). "That a CTA helps": overbroad; scope to personal posts (section 3, B7). "That automation should come first": the quote at `INFRA-AUDIT:15` is Musk's, delivered via the elon-musk brain atom 7c5da953; it is a borrowed belief Rob acted on once. "That a sanitized story is a good story": grounded (`HANDOFF-brain-qa.md:30`).

**would_not_say.** Em-dashes: prefs plus rb 2026-05-29 slack; good, with the caveat that he ships em-dash copy on his site (section 3). Banned list: grounded (`BRAND.md:114-135`, voice rules). "'It depends' with no lean": prefs only, unverifiable. "'What do you think?' as a closer": grounded (voice rules Anti-Rob), but the entry should not imply he never ends on a question; the rules allow an honest one.

**hard_lessons against the rubric** (must name a real, corpus-grounded cost):

1. "I built a factory before I had a customer." Cost named: three months, zero external users, "dumbest requirement". Grounded (`INFRA-AUDIT:25`, `LAUNCH.md:149`). Passes. But the "change" field overclaims: "Catalog freeze, 10-beta-user gate, delete pass." The delete pass happened (`e7ec4ac`). The 10-user gate was written down. The catalog freeze was a recommendation marked "discipline" (`INFRA-AUDIT:143`, "Still open" at `:12`). And the cost has grown: it is now seven months and zero users, and the repo has been idle since July 22. The lesson is unresolved, which by A16's logic is the more honest entry.

2. "I let my own feedback loop go dark while preaching loops." Cost named: 26+ days blind, misdiagnosed twice, 50+ ungraded reviews, 13 undeployed stories. All grounded (rb 2026-05-11; voice rules; playbook "misdiagnosed twice"). Passes. Two corrections. First, "26+ days" is stale: the playbook header of 2026-11-05 says the last scrape is 48 days old, the last post 53 days, and the fix is "Blocked on Rob: sign Chrome into LinkedIn as robgabel@gmail.com." So the loop is still dark and the "change" (DB fix, one-blocker-one-alert) did not close it; the DB fix only made the blindness honest. Second, the "one-blocker-one-alert rule" is attributed to the unsupported 2026-09-29 atom; use rb 2026-07-29 session instead or drop it.

3. "I let a verifier scrub true facts to clear a gate." Cost named: Elon's $100M / $44B figures stripped from a public brain. Partly overstated. commit `6e8c2bb` (#42, 2026-06-23) says in its own body: "not yet re-exported into the shipped pack / Explorer (the live pack still shows the old figures until a re-export)." commit `1669e3b` restored them 2026-07-03. So the figures were stripped from `brain.json` in the repo for eleven days and the score moved 47 to 64 on a worse synthesis; it is not established that the public pack ever lost them. The real cost is "a gate I built rewarded making the brain worse, and I merged it." That is a stronger lesson than the one written, and it is true. Also note the actor: the scrub was authored by Claude with Rob's merge, which the first-person framing hides.

All three lessons are about systems that are under a year old. Per A16 and HANDOFF-brain-qa.md:102, the correct next step is to mine the failure-heavy sources (Tubular, LowerMyBills, the Spotter role), not to accept thinness as the answer.

---

## 6. Verdict

### (a) Principle table

| # | Grade | One-line reason |
|---|---|---|
| A1 | WEAK | Receipts check out, but behavior on this product contradicts it (repo idle since 2026-07-22, site still gated); only prefs is Rob's voice. |
| A2 | CONFIRMED (as MED) | Every receipt verified; all Claude-drafted artifacts Rob merged, so MED not HIGH. |
| A3 | CONFIRMED (as MED-HIGH) | LOOP pillar is Rob's; LAUNCH.md is Claude-authored in git; zero loops actually completed on BrainsFor. |
| A4 | CONFIRMED | Approval quote at INFRA:3 is narrower than the principle; deletions were merged. LAUNCH.md:3 quote is approximate. |
| A5 | WEAK | Two of three rb receipts unsupported; repo shows automate-first for three months before one delete pass. |
| A6 | CONFIRMED | Strongest principle; explicit Rob standard (rb 2026-03-12). Add the date the pipeline actually enforced it. |
| A7 | CONFIRMED | Explicit Rob-approved and vetoed verdicts on record. |
| A8 | CONFIRMED (MED) | Receipts verified; 11b899d belongs under A9 as a tension. |
| A9 | CONFIRMED | Rob chose Option C; but the interim-dip guard holds a lower score back, which the doc should carry. |
| A10 | CONFIRMED (MED-HIGH) | Verified; rests on prefs plus Claude design docs; same-base-model judges acknowledged at HANDOFF:85. |
| A11 | CONFIRMED | Rob's Edge and the 50-point rubric are Rob's constructs. |
| A12 | CONFIRMED | All receipts verified, including the CHECK-constraint story. |
| A13 | MISATTRIBUTED | Receipts are the bot's self-critique; two of four rb receipts unsupported. Reframe as "wants a default proposed because he defers." |
| A14 | CONFIRMED (MED) | Verified; true only after 2026-07-03. |
| A15 | WEAK | Brand claim; the only tested platform is Claude; rb 2026-03-01 is a paraphrase atom. |
| A16 | CONFIRMED (MED-HIGH) | Verified; applied to Rob's own seed only half-way. |
| A17 | CONFIRMED (MED-HIGH) | Verified. |
| B1 | CONFIRMED | Rob instruction on record (rb 2026-05-29) plus data rules. |
| B2 | CONFIRMED (MED-HIGH) | Prefs plus Claude-drafted brand guide; voice rule verified. |
| B3 | CONFIRMED (MED-HIGH) | Same. |
| B4 | CONFIRMED | Rob instruction on record; brand docs violate it ("clone", em-dashes in shipped copy). |
| B5 | CONFIRMED | Data-backed and Rob-stated. |
| B6 | CONFIRMED | Verified; rb 2026-04-20 slack is a recorded Rob decision. |
| B7 | CONFIRMED, scope it | Data is verbatim; applies to personal posts, not marketing; honest-question close is allowed. |
| B8 | CONFIRMED | Rob's strategic shift on record (rb 2026-05-10). |
| B9 | CONFIRMED | Rob's own post, partly paraphrased in the atom. |
| B10 | CONFIRMED | Two Rob instructions on record (rb 2026-04-25). |
| B11 | CONFIRMED (MED-HIGH) | Prefs plus Claude docs; voice rule verified. |
| B12 | CONFIRMED (MED) | Data rule verified; prefs unverifiable. |
| C1 | CONFIRMED | Verified and worse than stated (now seven months). |
| C2 | CONFIRMED | Verified and still open as of 2026-11-05. |
| C3 | CONFIRMED | Verified. |
| C4 | WEAK | Commits are Claude-authored; "two weeks" is eleven days; who suggested $30M is not on record. |
| C5 | CONFIRMED | Verified, still unchecked. |

### (b) Five corrections the author must make

1. **Re-tier against the doc's own definitions.** A1, A2, A13 drop to MED; A3, A4, A10, A16, B2, B3, B7, B8, B11 drop to MED-HIGH unless a prefs line or a Rob-instruction atom is added. "HIGH" currently means "I found many Claude-drafted receipts," which the preamble itself warns against.

2. **Remove or replace the four unsupported rob-brain receipts** (rb 2026-09-29 session ×2, rb 2026-10-12 session ×2) in A5 and A13 and in hard_lesson 2's "change" field. Substitutes that exist: rb 2026-09-21 session (grading column nobody fills; default action on Nth repeat), rb 2026-07-29 session (consolidate alerts to one root-cause escalation), rb 2026-08-26 session (false closure).

3. **Move the behavior contradictions into the principles they contradict.** A1 needs the idle-since-July fact. A5 needs the doc-refresh-log history. A9 needs 11b899d. B7 needs the marketing-CTA scope. B4 needs the "clone"/em-dash violations. Part C is good, but a synthetic Rob reads Part A as the rules and Part C as footnotes.

4. **Fix the three hard lessons.** (1) is unresolved, not fixed; say so. (2) is still dark as of 2026-11-05 and the "change" did not close it. (3) overstates the public cost (the live pack may never have lost the figures, per `6e8c2bb`'s own note) and hides that Claude did the scrubbing and Rob merged it. Then do what A16 says: mine Tubular, LowerMyBills, Spotter for lessons with real cost before accepting thinness.

5. **Add the missing principles with the strongest receipts:** M1 (Go/No-Go date plus kill criterion), M3 (silence must never look like health), M2 (auto-execute with confirmation), M7/M8 (no reshares; lists without CTAs), and add M9 (first-person impersonation vs. BRAND.md:76/367) as C6.

### (c) Confidence that this document lets a model answer like Rob: 58/100

Reasoning. On **writing**, the document is strong: the B-series is data-backed, verbatim where it matters (CTA tax, length buckets, hook table), and anchored by recorded Rob instructions (no em-dashes, no hedging, "smirk"). A model following Part B would produce posts that pass the "could anyone else have written this" test more often than not. I would put the writing half alone at about 75.

On **building**, the document describes the July-2026 Rob who had just run a delete pass, not the April-to-June Rob who built 26 brains, 47 scripts and a five-tier QA regime for zero users, and not the August-to-November Rob who stopped committing with the site still gated. The principles are what he says and what he approved once; the record shows the opposite reflex most of the time. A synthetic Rob seeded from Part A would be more disciplined, more decisive and more cost-aware than the human, which is the "convincing impersonation that misrepresents" case the repo's own self-recognition QA warns about (`CLAUDE.md`, Self-Recognition section). Part C partly saves this, and the doc deserves credit for writing it. The building half alone is about 45.

Two structural gaps hold the overall number down. First, almost no verbatim Rob exists in the evidence base: the rob-brain atoms are bot paraphrases, the repo prose is Claude's, the voice rules are Claude-rebuilt from data, and the 99 original posts were never read. Second, the hard lessons are thin and about products younger than a year; a synthetic Rob with no Tubular cost in it cannot "tell on himself" the way B6 says he does. Fix corrections 1 through 5 and read the 99 posts, and I would expect 70 or above.
