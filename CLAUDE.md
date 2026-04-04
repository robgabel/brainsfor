# BrainsForSale — Project CLAUDE.md

## Canonical Location

**All BrainsForSale work lives here: `~/rob-ai/brainsforsale/`**

Do NOT create or save files to a standalone `Brainsforsale` Cowork mount, `~/.claude/`, or anywhere else. Everything goes in this directory under `~/rob-ai/` so it's version-controlled, backed up, and visible to all sessions that mount `rob-ai/`.

If a Cowork session mounts a separate `Brainsforsale` folder, redirect work here instead.

## What This Is

BrainsForSale is a product concept: packaged "brain packs" — curated knowledge sets from notable thinkers (starting with Scott Belsky) that users can load into AI assistants to get that person's thinking framework applied to their own problems.

## Directory Structure

```
brainsforsale/
  CLAUDE.md                          ← this file
  business-plan.md                   ← full business plan
  belsky-brain.html                  ← interactive Belsky brain visualization
  belsky-implications-extracted-insights.md  ← extracted insights from Belsky's work
  brain-visual-prototype.html        ← brain pack visual prototype
  landing-page-prototype.html        ← landing page prototype
  brainsforsale-belsky/              ← exported Belsky brain data (JSON + markdown per cluster)
  brains/                            ← additional brain packs (future)
  scripts/
      export-belsky-brain.py         ← Supabase → local export script (needs SUPABASE_SERVICE_KEY env var)
  templates/                         ← brain pack templates
```

## Key Dependencies

- **Supabase project:** `uzediwokyshjbsymevtp` (same as PAOS)
- **Tables:** `belsky_thinking_skills`, `belsky_brain_entries`, `belsky_clusters` (and related)
- **Export script** requires `SUPABASE_SERVICE_KEY` env var — store in `.env` (gitignored) or pass inline

## Remaining Questions

- [ ] Pricing model — subscription vs. one-time purchase vs. freemium?
- [ ] Distribution channel — standalone app, plugin marketplace, or embedded in existing AI tools?
- [ ] Next brain pack after Belsky?
- [ ] Legal/licensing framework for packaging a person's published thinking?
