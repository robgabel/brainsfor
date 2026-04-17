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
- [ ] Voice recovery: original_quote + implication fields added, 240/284 atoms enriched (85%) — nearing completion, 44 atoms remaining
- [x] Context window optimization: cluster-level files + manifest + targeted loading
- [x] Connection enrichment: 161 → 430 connections (273 related, 105 supports, 38 extends, 14 contradicts)
- [x] Thin topic graceful degradation in all skills
- [x] Skill template compression (1,317 → ~500 lines)
- [x] Confidence simplification (numeric → high/medium/low tiers)
- [x] MCP server for selective atom retrieval — 6 tools (list_brains, get_synthesis, query_atoms, search_atoms, get_connections, get_atom). 19x context reduction vs full brain-context.md. Registered via `.mcp.json`. (2026-04-15)
- [x] MCP-first context loading in all 8 skills — `/advise`, `/teach`, `/debate`, `/connect`, `/evolve`, `/surprise`, `/coach`, `/predict` now use MCP tools when available, file fallback when not. (2026-04-15)
- [x] `/board` — Board of Advisors skill — multi-brain orchestrator. Fan out to N independent sub-agents (one per brain), converge with agreement/disagreement/confidence analysis. Solves autoregressive contamination from sequential role-play. (2026-04-15)

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

*Last updated: 2026-04-17 (run 5) — Catalog at 13 brains / 3,231 atoms / 5,129 connections (Peter Zeihan atom count synced 362→460 across index.json, website/public/brains/index.json, and business-plan.md after pack re-export). Audit avg score 97/100 across all 13 brains. **brainsforfree.com is live** (Next.js app in `website/`, auto-deploy from `main` to Vercel). Same-session fix: brain Explorer iframe was blank on every brain page due to `X-Frame-Options: DENY` — changed to `SAMEORIGIN` (commit 364fa75). Deleted obsolete `storefront/landing-page-prototype.html` (commit fb44bbf). `@brainsfor/mcp` v0.1.0 (6 tools) and `/board` skill live. `/coach` upleveled (2026-04-17) to 3 modes: sequential default (adaptive, one-Q-at-a-time), `/coach quick` (all-at-once list), and legacy `/coach <slug>` persona. Open flags: jensen_huang Supabase tables still empty (0/0) despite shipped pack having 253 atoms — needs re-ingestion; peter_zeihan Supabase 362 vs pack 460 — re-ingestion pending.*
