#!/usr/bin/env python3
"""/brain-qa orchestrator — one scorecard, four tiers, one ship verdict.

Ties the QA regime together for a brain (or the whole fleet):

  Tier 1  Structural   audit-brains.py        files, counts, orphans, voice    (free, always runs)
  Tier 2  Behavioral   eval-brains.py         answers like them (20 prompts)   (cached only — never auto-spends)
  Numeric verify-claims.py                    every hard figure vs the corpus  (cheap; run-if-missing)
  Tier 3  Persona QA   persona-qa.py          Annie-chaired 4-judge panel      (run-if-missing; the headline)

Emits a composite scorecard and the SHIP-GATE verdict (the RSP for brains):
  hidden -> live ONLY when
    (1) Persona-QA >= PERSONA_PASS,
    (2) zero high-severity numeric defects ("zero unverified hard numbers"), and
    (3) voice >= VOICE_GATE  (audit's normalized voice-enrichment score — the
        defensible reading; raw atom-quote coverage tops out ~47% on healthy brains,
        so a literal 60% atom gate is unattainable. Tunable below).

The three field dimensions map to the handoff's "interesting + useful + faithful":
  coverage (Brené) ≈ is the whole person here  ·  rigor (Munger) ≈ useful, non-slop
  authenticity (Kara) ≈ faithful/recognizable.  --all ranks by the composite persona score.

Cost discipline: a single --brain runs the missing cheap tiers (~$0.27). --all reads
CACHED results by default and reports what's missing; pass --run to actually spend
across the fleet (~$6 for 21 live brains). --refresh forces re-run.

Usage:
  python3 scripts/brain-qa.py --brain jesse-pujji            # one brain, run missing tiers
  python3 scripts/brain-qa.py --brain jesse-pujji --no-run   # cached only, no API
  python3 scripts/brain-qa.py --brain jesse-pujji --refresh  # force re-run numeric + persona
  python3 scripts/brain-qa.py --all                          # fleet scorecard from cache
  python3 scripts/brain-qa.py --all --run                    # fleet, spending across all (~$6)
  python3 scripts/brain-qa.py --all --json                   # machine-readable
"""
from __future__ import annotations
import argparse
import glob
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
BRAINS_DIR = ROOT / "brains"
sys.path.insert(0, str(SCRIPT_DIR))

from auto_build_config import step, success, warn, error  # noqa: E402

# --- Ship-gate thresholds (tunable) ---
PERSONA_PASS = 70       # persona-QA score
VOICE_GATE = 0.60       # audit scores.voice.raw (normalized voice-enrichment)
# zero high-severity numeric defects is condition (2), not a threshold.


def _latest(slug: str, pattern: str) -> dict | None:
    files = sorted(glob.glob(str(BRAINS_DIR / slug / "evals" / pattern)))
    if not files:
        return None
    try:
        return json.loads(Path(files[-1]).read_text())
    except Exception:
        return None


def run_audit(slug: str) -> dict | None:
    """Tier 1 — free, always fresh."""
    try:
        r = subprocess.run(["python3", str(SCRIPT_DIR / "audit-brains.py"), "--brain", slug, "--json"],
                           capture_output=True, text=True, cwd=str(ROOT), timeout=120)
        data = json.loads(r.stdout)
        return (data.get("brains") or [None])[0]
    except Exception as e:
        warn(f"{slug}: audit failed ({e})")
        return None


def ensure_numeric(slug: str, no_run: bool, refresh: bool) -> dict | None:
    cached = _latest(slug, "numeric-claims-*.json")
    if cached and not refresh:
        return cached
    if no_run:
        return cached
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    step(f"{slug}: running verify-claims.py...")
    subprocess.run(["python3", str(SCRIPT_DIR / "verify-claims.py"), "--brain", slug, "--date", date],
                   capture_output=True, text=True, cwd=str(ROOT), timeout=600)
    return _latest(slug, "numeric-claims-*.json")


def ensure_persona(slug: str, no_run: bool, refresh: bool, model: str | None) -> dict | None:
    cached = _latest(slug, "persona-qa-*.json")
    if cached and not refresh:
        return cached
    if no_run:
        return cached
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    step(f"{slug}: running persona-qa.py (4-judge panel)...")
    cmd = ["python3", str(SCRIPT_DIR / "persona-qa.py"), "--brain", slug, "--date", date]
    if model:
        cmd += ["--model", model]
    subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT), timeout=1200)
    return _latest(slug, "persona-qa-*.json")


def evaluate(slug: str, no_run: bool, refresh: bool, model: str | None) -> dict:
    audit = run_audit(slug)
    # Numeric must precede persona so the panel reads the fresh defect report.
    numeric = ensure_numeric(slug, no_run, refresh)
    persona = ensure_persona(slug, no_run, refresh, model)

    structural = (audit or {}).get("completeness_score")
    voice_raw = (((audit or {}).get("scores") or {}).get("voice") or {}).get("raw")
    voice_pct = ((audit or {}).get("stats") or {}).get("voice_enrichment_pct")
    behavioral = (audit or {}).get("behavioral") or {}
    behavioral_score = behavioral.get("overall") or behavioral.get("score")

    persona_score = (persona or {}).get("persona_qa_score")
    high_numeric = (numeric or {}).get("high_severity_count", None)
    dims = (persona or {}).get("dimension_scores", {})

    # --- Ship-gate (3 conditions) ---
    have = persona is not None and numeric is not None and audit is not None
    cond_persona = persona_score is not None and persona_score >= PERSONA_PASS
    cond_numeric = high_numeric == 0
    cond_voice = voice_raw is not None and voice_raw >= VOICE_GATE
    ship = bool(have and cond_persona and cond_numeric and cond_voice)

    blockers = []
    if not have:
        blockers.append("incomplete QA (missing tier output)")
    if persona_score is not None and not cond_persona:
        blockers.append(f"persona {persona_score} < {PERSONA_PASS}")
    if high_numeric and high_numeric > 0:
        blockers.append(f"{high_numeric} high-severity numeric defect(s)")
    if voice_raw is not None and not cond_voice:
        blockers.append(f"voice {voice_raw:.2f} < {VOICE_GATE}")

    return {
        "slug": slug,
        "structural": structural,
        "behavioral": behavioral_score,
        "persona": persona_score,
        "dimensions": dims,
        "voice_raw": voice_raw,
        "voice_pct": voice_pct,
        "high_numeric_defects": high_numeric,
        "ship": ship,
        "blockers": blockers,
        "ship_recommendation": (persona or {}).get("ship_recommendation"),
        "ranked_fixes": (persona or {}).get("ranked_fixes", [])[:3],
        "have_persona": persona is not None,
        "have_numeric": numeric is not None,
    }


def _fmt(v, width=4):
    return f"{v:>{width}}" if v is not None else "  - "


def print_brain(r: dict):
    gate = "✅ SHIP" if r["ship"] else "⛔ HOLD"
    d = r["dimensions"]
    print()
    success(f"{r['slug']}  —  {gate}")
    print(f"  Persona-QA   {_fmt(r['persona'])}/100   "
          f"(auth {_fmt(d.get('authenticity'),3)} · rigor {_fmt(d.get('rigor'),3)} · "
          f"cover {_fmt(d.get('coverage'),3)} · calib {_fmt(d.get('calibration'),3)})")
    print(f"  Structural   {_fmt(r['structural'])}/100        Behavioral {_fmt(r['behavioral'])}        "
          f"Voice {r['voice_raw'] if r['voice_raw'] is not None else '-'}")
    print(f"  Numeric high-severity defects: {r['high_numeric_defects'] if r['high_numeric_defects'] is not None else 'not run'}")
    if r["blockers"]:
        print(f"  Gate blockers: {'; '.join(r['blockers'])}")
    for f in r["ranked_fixes"]:
        print(f"    fix {f.get('priority','?')}. {f.get('fix','')[:96]}")


def live_slugs() -> list[str]:
    idx = json.loads((BRAINS_DIR / "index.json").read_text())
    brains = idx.get("brains", idx) if isinstance(idx, dict) else idx
    return [b["slug"] for b in brains if b.get("status") == "live"]


def all_slugs() -> list[str]:
    idx = json.loads((BRAINS_DIR / "index.json").read_text())
    brains = idx.get("brains", idx) if isinstance(idx, dict) else idx
    return [b["slug"] for b in brains]


def main():
    ap = argparse.ArgumentParser(description="Brain QA orchestrator + ship-gate")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--brain", help="Single brain slug")
    g.add_argument("--all", action="store_true", help="Whole fleet")
    ap.add_argument("--include-hidden", action="store_true", help="With --all, include hidden brains")
    ap.add_argument("--no-run", action="store_true", help="Read cached tier outputs only; never call the API")
    ap.add_argument("--run", action="store_true", help="With --all, actually run missing tiers (spends ~$6 fleet)")
    ap.add_argument("--refresh", action="store_true", help="Force re-run numeric + persona even if cached")
    ap.add_argument("--model", default=None, help="Model override for persona panel")
    ap.add_argument("--json", action="store_true", help="Machine-readable output")
    args = ap.parse_args()

    if args.brain:
        no_run = args.no_run
        r = evaluate(args.brain, no_run, args.refresh, args.model)
        if args.json:
            print(json.dumps(r, indent=2))
        else:
            print_brain(r)
        sys.exit(0 if r["ship"] else 1)

    # --all : default to cached unless --run given (cost guard)
    no_run = not args.run
    slugs = all_slugs() if args.include_hidden else live_slugs()
    if no_run and not args.json:
        warn(f"--all in CACHED mode ({len(slugs)} brains) — pass --run to execute missing tiers (~$6 fleet). "
             f"Brains without cached persona/numeric show '-'.")
    results = [evaluate(s, no_run, args.refresh, args.model) for s in slugs]
    # Rank by persona (faithful+useful+interesting composite), missing -> bottom.
    results.sort(key=lambda r: (r["persona"] is None, -(r["persona"] or 0)))

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"\n{'BRAIN':24s} {'PERSONA':>7} {'STRUCT':>6} {'BEHAV':>5} {'VOICE':>5} {'NUMdef':>6}  GATE")
    print("-" * 72)
    shipped = 0
    for r in results:
        gate = "SHIP" if r["ship"] else "hold"
        shipped += r["ship"]
        nd = r["high_numeric_defects"]
        print(f"{r['slug']:24s} {_fmt(r['persona'],7)} {_fmt(r['structural'],6)} "
              f"{_fmt(r['behavioral'],5)} "
              f"{(f'{r['voice_raw']:.2f}' if r['voice_raw'] is not None else '   -'):>5} "
              f"{(str(nd) if nd is not None else '-'):>6}  {gate}")
    print("-" * 72)
    print(f"{shipped}/{len(results)} clear the ship-gate"
          + ("" if not no_run else "  (cached mode — run --run for full coverage)"))


if __name__ == "__main__":
    main()
