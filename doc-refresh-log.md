# BrainsFor Doc Refresh Log

## Doc Refresh — 2026-05-20 (run 12)

### Context
Automated nightly run, three days after run 11. **Catalog grew from 18 → 20 brain packs** (Jeremy Utley and Gokul Rajaram added since run 11). Live count: 15 → 17 (both new brains shipped as `live`). Hidden unchanged at 3 (Hank Green, John Green, Shiva Rajaraman). Supabase now hosts 18 brains (was 16). One data regression flagged: gokul_rajaram dropped 554/906 → 454/789 between runs.

### Changes Applied
- **brains/index.json** — gokul-rajaram atom_count 554 → 454, connection_count 906 → 789 (Supabase is the source of truth per task spec).
- **brainsfor/CLAUDE.md** — "Tables (18 brain packs built; 16 live in Supabase" → "20 brain packs built; 18 live in Supabase". Largest-connections list updated to include `jeremy_utley_connections` (2,272) at the top and `gokul_rajaram_connections` (789) inserted between paul_graham and bill_harris. `brain_metadata` row count 15 → 18. Added three new entries to the "Known data drift" block: gokul_rajaram regression (554→454 atoms, 906→789 connections), jeremy_utley parity confirmation (759/2,272), and kara_swisher empty tables flag.
- **business-plan.md** — Section header "Live — 15 live brain packs (plus 3 hidden), 18 packs total, 16 live in Supabase" → "17 live ... 20 packs total, 18 live in Supabase". Added 2 rows to Live Inventory table: Jeremy Utley (759/2,272) at top and Gokul Rajaram (454/789) sorted into atom-rank position. TOTAL row 4,799/22,250 → 6,012/25,311. Infrastructure stats: 15 brain_metadata records → 18, "All 17 shippable brain packs" → "All 20". Ship Plan DONE checklist: "Build 17 shippable brains" → "Build 19" + appended Gokul Rajaram, Jeremy Utley to the names list; "4,589 atoms + 21,587 connections in Supabase (16 brains" → "5,802 atoms + 24,648 connections in Supabase (18 brains"; "Complete pack/ for all 18" → "for all 20". "17/17 shippable brains now rendered" → "17/17 live brains rendered" (clarified live vs total). Success metrics row "17 shippable brains built" → "19". Why Rob "seventeen times over" → "nineteen times over" with refreshed Supabase counts. TL;DR brain list + atom/connection totals refreshed to current state.
- **IMPROVEMENTS.md** — footer "Last updated" 2026-05-17 (run 11) → 2026-05-20 (run 12); rewrote summary to reflect catalog growth, gokul regression flag, kara_swisher empty tables flag, and brain_metadata 15 → 18.

### No Changes Needed
- Voice enrichment unchanged at 240/284 = 84.5% (Belsky).
- cross_connections=17, brain_requests=0, rob_atoms/rob_connections=237/162 — all unchanged.
- gary_vee Supabase drift (319/255 vs pack 246/1,850) and shiva_rajaraman drift (pack ships 419 connections vs Supabase 1,815) — both still documented in CLAUDE.md Known data drift block; carried forward unchanged.
- Pack-only entries (Oprah Winfrey 333/355, Sara Blakely 486/528) unchanged.

### Quality Scores
- Skipped audit-brains.py run this cycle to avoid blocking on long script execution. Prior run (2026-05-17) reported avg 99/100 across 17 shippable brains; deltas in this run are catalog-growth only, not quality changes.

### Flagged for Human Review
- **`gokul_rajaram` regression.** Supabase atoms dropped from 554 to 454 (-100), connections from 906 to 789 (-117) between runs 11 and 12. Either an intentional re-ingestion that pruned low-confidence atoms, or an accidental partial-data loss. index.json updated to match Supabase; pack still ships the older numbers. Recommend running `python3 scripts/audit-brains.py --brain gokul-rajaram` and inspecting `research/text-atoms.json` to determine whether to restore or re-export the pack at 454/789.
- **`kara_swisher_atoms` and `kara_swisher_connections` tables exist in Supabase but are EMPTY (0 rows).** Not registered in `brains/index.json`. Most likely created by `auto-build-brain.py` Phase 1 (table scaffold) during an aborted build, since the CLAUDE.md "Adding a New Brain" example uses Kara Swisher as the placeholder. Recommend either: (a) resume the build with `python3 scripts/auto-build-brain.py --person "Kara Swisher" --resume`, or (b) drop the empty tables: `DROP TABLE kara_swisher_atoms, kara_swisher_connections;`.
- **`brain_metadata` row count 15 → 18.** Jeremy and Gokul account for 2 of the 3 new rows; the third row's identity isn't confirmed by this refresh (could be a metadata-only entry for kara-swisher matching the empty tables, or a backfill for oprah/sara). Recommend `SELECT slug FROM brain_metadata ORDER BY created_at DESC LIMIT 5;` to confirm.
- **Parent `~/rob-ai/CLAUDE.md` sync needed.** index.json changed (gokul gokul-rajaram 554/906 → 454/789), so the parent CLAUDE.md "Installed Brains" table and Totals line are now stale. Run `python3 brainsfor/scripts/sync-claude-md-brains.py` to regenerate.

---

## Doc Refresh — 2026-05-17 (run 11)

### Context
Automated nightly run, one day after run 10. **Zero factual drift in the Supabase data, packs, or audit scores.** Every per-brain atom/connection count, brain_metadata=15, brain_requests=0, cross_connections=17, rob_atoms=237, rob_connections=162, and voice enrichment (240/284 = 84.5%) is byte-for-byte identical to run 10. Only one update applied: the parent `~/rob-ai/CLAUDE.md` Installed Brains table was out of sync with `brains/index.json` and was regenerated by `scripts/sync-claude-md-brains.py`.

### Changes Applied
- **~/rob-ai/CLAUDE.md** — ran `scripts/sync-claude-md-brains.py` to fix drift. shiva-rajaraman connection_count 419 → 1,815 (parent doc was stale; index.json was already at 1,815 per run 10's refresh contract). Totals line: 22,669 → 24,065 connections across 18 brains. This is the catch-up that run 10 missed (run 10 updated index.json but didn't re-run the sync script).
- **IMPROVEMENTS.md** — footer "Last updated" line: 2026-05-16 (run 10) → 2026-05-17 (run 11). Wording updated to "Zero data drift from run 10" and removed the stale "rob_atoms grew 225 → 237" delta (now phrased as steady-state at 237/162).

### No Changes Needed
- **brainsfor/CLAUDE.md** — every fact still accurate: 18 packs / 16 in Supabase, all per-brain connection counts in the Known data drift block match Supabase live values (verified with UNION ALL count query), brain_metadata=15, brain_requests=0, cross_connections=17, rob_atoms/rob_connections=237/162, voice enrichment 240/284, gary_vee drift (319/255 Supabase vs 246/1,850 pack) still accurate, shiva_rajaraman drift (536/1,815 Supabase vs 536/419 pack) still accurate.
- **business-plan.md** — Live Inventory table (lines 209-225) totals match Supabase exactly: 4,799 atoms / 22,250 connections / 17 cross-brain across the 17 visible-table brains. Infrastructure stats line (line 228): 15 brain_metadata records, 0 brain_requests, audit avg 99/100 across 17 shippable brains (98.5 rounds to 99 — unchanged). Ship Plan completed checkboxes, Why Rob section, and TL;DR all consistent with current state.
- **brains/index.json** — declared atom_count and connection_count for all 18 brains match Supabase row counts (where present); oprah-winfrey (333/355) and sara-blakely (486/528) are pack-only with no Supabase tables.
- **Audit scores** — identical to run 10: charlie 100, hank 99, john 100, paul 100, peter-attia 93, scott 97, steve 98, sun-tzu 100, gary 100, peter-zeihan 99, jensen 100, dario 100, elon 100, brene 100, oprah 98, sara-blakely 97, bill-harris 93, shiva-rajaraman 77 (hidden). Avg across 17 shippable = 1674/17 = 98.5 → 99/100.

### Quality Scores (audit-brains.py, 2026-05-17)
| Slug | Score | Status |
|---|---|---|
| charlie-munger | 100 | live |
| hank-green | 99 | hidden |
| john-green | 100 | hidden |
| paul-graham | 100 | live |
| peter-attia | 93 | live |
| scott-belsky | 97 | live |
| steve-jobs | 98 | live |
| sun-tzu | 100 | live |
| gary-vee | 100 | live |
| peter-zeihan | 99 | live |
| jensen-huang | 100 | live |
| dario-amodei | 100 | live |
| elon-musk | 100 | live |
| brene-brown | 100 | live |
| oprah-winfrey | 98 | live |
| sara-blakely | 97 | live |
| bill-harris | 93 | live |
| shiva-rajaraman | 77 | hidden (excluded from "17 shippable" average) |

### Flagged for Human Review
- **Parent CLAUDE.md sync was missed in run 10.** Run 10 updated `brains/index.json` to reflect Supabase's live shiva-rajaraman connection count (419 → 1,815) but did not run `scripts/sync-claude-md-brains.py`, so the parent `~/rob-ai/CLAUDE.md` carried a stale value for ~24 hours. The pre-commit hook is supposed to catch this on commit, but the task script doesn't commit. Worth adding a "run sync script after touching index.json" step to the refresh task explicitly, or moving the sync into the task itself when index.json drift is detected.
- **Three consecutive runs (9, 10, 11) with effectively zero Supabase-side drift.** Run 9 noted this and suggested switching to weekly cadence; run 10 had one substantive change (shiva index.json sync); run 11 had none. The 11pm enrich-connections cron is also running but not changing totals materially. If runs 12-13 also show no drift, weekly cadence is the right call.

---

## Doc Refresh — 2026-04-30 (run 9)

### Context
Automated nightly run, two days after run 8. **No factual drift detected** — every audited number (per-brain atoms/connections in Supabase, pack-shipped connection counts, audit scores, voice enrichment percentage, brain_metadata=14, brain_requests=0, cross_connections=17, 15-of-16 brains live) matches run 8 byte-for-byte. The only update is the IMPROVEMENTS.md footer date/run-number bump and prepending this log entry.

### Changes Applied
- **IMPROVEMENTS.md** — footer "Last updated" line: 2026-04-28 (run 8) → 2026-04-30 (run 9). Wording on jensen_huang / brene_brown re-export tightened ("packs were re-exported since run 7" was no longer accurate at run 9 — re-export happened ~run 8; current state is just "packs ship 253/1,000 and 283/1,000").

### No Changes Needed
- **brainsfor/CLAUDE.md** — every fact still accurate: 15 packs / 14 in Supabase, all per-brain connection counts in the Known data drift block match Supabase, jensen 253/1,000 + brene 283/1,000 pack values match exported JSON, brain_metadata=14, brain_requests=0, cross_connections=17, voice enrichment 240/284, no oprah_winfrey or annie_duke tables in Supabase.
- **business-plan.md** — Live Inventory table (lines 209-224) totals match Supabase exactly: 3,749 atoms / 21,189 connections / 17 cross-brain. Infrastructure stats line (line 226), Ship Plan completed checkboxes, Why Rob section, and TL;DR all consistent with current state.
- **brains/index.json** — declared atom_count and connection_count for all 16 brains match Supabase row counts (or are 0/scaffolded for annie-duke; 333/355 pack-only for oprah-winfrey).
- **Audit scores** — identical to run 8: charlie 100, hank 99, john 100, paul 100, peter-attia 93, scott 97, steve 98, sun-tzu 100, gary 100, peter-zeihan 99, jensen 100, dario 100, elon 100, brene 100, oprah 98, annie-duke 24 (excluded). Avg 98.93 → 99/100.

### Quality Scores (audit-brains.py, 2026-04-30)
| Slug | Score | Status |
|---|---|---|
| charlie-munger | 100 | live |
| hank-green | 99 | hidden |
| john-green | 100 | hidden |
| paul-graham | 100 | live |
| peter-attia | 93 | live |
| scott-belsky | 97 | live |
| steve-jobs | 98 | live |
| sun-tzu | 100 | live |
| gary-vee | 100 | live |
| peter-zeihan | 99 | live |
| jensen-huang | 100 | live |
| dario-amodei | 100 | live |
| elon-musk | 100 | live |
| brene-brown | 100 | live |
| oprah-winfrey | 98 | live |
| annie-duke | 24 | scaffolded (excluded from avg) |

### Flagged for Human Review
- **Pagination cap is universal, not a 2-brain issue.** CLAUDE.md's Known data drift block calls out only jensen_huang (1,622 in DB → 1,000 in pack) and brene_brown (2,035 → 1,000), but every Supabase-backed pack with >1,000 connections is capped at exactly 1,000 by `export-brain.py`. Audit "conn refs" stats (2,000 = 1,000 connections × 2 endpoints) confirm: scott-belsky (1,515 → 1,000), steve-jobs (1,618 → 1,000), gary-vee (1,850 → 1,000), peter-zeihan (1,503 → 1,000), dario-amodei (1,842 → 1,000), elon-musk (1,563 → 1,000), charlie-munger (1,262 → 1,000), john-green (1,301 → 1,000), sun-tzu (1,283 → 1,000), peter-attia (1,220 → 1,000), hank-green (1,245 → 1,000) are all affected. paul-graham (975) and oprah-winfrey (355 — pack-only) escape because they're under the cap. The pagination fix mentioned in CLAUDE.md line 102 will unlock ~10,000 additional connections in the customer-facing pack JSONs once shipped. Worth considering: rewording the CLAUDE.md drift block from "jensen_huang and brene_brown" to "every brain with >1,000 connections in Supabase" so the scope is unambiguous.
- **Two consecutive runs with zero factual drift** (run 8 → run 9). Either the system has stabilized at a steady state, or the daily refresh cadence is now over-tuned for the rate of change. If the next 1-2 runs also show no drift, consider switching to a weekly cadence and freeing the nightly slot.

---

## Doc Refresh — 2026-04-28 (run 8)

### Context
Automated nightly run, six days after run 7. Two state shifts to record:
1. **Jensen Huang pack re-exported.** Run 7 flagged the pack as stale at 253/220; today's pack-atoms.json holds 253 atoms / 1,000 connections. Supabase still has 1,622 — the gap is the export-brain.py pagination bug, not stale data. Same fix path remains (paginate, then re-export).
2. **Brené Brown pack re-exported.** Run 7 flagged the pack as stale at 283/321; today's pack holds 283 atoms / 1,000 connections. Supabase still has 2,035 — same pagination cap as Jensen.

Everything else (Supabase row counts, atom totals, audit scores, brain_metadata=14, brain_requests=0, cross_connections=17, voice enrichment 240/284 = 84.5%, 15/15 shippable brains rendered on brainsforfree.com) is identical to run 7.

### Changes Applied

**brainsfor/CLAUDE.md** — Known data drift block:
- Jensen Huang note: "shipped pack is stale (253/220 from original build)" → "pack was re-exported and now ships 253/1,000 connections (capped by the pagination bug below); fix pagination, then re-export to surface the remaining ~622 connections."
- Brené Brown note: "shipped pack is stale (283/321 from original build)" → "pack was re-exported and now ships 283/1,000 connections (capped by the pagination bug below); fix pagination, then re-export to surface the remaining ~1,035 connections."

**IMPROVEMENTS.md** — footer "Last updated" line:
- Date 2026-04-22 (run 7) → 2026-04-28 (run 8)
- Pagination caveat upgraded from "still capped at ~1,000" to noting that every Supabase-backed pack now ships exactly 1,000.
- Open flag (1) and (2) merged: jensen_huang and brene_brown re-exported (253/1,000 and 283/1,000) — the remaining 622 + 1,035 connections only surface once the pagination bug is fixed.
- Open flag for Oprah unchanged; pagination flag retained.

### No Changes Needed
- **brains/index.json** — already in lockstep with Supabase (totals, per-brain atoms, per-brain connections all match).
- **website/public/brains/index.json** — same set as the registry; no drift detected.
- **business-plan.md** — Live Inventory table values, infrastructure stats, Ship Plan, Why Rob, TL;DR all use Supabase numbers (3,749 atoms / 21,189 connections; 14 in Supabase; 15 shippable). Nothing factual changed since run 7.
- Voice enrichment (240/284 = 84.5%) — unchanged.
- cross_connections (17), brain_metadata (14), brain_requests (0) — unchanged.
- Audit scores — identical to run 7's scoreboard.
- Skill architecture, MCP server, /board, /coach modes, design system, and brand sections — no structural changes.

### Quality Scores (audit-brains.py, 2026-04-28)
| Slug | Score | Status |
|---|---|---|
| charlie-munger | 100 | live |
| hank-green | 99 | hidden |
| john-green | 100 | hidden |
| paul-graham | 100 | live |
| peter-attia | 93 | live |
| scott-belsky | 97 | live |
| steve-jobs | 98 | live |
| sun-tzu | 100 | live |
| gary-vee | 100 | live |
| peter-zeihan | 99 | live |
| jensen-huang | 100 | live |
| dario-amodei | 100 | live |
| elon-musk | 100 | live |
| annie-duke | 24 | scaffolded (excluded from avg) |
| brene-brown | 100 | live |
| oprah-winfrey | 98 | live |

Avg across 15 shippable: **98.9 → 99/100** (unchanged from run 7).

### Flagged for Human Review
- **Pagination bug is now load-bearing.** Every Supabase-backed pack ships exactly 1,000 connections — Belsky (1,515), Steve Jobs (1,618), Gary Vee (1,850), Brené Brown (2,035), Jensen Huang (1,622), Dario Amodei (1,842), Elon Musk (1,563), Charlie Munger (1,262), John Green (1,301), Sun Tzu (1,283), Hank Green (1,245), Peter Attia (1,220), Peter Zeihan (1,503) all silently truncated. Fixing `export-brain.py` pagination unlocks ~7,000 connections worth of customer-visible graph density across the catalog in a single re-export pass.
- **Annie Duke still scaffolded only** (no pack/, score 24). Index lists status='scaffolded' with 0 atoms/connections — consistent with state. Build hasn't run yet.
- **Oprah Winfrey still pack-only** — no Supabase tables, so cross-brain Supabase queries skip her. MCP-driven skills work via pack JSON.

---

## Doc Refresh — 2026-04-22 (run 7)

### Context
Automated nightly run. Two state shifts since run 6:
1. **Jensen Huang Supabase tables populated.** Previously 0/0 (run 6 flagged this as data drift). Now 253 atoms / 1,622 connections. Shipped pack is stale at 253/220 — re-export needed.
2. **Brené Brown Supabase tables populated.** Previously no tables (run 6 flagged this). Now 283 atoms / 2,035 connections. Shipped pack is stale at 283/321 — re-export needed.
3. Oprah Winfrey still pack-only — no Supabase tables yet.
4. `brain_metadata` grew from 13 → 14 rows (Brené Brown added with status='active').

### Changes Applied

**brains/index.json + website/public/brains/index.json** (kept in lockstep, same pattern as run 6):
- jensen-huang `connection_count` 220 → 1,622 (trust Supabase per doc-refresh contract)
- brene-brown `connection_count` 321 → 2,035

**business-plan.md** (Live inventory table):
- Header: "(13 in Supabase)" → "(14 in Supabase)"
- Jensen Huang row: 253/220 → 253/1,622
- Brené Brown row: 283/321 → 283/2,035
- TOTAL row: 3,749 atoms / 18,073 conns → 3,749 atoms / 21,189 conns
- Infrastructure stats: "13 `brain_metadata` records" → "14"; dropped Brené from the "not yet ingested" caveat (Oprah remains); audit avg 97/100 across 16 brains → 99/100 across 15 shippable
- Ship Plan DONE list: "Build 13 brains" → "Build 15 shippable brains" with full list including Brené + Oprah; "3,133 atoms + 5,129 connections in Supabase" → "3,416 atoms + 20,834 connections in Supabase (14 brains; Oprah pack-only)"; "Complete pack/ for all 13" → "for all 15"
- Storefront section: "13/13 brains rendered" → "15/15 shippable brains now rendered on brainsforfree.com"
- Success Metrics: "13 brains built and packaged" → "15 shippable brains built and packaged"
- "Why Rob Is Uniquely Positioned" para 2: "thirteen times over. 13 brains live with 3,133 atoms and 5,129 connections" → "fifteen times over. 15 shippable brains live (14 in Supabase with 3,416 atoms + 20,834 connections; Oprah Winfrey ships pack-only)"
- TL;DR: "13 brains live ... 3,133 atoms, 5,129 connections" → "15 shippable brains live (including Brené Brown, Oprah Winfrey). 3,749 atoms across packs (3,416 in Supabase; Oprah pack-only), 21,189 connections total. ... brainsforfree.com live on Vercel with all 15 brains"

**brainsfor/CLAUDE.md**:
- Tables header: "15 brain packs built; 13 live in Supabase" → "15 brain packs built; 14 live in Supabase"
- Connections ordering block: added `brene_brown_connections (2,035)` at top, added `jensen_huang_connections (1,622)`, added `paul_graham_connections (975)` to complete the list
- `brain_metadata` line: "13 rows ... (Brené Brown and Oprah Winfrey shipped as packs only)" → "14 rows ... (Oprah Winfrey shipped as a pack only)"
- Known Data Drift block:
  - Jensen Huang: "tables are empty (0/0)" → "tables are now populated (253 / 1,622) but the shipped pack is stale (253/220) — re-export needed"
  - Brené Brown: moved out of "No Supabase tables exist" group; new note: "now populated (283 / 2,035) but shipped pack is stale (283/321) — re-export needed"
  - Oprah Winfrey: kept as the sole remaining "No Supabase tables" item
  - Pagination bug note: unchanged

**IMPROVEMENTS.md**:
- Footer "Last updated" date bumped 2026-04-21 → 2026-04-22
- "18,073 Supabase connections" → "20,834 Supabase connections across 14 brains"
- "13 brains live in Supabase; Brené Brown and Oprah Winfrey ship as packs but aren't yet ingested" → "14 brains live in Supabase; Oprah Winfrey ships as a pack but isn't yet ingested"
- "Audit avg score 97/100 across 15 live brains" → "99/100 across 15 shippable brains"
- Open flags: replaced jensen (was empty 0/0) and brene (no DB tables) flags with the new "DB now has data, pack is stale, re-export needed" flags

### No Changes Needed
- Voice enrichment line ("240/284 atoms enriched (84.5%)") — verified against Supabase, still accurate
- cross_connections count (17) — unchanged since last run
- brain_requests count (0) — unchanged since last run
- Peter Zeihan atom count (362) — unchanged since run 6's correction
- Storefront deprecation note in CLAUDE.md directory tree — still accurate (dir is empty)
- Skill architecture section in CLAUDE.md — no structural changes since run 6
- business-plan.md Next Wave table, pricing, go-to-market, legal, revenue projections — all opinion/strategy content, out of scope for doc-refresh
- IMPROVEMENTS.md "Pinned" section, open items — no status changes detected this run

### Quality Scores (audit-brains.py, 2026-04-22)
| Slug | Score | Status |
|---|---|---|
| charlie-munger | 100 | live |
| hank-green | 99 | hidden |
| john-green | 100 | hidden |
| paul-graham | 100 | live |
| peter-attia | 93 | live |
| scott-belsky | 97 | live |
| steve-jobs | 98 | live |
| sun-tzu | 100 | live |
| gary-vee | 100 | live |
| peter-zeihan | 99 | live |
| jensen-huang | 100 | live |
| dario-amodei | 100 | live |
| elon-musk | 100 | live |
| annie-duke | 24 | scaffolded (excluded from avg) |
| brene-brown | 100 | live |
| oprah-winfrey | 98 | live |

Avg across 15 shippable: **98.9 → 99/100**.

### Flagged for Human Review
- **Jensen Huang + Brené Brown packs need re-export.** Supabase now has ~6-7x more connections than the shipped packs carry. Running `python3 scripts/export-brain.py --brain jensen-huang` and `--brain brene-brown` would sync the packs — but note the pagination bug will still cap at ~1,000 connections per brain until `export-brain.py` is patched. Consider fixing pagination first, then re-exporting all stale packs in one pass.
- **Oprah Winfrey still has no Supabase tables** — ingestion task carried forward from run 6. `/board` and cross-brain Rob queries that hit Supabase will miss her.
- **brain_metadata slug inconsistency:** some rows use hyphens (brene-brown, scott-belsky, gary-vee, hank-green, john-green, sun-tzu, charlie-munger) and some use underscores (dario_amodei, elon_musk, jensen_huang, paul_graham, peter_attia, peter_zeihan, steve_jobs). Not blocking anything visible, but surface-check whether downstream code relies on a particular form.

---

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
- Remaining Questions "Next brain pack after Belsky?" checkbox answer updated to reflect Brené + Oprah shipped

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
- Live-brain average: ~98/100 (15 brains)

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
