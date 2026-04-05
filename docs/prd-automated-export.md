# PRD: Automated Brain Pack Export Pipeline

**Author:** Rob Gabel
**Date:** 2026-04-05
**Status:** Draft

---

## Problem

The export pipeline (`export-brain.py`) is manual and multi-step: dump atoms from Supabase to JSON, dump connections to JSON, then run the script with file paths. This means pack files drift out of sync with Supabase data (as just happened — pack showed 359 atoms / 161 connections while Supabase had 284 / 430). Nobody remembers to re-export after ingestion or enrichment runs.

## Goal

A single command or automated trigger that regenerates the pack directly from Supabase, with no intermediate file juggling. The pack should never be more than 24 hours stale.

---

## Approach: Supabase Edge Function + pg_cron

### Why edge function (not local script)

The enrichment pipeline already runs as an edge function on pg_cron (`enrich-connections`, daily 11:30pm PT). Export should follow the same pattern — runs where the data lives, no local env setup, no credential management beyond what Supabase already has. The edge function generates the pack files and writes them to Supabase Storage, where they can be downloaded or served.

### Why not just add `--supabase` to export-brain.py

That was the original plan (line 481-483 of the script says "not yet implemented"). It would work for manual runs but still requires someone to run it. The real fix is automation — and if we're automating, an edge function is simpler than a cron job on a local machine or a CI runner.

---

## Design

### Component 1: Add `--supabase` mode to export-brain.py (quick win)

**What:** Enable the script to fetch directly from Supabase using `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` from env vars. No intermediate JSON files.

**Implementation:**
- Add `--supabase` flag to argparse
- Use `httpx` or `requests` to call Supabase REST API: `GET /rest/v1/belsky_atoms?select=id,content,original_quote,implication,...` and `GET /rest/v1/belsky_connections?select=id,atom_id_1,atom_id_2,relationship,confidence`
- Pagination: Supabase REST defaults to 1000 rows, which covers 284 atoms and 430 connections with no pagination needed. Add Range header handling for future growth.
- Everything else in the pipeline stays the same — just swap the data source.

**Usage:**
```bash
export-brain.py --brain scott-belsky --supabase
```

**Effort:** ~1 hour. This is the immediate fix.

### Component 2: Edge function `export-pack`

**What:** A Supabase edge function that runs the export logic server-side and writes output to Supabase Storage bucket `brain-packs`.

**Trigger options:**
1. **pg_cron** — run daily at midnight PT (after `enrich-connections` at 11:30pm). Simplest.
2. **Database trigger** — fire on INSERT/UPDATE to `belsky_atoms` or `belsky_connections`. More responsive but noisier (batch ingestion could trigger dozens of rebuilds).
3. **Manual invoke** — `POST /functions/v1/export-pack?brain=scott-belsky`. Always available regardless of automation choice.

**Recommendation:** pg_cron (daily) + manual invoke. Keep it simple. Daily is fresh enough — nobody needs real-time pack updates.

**Implementation:**
- Rewrite the core export logic (JSON generation, markdown generation, template rendering) in TypeScript/Deno for the edge function runtime
- Or: keep Python logic, call it from a lightweight edge function that shells out (less clean but faster to ship)
- Write outputs to Supabase Storage bucket `brain-packs/{slug}/` — `brain-atoms.json`, `brain-context.md`, `SKILL.md`, `README.md`, `skills/`
- Return a manifest with file URLs + stats (atom count, connection count, generation timestamp)

**Storage bucket structure:**
```
brain-packs/
  scott-belsky/
    brain-atoms.json
    brain-context.md
    SKILL.md
    README.md
    explore.html
    skills/
      advise/SKILL.md
      teach/SKILL.md
      ...
    meta.json  ← {atom_count, connection_count, generated_at, version}
```

**Effort:** 4-6 hours (TypeScript rewrite of export logic + storage integration + cron setup).

### Component 3: Pack version tracking

**What:** Add a `brain_pack_versions` table to track every export run.

**Schema:**
```sql
create table brain_pack_versions (
  id uuid primary key default gen_random_uuid(),
  brain_slug text not null,
  atom_count int,
  connection_count int,
  cluster_count int,
  voice_coverage float,  -- % of atoms with original_quote
  storage_path text,
  generated_at timestamptz default now(),
  trigger text  -- 'cron', 'manual', 'webhook'
);
```

**Why:** Answers "when was the pack last built?" and "is it stale?" without checking file timestamps. Enables the Brain Score feature (track completeness over time). Enables diff detection — skip export if nothing changed since last run.

**Effort:** 30 minutes.

### Component 4: Webhook for `npx skills add` distribution (future)

**What:** When a new pack version is generated, POST to the skills registry to update the published artifact. This is the distribution trigger — ensures `npx skills add brainsforsale/belsky` always gets the latest pack.

**Depends on:** Skills registry API existing and BrainsForSale being published there. Not built yet — park this until distribution is solved.

---

## Sequencing

| Phase | What | Effort | Unblocks |
|-------|------|--------|----------|
| 1 | `--supabase` flag on export-brain.py | 1 hour | Manual export without JSON juggling |
| 2 | `brain_pack_versions` table | 30 min | Staleness tracking |
| 3 | `export-pack` edge function + pg_cron | 4-6 hours | Fully automated daily builds |
| 4 | Distribution webhook | TBD | Auto-publish to skills registry |

**Recommendation:** Do Phase 1 now. It's the 80/20 — eliminates the manual JSON dump step and takes an hour. Phase 3 matters once there are actual users who'd notice stale packs.

---

## Success Criteria

- Pack files are never more than 24 hours behind Supabase data
- Zero manual steps to regenerate after atom ingestion or connection enrichment
- `meta.json` in storage bucket always reflects actual counts (verifiable)
- Voice coverage percentage tracked over time (currently 7%, target 80%+)

---

## Open Questions

- Should the edge function also regenerate `explore.html`? It's 58KB and currently hand-edited. If it reads from `brain-atoms.json` at runtime (client-side fetch), it never needs regeneration — just needs to point to the right storage URL.
- Should pack generation be blocked if voice coverage drops below a threshold? (Prevents shipping a regression.)
- When brain #2 ships, does each brain get its own cron job, or one job iterates all brains in `index.json`?
