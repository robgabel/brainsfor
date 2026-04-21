# BrainsFor — Project CLAUDE.md

## Canonical Location

**All BrainsFor work lives here: `~/rob-ai/brainsfor/`**

Do NOT create or save files to a standalone `Brainsfor` Cowork mount, `~/.claude/`, or anywhere else. Everything goes in this directory under `~/rob-ai/` so it's version-controlled, backed up, and visible to all sessions that mount `rob-ai/`.

## What This Is

BrainsFor is a product: packaged "brain packs" — curated knowledge sets from notable thinkers (starting with Scott Belsky) that users install into AI assistants. Each brain ships with 8 thinking skills (`/advise`, `/teach`, `/debate`, `/connect`, `/evolve`, `/surprise`, `/coach`, `/predict`).

## Directory Structure (v2)

```
brainsfor/
  CLAUDE.md                          ← this file
  DESIGN.md                          ← design system (Stripe-inspired, indigo-tinted premium knowledge aesthetic)
  BRAND.md                           ← brand style guide (voice, messaging, vocabulary, visual identity)
  IMPROVEMENTS.md                    ← improvement backlog
  BACKLOG.md                         ← **BRAIN CANDIDATE BACKLOG** — next brains to build (8 women thinkers queued)
  business-plan.md                   ← strategy doc
  .gitignore

  scripts/                           ← SHARED pipeline (brain-agnostic)
    auto-build-brain.py              ← **FULL AUTOMATION** — person name in, brain pack out (~$23, ~60-90 min)
    auto_build_config.py             ← config/utilities for auto-build (cost tables, prompts, Claude wrapper)
    audit-brains.py                  ← QA validator: structural + data quality checks across all brains
    build-brain.py                   ← staged builder (generate → merge → synthesis → export)
    export-brain.py                  ← generic: --brain scott-belsky
    enrich-voice.py                  ← generic: --brain scott-belsky
    enrich-connections.py            ← generic: --brain scott-belsky
    ingest-youtube.py                ← generic: --brain peter-attia (download + extract)

  templates/                         ← SHARED templates
    SKILL.md.template                ← brain-setup template
    README.md.template
    README.dev.md                    ← **START HERE** for building a new brain (full step-by-step guide)
    explore.html.template            ← data-driven human UI (reads brain-atoms.json)
    create-brain-tables.sql          ← Supabase table creation template
    skills/                          ← 8 skill templates
      advise.md.template, teach.md.template, etc.

  packages/                           ← npm packages
    brainsfor-mcp/                   ← @brainsfor/mcp — MCP server for selective atom retrieval
      src/                           ← TypeScript source (index.ts, types.ts, loaders/, tools/)
      dist/                          ← compiled JS (ready to run)
      package.json

  website/                           ← **LIVE SITE** — brainsforfree.com (Next.js app on Vercel, auto-deploy from main)
    AGENTS.md                        ← ⚠️ "This is NOT the Next.js you know" — check node_modules/next/dist/docs/ before writing code
    app/                             ← app router pages (brains/[slug], pricing, dashboard, auth, api)
    lib/                             ← brains.ts (reads brains/index.json as source of truth for atomCount/connectionCount)
    public/brains/                   ← per-brain static assets: brain-atoms.json, brain-context.md, explore.html, SKILL.md, <slug>-brain-pack.zip
    next.config.ts                   ← **X-Frame-Options: SAMEORIGIN** (DENY would break the Brain Explorer iframe)

  storefront/                        ← DEPRECATED — pre-production prototype. Superseded by website/.

  .mcp.json                          ← MCP server registration (auto-loaded by Claude Code)
  HANDOFF-MCP-BOARD.md               ← handoff doc for MCP server + /board skill build
  PRD-site-overhaul.md               ← PRD for website overhaul work
  naming-exploration.md              ← brand naming exploration
  doc-refresh-log.md                 ← audit trail of every /doc-refresh run

  brains/
    index.json                       ← registry: all brains, slugs, status
    scott-belsky/                    ← EVERYTHING for this brain
      brain.json                     ← config (clusters, skill examples, Supabase refs)
      synthesis.md                   ← thinking analysis layer
      source/                        ← raw inputs + brain-specific scripts
        extracted-insights.md
        export-direct.py             ← Supabase direct fetch
        visual-prototype.html
      research/                      ← enrichment atoms (pipeline inputs)
        interview-atoms.json, book-atoms.json, etc.
      data/                          ← gitignored ephemeral
      pack/                          ← CUSTOMER DELIVERABLE
        SKILL.md                     ← brain-setup (loads brain-context.md)
        brain-context.md             ← THE LLM file (synthesis + rules + atoms + skills)
        brain-atoms.json             ← structured data (atoms + connections + index)
        explore.html                 ← THE human file (reads brain-atoms.json)
        README.md                    ← quick start
        skills/                      ← 8 reasoning modes
          advise/SKILL.md, teach/SKILL.md, etc.
```

## Key Dependencies

- **Supabase project:** `uzediwokyshjbsymevtp` (same as PAOS)
- **Tables (15 brains live, per-brain schema):**
  - `<slug>_atoms` — e.g. `scott_belsky_atoms` (284 atoms), `dario_amodei_atoms` (353), `peter_zeihan_atoms` (362 in DB / 460 in pack — see note below), `oprah_winfrey_atoms` (333), `brene_brown_atoms` (283), `paul_graham_atoms` (213), `steve_jobs_atoms` (170), etc. Columns: `content`, `original_quote`, `implication`, `confidence_tier`, `cluster`, `topics`, `embedding`
  - `<slug>_connections` — typed relationships (supports, contradicts, extends, related). Largest: `steve_jobs_connections` (792), `gary_vee_connections` (505), `dario_amodei_connections` (502), `scott_belsky_connections` (430), `oprah_winfrey_connections` (355), `brene_brown_connections` (321)
  - `brain_metadata` — 15 rows, one per brain
  - `cross_connections` — 17 rows, Rob ↔ brain cross-brain links
  - `rob_atoms` / `rob_connections` — Rob's personal knowledge graph (225 / 162)
  - `scott_belsky_enrichment_log` — connection enrichment run history (mode, counts, duration, errors). Legacy `belsky_enrichment_log` table still exists from pre-rename but is unused.
  - **Known data drift:** `jensen_huang_atoms` / `jensen_huang_connections` are empty (0/0) despite the shipped pack having 253 atoms and 220 connections. Pack data is authoritative; Supabase needs re-ingestion. `peter_zeihan_atoms` in DB is 362 while the pack has 460 — pack is authoritative, re-ingestion pending.
- **Edge function:** `enrich-connections` — automated connection discovery (topic overlap + temporal + LLM). Runs daily at 11:30pm PT via pg_cron. Modes: `discover` (cron), `discover-llm` (manual), `stats`.
- **Export scripts** require `SUPABASE_SERVICE_KEY` — set in `~/rob-ai/.env`
- **Voice enrichment** requires `ANTHROPIC_API_KEY` env var

## Architecture

### MCP Server (`packages/brainsfor-mcp/`)

A stdio-based Model Context Protocol server for selective atom retrieval. Gives AI agents access to brain data without loading full 290KB brain-context.md files (~15KB per brain, 19x reduction).

**Package:** `@brainsfor/mcp` v0.1.0 — TypeScript, `@modelcontextprotocol/sdk` ^1.29.0, Zod.

**6 tools:**

| Tool | Purpose |
|------|---------|
| `list_brains` | All installed brains with slug, name, source, atom/connection counts |
| `get_synthesis` | Thinker's intellectual OS (~4KB): first principles, thinking patterns, contrarian positions, does_not_believe, would_not_say |
| `query_atoms` | Filter atoms by topics (union), cluster, confidence_min, limit |
| `search_atoms` | Weighted full-text search (content 3x, quote 2x, implication 1x, topics 1x, confidence boost) |
| `get_connections` | Typed connections for an atom, supports depth=2 graph traversal |
| `get_atom` | Full atom by ID |

**Registration:** `.mcp.json` at project root (auto-loaded by Claude Code on launch):
```json
{
  "brainsfor": {
    "command": "/opt/homebrew/bin/node",
    "args": ["/Users/robgabel/rob-ai/brainsfor/packages/brainsfor-mcp/dist/index.js"],
    "env": { "BRAINSFOR_HOME": "/Users/robgabel/rob-ai/brainsfor" }
  }
}
```

**Build:** `cd packages/brainsfor-mcp && npm run build` — compiles to `dist/`.

**Key design:** In-memory indexes (atomsById, atomsByTopic, atomsByCluster) built on first load per brain, then cached. Weighted full-text search, not vector (keeps MCP self-contained — no API keys needed). Supabase semantic search is the future upgrade path for a hosted API.

### Two Audiences, Two Paths

- **LLMs** load `brain-context.md` — the single file with everything: synthesis, LLM rules, all atoms, and skill instructions
- **Humans** open `explore.html` — fully data-driven, reads brain-atoms.json (including synthesis section) and renders a browsable UI. Same template for all brains.

### brain.json Synthesis Section

The `synthesis` key in brain.json contains structured data for the "How They Think" tab in explore.html:
- `first_principles` — array of {title, desc}
- `thinking_patterns` — array of {name, desc}
- `contrarian_positions` — array of {title, desc}
- `does_not_believe` — array of {title, desc}
- `would_not_say` — array of {title, desc}
- `biography` — array of {date, role, lesson}
- `skills` — array of {name, title, desc, example}
- `hero_tagline`, `hero_updated` — strings for hero section

This data is exported into brain-atoms.json's `synthesis` key and rendered by explore.html dynamically.

### Atom Schema (belsky_atoms)

| Column | Type | Purpose |
|--------|------|---------|
| content | text | Distilled insight (always present) |
| original_quote | text | Belsky's ACTUAL voice — provocative framing, stories, metaphors |
| implication | text | The "so what" — what this means for builders/leaders |
| confidence_tier | text | high / medium / low |
| cluster | text | One of 16 topic clusters |
| topics | text[] | Topic tags for cross-cluster search |
| embedding | vector(1536) | For semantic search |
| source_ref | text | URL to original newsletter edition |
| source_date | timestamp | Publication date |

### Fully Automated Pipeline (NEW — April 2026)

```
scripts/auto-build-brain.py --person "Jensen Huang"             # Full end-to-end build (~$23, ~60-90 min)
scripts/auto-build-brain.py --person "Annie Duke" --dry-run     # Cost estimate only
scripts/auto-build-brain.py --person "Jensen Huang" --resume    # Resume from last completed phase
scripts/auto-build-brain.py --person "Jensen Huang" --resume-from 3  # Resume from specific phase
```

Takes a person's name and produces a complete, shippable brain pack with ZERO manual approval gates. 6 phases:
- **Phase 0:** Source discovery (web search via Firecrawl → sources.json)
- **Phase 1:** Scaffolding (dirs, brain.json via LLM, Supabase tables, index.json)
- **Phase 2:** Content ingestion (YouTube transcripts + deep research atoms → Supabase)
- **Phase 3:** Synthesis (LLM-generated synthesis.md + brain.json synthesis section)
- **Phase 4:** Enrichment (connections via topic overlap + LLM, auto-applied)
- **Phase 5:** Export & QA (pack generation + audit scoring + remediation loop)

Supports `--skip-phase N`, `--resume`, `--resume-from N`, `--max-sources`, `--target-atoms`, `--model`, `--synthesis-model`. Progress tracked in `brains/{slug}/build-progress.json`.

Config module: `scripts/auto_build_config.py` (shared constants, cost tables, Claude API wrapper with retry logic, prompt templates). **This is the canonical source of truth for all Anthropic model strings used by BrainsFor scripts.** Every Python script in `scripts/` imports `DEFAULT_MODEL`, `SYNTHESIS_MODEL`, and `FAST_MODEL` from here. `website/app/api/skill/route.ts` hardcodes its string separately (TS can't import from Python) with a comment pointing to this file. Current targets: Sonnet 4.6 / Opus 4.7 / Haiku 4.5.

### Export Pipeline

```
brains/{slug}/brain.json (config) + Supabase data
  → scripts/export-brain.py --brain {slug}
    → brains/{slug}/pack/brain-atoms.json (structured data + synthesis)
    → brains/{slug}/pack/brain-context.md (full narrative + skills)
    → brains/{slug}/pack/explore.html (copied from templates/, reads brain-atoms.json)
    → brains/{slug}/pack/skills/{name}/SKILL.md (thin reasoning modes)
    → brains/{slug}/pack/SKILL.md, README.md (from templates)
```

### YouTube Transcript Ingestion (generic — `--brain {slug}`)

```
scripts/ingest-youtube.py --brain {slug} --download                   # Download transcripts from youtube_sources in brain.json
scripts/ingest-youtube.py --brain {slug} --extract                    # Extract atoms from transcripts using Claude Haiku
scripts/ingest-youtube.py --brain {slug} --download --extract         # Both phases
scripts/ingest-youtube.py --brain {slug} --download --video VIDEO_ID  # Single video
scripts/ingest-youtube.py --brain {slug} --extract --limit 5          # Limit to N transcripts
scripts/ingest-youtube.py --brain {slug} --stats                      # Show download/extraction stats
scripts/ingest-youtube.py --brain {slug} --dry-run                    # Preview without writing
```

Requires `youtube-transcript-api` (`pip install youtube-transcript-api`). Configure videos in brain.json `youtube_sources.videos`. Output: `brains/{slug}/research/youtube-atoms.json`.

### Enrichment Scripts (generic — all accept `--brain {slug}`)

```
scripts/enrich-voice.py --brain {slug}                                # Extract original voice from source URLs
scripts/enrich-connections.py --brain {slug} --discover               # Topic overlap + temporal (within + cross-cluster)
scripts/enrich-connections.py --brain {slug} --discover --llm         # + Sonnet LLM analysis (within + cross-cluster)
scripts/enrich-connections.py --brain {slug} --discover --llm --auto-apply  # Autonomous: discover + apply, no review step
scripts/enrich-connections.py --brain {slug} --stats                  # Quality assessment with targets
```

### SQL Table Template

```
templates/create-brain-tables.sql   # sed 's/{{SLUG}}/peter_attia/g' | psql
```

### Skill Architecture (v4 — Unified, 2026-04-11)

**Important:** The PAOS install at `~/rob-ai/skills/` uses a **unified skill architecture** — ONE set of 8 generic reasoning skills + a `/brain` router, not per-brain copies. Any skill can use any installed brain.

- `~/rob-ai/skills/brain/` — router: `/brain <slug>` sets the active brain for the session (writes `~/.claude/state/active-brain.txt`). `/brain list`, `/brain` (show), `/brain clear` supported.
- `~/rob-ai/skills/{advise,teach,debate,connect,evolve,surprise,coach,predict}/` — 8 generic thinking skills. Each resolves the brain via: (1) inline first-token slug override, (2) active brain state file, (3) error if neither.
- Cross-brain mode: `/debate <slug-a> <slug-b> <topic>` and `/connect <slug-a> <slug-b> <topic>`.

Why this design: installing 7+ brain packs naively creates 63+ prefixed skills (`scott-belsky-advise`, `paul-graham-advise`, ...) which collide with the README-documented `/advise` UX. Unified skills match the original v3 intent and README promise. See `IMPROVEMENTS.md` → Architecture & Distribution for the history.

Customer deliverable (`brains/<slug>/pack/skills/`) still ships the per-brain skill files for users who install a single brain pack — those are templates for solo use. The PAOS install flattens them into one generic set because PAOS runs all 8 brains simultaneously.

### /board — Board of Advisors (Multi-Brain Orchestrator)

**Skill:** `~/rob-ai/skills/board/SKILL.md` — orchestrates N independent sub-agents, one per brain, to answer a single question without serial autoregressive contamination.

**Why sub-agents:** When generating 4 persona opinions sequentially in one context window, each output conditions on all prior outputs. By person 3, you get consensus mush. Sub-agents enforce real independence — each brain NEVER reads the other brains' output.

**Commands:** `/board <question>`, `/board set <slug1> <slug2> ...`, `/board list`, `/board clear`.
**State:** `~/.claude/state/board.json`
**Depends on:** `brainsfor` MCP server (selective retrieval) + Claude Code Agent tool (parallel sub-agents).

### MCP-First Skill Loading (all 8 skills)

All 8 reasoning skills (`/advise`, `/teach`, `/debate`, `/connect`, `/evolve`, `/surprise`, `/coach`, `/predict`) now support two context loading paths:

1. **MCP-first (preferred):** `get_synthesis` → `query_atoms` → `search_atoms` → `get_connections` — ~15KB per brain
2. **File fallback:** brain-atoms.json → brain-context.md (when MCP server unavailable)

### Skill Design (v3 — 8 skills, zero overlap)

8 skills, each a distinct reasoning mode with a unique output type:

| # | Skill | Output Type | What It Does |
|---|-------|-------------|--------------|
| 1 | `/advise` | Recommendations | Strategic counsel from the thinker's frameworks |
| 2 | `/teach` | Explanations | Explain concepts through the thinker's lens |
| 3 | `/debate` | Counterarguments | Steel-man the other side (absorbs old `/brainfight`) |
| 4 | `/connect` | Bridges | Find unexpected links between ideas (absorbs old `/mashup`) |
| 5 | `/evolve` | Timeline of thought | Trace how thinking changed over time |
| 6 | `/surprise` | Serendipity | Surface a high-quality atom you haven't seen |
| 7 | `/coach` | Questions | Socratic questioning — no answers, just what to ask yourself |
| 8 | `/predict` | Implication chains | Cascade second and third-order effects of a trend |

**Cut from v2:** `/brainfight` (into `/debate`), `/mashup` (into `/connect`), `/deep-dive` (into `/advise`), `/apply` (into `/advise`).
**Added in v3:** `/coach` (Socratic mode), `/predict` (implication chains — plays to thinkers who forecast).

- Each skill ~15 lines in `skills/{name}/SKILL.md`
- Each skill assumes `brain-context.md` is loaded — no manifest routing, no cluster discovery
- Skill instructions also inline at bottom of `brain-context.md` for LLMs that load that file
- All skills: voice-first (original_quote), thin-topic graceful degradation, suggest next skill
- Template variables: `{{brain_name}}`, `{{brain_first_name}}`, `{{atom_count}}`, etc.

### QA / Audit

**Script:** `scripts/audit-brains.py` — deterministic validator, zero API calls, runs in <2s. Produces a **0-100 completeness score** per brain across 6 weighted criteria.

```
python3 scripts/audit-brains.py                       # Audit all brains (scores + issues)
python3 scripts/audit-brains.py --brain scott-belsky   # Audit one brain
python3 scripts/audit-brains.py --json                 # Machine-readable output
python3 scripts/audit-brains.py --fix-hints            # Include remediation hints
python3 scripts/audit-brains.py --remediate            # Generate runnable fix script
```

**Scoring criteria (6, weighted to 100):**
| Criterion | Weight | What 100% Looks Like |
|-----------|--------|---------------------|
| Structure & Files | /20 | All files, canonical paths, zero duplicates |
| Schema Completeness | /15 | All brain.json keys filled, all synthesis sections |
| Atom Volume | /15 | 200+ atoms |
| Connection Density | /15 | <15% orphans, all atoms linked |
| Voice Enrichment | /20 | 100% original_quote + implication coverage |
| Synthesis Depth | /15 | 1500+ words, all sections, synthesis in export |

**Remediation:** `--remediate` generates a shell script ordered by impact (structural cleanup → re-export → enrichment). Each issue maps to a specific pipeline command.

**Cowork skill:** `/brain-audit` — runs the script (Phase 1), presents scores, generates remediation plan (Phase 2), optionally does LLM-powered semantic review (Phase 3: voice quality spot-check, synthesis coherence, connection quality, cross-brain consistency).

**When to run:** After any export, before deploy, after adding a new brain.

**Behavioral evals (Phase 1 — planned, not yet built):** The current audit is a deterministic linter (structure, schema, coverage). It doesn't test whether a brain actually answers like the thinker. A behavioral eval harness is specced in [`projects/brain-evals-phase1.md`](../projects/brain-evals-phase1.md) — 20 prompts per brain, Haiku judge, 0-100 behavioral score, adversarial prompts derived from each brain's `would_not_say` / `does_not_believe` synthesis sections. Integrates with `audit-brains.py --with-behavioral`. Phase 2 (public Quality Score on brainsforfree.com + monthly regression) is in `~/rob-ai/ideas/OPPORTUNITIES.md`.

### Adding a New Brain

**Automated (recommended):** One command, zero babysitting.

**Local** (at desktop, uses `~/rob-ai/.env`):
```bash
cd ~/rob-ai/brainsfor
python3 scripts/auto-build-brain.py --person "Annie Duke"
```

**Remote** (mobile, or walk-away — runs as GitHub Action, 180-min timeout, auto-commits pack to `main` on success → Vercel auto-deploys to brainsforfree.com):
```bash
gh workflow run build-brain.yml --repo robgabel/brainsfor \
  -f person="Annie Duke" -f confirm_cost=yes-23
gh run watch --repo robgabel/brainsfor
```
Workflow: `.github/workflows/build-brain.yml`. Required repo secrets: `ANTHROPIC_API_KEY`, `SUPABASE_SERVICE_KEY`, `SUPABASE_URL`. Optional: `FIRECRAWL_API_KEY` (degrades phase 0), `SLACK_BUILD_WEBHOOK` (phase pings silent if unset). Resume with `-f resume=true`.

Both paths run the same 6 phases (source discovery → scaffolding → ingestion → synthesis → enrichment → export + QA) end-to-end. Cost: ~$23. Time: ~60-90 min. See "Fully Automated Pipeline" section above for flags and details.

**Or via Cowork skill:** `/brain-build Annie Duke` — auto-picks local or remote based on whether `~/rob-ai/.env` is present.

**Manual fallback** (if automation fails or you want fine-grained control):
1. **Create directory:** `brains/{slug}/` with `brain.json`, `synthesis.md`, `source/`, `research/`, `data/`, `pack/`
2. **Create Supabase tables:** `sed 's/{{SLUG}}/{slug}/g; s/{{NAME}}/{Name}/g' templates/create-brain-tables.sql | psql`
3. **Fill brain.json:** Copy from scott-belsky, replace all values (name, source, clusters, skill examples, synthesis)
4. **Write synthesis.md:** First principles, thinking patterns, contrarian positions (manual research, 4-8 hours)
5. **Ingest atoms:** Load source content into `{slug}_atoms` table
6. **Run enrichment:** `python scripts/enrich-voice.py --brain {slug}` and `python scripts/enrich-connections.py --brain {slug} --discover --llm`
7. **Export pack:** `python scripts/export-brain.py --brain {slug} --from-files atoms.json connections.json`
8. **Register:** Add entry to `brains/index.json`
9. **Verify:** Open `pack/explore.html` in browser, check all tabs render correctly

## Design System

`DESIGN.md` in the project root defines BrainsFor's visual identity. Based on the [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) format (Google Stitch DESIGN.md standard). Any AI agent can read it and generate on-brand UI.

**Design DNA:** Stripe-inspired premium knowledge aesthetic. Light-first with warm paper alternating sections. Space Grotesk weight-300 display type ("whispered authority"). Brain Indigo (`#6366f1`) as the singular accent. Indigo-tinted multi-layer shadows. Knowledge Gold (`#d97706`) reserved for premium moments only.

**How to use:** Drop `DESIGN.md` into any project folder or paste into an AI agent context, then say "build me a page that looks like this." All 9 sections (theme, colors, typography, components, layout, depth, do's/don'ts, responsive, agent prompts) give agents everything they need for pixel-perfect output.

**Cluster colors** (for atom cards and topic visualization): Product/Design `#6366f1`, AI/Tech `#0ea5e9`, Leadership `#d97706`, Creativity `#ec4899`, Business `#059669`, Culture `#8b5cf6`.

## Key Documents

- **`BACKLOG.md`** — **Brain candidate backlog.** 8 women thinkers queued for future brain packs, with source richness ratings, rationale, cross-brain potential, and build priority. **Start here when deciding what brain to build next.**
- `personas.md` — 7 customer personas with JTBD, objections, channels, WTP, killer features. Stack-ranked by priority.
- `IMPROVEMENTS.md` — Full improvement backlog from April 2026 critique panel.
- `business-plan.md` — Strategy doc (Greg Isenberg style).
- [`~/rob-ai/projects/brain-evals-phase1.md`](../projects/brain-evals-phase1.md) — Spec for the behavioral eval harness (20 prompts × 15 brains, Haiku judge, constitutional constraints). Not yet built — target 2026-05-04.

## Remaining Questions

- [ ] Pricing model — subscription vs. one-time purchase vs. freemium?
- [ ] Distribution: working `npx skills add` command pointing to `brains/{slug}/pack/`
- [x] Next brain pack after Belsky? → See `BACKLOG.md` — 8 candidates queued, top 3: Brené Brown, Annie Duke, Kara Swisher
- [ ] Legal/licensing framework for packaging a person's published thinking?
- [ ] Supabase schema migration to generic `brain_atoms` table (Phase 7)

See `IMPROVEMENTS.md` for the full backlog from the April 2026 critique panel.
