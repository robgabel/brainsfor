# BrainsFor Doc Refresh Log

## Doc Refresh — 2026-04-21 (run 6)

### Context
Automated nightly run. Discovered two large state shifts since run 5:
1. Two new brains (Brené Brown, Oprah Winfrey) shipped as packs but aren't yet ingested into Supabase — they exist as `brains/<slug>/pack/` + `website/public/brains/<slug>/` only, with no `brene_brown_*` or `oprah_winfrey_*` tables in the DB.
2. Peter Zeihan pack was re-exported down to 362 atoms (matches Supabase now). Run 5's sync of `atom_count` up to 460 is stale — reverted back to 362.
3. Supabase connection tables have grown substantially via the daily `enrich-connections` edge function cron — most brains' DB connection counts are now 2-6x what the shipped packs contain. Root cause: `export-brain.py` calls Supabase with a single `.execute()` (no pagination), so shipped packs are capped at ~1,000 connections regardless of true DB totals.

### Changes Applied

**brains/index.json + website/public/brains/index.json** (kept in lockstep):
- peter-zeihan `atom_count` 460 → 362 (reverts run-5 change; pack + Supabase both say 362)
- Connection counts updated to live Supabase values per doc-refresh contract ("trust Supabase"):
  - charlie-munger 200 → 1,262
  - hank-green 366 → 1,245
  - john-green 385 → 1,301
  - paul-graham 409 → 975
  - peter-attia 433 → 1,220
  - scott-belsky 430 → 1,515
  - steve-jobs 792 → 1,618
  - sun-tzu 377 → 1,283
  - gary-vee 505 → 1,850
  - peter-zeihan 308 → 1,503
  - dario-amodei 502 → 1,842
  - elon-musk 202 → 1,563
  - jensen-huang 220 (unchanged — Supabase is 0/0, pack authoritative)
  - brene-brown 321 (unchanged — no Supabase table)
  - oprah-winfrey 355 (unchanged — no Supabase table)

**business-plan.md** (Live inventory table):
- Header: "13 brains built, packaged, and in Supabase" → "15 brain packs built, packaged, and shippable (13 in Supabase)"
- Peter Zeihan row: 460 atoms / 308 conns → 362 atoms / 1,503 conns
- Added Brené Brown row: 283 / 321 / "20+ years of research, 6 bestselling books, TED talks, Dare to Lead podcast" / "Leadership, vulnerability research, organizational culture"
- Added Oprah Winfrey row: 333 / 355 / "Decades of The Oprah Winfrey Show, O Magazine, SuperSoul conversations, commencement addresses, and published books" / "Influence, interview craft, personal transformation, cultural reach"
- Updated all other brains' connection counts to Supabase values (same deltas as index.json above)
- TOTAL row: 3,231 atoms / 5,129 conns → 3,749 atoms / 18,073 conns
- Infrastructure stats: "13 `brain_metadata` records" → added note that Brené Brown and Oprah Winfrey aren't yet ingested; added "0 `brain_requests` logged to date"; audit avg line updated to cite 15 live brains
- Removed Brené Brown from the "Next Wave" candidate table (promoted to Live)

**brainsfor/CLAUDE.md**:
- Tables header: "15 brains live" → "15 brain packs built; 13 live in Supabase"
- Rewrote `<slug>_atoms` and `<slug>_connections` example lists to cite current Supabase counts (Gary Vee 1,850 is now the largest connection table; Steve Jobs dropped to #3)
- `brain_metadata` line: "15 rows" → "13 rows (Supabase-hosted brains; Brené Brown and Oprah Winfrey shipped as packs only, not yet ingested)"
- Added `brain_requests — 0 rows` line
- Expanded Known Data Drift block: kept jensen_huang note; added Brené Brown / Oprah Winfrey "no Supabase tables" note; added new "pack connection count ~1,000 cap" note citing the `export-brain.py` pagination bug
- Removed "peter_zeihan_atoms in DB is 362 while the pack has 460 — pack is authoritative, re-ingestion pending" — obsolete now that pack was re-exported to 362
- Storefront directory entry: added "Directory is now empty" note
- Remaining Questions "Next brain pack after Belsky?" checkbox answer updated to reflect Brené + Oprah shipped and Annie Duke scaffolded

**IMPROVEMENTS.md**:
- Voice enrichment line: "(85%)" → "(84.5%)" (same 240/284 count, more precise)
- Footer Last-updated block rewritten end-to-end: run 5 → run 6; "13 brains / 3,231 atoms / 5,129 connections" → "15 shippable brain packs / 3,749 atoms / 18,073 Supabase connections"; added 3 open flags (jensen_huang empty tables, brene/oprah no Supabase tables, export-brain.py pagination bug)

### No Changes Needed
- `BACKLOG.md` — not a target doc for this run
- Ship Plan (Pinned "Next Up for First Users" section in IMPROVEMENTS.md) — none of the three tier items have shipped; no checkboxes to flip
- `DESIGN.md`, `BRAND.md`, `PRD-site-overhaul.md` — not target docs
- `personas.md` — not a target doc
- Pricing, revenue, go-to-market sections in business-plan.md — per refresh contract, don't touch strategic/opinion content

### Quality Scores (audit-brains.py)
- charlie-munger 100, paul-graham 100, gary-vee 100, jensen-huang 100, dario-amodei 100, john-green 100
- sun-tzu 99, peter-zeihan 99, elon-musk 99
- brene-brown 98, hank-green 97, scott-belsky 97, steve-jobs 97, oprah-winfrey 97
- peter-attia 93
- annie-duke 24 (scaffolded — expected)
- Live-brain average: ~98/100 (15 brains, annie-duke excluded)

### Flagged for Human Review
1. **Connection-count jump in customer-facing surfaces.** Per-brain `connection_count` on index.json and business-plan.md jumped 2-6x (e.g. Belsky 430 → 1,515; Gary Vee 505 → 1,850). These reflect live Supabase totals, but the *shipped* pack JSON files are still capped at ~1,000. Customer-visible counts may now overstate what a buyer actually gets until the export bug is fixed and packs are re-exported.
2. **`export-brain.py` connection pagination bug.** Line 494: `sb.table(connections_table).select("*").execute().data` — no pagination, so Supabase's default row cap truncates everything above ~1,000. Atoms are paginated correctly (lines 477-485); connections are not. Suggested fix: mirror the atoms pagination loop.
3. **Brené Brown and Oprah Winfrey missing from Supabase.** Packs shipped and live on brainsforfree.com, but `brene_brown_atoms/connections` and `oprah_winfrey_atoms/connections` tables don't exist. `brain_metadata` only has 13 rows. `/board`, cross-brain search, and any Supabase-backed flow will silently skip these two brains.
4. **Jensen Huang Supabase tables still empty** (0/0) — unchanged since run 5. Pack authoritative. Re-ingestion still pending.
5. **Peter Zeihan atom count reverted** (460 → 362) — run 5 sync was based on a stale pack file; pack has since been re-exported to 362, which matches Supabase. If 460 was the "correct" target, the pack needs to be rebuilt, not the index.

---

## Doc Refresh — 2026-04-17 (run 5)

### Context
Follow-up run after a live debugging session: user reported broken "Explore this brain" preview on brainsforfree.com. Diagnosis: `next.config.ts` was sending `X-Frame-Options: DENY` on every URL, which blocked the page at `/brains/<slug>` from iframing `/brains/<slug>/explore.html`. Fixed to `SAMEORIGIN` and pushed. Run 4 log entry noted that Peter Zeihan pack (460 atoms) disagreed with index.json (362) — user noticed the site was showing 362, so we synced index.json + website/public/brains/index.json up to 460 (pack was re-exported, docs had lagged).

### Changes Applied

**website/next.config.ts** (prod bug fix — commit 364fa75):
- `X-Frame-Options: DENY` → `SAMEORIGIN` — unblocks same-origin iframe for brain Explorer. Was breaking every brain page.

**brains/index.json + website/public/brains/index.json** (commit 4e1c432):
- peter-zeihan `atom_count` 362 → 460 (pack was authoritative; indices had lagged)

**Deleted** (commit fb44bbf):
- `storefront/landing-page-prototype.html` — obsolete, superseded by live `website/` Next.js app

**business-plan.md**:
- Peter Zeihan inventory row: 362 → 460 atoms
- TOTAL row: 3,133 → 3,231 atoms (connections unchanged at 5,129)
- Infrastructure stats: landing page prototype sentence → **"brainsforfree.com is live"** (Next.js app in `website/`, Vercel auto-deploy from `main`)

**brainsfor/CLAUDE.md** (major revision):
- Tables section rewritten: `belsky_atoms` → `scott_belsky_atoms`, `belsky_connections` → `scott_belsky_connections`, `belsky_enrichment_log` → `scott_belsky_enrichment_log` (legacy `belsky_enrichment_log` still exists, noted). Listed 13 brains with actual DB counts.
- Added Known Data Drift block: `jensen_huang_*` empty (0/0), `peter_zeihan_atoms` in DB (362) vs pack (460) — pack authoritative
- Added `rob_atoms` / `rob_connections` (225 / 162) to table list
- Directory Structure: added `website/` tree (full — app/, lib/, public/brains/, AGENTS.md with warning, next.config.ts SAMEORIGIN note); marked `storefront/` DEPRECATED; added `PRD-site-overhaul.md`, `naming-exploration.md`, `doc-refresh-log.md` to top-level entries

**IMPROVEMENTS.md**:
- Last-updated footer: run 4 → run 5 entry. Notes catalog at 3,231 atoms, brainsforfree.com live, the SAMEORIGIN prod fix, landing-page-prototype deletion, `/coach` 3-mode uplevel.

### No Changes Needed
- `brains/<slug>/pack/brain-atoms.json` files — all in sync with website/public/brains/
- `audit-brains.py` scores — same as run 4 (avg 97/100)
- Cross-connections — still 17

### Quality Scores (audit-brains.py) — avg 97/100
Same as run 4 — no new brain builds since then. Highlights:
- jensen-huang: 100 (pack quality high despite Supabase being empty)
- dario-amodei: 98 (orphan 22%, still flagged)
- elon-musk: 99 (template var `{{brain_source_ethics}}` still unresolved in pack/SKILL.md)

### Flagged for Human Review
- **jensen-huang Supabase tables still empty** (0/0) — not touched this run. Action unchanged: re-seed.
- **peter-zeihan pack (460) > Supabase (362)** — docs now consistent at 460 (site displays 460, pack says 460), but Supabase is out of sync with both. Action: `python3 scripts/enrich-voice.py --brain peter-zeihan` or re-ingest into Supabase.
- **dario-amodei orphan rate 22%** — still open: `python3 scripts/enrich-connections.py --brain dario-amodei --discover --llm --auto-apply`
- **`{{brain_source_ethics}}` template var** — still unresolved in several `pack/SKILL.md` files. Fix: re-run `export-brain.py` for affected brains.
- **Legacy `belsky_enrichment_log` table** — safe to drop after confirming `scott_belsky_enrichment_log` is the only consumer.

---

## Doc Refresh — 2026-04-17

### Changes Applied

**business-plan.md** (8 edits):
- Live brains header: "10 brains" → "13 brains"
- Added 3 rows to inventory table: Dario Amodei (353/502), Elon Musk (247/202), Jensen Huang (253/220)
- Peter Attia row: 73/40 → 153/433 (catalog-level enrichment)
- Peter Zeihan row: 460/0 → 362/308 (DB now has connections)
- TOTAL row: 2,298 / 3,504 → 3,133 / 5,129
- Infrastructure stats: "10 `brain_metadata` records" → "13", pipeline pointer updated from `build-brain.py` (7 stages) to `auto-build-brain.py` (6 phases, ~$23), added "avg score 97/100 across 13 brains"
- Brain Score note (product section): voice enrichment 84% / 45 remaining → 85% / 44 remaining
- Ship Plan "What's DONE": 10 brains → 13 brains, 2,298/3,504 → 3,133/5,129, 10 packs → 13, "(5/10 brains rendered)" → "(13/13 brains rendered)", added `@brainsfor/mcp` + `/board` rows, pipeline line updated to `auto-build-brain.py`
- Ship Plan "What's LEFT" Storefront: checked off "Add 5 missing brains to landing page" → complete (13/13)
- Ship Plan Quality: voice 84% (239/284) → 85% (240/284)
- Success Metrics Week 1: "7 brains built" → "13 brains built"
- Why Rob section: "ten times over, 10 brains live with 2,298 atoms, 3,504 connections" → "thirteen times over, 13 brains live with 3,133 atoms, 5,129 connections"
- Channel 8 micro-content: "10 brains today, 2,298 pieces" → "13 brains today, 3,133 pieces"
- TL;DR current state: 10 brains / 2,298 / 3,504 → 13 brains / 3,133 / 5,129, added Dario Amodei + Elon Musk + Jensen Huang to name list, "landing page prototype with all 13 brains"

**IMPROVEMENTS.md** (2 edits):
- Voice recovery bullet: 239/284 (84%), 45 remaining → 240/284 (85%), 44 remaining
- Last-updated footer: 2026-04-15 (run 3) → 2026-04-17 (run 4); summarized catalog growth, DB remediation for charlie-munger + peter-zeihan + peter-attia, and flagged jensen_huang empty-DB anomaly

**brains/index.json**: No changes — all 13 declared counts match Supabase (except jensen-huang, flagged rather than overwritten; see below).

**brainsfor/CLAUDE.md**: No changes — Belsky-specific facts (284/430) still accurate; all other sections are architecture/pipeline docs without drift.

### No Changes Needed
- `brainsfor/CLAUDE.md`: no per-brain counts to drift
- `brains/index.json`: 12/13 entries match Supabase exactly; jensen-huang flagged (see below)
- `cross_connections`: still 17, matches business-plan
- Storefront: 13 brain cards already present in landing-page-prototype.html

### Quality Scores (audit-brains.py) — avg 97/100, 7/13 passing
- charlie-munger: 100 ✓
- john-green: 100 ✓
- dario-amodei: 98 (orphan 22%)
- elon-musk: 99 (missing synthesis.skills, template var in pack/SKILL.md)
- hank-green: 96 (template var in pack/SKILL.md)
- (others scored similarly; template var `{{brain_source_ethics}}` persists in multiple pack/SKILL.md files)

### Flagged for Human Review
- **NEW: jensen-huang Supabase tables empty (0/0)** despite pack files shipping 253 atoms / 220 connections and brain listed live in index.json. Either data was never loaded to Supabase or was dropped after pack export. Not trusting Supabase blindly here because the pack is shipped; left index.json at 253/220 pending investigation. Action: verify source of truth and re-seed `jensen_huang_atoms` + `jensen_huang_connections` if needed.
- **peter-zeihan: pack still shows 460 atoms** but Supabase/index.json now agree on 362. Pack drifted above DB. Action: `python3 scripts/export-brain.py --brain peter-zeihan` to align pack with authoritative DB.
- **RESOLVED: charlie-munger DB** now populated (218/200) ✓
- **RESOLVED: peter-attia underenriched** — now 153 atoms / 433 connections (catalog-level)
- **Ongoing: `{{brain_source_ethics}}` template var** unresolved in several brains' pack/SKILL.md (hank-green, elon-musk confirmed; re-run export to fix)
- **Ongoing: dario-amodei orphan rate 22%** (target <15%) — run `enrich-connections.py --brain dario-amodei --discover --llm --auto-apply`

---

## Doc Refresh — 2026-04-15 (run 2)

### Changes Applied
- `brains/index.json`: peter-zeihan connection_count 308 → 0 (align with Supabase + all docs)
- `business-plan.md`: Ship Plan "Landing page prototype (5/7 brains rendered)" → "(5/10 brains rendered)"
- `business-plan.md`: Ship Plan TODO updated from "John Green + Hank Green" → "5 missing brains" (added Charlie Munger, Gary Vaynerchuk, Peter Zeihan)
- `IMPROVEMENTS.md`: Last-updated note refreshed with run 2 status

### No Changes Needed
- `brainsfor/CLAUDE.md`: Belsky 284/430 still accurate; no other per-brain counts to drift
- `business-plan.md`: All per-brain atom/connection counts in inventory table match (Zeihan 460/0 matches pack files)
- `business-plan.md`: Totals 2,298 atoms / 3,504 connections / 17 cross-connections all correct
- `business-plan.md`: Belsky voice enrichment 84% (239/284) confirmed by DB

### Quality Scores (audit-brains.py) — avg 94, 5/10 passing
- charlie-munger: 100 ✓
- john-green: 100 ✓
- gary-vee: 100 ✓ (was 85 — pack re-exported, connections now included)
- sun-tzu: 99 ✓
- peter-zeihan: 97 (new — first scored this run)
- scott-belsky: 97
- hank-green: 96
- paul-graham: 95
- steve-jobs: 93
- peter-attia: 66

### Flagged for Human Review
- **RESOLVED: gary-vee pack re-exported** — audit score 85→100, connections now in pack. Remove from prior flags.
- **PROGRESS: peter-zeihan DB now has 408 atoms** (was 0). 52-atom gap vs pack files (460). Connections still 0 in DB, 0 in docs. index.json connection_count corrected 308→0.
- **Ongoing: charlie-munger DB empty** (0/0 in Supabase, 218/200 in pack files)
- **Ongoing: peter-attia underenriched** (73 atoms, 40 connections, voice 0%, orphan 36%, score 66)
- **Ongoing: {{brain_source_ethics}} template var** unresolved in multiple brains' pack/SKILL.md

---

## Doc Refresh — 2026-04-15

### Changes Applied

**business-plan.md** (6 edits):
- "9 brains built" → "10 brains built" in Live header
- Added Peter Zeihan row to inventory table; TOTAL atoms 1,838 → 2,298
- Ship Plan checklist: "Build 9 brains" → 10, atom count 1,838 → 2,298, "pack/ for all 9" → 10
- Micro-content section: "9 brains today, 1,838 micro-content" → "10 brains, 2,298"
- Proof-of-concept: "nine times over, 9 brains live with 1,838 atoms" → "ten times over, 10 brains live with 2,298 atoms"
- TL;DR: "9 brains live, 1,838 atoms" → "10 brains live, 2,298 atoms" + added Peter Zeihan to name list
- Infrastructure stats: "All 9 brains" → "All 10 brains"

**~/rob-ai/CLAUDE.md** (2 edits):
- "9 brain packs" → "10 brain packs"
- Added Peter Zeihan row to Installed Brains table (460 atoms, 0 connections)

**brainsfor/IMPROVEMENTS.md** (1 edit):
- Last-updated date 2026-04-13 → 2026-04-15; added Peter Zeihan note and peter-zeihan DB empty flag

**brainsfor/CLAUDE.md**: No changes needed — Belsky-specific facts unchanged.

### Flagged Items
- `charlie_munger`: 0 atoms / 0 connections in Supabase (pack files exist locally with 218 atoms)
- `peter_zeihan`: 0 atoms / 0 connections in Supabase (pack files exist locally with 460 atoms)
- `peter_attia`: underenriched (73 atoms, 40 connections — lowest of all brains)
- `gary_vee`: pack may need re-export (flagged in prior runs)

### State Snapshot
- **Brains:** 10 live (up from 9)
- **Total atoms (index.json):** 2,298 (up from 1,838 — Peter Zeihan added 460)
- **Total connections (index.json):** 3,504 (unchanged)
- **brain_metadata rows:** 10
- **cross_connections:** 17

## Doc Refresh — 2026-04-13

### Changes Applied
- `IMPROVEMENTS.md`: Last updated date 2026-04-11 → 2026-04-13

### No Changes Needed
- `business-plan.md`: All 9 brain counts match Supabase and index.json (totals: 1,838 atoms / 3,504 connections / 17 cross-connections ✓)
- `business-plan.md`: brain_metadata 10 ✓, voice enrichment 84% (239/284) ✓
- `brainsfor/CLAUDE.md`: belsky_atoms 284 / belsky_connections 430 — no factual drift
- `brains/index.json`: All counts match Supabase for 8/9 brains (charlie-munger is pack-only, no DB rows — unchanged from prior run)

### Quality Scores (audit-brains.py) — avg 92, 3/9 passing
- charlie-munger: 100 ✓
- john-green: 100 ✓
- sun-tzu: 99 ✓
- scott-belsky: 97 (template var)
- hank-green: 96 (template var, missing synthesis sections)
- paul-graham: 95
- steve-jobs: 93 (template var, missing synthesis sections)
- gary-vee: 85 (pack export has 0 connections despite 505 in DB)
- peter-attia: 66 (orphan 36%, voice 0%, only 73 atoms)

### Flagged for Human Review
- **Ongoing: charlie_munger DB empty** (0 atoms, 0 connections in Supabase) but index.json declares 218/200. Data is pack-only. Either seed DB or document as intended.
- **Ongoing: peter_zeihan tables exist** in Supabase (empty) with brain_metadata row — not in index.json. New brain in early setup?
- **Ongoing: gary-vee pack export stale** — 505 connections in Supabase, 0 in local pack. Needs: `python3 scripts/export-brain.py --brain gary-vee`
- **Ongoing: `{{brain_source_ethics}}` template var** unresolved in 6/9 brains' pack/SKILL.md
- **Ongoing: peter-attia** — voice 0%, orphans 36%, only 73 atoms

---

## Doc Refresh — 2026-04-11 (run 2)

### Changes Applied
- `brains/index.json`: gary-vee connection_count 0 → 505 (Supabase source of truth)
- `business-plan.md`: brain count 7 → 9 (added Charlie Munger + Gary Vaynerchuk rows to inventory table)
- `business-plan.md`: total atoms 1,374 → 1,838, total connections 2,799 → 3,504
- `business-plan.md`: brain_metadata count 7 → 10
- `business-plan.md`: Belsky voice enrichment 7% (20/284) → 84% (239/284) — 3 occurrences updated
- `business-plan.md`: "7 brains" → "9 brains" across Ship Plan, proof-of-concept, TL;DR sections
- `IMPROVEMENTS.md`: voice recovery 20/284 (7%) → 239/284 (84%)
- `IMPROVEMENTS.md`: last updated date refreshed
- `~/rob-ai/CLAUDE.md` (root): brain count 8 → 9, added gary-vee row to Installed Brains table

### No Changes Needed
- `brainsfor/CLAUDE.md`: belsky_atoms 284 ✓, belsky_connections 430 ✓ — no factual drift in project CLAUDE.md
- Atom/connection counts for 7 original brains all match between index.json and Supabase

### Quality Scores (audit-brains.py) — avg 92, 3/9 passing
- charlie-munger: 100 ✓
- john-green: 100 ✓
- sun-tzu: 99 ✓
- scott-belsky: 97 (template var unresolved)
- hank-green: 96 (template var, missing synthesis sections)
- paul-graham: 95
- steve-jobs: 93 (template var, missing synthesis sections)
- gary-vee: 85 (0 connections in pack export despite 505 in DB, 100% orphans)
- peter-attia: 66 (orphan 36%, voice 0%, only 73 atoms)

### Flagged for Human Review
- **NEW: peter_zeihan tables exist in Supabase (atoms + connections, both empty) + brain_metadata row — not in index.json.** New brain in early setup?
- **NEW: charlie_munger DB tables empty (0 atoms, 0 connections) but index.json declares 218/200.** Data lives in pack files only — never loaded to Supabase. Either seed DB or document as pack-only brain.
- **NEW: gary-vee has 505 connections in Supabase but pack export shows 0 connections (100% orphan atoms).** Needs re-export: `python3 scripts/export-brain.py --brain gary-vee`
- Unresolved `{{brain_source_ethics}}` template var in 6/9 brains' pack/SKILL.md — re-run export-brain.py
- Peter Attia voice enrichment still at 0%, orphan rate 36%
- Belsky voice enrichment improved significantly: 7% → 84% (239/284). 45 atoms remaining.

---

## Doc Refresh — 2026-04-11

### Changes Applied
- `IMPROVEMENTS.md`: Last updated 2026-04-10 → 2026-04-11

### No Changes Needed
- `brains/index.json`: all 7 brain counts match Supabase exactly (Belsky 284/430, Peter Attia 73/40, Paul Graham 213/409, Steve Jobs 170/792, John Green 205/385, Sun Tzu 207/377, Hank Green 222/366)
- `business-plan.md` Ship Plan: totals still 1,374 atoms / 2,799 connections / 17 cross-connections ✓
- `business-plan.md` voice enrichment: still 20/284 Belsky atoms (7%) ✓
- `business-plan.md` infrastructure: 7 brain_metadata records ✓, 0 brain_requests (form still unwired) ✓
- `CLAUDE.md`: Belsky 284 atoms / 430 connections still accurate — no factual drift
- `IMPROVEMENTS.md` Active Plan checkboxes: no status changes since 2026-04-10

### Quality Scores (audit-brains.py) — avg 90, 2/7 passing
- scott-belsky: 81 (warning: voice 7%, template var unresolved)
- peter-attia: 66 (orphan atoms 36%, voice 0%, 73 atoms, template var)
- paul-graham: 95 ✓
- steve-jobs: 93
- john-green: 100 ✓
- sun-tzu: 99
- hank-green: 96

### Flagged for Human Review
- No new discrepancies since the 2026-04-10 run. All prior flags still open:
  - Unresolved `{{brain_source_ethics}}` template var in scott-belsky + peter-attia pack/SKILL.md — re-run `export-brain.py`
  - Peter Attia voice enrichment at 0%, orphan rate 36%
  - Belsky voice enrichment still at 7% (no change in 24hrs)
  - Live site brainsforfree.com renders all 7 brains ✓ — but local `storefront/landing-page-prototype.html` only has 5 (missing John Green + Hank Green). Prototype has drifted from production; either update the prototype or retire it.
  - Cowork skills registered for only 2/7 brains (scott-belsky + paul-graham); peter-attia, steve-jobs, john-green, sun-tzu, hank-green not symlinked into `~/rob-ai/skills/`
  - `brain_requests` table still 0 rows (form unwired — matches Ship Plan status)

---

## Doc Refresh — 2026-04-10

### Changes Applied
- `brains/index.json`: peter-attia connection_count 0 → 40 (Supabase source of truth)
- `IMPROVEMENTS.md`: Last updated 2026-04-04 → 2026-04-10

### No Changes Needed
- `business-plan.md` Ship Plan: all 7 brain counts match Supabase (Belsky 284/430, Hank Green 222/366, Paul Graham 213/409, Sun Tzu 207/377, John Green 205/385, Steve Jobs 170/792, Peter Attia 73/40)
- `business-plan.md` totals: 1,374 atoms / 2,799 connections / 17 cross-connections ✓
- `business-plan.md` infrastructure stats: 7 brain_metadata records ✓, 5/7 landing page coverage ✓ (John Green + Hank Green still not rendered), voice enrichment 7% (20/284 Belsky) ✓
- `CLAUDE.md`: structural/reference content only, no factual counts to drift
- `IMPROVEMENTS.md` Active Plan checkboxes: voice recovery still at 20/284 (7%), all other items unchanged

### Quality Scores (audit-brains.py)
- scott-belsky: 81 (warning: voice enrichment 7%, template var unresolved)
- peter-attia: 66 (orphan atoms 36%, voice 0%, only 73 atoms, template var unresolved)
- paul-graham: 95 ✓
- (full output truncated — remaining 4 brains not captured in this run)

### Flagged for Human Review
- `peter_attia_connections` table has 40 rows in Supabase but audit JSON shows `declared_connection_count: 40` with `actual_connections_refs: 80` — possible double-counting in export pipeline. Also 26/73 (36%) orphan atoms. Consider running `enrich-connections.py --brain peter-attia --discover --llm --auto-apply`.
- `scott_belsky_connections` shows 430 declared vs 860 actual refs — same 2× pattern, may be expected (each connection references two atoms).
- Unresolved template var `{{brain_source_ethics}}` in pack/SKILL.md files — re-run `export-brain.py` to fix.
- Cowork skills registered in `~/rob-ai/skills/`: only `scott-belsky-brain`, `scott-belsky-brainfight`, `paul-graham-brain`, `paul-graham-brainfight`. The other 5 live brains (peter-attia, steve-jobs, john-green, sun-tzu, hank-green) have pack/ dirs but no registered Cowork skills — distribution gap.
- `brain_requests` table has 0 rows — "Request a Brain" form not yet wired to storefront (expected, still in Ship Plan).

---
