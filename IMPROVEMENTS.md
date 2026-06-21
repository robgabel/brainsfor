# BrainsFor — Improvement Backlog

Captured from expert critique panel (April 4, 2026): Calacanis, Bartlett, Hassid, Amodei, Belsky, MrBeast.

---

## 📌 Next Up for First Users (Pinned)

These are the items that define the offering for BrainsFor's first paying customers. Everything else in this file is downstream of getting these three tiers shipped.

### 1. Free brain pack (1 brain, local install) — the jab
- Pick the strongest brain (Belsky or Graham) as the free demo
- Ship full quality: all atoms, explore.html, synthesis
- Distribute via npm (`@brainsfor/mcp`) + hosted JSON files (GitHub Releases or S3)
- Install flow: `npx @brainsfor/install belsky` → adds to `.mcp.json` → done
- **Owner:** Rob | **Depends on:** npm publish of `@brainsfor/mcp`

### 2. Paid brain catalog ($29 one-time, per brain) — the revenue base
- Remaining 9 brains priced at $29 each
- Same local-install architecture as free tier
- License key check at install time (simple Supabase endpoint — 100 req/day even at launch)
- Stripe checkout, email delivers download link + license key
- **Owner:** Rob | **Depends on:** landing page, Stripe, license validation endpoint

### 3. Pro subscription ($15-25/mo, hosted MCP) — the moat *(don't build yet, pin for future)*
- **Status:** Design documented, build deferred — see `ideas/OPPORTUNITIES.md` entry dated 2026-04-17
- Hosted MCP server as Supabase Edge Function at `https://<project>.supabase.co/functions/v1/mcp-pro`
- Unlocks `/board`, semantic search (pgvector), cross-brain connections, personalization memory, ChatGPT connector compatibility
- Users add one connector URL to Claude Code / Claude Desktop / ChatGPT — no local files
- **Why this is the moat:** paywall-enforceable at the protocol level (free/paid tiers ship files — unenforceable). Also unlocks features that keyword-search local MCP can't deliver.
- **Kill criterion:** <10 Pro subscribers within 90 days of launch → pivot to volume pricing on per-brain purchases
- **Owner:** Rob | **Depends on:** free + paid tiers shipping first, measurable demand signal

---

## In Active Plan (see plan file)

- [x] Full corpus ingestion: all 77 Implications editions ingested (100% coverage, 284 atoms)
- [ ] Voice recovery: original_quote + implication fields added, 240/284 atoms enriched (84.5%) — nearing completion, 44 atoms remaining
- [x] Context window optimization: cluster-level files + manifest + targeted loading
- [x] Connection enrichment: 161 → 430 connections (273 related, 105 supports, 38 extends, 14 contradicts)
- [x] Thin topic graceful degradation in all skills
- [x] Skill template compression (1,317 → ~500 lines)
- [x] Confidence simplification (numeric → high/medium/low tiers)
- [x] MCP server for selective atom retrieval — 6 tools (list_brains, get_synthesis, query_atoms, search_atoms, get_connections, get_atom). 19x context reduction vs full brain-context.md. Registered via `.mcp.json`. (2026-04-15)
- [x] MCP-first context loading in all 8 skills — `/advise`, `/teach`, `/debate`, `/connect`, `/evolve`, `/surprise`, `/coach`, `/predict` now use MCP tools when available, file fallback when not. (2026-04-15)
- [x] `/board` — Board of Advisors skill — multi-brain orchestrator. Fan out to N independent sub-agents (one per brain), converge with agreement/disagreement/confidence analysis. Solves autoregressive contamination from sequential role-play. (2026-04-15)
- [x] **Board demo mode-collapse fix (`website/app/api/board/route.ts`)** — every brain in the live demo defaulted to its canonical mental model regardless of question (Belsky → "taste as a moat", Munger → "latticework", Graham → "schlep blindness"). Three root causes: (a) BOARD_FORMAT explicitly told each brain to "lead with the noun you're identifiable from"; (b) full brain-context.md (which leads with the #1 First Principle) sat at position [0] of the system prompt; (c) no question-aware atom retrieval. **Fix shipped 2026-05-20** in two layers. Layer 1 — prompt surgery: added ANTI-DEFAULT RULE listing forbidden taglines, reordered `buildSystem` so BOARD_FORMAT + question + retrieved atoms come BEFORE brain context, dropped the self-incriminating example openers. Layer 2 — new helper `website/lib/brain-atom-retrieval.ts` embeds the query (`text-embedding-3-large`, 1536-dim) and pulls top-15 atoms per brain via new Supabase RPC `search_brain_atoms(p_slug, p_embedding, p_k)` (slug-allowlisted, k-capped at 50, anon-callable since atoms are already public via shipped JSON packs). Degrades gracefully — if `OPENAI_API_KEY` is missing, Supabase is unreachable, or RPC errors, the route falls back to static brain-context.md and Layer 1 alone. Verified with two adversarial smoke tests (pricing, hiring; 4 brains each) — every brain led with a fresh question-specific lens, cited a retrieved atom verbatim, and the four perspectives diverged productively. **Layer 2 still needs `OPENAI_API_KEY` added to Vercel:** `vercel env add OPENAI_API_KEY production` (also preview + development). Layer 1 carries the demo without it.

---

## Product & Packaging (Not Yet Started)

- [ ] **Launch with /advise + /surprise only** (MrBeast) — Ship 2 skills first, phase in rest. Reduce cognitive load. "No one is going to install 8 skills."
- [ ] **Free sample brain** — Build Einstein or another public domain figure as a fully free brain. Eliminates purchase friction. Demonstrates the skill pack without risk.
- [ ] **Working `npx skills add` command** — Currently specced but not built. Requires publishing to the skills registry. This IS the distribution channel.
- [ ] **Naming review** — "brainsfor" sounds like a zombie movie (MrBeast). Test alternatives. "Load a genius into your AI" is the only good copy.
- [ ] **Minimum atom threshold** — What's the minimum for a brain to feel "worth $29"? Hypothesis: 75-100 atoms with connections + working skills. Validate with beta users.

## Retention & Engagement

- [ ] **Daily /surprise email or Slack** (MrBeast) — The retention loop. `/surprise` sends a daily atom via email or Slack webhook. Turns one-time purchase into daily habit. Build before storefront.
- [ ] **Social proof in product** (MrBeast) — Show real-time usage: "This brain loaded in 847 AI sessions this week. Most-asked: Should I raise a Series A?" In the skill output, not on a separate page.
- [ ] **Brain Score as re-engagement** — "Belsky brain just hit 50%!" notifications. Progress bars are addictive. Ship with v1.
- [ ] **Founding Supporters program** — First 100 buyers per brain get names embedded, free updates forever, vote on next brain. Creates urgency + evangelists.

## Voice & Quality (Beyond Phase 1)

- [x] **Full corpus ingestion** — All 77 Implications editions ingested (100%). 284 atoms spanning May 2014 – April 2026.
- [x] **Quote fabrication guardrails (provenance fix)** — RESOLVED 2026-05-25 (PR #23). Three-layer defense: (1) Phase 2.3 deep-research prompt forbids `original_quote` + defensive strip in `generate_cluster_atoms`; (2) new `verify_quotes_against_corpus()` substring-matches every quote against scraped MD + YouTube transcripts before Phase 3 ever sees them; (3) `MIN_QUOTE_PROVENANCE = 50` floor in Phase 5 remediation aborts the build if provenance can't be brought above 50%. Fix was prompted by yann-lecun shipping at 27% (140/197 atom quotes were LLM-fabricated). Verifier mirrors the audit's normalize + 35-char signature algorithm so passes line up.
- [ ] **Backfill quote provenance on existing brains** — The 2026-05-25 fix only protects new builds and `--resume-from 2` reruns. Existing shipped brains (Yann at 27%, plus whatever other brains have similar fabrication rates — audit them) still carry whatever quotes they were built with. Build a one-shot script that runs `verify_quotes_against_corpus()` against every brain in `brains/index.json`, nulls fabricated quotes, re-exports the pack, re-uploads to Supabase, and re-syncs `website/public/brains/<slug>/`. Generate a before/after report so we know how many quotes were stripped per brain. Likely a several-day pass if we want to add real corpus matches at the same time (vs just stripping). **Owner:** Rob | **Est:** 1-2 days.
- [ ] **Retrieval-grounded quote *attachment*** — The verifier today only STRIPS unfounded quotes; it doesn't REPLACE them with real ones from corpus. Layer 1c from the original architecture discussion. For each atom with `original_quote = null`, semantic-search the scraped corpus + transcripts for a quote that supports the atom's `content`, attach if cosine > 0.75. Would meaningfully raise voice enrichment % on brains with rich corpus (Yann, Brené, anyone with hours of transcripts) without inventing anything. Bigger build than the verifier — needs an embedding pass over the corpus and a per-atom search loop. **Est:** 3-5 days. **Depends on:** corpus embedding store (could reuse existing `embedding` columns on `<slug>_atoms` against per-paragraph corpus chunks).
- [ ] **Synthesis grounding fix (same fabrication pattern, different code path)** — `synthesis.md` `first_principles`, `contrarian_positions`, `would_not_say`, `does_not_believe` lists are also LLM-generated with no corpus check. Yann shipped with synthesis grounding at 0/31 principles — every principle's distinctive phrases were absent from source corpus. Need a similar verifier for synthesis: extract n-grams from each principle's title + desc, substring-check against corpus, flag (or strip) any that don't ground. Audit already computes this in `check_synthesis_grounding()` (audit-brains.py:754-859); just needs a "block at threshold" mechanism in Phase 5 mirroring `MIN_QUOTE_PROVENANCE`. **Est:** 1 day.
- [ ] **Story preservation** — Atoms stripped stories/examples. Belsky's persuasion comes from narrative, not just thesis statements. Consider a `story` or `example` field on atoms.
- [ ] **Curation layer** — If/when Belsky claims his brain, he should be able to curate: "these 50 atoms are my best work." Editorial control, not just fact-check. (Belsky feedback)
- [ ] **Contradiction mining** — Belsky contradicts himself constantly — that's the point. Tensions are the most interesting content. Target: every brain should have at minimum 15% "contradicts" connections.

## Architecture & Distribution

- [x] **Multi-brain skill collision — README promises `/advise`, install gave `/scott-belsky-advise`** — RESOLVED 2026-04-11. Refactored PAOS install to unified skill architecture: 8 generic reasoning skills (`/advise`, `/teach`, `/debate`, `/connect`, `/evolve`, `/surprise`, `/coach`, `/predict`) + 1 router (`/brain <slug>` that writes active brain to `~/.claude/state/active-brain.txt`). Each skill resolves brain via: inline first-token override → active state file → error. Cross-brain mode works for `/debate` and `/connect` via two inline slugs. Deleted 63 prefixed brain skill dirs. Matches README UX. Customer deliverable at `brains/<slug>/pack/skills/` still ships per-brain versions for single-brain installs. **Still TODO on the customer side:** the README's "install multiple brain packs and they auto-discover each other" promise needs the same unified router treatment in the installer, or the README language needs to change.
- [x] **MCP server for selective retrieval** — `@brainsfor/mcp` v0.1.0. stdio-based, 6 tools, in-memory indexes, weighted full-text search. Registered via `.mcp.json`. (2026-04-15)
- [ ] **SQLite brain format** — Portable SQLite with sqlite-vec for embeddings, connections, people. Solves "flat files can't carry a graph." (v2 roadmap item)
- [ ] **Hosted semantic search API** — Brain stays in Supabase. Skills call edge function for vector search + graph traversal. Real-time updates + usage tracking built in. (MCP server is the local-first version of this; hosted API is the cloud version.)
- [ ] **Hybrid delivery** — Flat files for offline context + API key for semantic search online. Best of both. (MCP server is step 1 — local selective retrieval. Step 2 is adding a Supabase-backed remote mode.)
- [ ] **Cowork plugin packaging** — Should brain packs also be `.claude-plugin` format for the Anthropic plugin marketplace?
- [ ] **`--force-synthesis` flag on `auto-build-brain.py`** — Re-running Phase 3 on a brain with a populated `brain.json["synthesis"]` section produces near-identical output because Opus anchors on the draft embedded in the synthesis prompt (`SYNTHESIS_PROMPT` in `scripts/auto_build_config.py` line 291-293: "Here is the draft synthesis from brain.json (use as a starting point but improve significantly)"). Observed 2026-04-21 during Opus 4 → 4.7 upgrade: Steve Jobs and Hank Green regenerated byte-identically on first attempt; only manually clearing `brain.json["synthesis"]` (preserving `skills` array) forced a real regeneration. Proposed fix: add `--force-synthesis` flag to `auto-build-brain.py` that clears `brain.json["synthesis"]` (preserving `skills`) before calling `phase_3_synthesize`. Deliverable: one-line arg parser addition + 3-line clear logic in main(). Also: document this as a pipeline gotcha in `brainsfor/CLAUDE.md`.

## Cross-Brain Features

- [ ] **Cross-connection surfacing in skills** (Calacanis — "the REAL product") — `/advise`, `/connect`, `/surprise` should pull from both the brain AND user's personal atoms. "Belsky thinks X, and you wrote something similar 3 weeks ago." 17 Rob-Belsky cross-connections already exist.
- [ ] **Personal atom ingestion** — Let buyers add their own atoms (notes, Slack, docs) into a personal graph. Cross-connections auto-generate via embedding similarity.
- [ ] **Brain Fights content series** — Debate format: Brain A vs Brain B on a topic. Tag both people. 20 brains x 25 clusters = hundreds of debates. Content engine that sells two brains per post.

## Go-to-Market

- [ ] **Get 5 beta users this week** — Zero users, zero feedback. Critical. (Calacanis: "Show me someone who isn't you using /advise and getting value.")
- [ ] **Jason Calacanis outreach** — First claimer. 100% rev share offer. Buy a case study and megaphone, not a customer.
- [ ] **Build storefront** — Static site on Vercel + Stripe checkout. Not built yet.
- [ ] **"This Week in Brains" newsletter** — Auto-generated weekly from atoms. Zero marginal cost content flywheel.
- [ ] **Context window future-proofing** (Amodei) — In 12-18 months, 2M+ token windows are standard. "Why wouldn't I just paste the full newsletter archive?" Answer: connections, evolution tracking, cross-brain, and skills. Make sure THAT is the value prop, not "pre-chunked knowledge."

## Ethics & Legal

- [ ] **Ethics of building without consent** (Amodei) — "Fair use" is legal, not ethical. Consider asking first, not building-then-inviting. The power dynamic matters.
- [ ] **Book content handling** — Will use discussion and reviews of books, NOT transcripts. Copyright is clearer for extracted ideas vs. direct quotes. Establish guidelines before building book-sourced brains.
- [ ] **International brains** — Is there demand for non-English thinkers? (Yuval Noah Harari, etc.)

---

*Last updated: 2026-05-20 (doc-refresh run 12) — Catalog grew from 18 → 20 brain packs since run 11. Added: **Jeremy Utley** (759 atoms / 2,272 connections — now the largest brain by both metrics) and **Gokul Rajaram** (454 atoms / 789 connections). Both live on brainsforagents.com. Live count: 17 (was 15). Hidden: 3 (Hank Green, John Green, Shiva Rajaraman) — unchanged. **Data regression flagged:** gokul_rajaram dropped from 554/906 (prior index.json) to 454/789 (Supabase) — atoms down 100, connections down 117. index.json updated to match Supabase per doc-refresh policy; pack re-export likely needed. **Other deltas:** brain_metadata 15 → 18 (Gokul, Jeremy, plus a third row), `kara_swisher_atoms`/`kara_swisher_connections` tables exist but EMPTY (0/0) — scaffolded by an aborted build, not in index.json, flagged for human review. cross_connections=17, brain_requests=0, voice enrichment unchanged at 240/284 = 84.5% (Belsky). **Open flags carried forward:** (1) export-brain.py pagination bug still caps shipped pack connections at ~1,000 per brain; (2) gary_vee Supabase shows 319/255 vs pack 246/1,850 — needs re-enrichment + re-export; (3) shiva_rajaraman pack ships 419 connections vs Supabase's 1,815 — re-export needed; (4) Oprah Winfrey and Sara Blakely lack Supabase tables. **New flag this run:** (5) gokul_rajaram regression — confirm whether 454 atoms is the new correct count or whether ~100 atoms need to be restored.*
