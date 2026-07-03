# BrainsFor Infrastructure Audit — 2026-07-01

> **EXECUTION STATUS (2026-07-03).** Rob approved the plan ("auth: park, dedicated Supabase stays free-tier, new model family, drop cross_connections"). Shipped:
> - **Move 1 (runtime COGS)** ✅ — `/api/skill` + `/api/board` now send the synthesis slice of brain-context.md (`loadBrainContextLite`, 20-63KB vs 590-890KB — a 93-98% cut) + question-retrieved atoms (now with `source_date` for /evolve). Models upgraded `claude-sonnet-4-6` → `claude-sonnet-5` with `thinking: {type: "disabled"}` (Sonnet 5 defaults adaptive-ON when omitted); board's `temperature: 1` removed. Prompt caching intentionally skipped: the mode-collapse ordering puts the question at the top of the system prompt, so a cache prefix would never hit — trimming captures the savings without regressing Layer 1.
> - **Move 2 (prod DB)** ✅ *already shipped before this audit executed* — `brain-atoms-db.ts` fetches static pack JSON from the site's own CDN; the dedicated Supabase project is auth-only (free tier, parked per Rob).
> - **R2 correction** — no live 200K-window bug: Sonnet 4.6 has a native 1M window (verified against prod). The cost finding stood.
> - **Move 3 (un-track public/brains)** ⛔ BLOCKED on a Vercel dashboard toggle: prebuild sync is a NO-OP on Vercel (`../brains` unavailable — Root Directory is `website/`). Enable "Include source files outside of the Root Directory" in Vercel project settings, verify a preview deploy regenerates `public/brains`, THEN gitignore + `git rm -r --cached website/public/brains`.
> - **Move 4 (ship gate)** ✅ — `promote-brain.py --persona-gate` now defaults ON (`--no-persona-gate` to skip).
> - **Move 7 (doc sync)** ✅ — parent CLAUDE.md table replaced with an index.json pointer; `sync-claude-md-brains.py`, `install-hooks.sh`, `hooks/pre-commit` deleted (the installed git hook symlink was already dangling); auto-build no longer invokes the sync.
> - **Move 8 (deletions)** ✅ — dead loaders deleted, completed migrations/backfills archived to `scripts/archive/`; `cross_connections` + legacy `belsky_enrichment_log` dropped in Supabase (verified 0 rows first). NOTE: kara_swisher tables were NOT empty (885/772 rows — live brain data); the May "empty scaffold" flag was stale. Pricing page de-tiered honestly (Pro/API = "Coming soon"); auth had no nav entry points already.
> - **Factory models** ✅ — `DEFAULT_MODEL=claude-sonnet-5`, `SYNTHESIS_MODEL=claude-opus-4-8` (+pricing rows). Watch the first build: Sonnet 5's new tokenizer counts ~30% more tokens; it follows prompts more literally.
> - **Still open:** Moves 5 (catalog freeze — discipline), 6 (multi-tenant `sites.ts`), 9 (shared retrieval lib in the open runtime), 10 (Phase 4 Haiku-first); doc-refresh retargeting to invariant-checker. Side-find worth a look: brene-brown's shipped `original_quote`s are in **Albanian** (auto-caption language leak from the TED source).
> - **Language-leak fix (2026-07-03, same day):** scope turned out to be **103 quotes across 4 brains** (brene-brown 38 + reshma-saujani 23 + peter-attia 21 Albanian; steve-jobs 21 Spanish — all TED/commencement videos where a human-authored foreign caption track beat the English auto-track in `fetch_transcript`'s "first non-generated" pick). Fixed three ways: (1) quotes nulled in Supabase + all 4 packs re-exported + public copies resynced (counts unchanged, scan now 0); (2) both transcript fetchers (`build-brain.py`, `ingest-youtube.py`) now select human-EN → auto-EN → auto-translate-to-EN → skip, verified live against the leak video (old pick: Albanian, new pick: English); (3) `audit-brains.py` gained a deterministic two-sided stopword language check — non-English quotes are excluded from voice coverage and raise an error-level issue. Bonus root-cause find while re-exporting: `export-brain.py` preferred `NEXT_PUBLIC_SUPABASE_URL` (the **paused, non-resolving** auth-only project — its DNS is dead, confirming the free-tier pause) over the factory `SUPABASE_URL`, with `override=True` dotenv loading; exports now prefer the factory project and dotenv fills gaps only.

*Principal-engineer pass using Musk's five-step algorithm: (1) make requirements less dumb, (2) delete the part or process, (3) simplify/optimize, (4) accelerate cycle time, (5) automate. Applied in that order — "most organizations jump straight to step five, automating processes that should never have existed" (elon-musk brain, atom 7c5da953, TED 2017).*

*Grounded in: `business-plan.md` (April 2026), `personas.md`, the June go-public plan (runtime open / factory private / free-in-beta / new clean `brainsforhq/brainsfor` repo), and the engine + local-sites strategy proven by hwy4-events → thisweekineugene (Eugene sister site).*

---

## Verdict

**The factory is the moat and it's genuinely good. The infrastructure problem is accumulation, not construction.** Every layer that was ever built is still running: two Supabase projects, 57+ tables, three copies of every brain pack, 47 scripts (16,487 LOC), a 5-tier QA regime, four documents restating the same registry, and two independent implementations of the same keyword-retrieval algorithm.

Meanwhile the business plan's own critical gap — flagged in April, still true in July — is **zero beta users**. The personas doc stack-ranks "AI Power Users (beta)" as audience #1. The infrastructure is optimized for supply (26 brains, deeper QA) while the binding constraint is demand (launch, 5 beta users, demo quality). That's the dumbest requirement in the system, and it isn't a line of code.

**Target architecture in one sentence:** Factory (private) → **Pack Registry** (the single interface: `brains/index.json` + `pack/` artifacts) → N thin surfaces (website(s), MCP, plugin marketplace, public runtime repo) that all derive from the registry and hold no state of their own.

### Parts count

| Layer | Today | Target |
|---|---|---|
| Supabase projects | 2 (build + prod runtime) | 1 (factory only) |
| Supabase tables | 57+ (26×2 per-brain + metadata/zombies) | ~5 (generic schema, Phase 7) |
| Copies of each pack in git | 2 tracked (+ zip + `.js` twins = 5 copies of the bytes) | 1 (pack/ only; rest generated) |
| Retrieval implementations | 2 (MCP TS + website TS, both keyword) | 1 shared lib (= the open runtime) |
| Tokens sent per `/api/skill` call | ~150–220K (full brain-context.md, no caching) | ~8–12K (synthesis + top-K atoms) |
| Scripts | 47 / 16,487 LOC | ~35 / ~14K LOC (delete + archive) |
| Docs restating the registry | 4 (2× CLAUDE.md, business-plan, IMPROVEMENTS) | 0 (link to index.json) |
| QA tiers acting as gates | ambiguous (ship-gate exists but unwired) | 2 (build gate + promote gate) |
| Marginal cost of a sister site | ~a full stack (if copied like hwy4) | ~$0 (config entry + DNS) |

---

## Step 1 — Question the requirements

**R1. "The runtime needs a database for atoms."** No persona requires it. Atoms are public, static, and already shipped twice in the repo and served as static assets by the same Vercel deployment that queries Supabase for them (`website/lib/brain-atoms-db.ts` → `{slug}_atoms` via anon key, keyword scoring only, silent `[]` fallback). The dedicated prod project (`jefjvgbawmsloerqsgby`) exists because prod once pointed at the wrong DB — a scar, not a requirement. Embeddings and the `search_brain_atoms` RPC were never migrated to it; prod retrieval is lexical. **Verdict: requirement invalid. Runtime should be stateless.**

**R2. "Send the full brain-context.md on every API call."** `loadBrainContext()` reads the whole file untruncated (`website/lib/brain-context.ts:60`); files run 594KB (sun-tzu) to 892KB (brene-brown) — roughly 150–220K tokens — with **no prompt caching** (`cache_control` absent from both routes). The retrieval layer (15 question-relevant atoms) was built precisely so full context isn't needed; today the routes send both. This is also the mode-collapse enemy: the full context leads with the canonical taglines the ANTI-DEFAULT rule then fights. **Verdict: requirement invalid — and probably a live defect: the largest contexts (~220K tokens) likely exceed the 200K standard window on `claude-sonnet-4-6` without the 1M beta header. Verify `/api/skill` on brene-brown/paul-graham/dario-amodei.**

**R3. "Auth, dashboard, and a 3-tier pricing page now."** The go-public decision is free-in-beta; the whole site is password-gated by `middleware.ts` (`SITE_PASSWORD`) except the APIs and `/brains/*`. Yet the deploy carries GitHub OAuth + magic links, a dashboard that says "launching next week", `profiles`/`brain_access` tables, and a pricing page rendering $79/$199 tiers whose CTAs loop back to `/brains` (no Stripe anywhere). **Verdict: requirement premature. Park it; a half-wired storefront costs launch credibility.**

**R4. "Docs must carry the brain inventory."** The registry is duplicated into prose four times and drifts anyway: `business-plan.md` says 19 brains / 6,012 atoms; parent CLAUDE.md says 25–26 / 21,806; `brains/index.json` (truth) says **26 brains (22 live, 4 hidden), 21,805 atoms, 23,387 connections**. A sync script, a pre-commit hook, a nightly doc-refresh skill, and a memory file all exist to defend the duplication — automation of a process that shouldn't exist (that's the Musk atom, verbatim). **Verdict: requirement invalid. One registry; docs link to it.**

**R5. "Keep scaling the catalog and deepening QA."** 26 brains, avg audit 89.8/100, 5 QA tiers (structural, behavioral, numeric, persona panel on Opus, self-recognition) — and 0 users. QA effort should follow usage, not precede it. The ship-gate that matters (numeric + persona) isn't even wired into the pipeline or `promote-brain.py` by default. **Verdict: freeze catalog growth until 5 beta users exist (the plan's own Week-1 metric). Wire the ship gate; run the rest on demand.**

**R6. "A sister surface needs its own infrastructure."** hwy4 needs per-city Supabase + scrapers because its content is live and local. BrainsFor content is **static artifacts**. A sister site (brainsforfree funnel, a thinker microsite, a vertical catalog) is a domain + a config entry + a brain subset. **Verdict: requirement invalid for BrainsFor; multi-tenant one deploy.**

**R7. "Semantic search is shipped."** Docs (IMPROVEMENTS.md 2026-05-20 entry, CLAUDE.md) describe Layer 2 vector retrieval as live. Reality: `brain-atom-retrieval.ts` is pure keyword scoring; `OPENAI_API_KEY` is not in Vercel; the RPC exists only in the build project. **Verdict: the docs lie. Either declare keyword-only (it's carrying the demo fine) or ship vectors deliberately — not the current half-state.**

---

## Step 2 — Delete

| # | Delete | What it removes | Evidence |
|---|---|---|---|
| D1 | **Prod atom reads from Supabase** — serve retrieval from the pack JSON the site already ships (bundle atoms for live brains or fetch own static asset + in-memory cache) | The second Supabase project's 52 atom/connection tables, the manual `migrate-*.py` copy step, the "prod shows atomCount:0" failure class, the silent-`[]` degradation, the embeddings-backfill question | `brain-atoms-db.ts:58-83`, CLAUDE.md migration gotcha |
| D2 | **`website/public/brains/` from git** — `.gitignore` it; `npm prebuild` (`sync-brain-assets.mjs`) already generates it from `brains/*/pack/` | ~85–90MB of tracked duplication (263MB total tracked; brains/ 172MB + website/ 89MB), plus ~7–10MB of permanent git history per future brain | `website/package.json:6` prebuild hook |
| D3 | **`brain-atoms.js` twins from git** (48 tracked) — derived from `brain-atoms.json` at export; generate at prebuild/zip time | ~40MB tracked; one less artifact to drift | export pipeline |
| D4 | **Dead factory scripts** (~800 LOC): `load-to-supabase.py`, `load-via-execsql.py` (only `upload-atoms.py` is called), `migrate-via-api.py`, one of `backfill-source-url{,s}.py`; archive `migrate-proper.py`/`migrate-fix.py` to `scripts/archive/`; mark `build-brain.py` as library-only (it's imported by auto-build, not an entry point) | Source-of-truth confusion; 47 → ~38 scripts | scripts agent inventory |
| D5 | **Zombie DB objects** (factory project): `cross_connections` (0 rows, was 17), empty `kara_swisher_*` scaffolds if still present, legacy `belsky_enrichment_log`, duplicate slug-format rows in `brain_metadata` (59 rows for 26 brains) | Confusion + audit noise | CLAUDE.md flags |
| D6 | **CLAUDE.md table-sync machinery**: replace the auto-generated 26-row table in `~/rob-ai/CLAUDE.md` with 3 lines (count + totals + link to `brains/index.json`), then delete `sync-claude-md-brains.py`, the pre-commit hook, and the doc-refresh prose-patching duty | A script, a hook, a cross-repo commit coupling (brainsfor commits blocked on a *different repo's* file), and the whole drift class | `scripts/hooks/pre-commit` |
| D7 | **Fake pricing tiers + dead UI**: pricing page $79/$199 CTAs, `RequestBrainForm.tsx` (unrendered), dashboard "launching next week" copy — hide behind the free-in-beta message until Stripe is a real decision | Launch-credibility risk; misleading SEO | website agent findings |
| D8 | **`prd-automated-export.md` Phase 3** (edge function + pg_cron + Storage bucket): it automates copying between tiers D1–D3 delete. Keep Phase 1 (`--supabase` direct export) — that's the one legitimate copy step (factory DB → pack) | 4–6 hours of planned work + a new moving part | docs/prd-automated-export.md |
| D9 | **Stale local state**: 3 stale worktrees with orphan zips; canonical checkout at `~/rob-ai/brainsfor` sits behind main (memory already flags it) — either keep it pinned to main via cron `git pull` or stop treating it as canonical | The "which checkout is real" bug class (the `/brain` skill reads it) | memory: canonical-checkout-build-sandbox |

**Explicit non-deletes:** auth *code* (park, don't delete — re-adding at monetization is churn; just unlink from nav), Upstash rate limiting (fix fail-open instead), the eval/persona/self-recognition scripts (demote to diagnostics, don't delete), `rob_atoms`/`rob_connections` (personal graph, different product).

---

## Step 3 — Simplify

**S1. Make the Pack Registry the single seam.** `brains/index.json` + `brains/<slug>/pack/` is already the de-facto artifact store — formalize it: everything (site public dir, zips, MCP, plugin marketplace bundle, the public `brainsforhq/brainsfor` repo, future sister sites) *derives* from it at build time and nothing else holds brain state. This simultaneously solves launch blocker (b) from the go-public plan ("repo-gating ≠ data-gating"): when gating is ever needed, there is exactly one seam to gate (signed URLs on pack assets), and blocker (f) ("MCP needs a hosted atom API") — the site's static pack URLs *are* the hosted atom API; document the URL scheme.

**S2. One retrieval engine, right-sized calls.** Merge the two keyword scorers (MCP `src/tools/search` + `website/lib/brain-atom-retrieval.ts`) into one shared lib that lives in the **open-source runtime** — the public repo becomes the single engine every surface imports, exactly the hwy4 "frozen, tested core" pattern. Then change the API routes to send **synthesis + top-K atoms (~8–12K tokens)** instead of full brain-context.md, and add `cache_control` on whatever static prefix remains. Effect: ~10–20× cost cut per call, faster first token, less tagline-anchoring (the mode-collapse fix gets stronger, not weaker), and the >200K-window defect disappears.

**S3. Sister sites as config, not deployments.** One Next.js app, one Vercel project, N domains. A `sites.ts` map keyed by host: `{ brand, palette, brainSubset, copy, demoDefaults }`. brainsforagents.com = full catalog; brainsforfree.com = beta funnel (today it just 301s); future = thinker microsites or vertical catalogs ("Brains for Founders"). Where hwy4 pays ~$36–47/mo per city (own Supabase + scrapers + Vercel), a BrainsFor sister surface is ~$0 marginal because the content is static packs. This is the infrastructure expression of the "Brains For ___" house-brand system.

**S4. Two QA gates, everything else diagnostic.** Build gate = Tier 1 structural audit (free, already in Phase 5). Ship gate = `brain-qa.py` (numeric verifier + persona panel) **wired into `promote-brain.py` with `--persona-gate` default ON** and run as a job on `brain/*` PRs. Behavioral evals + self-recognition stay on-demand triage tools. Put every threshold in one table in `auto_build_config.py` (today MIN_BRAIN_ATOMS=250 vs MIN_ATOMS_LIVE=100 disagree).

**S5. Attack the $15 enrichment phase.** Phase 4 is 64% of the $23.45 build: ~300–400 Sonnet connection calls + voice extraction. Route pair-scoring to Haiku with Sonnet only adjudicating borderline pairs, and cap connections by marginal value (orphan-rate target) rather than count. Expected: $15 → $6–8, i.e. build cost ~$23 → ~$15. Worth doing before the next batch rebuild, not urgent otherwise.

**S6. Factory DB hygiene, opportunistically.** Adopt the Phase 7 generic schema (`brain_atoms` + `brain_connections` keyed by `brain_id`) the next time a migration is forced anyway; stop minting 2 tables per brain. Not urgent at 26 brains; mandatory before ~50.

---

## Step 4 — Accelerate

- **One release command.** The slow loop today isn't the build (60–90 min, resumable, remote-capable — good); it's the ship loop: export → audit → persona-QA → promote → prebuild sync → PR → deploy, with manual seams. Make `brain-qa.py` (or a thin `release-brain.py`) do gate → export → PR in one shot, and add it as the check on `brain/*` PRs so a green PR *means* shippable.
- **Slimmer repo = faster everything.** D2/D3 cut clone + Vercel build time (263MB tracked, 217MB history today; both compound per brain).
- **Keep** `--resume`/`--resume-from` cascade semantics and the GitHub Action walk-away build — that's the accelerator already working.

## Step 5 — Automate (only what survived deletion)

- Retarget the nightly **doc-refresh** from "patch counts in three prose docs" to "assert invariants and alarm": index.json ↔ packs ↔ site ↔ factory DB counts must agree; post a Slack line only on drift. Checking is automation; copying was the disease.
- CI ship-gate on brain PRs (S4) — cheap tiers only, Opus panel on promote.
- A weekly cost/usage snapshot (API route calls, Anthropic spend, top brains) to #claude-updates **once beta users exist** — the business plan's anti-vibe-revenue tracking, but only after there's revenue-shaped behavior to track.

---

## Cost model

**Fixed (monthly):** Supabase (shared PAOS project — effectively $0 marginal; dedicated project deletable or free-tier) + Vercel $20 + Upstash pay-as-you-go + Firecrawl $19 ≈ **$40–70 today → $40–60 after**. Immaterial either way; the fixed-cost story is fine.

**Variable is where the money is:**

| Unit | Today | After S2 | Mechanism |
|---|---|---|---|
| `/api/skill` call | ~$0.45–0.66 input (150–220K tok, uncached) | ~$0.03–0.05 | synthesis + top-K atoms + caching |
| `/api/board` run (5 brains + chair) | ~$2.30–3.00 | ~$0.15–0.30 | same, ×5 + synthesis pass |
| Brain build | $23.45 | ~$15 | Phase 4 Haiku-first (S5) |
| Full QA suite | ~$1.80/brain | unchanged | already right-sized |
| Sister site | a stack | ~$0 | S3 config-driven multi-tenant |

A modest launch week (1,000 skill calls + 200 board runs) costs **~$900–1,200 today vs ~$80–120 after S2**. The rate limiter caps abuse per IP but fails open when Upstash is unreachable (`/api/skill/route.ts` allow-on-error) — fix to fail closed with an in-memory fallback bucket.

---

## What NOT to touch

The auto-build pipeline (diarization, provenance guardrails, atom floors, resume), Tier-1 structural audit, the MCP server's local-first design (it *is* the open-runtime story), explore.html's data-driven single template, the anon-key/service-key security posture (correct — atoms are public by design), `brains/index.json` as registry, GitHub Action remote builds. These are the engine. Everything above is about deleting the scaffolding around the engine.

---

## Top 10 moves, ranked

| # | Move | Step | Effort | Impact |
|---|---|---|---|---|
| 1 | Right-size API calls: synthesis + atoms, add prompt caching; verify the >200K defect on big brains | S2/R2 | 0.5–1 day | 10–20× runtime COGS, faster demo, fixes probable live bug |
| 2 | Retire prod Supabase atom reads → static pack retrieval | D1 | 0.5 day | Deletes a project, 52 tables, a migration pipeline, a drift class |
| 3 | Un-track `website/public/brains/` + `.js` twins (prebuild generates) | D2/D3 | 1 hour | −125MB tracked, stops history bloat |
| 4 | Wire ship-gate into promote + brain PRs (`--persona-gate` ON) | S4 | 0.5 day | QA becomes enforcement, not ritual |
| 5 | Freeze catalog; spend the next cycles on launch + 5 beta users | R5 | discipline | Attacks the actual constraint |
| 6 | Multi-tenant `sites.ts` config (agents/free/futures) | S3 | 1 day | Sister sites at ~$0 marginal; brand system becomes real |
| 7 | Replace CLAUDE.md table sync with registry link; retarget doc-refresh to invariant alarm | D6/A5 | 1 hour | Kills the drift-defense industry |
| 8 | Delete/archive dead scripts + zombie tables; de-tier pricing page | D4/D5/D7 | 0.5 day | −~800 LOC, launch credibility |
| 9 | Shared retrieval lib in the open runtime repo (MCP + site import it) | S2 | 1 day | One engine, public proof of quality |
| 10 | Phase 4 Haiku-first enrichment | S5 | 0.5 day | Build $23 → ~$15 before next batch |

*~5 focused days total; items 1–3 alone are under a day and remove the majority of both cost and failure modes.*

## Open questions for Rob

- [ ] Auth: park (recommended) or fully delete until monetization? Parking keeps `login/dashboard` code dormant behind the password wall.
- [ ] Is the dedicated Supabase project on a paid plan? If yes, D1 saves real dollars; if free tier, D1 is purely failure-mode deletion.
- [ ] Model currency (last review 2026-03-11): runtime pinned to `claude-sonnet-4-6`, synthesis Opus 4.7, persona Opus 4.8. The Claude 5 family is out — worth a 30-min cost/quality pass on `auto_build_config.py` + the two route files.
- [ ] `cross_connections` = 0 rows: reseed deliberately when the "your brain × their brain" feature ships, or drop the table now?
- [ ] Verify whether `/api/skill` currently errors on brene-brown / paul-graham / dario-amodei (R2 window math).
