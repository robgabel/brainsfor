#!/usr/bin/env python3
"""Backfill source/raw/ for existing brains by re-scraping their text sources via Firecrawl.

Populates the audit corpus retroactively so brains built before raw-text persistence was
added to the pipeline can score full credit on Quote Verifiability. New brains get this
for free via auto-build-brain.py's scrape_text_sources() — this script is only for the
back catalog.

Usage:
  python3 scripts/backfill-raw-sources.py --brain jeremy-utley
  python3 scripts/backfill-raw-sources.py --all
  python3 scripts/backfill-raw-sources.py --all --dry-run
  python3 scripts/backfill-raw-sources.py --brain scott-belsky --force

Requires FIRECRAWL_API_KEY env var. Reads source/sources.json for each brain.
Idempotent: re-runs skip URLs whose filename already exists in source/raw/
(use --force to overwrite).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

# Reuse helpers from auto-build-brain.py to keep filename + index format consistent.
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "auto_build_brain", SCRIPT_DIR / "auto-build-brain.py"
)
_abb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_abb)

raw_source_filename = _abb.raw_source_filename
persist_raw_text = _abb.persist_raw_text
SCRAPE_MIN_CHARS = _abb.SCRAPE_MIN_CHARS
SCRAPE_MAX_CHARS = _abb.SCRAPE_MAX_CHARS
SCRAPE_TIMEOUT_SEC = _abb.SCRAPE_TIMEOUT_SEC
SCRAPE_SKIP_DOMAINS = _abb.SCRAPE_SKIP_DOMAINS


def step(msg: str) -> None:
    print(f"  > {msg}")


def success(msg: str) -> None:
    print(f"  OK {msg}")


def warn(msg: str) -> None:
    print(f"  WARN {msg}")


def backfill_brain(brain_dir: Path, force: bool, dry_run: bool, firecrawl_key: str) -> dict:
    """Scrape every text URL in source/sources.json and persist to source/raw/.
    Returns a stats dict {scraped, skipped_existing, skipped_thin, failed, total_chars}."""
    stats = {"scraped": 0, "skipped_existing": 0, "skipped_thin": 0, "failed": 0, "total_chars": 0}
    sources_path = brain_dir / "source" / "sources.json"
    if not sources_path.exists():
        warn(f"no source/sources.json — skipping")
        return stats

    try:
        sources_data = json.loads(sources_path.read_text(encoding="utf-8"))
    except Exception as e:
        warn(f"failed to parse sources.json: {e}")
        return stats

    text_sources = []
    for s in sources_data.get("sources", []):
        if s.get("youtube_id"):
            continue
        url = s.get("url", "")
        if not url.startswith("http"):
            continue
        if any(d in url for d in SCRAPE_SKIP_DOMAINS):
            continue
        text_sources.append(s)

    if not text_sources:
        step("no text sources to scrape")
        return stats

    raw_dir = brain_dir / "source" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    step(f"backfilling {len(text_sources)} text sources to source/raw/...")

    for i, source in enumerate(text_sources, 1):
        url = source["url"]
        title = source.get("title", "")[:60]
        filename = raw_source_filename(source)
        target = raw_dir / filename

        prefix = f"  [{i}/{len(text_sources)}] {title}..."
        if target.exists() and not force:
            stats["skipped_existing"] += 1
            print(f"{prefix} skip (exists)")
            continue

        if dry_run:
            print(f"{prefix} [DRY RUN]")
            continue

        try:
            resp = httpx.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {firecrawl_key}",
                    "Content-Type": "application/json",
                },
                json={"url": url, "formats": ["markdown"]},
                timeout=SCRAPE_TIMEOUT_SEC,
            )
            if resp.status_code != 200:
                stats["failed"] += 1
                print(f"{prefix} scrape failed ({resp.status_code})")
                continue

            data = resp.json()
            markdown = (data.get("data") or {}).get("markdown", "")
            if not markdown or len(markdown) < SCRAPE_MIN_CHARS:
                stats["skipped_thin"] += 1
                print(f"{prefix} too thin ({len(markdown)} chars)")
                continue

            if len(markdown) > SCRAPE_MAX_CHARS:
                markdown = markdown[:SCRAPE_MAX_CHARS] + "\n\n[...truncated]"

            persist_raw_text(brain_dir, source, markdown)
            stats["scraped"] += 1
            stats["total_chars"] += len(markdown)
            print(f"{prefix} {len(markdown)} chars")
            time.sleep(1)  # Match Firecrawl rate limit pattern from auto-build

        except Exception as e:
            stats["failed"] += 1
            print(f"{prefix} error: {e}")

    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--brain", help="Single brain slug to backfill (e.g. jeremy-utley)")
    group.add_argument("--all", action="store_true", help="Backfill all brains in brains/index.json")
    parser.add_argument("--force", action="store_true", help="Overwrite existing source/raw/ files")
    parser.add_argument("--dry-run", action="store_true", help="List what would be scraped without API calls")
    args = parser.parse_args()

    firecrawl_key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not firecrawl_key and not args.dry_run:
        print("ERROR: FIRECRAWL_API_KEY not set — source ~/rob-ai/.env or use --dry-run")
        sys.exit(1)

    brains_dir = REPO_ROOT / "brains"
    if args.brain:
        slugs = [args.brain]
    else:
        index_path = brains_dir / "index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        slugs = [b["slug"] for b in index.get("brains", [])]

    totals = {"scraped": 0, "skipped_existing": 0, "skipped_thin": 0, "failed": 0, "total_chars": 0}

    for slug in slugs:
        brain_dir = brains_dir / slug
        if not brain_dir.exists():
            warn(f"brain dir not found: {brain_dir}")
            continue
        print()
        print("=" * 70)
        print(f"  BACKFILL: {slug}")
        print("=" * 70)
        stats = backfill_brain(brain_dir, args.force, args.dry_run, firecrawl_key)
        for k, v in stats.items():
            totals[k] += v
        success(
            f"{slug}: scraped {stats['scraped']}, "
            f"skipped {stats['skipped_existing']} (existing) + {stats['skipped_thin']} (thin), "
            f"failed {stats['failed']}, {stats['total_chars']:,} chars total"
        )

    print()
    print("=" * 70)
    print("  TOTALS")
    print("=" * 70)
    print(
        f"  scraped:          {totals['scraped']}\n"
        f"  skipped (exists): {totals['skipped_existing']}\n"
        f"  skipped (thin):   {totals['skipped_thin']}\n"
        f"  failed:           {totals['failed']}\n"
        f"  total chars:      {totals['total_chars']:,}"
    )


if __name__ == "__main__":
    main()
