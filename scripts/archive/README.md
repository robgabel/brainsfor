# Archived one-shot scripts

Completed migrations and backfills kept for reference. These are NOT part of the
pipeline — do not run them without reading their docstrings first.

- `migrate-proper.py`, `migrate-fix.py` — 2026-06-02 migration of all brain tables
  from the shared PAOS Supabase project into the dedicated project. Completed.
  (The website no longer reads atoms from Supabase at all — it fetches the
  shipped static pack JSON — so a re-run should never be needed.)
- `migrate-via-api.py` — unused alternate migration path from the same effort.
- `backfill-source-url.py` — one-shot: added/populated source_url column on
  Supabase atom tables from pack JSON. Completed 2026-06.
- `backfill-source-urls.py` — one-shot: wrote source_url onto every pack
  brain-atoms.json from sources.json (citation chips fix). Completed 2026-05.
- `backfill-source-dates.py` — one-shot source_date backfill. Completed 2026-05.
