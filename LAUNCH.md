# LAUNCH.md — Canonical Launch Plan for brainsforagents.com

**This is the ONLY launch/marketing plan.** Strategy lives in `business-plan.md`; personas in `personas.md`; everything about *going public and getting the first 10 beta users* lives here. If another doc contradicts this one, this one wins.

*Created 2026-07-04 from the launch-readiness audit (personas + business plan + full website sweep). Supersedes the GTM sections previously scattered across `business-plan.md`, `IMPROVEMENTS.md`, and `PRD-site-overhaul.md` (deleted).*

---

## The Goal

**10 beta users** — people who are not Rob — who install a brain, use it in a real session, and email back one thing their agent did better. That's it. Not revenue, not HN front page, not Stripe. Ten completed feedback loops.

**Target persona:** #1 AI Power User only (see `personas.md`). They are the only persona the current product serves end-to-end (free zip → local install → Claude/Cursor session). Operators are acceptable if technical. Everyone else waits.

**Success metric per user:** time-to-aha under 5 minutes from download. The funnel we can measure today: `hero_demo_play` → `download_click` → `beta_email_click` → reply in inbox (Vercel Analytics + Gmail).

---

## Launch Checklist

Work top to bottom. **P0 = blocks going public. P1 = do before recruiting strangers. P2 = same week, after launch.**

### P0 — Blockers
- [x] **Legal pages** — ship `/privacy` + `/terms`, link in footer → [PRD-1](#prd-1--legal-pages-privacy--terms) *(code on branch 2026-07-04 — Rob: review the copy, esp. governing law = California, before merge)*
- [ ] **Verify Vercel prod env** — `ANTHROPIC_API_KEY`, `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, `OPENAI_API_KEY`, Supabase keys → [PRD-5](#prd-5--go-public-runbook)
- [ ] **Verify download pipeline** — Vercel root = monorepo root; zips generate at build; spot-check one `-brain-pack.zip` in prod → [PRD-5](#prd-5--go-public-runbook)
- [ ] **Remove `SITE_PASSWORD` from Vercel prod + redeploy** — the entire site 401s while it's set → [PRD-5](#prd-5--go-public-runbook)

### P1 — Before recruiting strangers
- [x] **Fix dashboard dead-end** — nothing writes `brain_access`; every signed-in user sees an empty "My Brains" forever → [PRD-2](#prd-2--dashboard-dead-end) *(code on branch 2026-07-04 — requires the RLS policy in PRD-2 before it records claims)*
- [x] **Install-path honesty** — demote the non-working `npx skills add` command; lead with the zip → [PRD-3](#prd-3--install-path-honesty) *(code on branch 2026-07-04)*
- [x] **Share/SEO metadata** — `metadataBase`, twitter card, canonicals → [PRD-4](#prd-4--seo--share-metadata) *(code on branch 2026-07-04 — validate unfurls after deploy)*
- [ ] **Recruit the 10** — warm DMs → LinkedIn → r/ClaudeAI + Claude Discord → [PRD-6](#prd-6--beta-recruitment-the-10-users)

### P2 — Launch week, after going public
- [ ] **Supabase SMTP** — real sender for magic links (default shared SMTP spam-filters/rate-limits) → [PRD-5](#prd-5--go-public-runbook)
- [ ] **Google Search Console** — add property, submit sitemap, request indexing
- [ ] **MCP directory listings** — Smithery, Glama, PulseMCP, mcp.so, awesome-mcp-servers → [PRD-6](#prd-6--beta-recruitment-the-10-users)
- [ ] **Content flywheel v0** — 1 atom post + 1 Brain Fight per week (assets already exist) → [PRD-7](#prd-7--launch-week-content)

### Explicitly NOT in scope for this launch
Stripe/checkout, delivery edge function, `npx skills` registry publish, Pro/API tiers, claim-your-brain outreach, HN/Product Hunt, `brain_events` usage-tracking table. All of it waits until 10 beta users have validated real usage. (Calacanis: *"Show me someone who isn't you using /advise and getting value."*)

---

## PRD-1 — Legal pages (privacy + terms)

**Problem.** The site collects personal data — email (Supabase magic link), GitHub OAuth identity, auth cookies, Vercel Analytics — with **zero** legal pages and no legal links in the footer. GDPR/CCPA exposure; GitHub OAuth apps are expected to link a privacy policy; technically sophisticated beta users notice.

**Scope.**
- `website/app/privacy/page.tsx` — plain-language privacy policy. Must cover: what's collected (email, auth cookies, analytics events, IP for rate limiting), processors (Supabase, Vercel, Anthropic, Upstash, OpenAI), no sale of data, retention, deletion-by-request (email contact), contact address.
- `website/app/terms/page.tsx` — terms of use. Must cover: beta/as-is disclaimer, acceptable use of the API demos, IP position on brain packs (derived from public sources, transformative analysis, **not endorsed by the subjects**), the takedown promise (subject objects → brain comes down promptly — this is already committed to in `business-plan.md`), governing law.
- `components/Footer.tsx` — add a "Legal" column or bottom-row links: Privacy · Terms.
- Add both pages to `app/sitemap.ts`.
- Style: match DESIGN.md (prose page, warm-paper section, no legalese wall — headings + short paragraphs).

**Acceptance.** `/privacy` and `/terms` return 200, are linked from every page's footer, appear in the sitemap, and the login page links the privacy policy near the OAuth buttons.

**Est:** 2-3 hours. **Files:** `app/privacy/page.tsx` (new), `app/terms/page.tsx` (new), `components/Footer.tsx`, `app/sitemap.ts`, `app/login/page.tsx`.

---

## PRD-2 — Dashboard dead-end

**Problem.** `app/dashboard/page.tsx` reads `brain_access` to render "My Brains," but nothing in the app ever writes that table. Every signed-in user permanently sees "You haven't claimed any brains yet." A hollow dashboard is the fastest way to lose an evaluator.

**Decision: wire the claim (option A), don't hide the dashboard.** The Get button already exists on the dashboard; recording the claim gives us the only per-user usage signal we'll have during beta.

**Scope.**
- When a signed-in user clicks "Get this brain," insert `{user_id, brain_slug}` into `brain_access` (upsert, ignore dupes) before/alongside triggering the zip download. Anonymous users keep the plain download — no signup wall on the primary CTA.
- Dashboard "My Brains" then renders claimed brains with re-download links (UI for this already exists).
- Empty state copy change: "Download any brain to see it here" (only shown to users who genuinely have none).

**Acceptance.** Sign in → download a brain from anywhere in the app → it appears under My Brains. Anonymous download flow unchanged.

**Shipped 2026-07-04 (client-side insert in `GetBrainButton`, best-effort — never blocks the download).** Remaining ops dependency: `brain_access` needs RLS policies in the auth Supabase project (`jefjvgbawmsloerqsgby`) or inserts silently fail:

```sql
alter table brain_access enable row level security;
create policy "users insert own access" on brain_access
  for insert with check (auth.uid() = user_id);
create policy "users read own access" on brain_access
  for select using (auth.uid() = user_id);
```

**Est:** 2-3 hours. **Files:** `components/GetBrainButton.tsx`, `app/dashboard/page.tsx`.

---

## PRD-3 — Install-path honesty

**Problem.** `npx skills add brainsfor/<slug>` is displayed as THE install command (`components/InstallCommand.tsx`, dashboard terminal block) but the registry isn't published — the copy even admits "ships soon." A beta user's first action failing is the single worst thing that can happen in the first mile.

**Scope.**
- Everywhere the npx command appears, make the **zip download the primary path** and the npx command a clearly-labeled "coming soon" secondary (grayed, not copy-pasteable as if live) — or remove it until real.
- Surfaces: `components/InstallCommand.tsx`, `app/dashboard/page.tsx` (worst offender: green terminal line showing npx above the actually-working zip), any `/brains/[slug]` usage.
- Zip path must be self-sufficient: the pack README covers install; the site shows the 3-step version (download → unzip into `.claude/skills/` or Claude Project → `/advise "..."`).

**Acceptance.** No surface presents a command that fails when copy-pasted. A first-time user can go from any Get button to a working `/advise` following only on-screen instructions.

**Est:** 1-2 hours. **Files:** `components/InstallCommand.tsx`, `app/dashboard/page.tsx`, `app/brains/[slug]/page.tsx`.

---

## PRD-4 — SEO & share metadata

**Problem.** Beta traffic arrives from X/LinkedIn/Discord links; unfurls and indexability need to be right on day one. robots.ts, sitemap.ts, llms.txt, and per-brain OG are already good. Gaps: no `metadataBase` (OG image URLs can resolve against previews/localhost + build warning), no `twitter` card object, `/brains` and `/skills` have titles but no descriptions, no canonicals.

**Scope.**
- `app/layout.tsx`: `metadataBase: new URL("https://brainsforagents.com")`; add `twitter: { card: "summary_large_image" }` (+ title/description mirroring OG); add `url` to the openGraph block.
- ~~`app/brains/page.tsx`, `app/skills/page.tsx`: add meta `description`~~ — already present (audit over-flagged).
- `app/brains/[slug]/page.tsx` `generateMetadata`: add `alternates: { canonical: … }`.
- Verify with an X card validator + a LinkedIn post inspector after deploy.

**Acceptance.** Homepage and a brain page unfurl with the side-by-side OG image on X and LinkedIn; `next build` emits no metadataBase warning; every indexed page has title + description.

**Est:** ~1 hour. **Files:** `app/layout.tsx`, `app/brains/page.tsx`, `app/skills/page.tsx`, `app/brains/[slug]/page.tsx`.

---

## PRD-5 — Go-public runbook

**Problem.** Going public is an ordered sequence of ops steps, most outside the repo (Vercel/Supabase dashboards). Done out of order, the failure modes are silent: demos 429, downloads 404, magic links vanish, crawlers hit 401s.

**Runbook (in order):**
1. **Vercel env audit (prod):** confirm `ANTHROPIC_API_KEY`, `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` (demos fail closed → 429 without them), `OPENAI_API_KEY` (Layer-2 board retrieval — flagged missing in IMPROVEMENTS.md), `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, optional `OWNER_BYPASS_TOKEN`.
2. **Supabase check:** apply the `brain_access` RLS policies from PRD-2 in the auth project; verify a signed-in download creates a row.
3. **Build-context check:** Vercel project Root Directory must be the monorepo root (NOT `website/`) — `prebuild`/`sync-brain-assets.mjs` needs `../brains` or every download link 404s and `lib/brains.ts` breaks the build. Nothing in the repo pins this; it's dashboard config.
4. **Ship P0/P1 code** (PRDs 1-4) to `main` → auto-deploy. *(Code complete on branch `claude/brainsforsale-launch-prep-gg0l9s`, 2026-07-04.)*
5. **Open the gate:** `vercel env rm SITE_PASSWORD production` → redeploy.
6. **Smoke test (prod, logged out, no bypass header):** homepage renders; hero demo autoplays; one `/api/skill` ask streams; download one `-brain-pack.zip` and unzip it; `/privacy`, `/terms`, `robots.txt`, `sitemap.xml`, `llms.txt` all 200; a `/brains/[slug]` unfurls correctly on X.
7. **Search Console:** add property, submit sitemap, request indexing of `/` and `/brains`.
8. **Supabase SMTP (P2):** configure a real sender (Resend/Postmark/SES) for magic links; send a test magic link to a non-Gmail address.

**Acceptance.** All smoke tests pass logged-out from a clean network. Checklist boxes above get checked with date + initials.

**Est:** 1-2 hours (excluding SMTP account setup).

---

## PRD-6 — Beta recruitment (the 10 users)

**Problem.** Zero external users since April. The product funnel is ready (free zip, mailto feedback loop, analytics events); nobody has been asked.

**The ask (same everywhere):** install one brain free, use it on something real, email one thing your agent did better (the BetaBand mailto pre-fills the questions). That email = a completed beta slot.

**Channel plan — in order, stop when 10 replies land:**

| Wave | Channel | Target | Expected yield |
|---|---|---|---|
| 1 | **Warm DMs** — AI-native friends, Spotter/Tubular/TubeBuddy network, anyone already using Claude Code/Cursor daily | 15-20 DMs | 3-5 users |
| 2 | **LinkedIn post** (Rob's audience — the unfair advantage) — HeroDemo GIF + "22 thinkers, free during beta, I want 10 people to break it" | 1 post | 3-4 users |
| 3 | **r/ClaudeAI post + Claude Developers Discord** (#show-and-tell) — technical framing: knowledge graphs, atoms, typed connections, works offline | 1 post + 1 share | 2-3 users |
| 4 (backfill) | **X build-in-public thread**; **Latent Space / AI-Engineer Discords**; **r/LocalLLaMA** (ownership-not-access framing); **Indie Hackers** | as needed | 1-2 each |

**Evergreen (P2, zero-maintenance):** list `@brainsfor/mcp` on Smithery, Glama, PulseMCP, mcp.so, awesome-mcp-servers. DM Paul Bakaus re: the `npx skills` registry — first knowledge pack in that ecosystem is the stated category play.

**Held in reserve (do NOT spend during beta):** Show HN, Product Hunt, brain-subject tagging. Those are firehoses for the *paid* launch once the funnel is proven.

**Tracking:** a simple table in this file (below) — name, channel, date downloaded, brain, replied Y/N, key quote. Vercel funnel events sanity-check the top of funnel.

| # | Who | Channel | Brain | Replied | One thing they said |
|---|---|---|---|---|---|
| 1 | | | | | |
| … | | | | | |

**Acceptance.** 10 rows with Replied = Y. Secondary: download→reply rate ≥ 25% (below that, the install path is broken — fix before recruiting more).

---

## PRD-7 — Launch-week content

**Problem.** The content flywheel (business-plan.md channels 6-8) has zero marginal cost — the atoms exist — but zero cadence. During beta it serves recruitment, not sales.

**Scope (deliberately tiny):**
- **1 atom post/week** — one strong `original_quote` atom, one screenshot, CTA = free brain + beta ask. LinkedIn + X.
- **1 Brain Fight/week** — two brains, one topic, pulled via `/debate` or the board demo; don't tag the subjects yet (that's the paid-launch play).
- Both end with the beta CTA, not a purchase CTA.

**Acceptance.** 4 weeks × 2 posts, each traceable to `download_click` upticks in Vercel Analytics.

**Est:** ~30 min/week using existing packs + `/surprise`.

---

## Post-beta gate

When 10 replies are in, run this decision, in this order:
1. **Usage real?** (users describe concrete sessions, not compliments) → wire Stripe per `business-plan.md` pricing; else fix the product first.
2. **Which brains got installed?** → informs the paid catalog's front page and the next builds (`BACKLOG.md`).
3. **Then and only then:** Show HN, Product Hunt, claim-your-brain outreach (Calacanis first), `npx skills` registry publish.
