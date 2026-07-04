#!/usr/bin/env python3
"""Publish QA scores into brains/index.json for the website.

Reads the latest per-brain QA artifacts and writes a `qa` block onto each
brain's entry in brains/index.json — the registry website/lib/brains.ts reads
(and sync-brain-assets.mjs copies to public/brains/ at build time), so the
catalog cards and detail pages pick scores up with no extra plumbing.

Sources (same tiers brain-qa.py composites):
  - brains/<slug>/evals/persona-qa-*.json  (latest) -> score, dimensions, confidence, date
  - brains/<slug>/evals/numeric-claims-*.json (latest) -> high-severity defect count
  - audit-brains.py --json                 -> voice (scores.voice.raw)

Brains with no persona-qa artifact (e.g. hidden brains) get their `qa` key
removed rather than left stale.

Run after every QA refresh:
  python3 scripts/publish-qa-scores.py            # write index.json
  python3 scripts/publish-qa-scores.py --dry-run  # print table, no write
"""

import argparse
import glob
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "brains" / "index.json"


def latest(slug: str, pattern: str) -> dict | None:
    files = sorted(glob.glob(str(ROOT / "brains" / slug / "evals" / pattern)))
    if not files:
        return None
    try:
        return json.loads(Path(files[-1]).read_text())
    except Exception:
        return None


def audit_voice() -> dict[str, float]:
    """slug -> normalized voice-enrichment score from audit-brains.py."""
    r = subprocess.run(
        ["python3", str(ROOT / "scripts" / "audit-brains.py"), "--json"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=120,
    )
    data = json.loads(r.stdout)
    out = {}
    for b in data.get("brains", []):
        raw = ((b.get("scores") or {}).get("voice") or {}).get("raw")
        if raw is not None:
            out[b["slug"]] = round(raw, 2)
    return out


def build_qa(slug: str, voice: dict[str, float]) -> dict | None:
    persona = latest(slug, "persona-qa-*.json")
    if not persona or persona.get("persona_qa_score") is None:
        return None
    numeric = latest(slug, "numeric-claims-*.json") or {}
    qa = {
        "score": persona["persona_qa_score"],
        "dimensions": persona.get("dimension_scores", {}),
        "confidence": persona.get("confidence"),
        "as_of": persona.get("date"),
    }
    if slug in voice:
        qa["voice"] = voice[slug]
    if "high_severity_count" in numeric:
        qa["numeric_defects"] = numeric["high_severity_count"]
    return qa


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="print table, don't write")
    args = ap.parse_args()

    index = json.loads(INDEX.read_text())
    voice = audit_voice()

    rows = []
    for entry in index["brains"]:
        slug = entry["slug"]
        qa = build_qa(slug, voice)
        if qa:
            entry["qa"] = qa
        else:
            entry.pop("qa", None)
        rows.append((slug, entry.get("status"), qa))

    print(f"{'slug':24s} {'status':8s} {'score':>5s} {'voice':>5s} {'as_of':>10s}")
    for slug, status, qa in rows:
        if qa:
            print(f"{slug:24s} {status:8s} {qa['score']:5d} "
                  f"{qa.get('voice', '-'):>5} {qa.get('as_of', '-'):>10}")
        else:
            print(f"{slug:24s} {status:8s} {'-':>5s} {'-':>5s} {'-':>10s}")

    if args.dry_run:
        print("\n(dry run — index.json not written)")
        return

    INDEX.write_text(json.dumps(index, indent=2) + "\n")
    scored = sum(1 for _, _, qa in rows if qa)
    print(f"\nWrote qa blocks for {scored}/{len(rows)} brains -> {INDEX}")


if __name__ == "__main__":
    sys.exit(main())
