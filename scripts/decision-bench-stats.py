#!/usr/bin/env python3
"""
Aggregate repeated decision-bench runs into mean +/- spread per brain.

A single run has a big error bar (binary scoring on ~20 cases + model sampling).
This reads R result files per brain and reports the mean and run-to-run spread of
brain accuracy, baseline accuracy, lift, and headroom-captured — so every number
carries its uncertainty instead of pretending to be precise.

Usage:
  python3 scripts/decision-bench-stats.py --brains jesse-pujji,paul-graham,charlie-munger,peter-attia,steve-jobs --dates r1,r2,r3
"""
from __future__ import annotations
import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_build_config import BRAINS_DIR  # noqa: E402


def load(slug, date):
    p = BRAINS_DIR / slug / "evals" / f"decision-bench-results-{date}.json"
    if not p.exists():
        return None
    s = json.loads(p.read_text()).get("summary", {})
    b = (s.get("brain") or {}).get("non_obvious")
    x = (s.get("baseline") or {}).get("non_obvious")
    n = (s.get("brain") or {}).get("n_non_obvious")
    if b is None or x is None:
        return None
    ceil = 1 - x
    head = (b - x) / ceil if ceil > 1e-6 else None
    return {"brain": b * 100, "baseline": x * 100, "lift": (b - x) * 100,
            "headroom": head * 100 if head is not None else None, "n": n}


def ms(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None, None
    return st.mean(vals), (st.pstdev(vals) if len(vals) > 1 else 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brains", required=True)
    ap.add_argument("--dates", required=True, help="comma list of run date-tags")
    ap.add_argument("--out", default="decision-bench-variance")
    args = ap.parse_args()
    slugs = [s.strip() for s in args.brains.split(",")]
    dates = [d.strip() for d in args.dates.split(",")]

    rows = []
    for slug in slugs:
        runs = [load(slug, d) for d in dates]
        runs = [r for r in runs if r]
        if not runs:
            continue
        bm, bs = ms([r["brain"] for r in runs])
        xm, xs = ms([r["baseline"] for r in runs])
        lm, ls = ms([r["lift"] for r in runs])
        hm, hs = ms([r["headroom"] for r in runs])
        rows.append({"slug": slug, "runs": len(runs), "n": runs[0]["n"],
                     "brain_mean": bm, "brain_sd": bs, "base_mean": xm,
                     "lift_mean": lm, "lift_sd": ls, "lift_min": min(r["lift"] for r in runs),
                     "lift_max": max(r["lift"] for r in runs),
                     "head_mean": hm, "head_sd": hs})

    rows.sort(key=lambda r: (r["head_mean"] is not None, r["head_mean"] or -1e9), reverse=True)
    print("\n" + "=" * 78)
    print(f"  DECISION-BENCH VARIANCE — {len(dates)} runs/brain")
    print("=" * 78)
    print(f"  {'brain':16s} {'predicts':>12s} {'baseline':>9s} {'lift (mean/range)':>20s} {'headroom':>12s}")
    for r in rows:
        print(f"  {r['slug']:16s} "
              f"{r['brain_mean']:5.0f}±{r['brain_sd']:<4.0f}% "
              f"{r['base_mean']:7.0f}% "
              f"{r['lift_mean']:+5.0f} [{r['lift_min']:+.0f},{r['lift_max']:+.0f}]     "
              f"{r['head_mean']:+5.0f}±{r['head_sd']:<3.0f}%")
    print("\n  A brain's signal is real only if lift_mean exceeds its run-to-run spread (sd).")
    print("  Bunched brains whose spread swamps their lift are not yet separable.")

    out = BRAINS_DIR.parent / "brains" / f"{args.out}.json"
    out.write_text(json.dumps({"dates": dates, "rows": rows}, indent=2))
    print(f"\n  wrote {out}")


if __name__ == "__main__":
    main()
