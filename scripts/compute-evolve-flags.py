#!/usr/bin/env python3
"""
compute-evolve-flags.py — Compute the `supports_evolve` flag for every brain in
brains/index.json based on temporal density of its pack atoms.

A brain "supports evolve" when:
  - ≥50% of its atoms have a non-null `source_date`, AND
  - the dated atoms span ≥3 distinct years.

This is what the /evolve skill needs to produce a real timeline. Brains that
fail either bar (Sun Tzu — single ancient source; Paul Graham — text-scraped
essays with no per-source dates) will trigger /evolve's graceful refusal mode.

Usage:
    python3 scripts/compute-evolve-flags.py             # update index.json
    python3 scripts/compute-evolve-flags.py --dry-run   # print, don't write
    python3 scripts/compute-evolve-flags.py --check     # exit 1 if drift

Importable: `from compute_evolve_flags import compute_supports_evolve, temporal_density`
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
BRAINSFOR_ROOT = SCRIPT_DIR.parent
BRAINS_DIR = BRAINSFOR_ROOT / "brains"
INDEX_PATH = BRAINS_DIR / "index.json"

COVERAGE_THRESHOLD = 0.50   # at least 50% of atoms must be dated
YEAR_SPAN_THRESHOLD = 3     # dated atoms must span ≥3 distinct years

YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")


def extract_year(raw) -> Optional[int]:
    """Best-effort year extraction from a source_date string."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.lower() in {"unknown", "none", "null", "n/a"}:
        return None
    m = YEAR_RE.search(s)
    return int(m.group(1)) if m else None


def temporal_density(atoms: list[dict]) -> dict:
    """Return {dated, total, coverage, years, year_span} for an atom list."""
    total = len(atoms)
    years: set[int] = set()
    dated = 0
    for a in atoms:
        y = extract_year(a.get("source_date"))
        if y is not None:
            dated += 1
            years.add(y)
    coverage = (dated / total) if total else 0.0
    year_span = len(years)
    return {
        "total": total,
        "dated": dated,
        "coverage": round(coverage, 3),
        "years": sorted(years),
        "year_span": year_span,
    }


def compute_supports_evolve(atoms: list[dict]) -> tuple[bool, dict]:
    """Apply the supports_evolve rule. Returns (bool, density_stats)."""
    d = temporal_density(atoms)
    ok = d["coverage"] >= COVERAGE_THRESHOLD and d["year_span"] >= YEAR_SPAN_THRESHOLD
    return ok, d


def load_brain_atoms(slug: str) -> Optional[list[dict]]:
    p = BRAINS_DIR / slug / "pack" / "brain-atoms.json"
    if not p.exists():
        return None
    try:
        return json.load(open(p)).get("atoms", [])
    except (json.JSONDecodeError, OSError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="Print computed flags but don't write index.json")
    ap.add_argument("--check", action="store_true", help="Exit 1 if any brain's flag differs from what's in index.json")
    args = ap.parse_args()

    if not INDEX_PATH.exists():
        print(f"ERROR: {INDEX_PATH} not found", file=sys.stderr)
        return 1

    index = json.load(open(INDEX_PATH))
    brains = index.get("brains", [])

    drift = 0
    changed = 0
    print(f"{'slug':<22} {'coverage':>9} {'years':>6} {'span':>5}  supports_evolve")
    print("-" * 68)
    for entry in brains:
        slug = entry.get("slug", "?")
        atoms = load_brain_atoms(slug)
        if atoms is None:
            print(f"{slug:<22} {'—':>9} {'—':>6} {'—':>5}  (no pack)")
            continue
        ok, d = compute_supports_evolve(atoms)
        existing = entry.get("supports_evolve")
        marker = ""
        if existing is None:
            marker = "  [new]"
            changed += 1
        elif existing != ok:
            marker = f"  [was {existing}]"
            changed += 1
            drift += 1
        years_str = f"{d['years'][0]}–{d['years'][-1]}" if d["years"] else "none"
        print(f"{slug:<22} {d['coverage']*100:>7.1f}%  {years_str:>6} {d['year_span']:>5}  {ok}{marker}")
        entry["supports_evolve"] = ok
        entry["temporal_density"] = {
            "coverage": d["coverage"],
            "year_span": d["year_span"],
            "year_min": d["years"][0] if d["years"] else None,
            "year_max": d["years"][-1] if d["years"] else None,
        }

    print()
    if args.check:
        if drift > 0:
            print(f"DRIFT: {drift} brains have a different supports_evolve value than what's in index.json.")
            return 1
        print("No drift detected.")
        return 0

    if args.dry_run:
        print(f"DRY RUN — {changed} brain(s) would be updated. No writes.")
        return 0

    json.dump(index, open(INDEX_PATH, "w"), indent=2)
    print(f"Wrote {changed} change(s) to {INDEX_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
