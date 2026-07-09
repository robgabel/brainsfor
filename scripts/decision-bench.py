#!/usr/bin/env python3
"""
Decision benchmark — score a brain on PREDICTING the person's real decisions.

This is the objective LeCun's critique demands: a brain is only intelligent if it
can predict what the person would DO in a situation, not merely echo their voice.

For each held-out case in brains/<slug>/evals/decision-bench.json:
  - Strip every atom AND synthesis item that contains a leak_marker (the answer's
    fingerprint), so the brain must PREDICT, not recall.
  - BRAIN arm: give the model the filtered synthesis + atoms and ask it to predict
    the person's decision.
  - BASELINE arm: no brain at all — a generic thoughtful founder. This is the control.
  - A judge scores each prediction against ground truth (semantic, not wording).

Headline metric: brain accuracy MINUS baseline accuracy on the non-obvious subset.
If the brain doesn't beat a generic operator on the non-obvious calls, the capture
isn't adding signal — it's guessing the base rate.

Usage:
  python3 scripts/decision-bench.py --brain jesse-pujji
  python3 scripts/decision-bench.py --brain jesse-pujji --arm brain      # brain only
  python3 scripts/decision-bench.py --brain jesse-pujji --dry-run        # no API
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_build_config import (  # noqa: E402
    BRAINS_DIR, DEFAULT_MODEL, CostTracker, call_claude, step, success, warn,
)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

ATOM_CAP = 50  # filtered atoms shown to the brain arm


def contains_leak(text: str, markers: list[str]) -> bool:
    t = (text or "").lower()
    return any(m.lower() in t for m in markers)


def render_synthesis(syn: dict, markers: list[str]) -> str:
    """Render the person's constitution, dropping any item that leaks the answer."""
    parts = []
    sections = [
        ("first_principles", "FIRST PRINCIPLES"),
        ("thinking_patterns", "THINKING PATTERNS"),
        ("contrarian_positions", "CONTRARIAN POSITIONS"),
        ("does_not_believe", "DOES NOT BELIEVE"),
        ("would_not_say", "WOULD NOT SAY"),
        ("live_uncertainties", "LIVE UNCERTAINTIES"),
    ]
    for key, label in sections:
        items = syn.get(key) or []
        lines = []
        for it in items:
            t = it.get("title") or it.get("name") or ""
            d = it.get("desc") or it.get("description") or ""
            if contains_leak(t + " " + d, markers):
                continue  # answer fingerprint — withhold
            lines.append(f"- {t}" + (f": {d}" if d else ""))
        if lines:
            parts.append(f"### {label}\n" + "\n".join(lines))
    # decision_rules layer (world-model structure) — leak-filtered per case like everything else
    rules = syn.get("decision_rules") or []
    rlines = []
    for r in rules:
        blob = " ".join(str(r.get(k, "")) for k in ("when", "then", "because", "unless", "tradeoff"))
        if contains_leak(blob, markers):
            continue
        s = f"- WHEN {r.get('when','')}, he {r.get('then','')} (because {r.get('because','')})"
        if r.get("unless"):
            s += f" — UNLESS {r['unless']}"
        if r.get("tradeoff"):
            s += f" [trades off: {r['tradeoff']}]"
        rlines.append(s)
    if rlines:
        parts.append("### DECISION RULES (how he decides — conditional, with boundaries)\n" + "\n".join(rlines))
    return "\n\n".join(parts)


def filtered_atoms(atoms: list, markers: list[str], cap: int) -> str:
    """Diverse, quote-first atom sample with leaking atoms removed."""
    kept = [a for a in atoms
            if not contains_leak((a.get("content", "") + " " + (a.get("original_quote") or "")), markers)]
    by_cluster: dict[str, list] = {}
    for a in kept:
        by_cluster.setdefault(a.get("cluster", "?"), []).append(a)
    for c in by_cluster:
        by_cluster[c].sort(key=lambda a: 0 if a.get("original_quote") else 1)
    picked, idx, clusters = [], {c: 0 for c in by_cluster}, list(by_cluster)
    while len(picked) < cap and any(idx[c] < len(by_cluster[c]) for c in clusters):
        for c in clusters:
            if idx[c] < len(by_cluster[c]):
                picked.append(by_cluster[c][idx[c]]); idx[c] += 1
                if len(picked) >= cap:
                    break
    out = []
    for a in picked:
        line = f"- [{a.get('cluster','?')}] {a.get('content','')[:200]}"
        if a.get("original_quote"):
            line += f'\n    voice: "{a["original_quote"][:160]}"'
        out.append(line)
    return "\n".join(out)


PREDICT_BRAIN_SYS = """You are modeling how {name} actually thinks, in order to PREDICT a real decision he made.
Below is his constitution (principles, patterns) and evidence from his own words. The specific episode has been withheld — you must predict, not recall.

Given the situation, predict which option {name} ACTUALLY chose and why. Reason from his principles applied to the specifics — do not hedge to the safe/conventional answer if his real view diverges from it.

Return ONLY JSON: {{"choice_index": <int 0-based into the options list>, "decision": "<one sentence: what he did>", "reasoning": "<2-3 sentences in his logic>"}}

## {name}'s mind
{brain}"""

PREDICT_BASELINE_SYS = """You are a thoughtful, experienced startup founder and operator. Predict the WISEST decision in the situation below — your honest best judgment, with no knowledge of any specific person's choice.

Return ONLY JSON: {{"choice_index": <int 0-based into the options list>, "decision": "<one sentence>", "reasoning": "<2-3 sentences>"}}"""

JUDGE_SYS = """You are grading a prediction of a real decision. Compare the PREDICTED decision to the ACTUAL decision on SUBSTANCE (the course of action chosen), ignoring wording and style. Partial credit is not given — either the prediction lands on the same essential choice or it does not.

Return ONLY JSON: {"correct": true|false, "note": "<one clause: why>"}"""


def user_block(case: dict) -> str:
    opts = "\n".join(f"  {i}. {o}" for i, o in enumerate(case["options"]))
    return f"SITUATION:\n{case['situation']}\n\nOPTIONS:\n{opts}"


def predict(client, model, sys_prompt, case, tracker, label):
    res = call_claude(client, model, system=sys_prompt,
                      messages=[{"role": "user", "content": user_block(case)}],
                      max_tokens=700, parse_json=True, cost_tracker=tracker, label=label)
    return res["parsed"]


def judge(client, model, case, pred, tracker):
    u = (f"ACTUAL decision: {case['actual_decision']}\n"
         f"ACTUAL reasoning: {case['actual_reasoning']}\n\n"
         f"PREDICTED decision: {pred.get('decision','')}\n"
         f"PREDICTED reasoning: {pred.get('reasoning','')}")
    res = call_claude(client, model, system=JUDGE_SYS,
                      messages=[{"role": "user", "content": u}],
                      max_tokens=300, parse_json=True, cost_tracker=tracker, label="judge")
    return res["parsed"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--arm", choices=["brain", "baseline", "both"], default="both")
    ap.add_argument("--limit", type=int, default=0, help="run only the first N cases (0 = all)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--date", default="unknown")
    args = ap.parse_args()

    bdir = BRAINS_DIR / args.brain
    brain = json.loads((bdir / "brain.json").read_text())
    name = brain.get("name") or args.brain
    syn = brain.get("synthesis", {}) or {}
    atoms = json.loads((bdir / "pack" / "brain-atoms.json").read_text()).get("atoms", [])
    bench = json.loads((bdir / "evals" / "decision-bench.json").read_text())
    cases = bench["cases"]
    if args.limit:
        cases = cases[:args.limit]

    step(f"Decision bench — {name}: {len(cases)} cases, arm={args.arm}")

    if args.dry_run:
        for c in cases:
            keptn = sum(1 for a in atoms if not contains_leak(
                a.get("content", "") + " " + (a.get("original_quote") or ""), c["leak_markers"]))
            print(f"  [{c['id']}] obvious={c['obvious']} atoms_after_leak_filter={keptn}/{len(atoms)}")
        return

    if Anthropic is None:
        print("ERROR: anthropic package not installed"); sys.exit(1)
    client = Anthropic()
    tracker = CostTracker()

    results = []
    for c in cases:
        row = {"id": c["id"], "obvious": c["obvious"], "actual": c["actual_decision"]}
        brain_ctx = (render_synthesis(syn, c["leak_markers"]) + "\n\n### EVIDENCE (his words)\n"
                     + filtered_atoms(atoms, c["leak_markers"], ATOM_CAP))
        if args.arm in ("brain", "both"):
            p = predict(client, args.model,
                        PREDICT_BRAIN_SYS.format(name=name, brain=brain_ctx), c, tracker, f"brain:{c['id']}")
            v = judge(client, args.model, c, p, tracker)
            row["brain"] = {"pred": p.get("decision", ""), "correct": bool(v.get("correct")), "note": v.get("note", "")}
        if args.arm in ("baseline", "both"):
            p = predict(client, args.model, PREDICT_BASELINE_SYS.format(name=name), c, tracker, f"base:{c['id']}")
            v = judge(client, args.model, c, p, tracker)
            row["baseline"] = {"pred": p.get("decision", ""), "correct": bool(v.get("correct")), "note": v.get("note", "")}
        results.append(row)
        bmark = "✓" if row.get("brain", {}).get("correct") else "✗"
        xmark = ("✓" if row.get("baseline", {}).get("correct") else "✗") if "baseline" in row else "-"
        print(f"  {c['id']:24s} brain={bmark}  baseline={xmark}")

    def acc(arm, subset=None):
        rows = [r for r in results if arm in r and (subset is None or r["obvious"] == subset)]
        if not rows:
            return None, 0
        n = sum(1 for r in rows if r[arm]["correct"])
        return n / len(rows), len(rows)

    summary = {}
    for arm in (["brain", "baseline"] if args.arm == "both" else [args.arm]):
        a_all, n_all = acc(arm)
        a_hard, n_hard = acc(arm, subset=False)
        summary[arm] = {"all": a_all, "n_all": n_all, "non_obvious": a_hard, "n_non_obvious": n_hard}

    print("\n" + "=" * 60)
    print(f"  DECISION ACCURACY — {name}")
    print("=" * 60)
    for arm, s in summary.items():
        print(f"  {arm:9s}  all {s['all']*100:5.1f}% ({s['n_all']})   "
              f"non-obvious {s['non_obvious']*100:5.1f}% ({s['n_non_obvious']})")
    if "brain" in summary and "baseline" in summary:
        lift = (summary["brain"]["non_obvious"] - summary["baseline"]["non_obvious"]) * 100
        print(f"\n  LIFT (brain − baseline, non-obvious): {lift:+.1f} pts")
        print("  → positive lift means the capture adds signal beyond a generic operator.")
    print(f"\n  cost ${tracker.total_cost:.3f}")

    out = {"brain": args.brain, "person": name, "date": args.date,
           "model": args.model, "summary": summary, "results": results,
           "cost": tracker.total_cost}
    path = bdir / "evals" / f"decision-bench-results-{args.date}.json"
    path.write_text(json.dumps(out, indent=2))
    success(f"wrote {path}")


if __name__ == "__main__":
    main()
