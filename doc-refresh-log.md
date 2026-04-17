# BrainsFor Doc Refresh Log

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
