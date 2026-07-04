# PRD — Homepage First-Mile Revamp

**Status: EXECUTED 2026-07-03** (same day, branch `claude/vigorous-sammet-23ca12`). All four phases shipped: `website/lib/hero-demos.ts` (9 atom-grounded canned demos), `website/components/HeroDemo.tsx` (autoplay side-by-side + lanes + live ask + board tab), rewritten `website/app/page.tsx` (5 beats, ~356 visible words vs ~3,150 before), `website/components/BetaBand.tsx` (mailto beta loop), `@vercel/analytics` events, `website/app/opengraph-image.tsx` (side-by-side share card), `LivePlayground.tsx` deleted, Request-a-brain → `/brains#request` + footer link. Production build green. Open-item resolutions and deviations logged at the bottom.

**Date:** 2026-07-03 · **Goal:** first beta users download a brain and start playing with it
**Decision:** Option 1 spine (one default brain, demo auto-running) with Option 2 folded in as a single lane-switcher row — not three separate showcases.
**Authored:** Belsky-brain session (`/brain scott-belsky`). Grounding: personas.md (Power User = beta target), DESIGN.md, BRAND.md.

---

## Diagnosis (why the current page underperforms)

1. **~3,150 words** of copy across homepage components (`page.tsx` + LivePlayground + SkillCatalog + BrainCard + InstallCommand + RequestBrainForm). A first-30-seconds visitor reads ~20 of them.
2. **The page explains before it shows.** "Three things your LLM can't do" + why-paragraphs = Explain-first. Belsky hierarchy: Do > Show > Explain.
3. **The first interactive object is the heaviest** — /board (5 brains, long stream, biggest API cost). The side-by-side "delta" demo (personas doc: "the side-by-side demo is everything") is buried as the *last* tab.
4. **The first object a visitor can act on is a command that doesn't work yet** (`npx skills add …` + "ships soon"). First action failing = vanity kill.
5. **The core CTA (free zip download, no signup — already great) is buried** in card #2 of "How it works."

## Core metric

**Downloads per unique visitor** (weekly). Secondary: demo-interaction → download conversion; beta replies. If the delta isn't obvious in 30 seconds, nothing else matters.

---

## The new page — 5 beats, ≤800 visible words

### Beat 1 — The demo IS the hero
- H1 stays: **"Load a genius into your AI."** No subhead paragraphs.
- Directly below: **auto-playing side-by-side**. One real builder question, answered twice:
  - Left column: "Claude" — generic, hedged answer (muted styling).
  - Right column: "Claude + 🚀 Elon Musk" — opinionated, first-person, with **cited atoms + confidence + dated source links** visible.
- Playback is **canned** (extend `lib/skill-demos.ts`) → zero latency, zero API cost, atom-verified content. Typing effect, respects `prefers-reduced-motion`.
- Below: 3 question chips (re-run canned) + **"Ask him yourself →"** (live, reuses `/api/skill`; 4/24h rate limit is fine at beta scale).
- Board demo becomes tab 2 of this same surface ("Convene five minds"), run-on-click, not autoplay.

### Beat 2 — Lane row (Option 2, folded to one line)
`Shipping code → 🚀 Elon · 🎨 Belsky   |   Thinking about AI → 🧪 Dario · 🤖 LeCun   |   Making a big bet → 🪙 Munger · 🃏 Annie`
Click = swaps demo brain + question set. One row, no sections.

### Beat 3 — The ask, at the moment of value
- **"Get Elon's brain — free ↓"** button directly under the enhanced column (per-lane slug).
- Sub-line: "A zip you drop into Claude Code, Cursor, or any agent. No signup."
- The dead `npx` command leaves the spotlight until it works; mention as "one-command install ships soon" under the install strip only.

### Beat 4 — Receipts strip (HN-skeptic insurance)
One band, dynamic per selected brain: **"836 atoms · 719 connections · every line cites a dated, real source — see the whole graph →"** (links to explore/brain page). One trust line: "Built from public sources only" → links to ethics section.

### Beat 5 — Install + beta + brain row
- Install in one visual line: `1 download → 2 drop into your project → 3 /advise` (+ "zip works today; npx soon").
- **Beta band:** "We're in beta. Every brain is free while we learn. The trade: tell us one thing your agent did better. → [email/Discord]"
- One row of 6 featured brains + "Browse all 21 →". Full grid stays on /brains.

## The kill list (moved, not deleted)

| Section | Destination |
|---|---|
| SkillCatalog section | `/skills` |
| Full 21-brain grid | `/brains` (homepage keeps 1 row of 6) |
| RequestBrainForm | `/brains` + footer link |
| "Three things your LLM can't do" header + explainer copy | deleted — the demo replaces the explanation |
| /evolve tab + teaser | brain detail pages (`/brains/[slug]`) |
| Sources & Ethics box | one line in Beat 4 + footer page |
| How-it-works 3 cards | compressed into Beat 5 install strip |

## Implementation phases

- **P1 — Structure cut** (~1 session): reorder/cut `website/app/page.tsx`. No new components. Word budget ≤800.
- **P2 — HeroDemo component** (~1–2 sessions): canned autoplay side-by-side + chips + lane switcher; extend `website/lib/skill-demos.ts` with 9 hero entries (3 per lane: elon-musk, scott-belsky / dario-amodei, yann-lecun / charlie-munger, annie-duke). Every canned answer **verified against real atoms via brainsfor MCP** (store atom ids + source_refs). Live-ask path reuses SkillsPlayground plumbing.
- **P3 — Conversion loop** (~1 session): download button placement per lane; beta capture (lightweight — email field or Discord link; reuse RequestBrainForm plumbing); Vercel Analytics events: `hero_demo_play`, `hero_demo_chip`, `hero_demo_live_ask`, `lane_switch`, `download_click(slug, position)`, `beta_join`.
- **P4 — Share surface + QA** (~0.5 session): OG image = the side-by-side card (beta users arrive from X/HN/Discord links); `/brain-qa`-style spot-check of the 9 hero answers; a11y + banned-words pass (BRAND.md §4).

## Risks / honesty notes

- **Elon's would-sign rate is 50%** (self-recognition QA). He's the front door for pull, but the 3 Elon hero answers must be hand-verified sign-able before ship. If they can't be, Belsky takes the default demo and Elon stays on the lane row.
- Rate limits: live asks capped 4/24h/IP (Upstash) — acceptable at beta scale; canned playback carries the load.
- DESIGN.md constraints hold: indigo-only accent, weight-300 display, no hype words, restraint is the taste signal.

## Open items — resolved at execution (2026-07-03)

- [x] 9 canned questions picked and atom-verified via brainsfor MCP — atom ids + source labels stored in `website/lib/hero-demos.ts`. Elon's 5-step-algorithm atom (7c5da953) has a suspect source_ref (TED 2017 — likely Everyday Astronaut 2021); the hero entry uses its content but cites the SXSW/JRE atoms for the visible source line. Background task filed to fix the pack.
- [x] Beta capture: mailto to robgabel@gmail.com with prefilled subject/body (`components/BetaBand.tsx`) + `beta_email_click` event. Zero infra for cohort one. ⚠️ Publishes Rob's personal Gmail in page HTML — swap for an alias or a `beta_signups` table before/after merge if unwanted. (RequestBrainForm's table pattern requires sign-in — wrong friction for this ask.)
- [x] OG image: `next/og` generated (`app/opengraph-image.tsx`), statically rendered at build. Side-by-side share card, 1200×630.
- [x] Evolve surface: died with LivePlayground on the homepage; `/evolve` remains live on `/skills` (skill picker) and per-brain playgrounds. No further move needed.

## Follow-ups (post-merge)

- [ ] Enable Web Analytics in the Vercel dashboard (events no-op until toggled)
- [ ] Watch the funnel weekly: `hero_demo_play` → `hero_lane_switch`/`hero_demo_chip` → `download_click` → `beta_email_click`
- [ ] Ship `npx skills add brainsfor/<slug>` and swap the install strip to lead with it
- [ ] Pre-existing lint errors (not from this change): BoardDemo.tsx:309 unescaped entity, RequestBrainForm.tsx:28 use-before-declare warning-class error
