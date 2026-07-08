#!/usr/bin/env python3
"""
Harden a decision bench so its numbers can be trusted.

Two failure modes in the raw benches:
  1. Leakage — an auto-generated case's leak_markers miss words that reveal the
     answer, so the brain arm just reads the answer instead of predicting it.
  2. Ceiling — lift is bounded by (1 - baseline); a bench full of cases a generic
     operator already gets leaves no headroom, so a good brain can't show lift.

This script fixes (1) directly and surfaces (2):
  - Auto-augments leak_markers from each case's own actual_decision + reasoning
    (proper nouns, numbers, distinctive content words) — deterministic, free.
  - Leak-verify pass: builds the exact filtered context the brain arm would see and
    asks a model whether the answer is present. Cases that still leak are DROPPED.

Run the runner afterward; the leaderboard's headroom-captured metric handles (2).

Usage:
  python3 scripts/decision-bench-harden.py --brain charlie-munger
  python3 scripts/decision-bench-harden.py --brain jesse-pujji --dry-run
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_build_config import BRAINS_DIR, DEFAULT_MODEL, CostTracker, call_claude, step, success, warn  # noqa: E402
# reuse the runner's context builders so leak-check sees EXACTLY what the brain sees
import importlib.util as _il
_spec = _il.spec_from_file_location("decbench", Path(__file__).resolve().parent / "decision-bench.py")
_dec = _il.module_from_spec(_spec); _spec.loader.exec_module(_dec)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

STOP = set("the a an and or but with from into that this your you his her their they them "
           "would could should when where what which while about over under after before then "
           "than have been being will shall must does doing done more most other rather instead "
           "full only just very much many some each both".split())


def auto_markers(case: dict) -> list[str]:
    text = f"{case.get('actual_decision','')} {case.get('actual_reasoning','')}"
    markers = set(m.lower() for m in case.get("leak_markers", []))
    # proper nouns (Capitalized, not sentence-start-only), numbers, distinctive long words
    for tok in re.findall(r"[A-Z][a-zA-Z]{2,}|\$?\d[\d,\.]*[MBK%]?|[a-zA-Z]{6,}", text):
        t = tok.strip(".,;:()").lower()
        if len(t) >= 3 and t not in STOP:
            markers.add(t)
    return sorted(markers)


LEAK_SYS = """You check a prediction benchmark for LEAKAGE. Below is the CONTEXT an AI would be given, then the HIDDEN ANSWER the AI is supposed to PREDICT (not read). Decide: does the context explicitly state, quote, or directly reveal this specific decision/outcome? Paraphrases and near-verbatim restatements count as leaked. General principles that merely make the answer guessable do NOT count as leaked — only actual presence of the specific answer.
Return ONLY JSON: {"leaked": true|false, "why": "<short>"}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bdir = BRAINS_DIR / args.brain
    brain = json.loads((bdir / "brain.json").read_text())
    syn = brain.get("synthesis", {}) or {}
    atoms = json.loads((bdir / "pack" / "brain-atoms.json").read_text()).get("atoms", [])
    path = bdir / "evals" / "decision-bench.json"
    bench = json.loads(path.read_text())
    cases = bench["cases"]

    step(f"Harden — {args.brain}: {len(cases)} cases")

    # 1) deterministic marker augmentation
    for c in cases:
        c["leak_markers"] = auto_markers(c)

    if args.dry_run:
        for c in cases[:6]:
            print(f"  [{c['id']}] markers now: {len(c['leak_markers'])}")
        return
    if Anthropic is None:
        print("ERROR: anthropic not installed"); sys.exit(1)
    client = Anthropic(); tracker = CostTracker()

    kept, dropped = [], []
    for c in cases:
        ctx = (_dec.render_synthesis(syn, c["leak_markers"]) + "\n\n### EVIDENCE\n"
               + _dec.filtered_atoms(atoms, c["leak_markers"], _dec.ATOM_CAP))
        u = f"CONTEXT:\n{ctx[:14000]}\n\nHIDDEN ANSWER: {c['actual_decision']}"
        res = call_claude(client, args.model, system=LEAK_SYS,
                          messages=[{"role": "user", "content": u}],
                          max_tokens=300, parse_json=True, cost_tracker=tracker, label=f"leak:{c['id']}")
        if res["parsed"].get("leaked"):
            c["_leak_why"] = res["parsed"].get("why", "")
            dropped.append(c)
        else:
            kept.append(c)
        print(f"  {c['id']:34s} {'LEAK→drop' if c in dropped else 'ok'}")

    bench["cases"] = kept
    bench["version"] = bench.get("version", 1) + 1
    bench["hardened"] = True
    path.write_text(json.dumps(bench, indent=2))
    success(f"{args.brain}: kept {len(kept)}, dropped {len(dropped)} leaky  (${tracker.total_cost:.3f})")
    if dropped:
        warn("dropped: " + ", ".join(d["id"] for d in dropped))


if __name__ == "__main__":
    main()
