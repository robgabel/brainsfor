#!/usr/bin/env python3
"""
backfill-source-dates.py — Populate `source_date` on existing atoms by matching
each atom's `source_ref`/`source_url` against per-source date metadata.

Why this exists:
  /evolve needs dated atoms to trace how a thinker's view shifted across years.
  The text-extraction prompt in auto-build-brain.py historically didn't request
  source_date, so atoms scraped from text URLs all have source_date == null.
  This script backfills them from per-brain source metadata.

Date metadata sources (checked in order, per brain):
  1. brains/<slug>/source/sources.json         — entries with "date" / "published" / "year"
  2. brains/<slug>/source/transcripts/*.json   — source_meta.date (if not "unknown")
  3. brains/<slug>/source/raw/_index.json      — per-source scraped_at / published
  4. brains/<slug>/source/dates.json           — optional manual override map
                                                  ({source_ref_or_url: "YYYY-MM-DD"})

Matching strategy:
  - Build url→date and title→date maps from the metadata above
  - For each atom, try matches in order: source_url == url, source_ref == url,
    source_ref == title (case-insensitive). First hit wins.

Operates on the Supabase tables ({slug}_atoms) by default. With --pack-only,
patches brains/<slug>/pack/brain-atoms.json directly (useful for verification
without DB credentials).

Usage:
    python3 scripts/backfill-source-dates.py --brain paul-graham --dry-run
    python3 scripts/backfill-source-dates.py --brain jensen-huang
    python3 scripts/backfill-source-dates.py --all --dry-run
    python3 scripts/backfill-source-dates.py --brain paul-graham --pack-only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
BRAINSFOR_ROOT = SCRIPT_DIR.parent
BRAINS_DIR = BRAINSFOR_ROOT / "brains"
INDEX_PATH = BRAINS_DIR / "index.json"


def normalize_date(raw) -> Optional[str]:
    """Accept various date shapes; return YYYY-MM-DD / YYYY-MM / YYYY or None."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.lower() in {"unknown", "none", "null", "n/a"}:
        return None
    # Already in expected shape — return as-is. The schema accepts year-only too.
    return s


def collect_date_maps(brain_dir: Path) -> tuple[dict[str, str], dict[str, str], dict]:
    """Return (url_to_date, title_to_date, stats) for a brain."""
    url_map: dict[str, str] = {}
    title_map: dict[str, str] = {}
    stats = {
        "sources_json": 0,
        "transcripts": 0,
        "raw_index": 0,
        "dates_json": 0,
    }

    # 1. sources.json (Phase-0 discovery output)
    sources_path = brain_dir / "source" / "sources.json"
    if sources_path.exists():
        try:
            data = json.load(open(sources_path))
            items = data if isinstance(data, list) else data.get("sources", [])
            for it in items:
                if not isinstance(it, dict):
                    continue
                date = normalize_date(it.get("date") or it.get("published") or it.get("year"))
                if not date:
                    continue
                url = (it.get("url") or "").strip()
                title = (it.get("title") or "").strip().lower()
                if url:
                    url_map.setdefault(url, date)
                    stats["sources_json"] += 1
                if title:
                    title_map.setdefault(title, date)
        except (json.JSONDecodeError, OSError):
            pass

    # 2. Transcripts (YouTube)
    trans_dir = brain_dir / "source" / "transcripts"
    if trans_dir.exists():
        for tp in trans_dir.glob("*.json"):
            try:
                t = json.load(open(tp))
            except (json.JSONDecodeError, OSError):
                continue
            sm = t.get("source_meta", {}) if isinstance(t, dict) else {}
            date = normalize_date(sm.get("date"))
            if not date:
                continue
            url = (sm.get("url") or "").strip()
            title = (t.get("title") or "").strip().lower()
            vid = (t.get("video_id") or "").strip()
            if url:
                url_map.setdefault(url, date)
                stats["transcripts"] += 1
            if vid:
                url_map.setdefault(f"https://www.youtube.com/watch?v={vid}", date)
            if title:
                title_map.setdefault(title, date)

    # 3. raw/_index.json (Firecrawl-scraped corpus index)
    raw_idx = brain_dir / "source" / "raw" / "_index.json"
    if raw_idx.exists():
        try:
            data = json.load(open(raw_idx))
            items = data if isinstance(data, list) else data.get("sources", data.get("items", []))
            for it in items:
                if not isinstance(it, dict):
                    continue
                date = normalize_date(it.get("date") or it.get("published") or it.get("scraped_at", "")[:10] if it.get("scraped_at") else None)
                if not date:
                    continue
                url = (it.get("url") or "").strip()
                title = (it.get("title") or "").strip().lower()
                if url:
                    url_map.setdefault(url, date)
                    stats["raw_index"] += 1
                if title:
                    title_map.setdefault(title, date)
        except (json.JSONDecodeError, OSError):
            pass

    # 4. Manual override map (last writer wins — explicit beats heuristic)
    dates_path = brain_dir / "source" / "dates.json"
    if dates_path.exists():
        try:
            overrides = json.load(open(dates_path))
            if isinstance(overrides, dict):
                for key, date in overrides.items():
                    date_n = normalize_date(date)
                    if not date_n:
                        continue
                    # Treat keys that look like URLs as url_map entries; else title.
                    if "://" in key:
                        url_map[key] = date_n
                    else:
                        title_map[key.lower()] = date_n
                    stats["dates_json"] += 1
        except (json.JSONDecodeError, OSError):
            pass

    return url_map, title_map, stats


def match_atom_date(
    atom: dict, url_map: dict[str, str], title_map: dict[str, str]
) -> Optional[str]:
    """Find a date for one atom by walking its identifying fields."""
    candidates = [
        atom.get("source_url"),
        atom.get("source_ref"),
    ]
    for c in candidates:
        if not c:
            continue
        c = str(c).strip()
        if c in url_map:
            return url_map[c]
    # Title fallback (atoms whose source_ref is a title, not a URL)
    for c in candidates:
        if not c:
            continue
        c_lower = str(c).strip().lower()
        if c_lower in title_map:
            return title_map[c_lower]
    return None


def backfill_pack(brain_dir: Path, dry_run: bool) -> dict:
    """Patch source_date in brains/<slug>/pack/brain-atoms.json. Returns stats."""
    pack_path = brain_dir / "pack" / "brain-atoms.json"
    if not pack_path.exists():
        return {"error": "pack/brain-atoms.json missing", "patched": 0, "total": 0}

    url_map, title_map, meta_stats = collect_date_maps(brain_dir)
    if not url_map and not title_map:
        return {
            "error": "no date metadata found in source/sources.json, transcripts, raw/_index.json, or dates.json",
            "patched": 0,
            "total": 0,
            "meta_stats": meta_stats,
        }

    try:
        data = json.load(open(pack_path))
    except (json.JSONDecodeError, OSError) as e:
        return {"error": f"failed to read pack: {e}", "patched": 0, "total": 0}

    atoms = data.get("atoms", [])
    total = len(atoms)
    missing_before = sum(1 for a in atoms if not a.get("source_date"))
    patched = 0

    for a in atoms:
        if a.get("source_date"):
            continue
        date = match_atom_date(a, url_map, title_map)
        if date:
            a["source_date"] = date
            patched += 1

    if patched and not dry_run:
        json.dump(data, open(pack_path, "w"), indent=2)

    return {
        "total": total,
        "missing_before": missing_before,
        "patched": patched,
        "missing_after": missing_before - patched,
        "meta_stats": meta_stats,
        "url_map_size": len(url_map),
        "title_map_size": len(title_map),
        "dry_run": dry_run,
    }


def backfill_supabase(slug: str, brain_dir: Path, dry_run: bool) -> dict:
    """UPDATE <slug>_atoms in Supabase. Returns stats. Falls back gracefully if
    the supabase client / env aren't present."""
    try:
        from supabase import create_client  # type: ignore
    except ImportError:
        return {"error": "supabase-py not installed; use --pack-only", "patched": 0}

    url = os.environ.get("SUPABASE_URL") or os.environ.get("SUPABASE_PROJECT_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return {"error": "SUPABASE_URL / SUPABASE_SERVICE_KEY not set; use --pack-only", "patched": 0}

    url_map, title_map, meta_stats = collect_date_maps(brain_dir)
    if not url_map and not title_map:
        return {
            "error": "no date metadata found for this brain",
            "patched": 0,
            "meta_stats": meta_stats,
        }

    client = create_client(url, key)
    table = f"{slug.replace('-', '_')}_atoms"

    # Page through atoms missing source_date
    page_size = 500
    offset = 0
    total_missing = 0
    patched = 0
    while True:
        resp = (
            client.table(table)
            .select("id, source_ref, source_url, source_date")
            .is_("source_date", "null")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            break
        total_missing += len(rows)
        for row in rows:
            date = match_atom_date(row, url_map, title_map)
            if not date:
                continue
            if not dry_run:
                client.table(table).update({"source_date": date}).eq("id", row["id"]).execute()
            patched += 1
        if len(rows) < page_size:
            break
        offset += page_size

    return {
        "table": table,
        "missing_before": total_missing,
        "patched": patched,
        "missing_after": total_missing - patched,
        "meta_stats": meta_stats,
        "url_map_size": len(url_map),
        "title_map_size": len(title_map),
        "dry_run": dry_run,
    }


def report(slug: str, stats: dict) -> None:
    print(f"\n=== {slug} ===")
    if stats.get("error"):
        print(f"  ⚠️  {stats['error']}")
    meta = stats.get("meta_stats", {})
    if meta:
        print(
            f"  date-source coverage: sources.json={meta.get('sources_json', 0)}, "
            f"transcripts={meta.get('transcripts', 0)}, "
            f"raw_index={meta.get('raw_index', 0)}, "
            f"dates.json={meta.get('dates_json', 0)}"
        )
    if "url_map_size" in stats:
        print(f"  map sizes: url={stats['url_map_size']}, title={stats['title_map_size']}")
    if "total" in stats:
        print(f"  atoms total: {stats['total']}")
    if "missing_before" in stats:
        print(
            f"  missing source_date before: {stats['missing_before']} → patched: "
            f"{stats['patched']} → missing after: {stats.get('missing_after', '?')}"
            + ("  (DRY RUN — no writes)" if stats.get("dry_run") else "")
        )


def list_brains() -> list[dict]:
    if not INDEX_PATH.exists():
        print(f"ERROR: {INDEX_PATH} not found", file=sys.stderr)
        sys.exit(1)
    return json.load(open(INDEX_PATH)).get("brains", [])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brain", help="Single brain slug (default: --all)")
    ap.add_argument("--all", action="store_true", help="Process all brains in index.json")
    ap.add_argument("--dry-run", action="store_true", help="Show what would change, write nothing")
    ap.add_argument(
        "--pack-only",
        action="store_true",
        help="Patch only brains/<slug>/pack/brain-atoms.json (skip Supabase). Useful when DB creds aren't available.",
    )
    args = ap.parse_args()

    if not args.brain and not args.all:
        ap.error("Provide --brain <slug> or --all")

    if args.brain:
        targets = [{"slug": args.brain}]
    else:
        targets = [{"slug": b["slug"]} for b in list_brains() if b.get("status") != "hidden"]

    for t in targets:
        slug = t["slug"]
        brain_dir = BRAINS_DIR / slug
        if not brain_dir.exists():
            print(f"\n=== {slug} ===\n  ⚠️  brain dir missing: {brain_dir}")
            continue

        pack_stats = backfill_pack(brain_dir, args.dry_run)
        report(f"{slug} (pack)", pack_stats)

        if not args.pack_only:
            db_stats = backfill_supabase(slug, brain_dir, args.dry_run)
            report(f"{slug} (supabase)", db_stats)

    print("\nDone.")
    if args.dry_run:
        print("This was a DRY RUN — rerun without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
