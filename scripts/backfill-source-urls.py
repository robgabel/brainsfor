#!/usr/bin/env python3
"""Backfill source_url field on every brain-atoms.json pack.

The website's citation chips render as `<a href={c.url}>` — and `c.url` was
previously populated from `source_ref`, which for most brains is a human label
("Lex Fridman Podcast #494"), not a URL. That made the chips 404 on click.

This script reads each brain's source/sources.json + source/raw/_index.json,
builds a fuzzy title→URL lookup, and writes a `source_url` field on every atom.
The website then prefers `source_url` over `source_ref`.

Idempotent. Safe to re-run. Updates both pack/ and website/public/brains/.
"""
from __future__ import annotations

import json
import os
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).parent.parent
BRAINS = ROOT / "brains"
PUBLIC_BRAINS = ROOT / "website" / "public" / "brains"

# Reuse the matching helpers from export-brain.py
spec = spec_from_file_location("export_brain", ROOT / "scripts" / "export-brain.py")
eb = module_from_spec(spec)
spec.loader.exec_module(eb)


def backfill_one(slug: str) -> tuple[int, int]:
    """Returns (atoms_total, urls_matched). Writes pack/ and public/ in lockstep."""
    pack_path = BRAINS / slug / "pack" / "brain-atoms.json"
    if not pack_path.exists():
        return 0, 0

    data = json.loads(pack_path.read_text())
    atoms = data.get("atoms", [])
    if not atoms:
        return 0, 0

    lookup = eb.build_source_url_lookup(slug)
    matched = 0
    for a in atoms:
        sr = a.get("source_ref")
        url = eb.match_source_url(sr, lookup) if sr else None
        a["source_url"] = url  # always write (None if no match) so schema is uniform
        if url:
            matched += 1

    pack_path.write_text(json.dumps(data, indent=2))

    # window.__BRAIN_DATA__ companion file
    js_path = pack_path.with_suffix(".js")
    if js_path.exists():
        js_path.write_text("window.__BRAIN_DATA__ = " + json.dumps(data) + ";\n")

    # Public mirror for the deployed Next.js app
    public_json = PUBLIC_BRAINS / slug / "brain-atoms.json"
    if public_json.exists():
        public_json.write_text(json.dumps(data, indent=2))
    public_js = PUBLIC_BRAINS / slug / "brain-atoms.js"
    if public_js.exists():
        public_js.write_text("window.__BRAIN_DATA__ = " + json.dumps(data) + ";\n")

    return len(atoms), matched


def main():
    targets = sys.argv[1:] or sorted(os.listdir(BRAINS))
    total_a = total_m = 0
    print(f'{"slug":25} {"atoms":>6} {"matched":>8} {"%":>5}')
    print("-" * 50)
    for slug in targets:
        if not (BRAINS / slug).is_dir():
            continue
        a, m = backfill_one(slug)
        if a == 0:
            continue
        pct = 100 * m / a
        total_a += a
        total_m += m
        print(f"{slug:25} {a:6d} {m:8d} {pct:4.0f}%")
    print("-" * 50)
    if total_a:
        print(f'{"TOTAL":25} {total_a:6d} {total_m:8d} {100*total_m/total_a:4.0f}%')


if __name__ == "__main__":
    main()
