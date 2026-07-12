#!/usr/bin/env python3
"""
Fleet decision benchmark — rank brains by how well they PREDICT their person's
real decisions, relative to a no-brain baseline.

For each brain: auto-generate a held-out decision bench if missing (--gen), run the
brain + baseline arms, then rank the fleet by non-obvious lift (brain - baseline).
A brain with high lift is a model of the person; one near/below zero is a transcript
wearing a voice.

Usage:
  python3 scripts/decision-bench-fleet.py --brains jesse-pujji,paul-graham,charlie-munger,sun-tzu,peter-attia --gen --limit 20
  python3 scripts/decision-bench-fleet.py --brains live --gen         # every live brain (expensive)
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_build_config import BRAINS_DIR  # noqa: E402

ROOT = BRAINS_DIR.parent
SCRIPTS = Path(__file__).resolve().parent
PY = sys.executable


def live_brains() -> list[str]:
    idx = json.loads((BRAINS_DIR / "index.json").read_text())
    return [b["slug"] for b in idx["brains"] if b.get("status") == "live"]


def run(cmd: list[str]) -> int:
    print("  $ " + " ".join(str(c) for c in cmd[-3:]))
    return subprocess.run(cmd, cwd=ROOT).returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brains", required=True, help="comma list of slugs, or 'live'")
    ap.add_argument("--model", default=None)
    ap.add_argument("--date", default="unknown")
    ap.add_argument("--limit", type=int, default=0, help="cap cases per brain (cost control)")
    ap.add_argument("--gen", action="store_true", help="auto-generate a bench when missing")
    ap.add_argument("--gen-n", type=int, default=22, help="cases to generate when missing")
    args = ap.parse_args()

    slugs = live_brains() if args.brains == "live" else [s.strip() for s in args.brains.split(",")]
    model_args = ["--model", args.model] if args.model else []

    rows = []
    for slug in slugs:
        bdir = BRAINS_DIR / slug
        if not (bdir / "brain.json").exists():
            print(f"  skip {slug}: no brain.json"); continue
        bench = bdir / "evals" / "decision-bench.json"
        if not bench.exists():
            if not args.gen:
                print(f"  skip {slug}: no decision-bench.json (pass --gen)"); continue
            print(f"[gen] {slug}")
            if run([PY, str(SCRIPTS / "decision-bench-gen.py"), "--brain", slug, "--n", str(args.gen_n), *model_args]) != 0:
                print(f"  gen failed for {slug}"); continue
        print(f"[run] {slug}")
        cmd = [PY, str(SCRIPTS / "decision-bench.py"), "--brain", slug, "--date", args.date, *model_args]
        if args.limit:
            cmd += ["--limit", str(args.limit)]
        if run(cmd) != 0:
            print(f"  run failed for {slug}"); continue
        res_path = bdir / "evals" / f"decision-bench-results-{args.date}.json"
        if not res_path.exists():
            print(f"  no results for {slug}"); continue
        r = json.loads(res_path.read_text())
        s = r["summary"]
        b = s.get("brain", {}); x = s.get("baseline", {})
        lift, headroom = None, None
        if b.get("non_obvious") is not None and x.get("non_obvious") is not None:
            lift = (b["non_obvious"] - x["non_obvious"]) * 100
            ceil = 1 - x["non_obvious"]
            headroom = (b["non_obvious"] - x["non_obvious"]) / ceil * 100 if ceil > 1e-6 else None
        rows.append({"slug": slug, "brain": b.get("non_obvious"), "baseline": x.get("non_obvious"),
                     "n": b.get("n_non_obvious"), "lift": lift, "headroom_captured": headroom})

    # rank by headroom captured (ceiling-normalized) — fairer than raw lift
    rows.sort(key=lambda r: (r["headroom_captured"] is not None, r["headroom_captured"] or -999), reverse=True)
    print("\n" + "=" * 74)
    print("  FLEET DECISION-ACCURACY LEADERBOARD (non-obvious subset)")
    print("=" * 74)
    print(f"  {'brain':18s} {'predicts':>9s} {'baseline':>9s} {'lift':>7s} {'headroom':>9s}  n")
    for r in rows:
        bp = f"{r['brain']*100:.0f}%" if r["brain"] is not None else "-"
        bl = f"{r['baseline']*100:.0f}%" if r["baseline"] is not None else "-"
        lf = f"{r['lift']:+.0f}" if r["lift"] is not None else "-"
        hr = f"{r['headroom_captured']:+.0f}%" if r["headroom_captured"] is not None else "-"
        print(f"  {r['slug']:18s} {bp:>9s} {bl:>9s} {lf:>7s} {hr:>9s}  {r['n']}")
    print("\n  headroom = lift / (1 - baseline): share of the ACHIEVABLE gap the brain captured.")
    print("  It neutralizes benches with high baselines (little room) vs low (lots of room).")
    print("  >0 → a decision model.  <=0 → coherent voice, not yet a model.")

    out = ROOT / "brains" / f"decision-bench-fleet-{args.date}.json"
    out.write_text(json.dumps({"date": args.date, "leaderboard": rows}, indent=2))
    print(f"\n  wrote {out}")


if __name__ == "__main__":
    main()
