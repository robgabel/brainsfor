#!/usr/bin/env python3
"""
Generate a decision_rules layer for a brain — the world-model structure the raw
atom-bag lacks. Each rule is a GENERAL conditional: WHEN <condition> he does <action>
BECAUSE <principle>, UNLESS <boundary/override>, trading off against <tension>.

The point (LeCun): a retrieval system stores episodes; a world model stores the
conditional rules that let you predict UNSEEN situations. These rules are general
(transfer across cases), not restatements of specific episodes — and at bench time
they get the same per-case leak-filtering as everything else, so a rule can only
help by genuine transfer, never by leaking an answer.

Writes synthesis.decision_rules into brain.json.

Usage:
  python3 scripts/decision-rules-gen.py --brain jesse-pujji --n 22
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_build_config import BRAINS_DIR, DEFAULT_MODEL, CostTracker, call_claude, step, success  # noqa: E402

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

CUES = re.compile(r"\b(when|if|because|unless|instead|rather than|only|always|never|"
                  r"trade[- ]?off|depends|boundary|first|until)\b", re.I)

GEN_SYS = """You extract the DECISION RULES that let someone PREDICT what {name} would do in situations he has never explicitly discussed. This is a world-model layer, not a quote bank.

Each rule must be:
- GENERAL and TRANSFERABLE — a conditional that applies across many situations, not a retelling of one episode. Never name a specific company, deal, person, or dollar figure; state the underlying pattern.
- CONDITIONAL — it must expose WHEN it fires and, crucially, the BOUNDARY where it flips or is overridden. The boundary condition is the most valuable part: it's what separates a real model from a slogan.
- GROUNDED — derived from his documented reasoning below, in his actual logic.
- Include real TENSIONS between his own rules (where two principles pull opposite ways and how he resolves it).

Return ONLY JSON: {{"decision_rules": [{{"id": "<kebab>", "when": "<the situation/condition>", "then": "<what he does>", "because": "<the principle>", "unless": "<the boundary/override where this flips>", "tradeoff": "<the competing principle it's balanced against, or empty>"}}]}}

Aim for up to {n} rules. Prefer rules with a real, non-trivial 'unless' — those are the ones that make the difference on hard cases."""


def corpus(brain, atoms):
    syn = brain.get("synthesis", {}) or {}
    parts = ["## PRINCIPLES"]
    for key in ("first_principles", "contrarian_positions", "does_not_believe", "would_not_say", "live_uncertainties"):
        for it in (syn.get(key) or []):
            parts.append(f"- {it.get('title','')}: {it.get('desc','')}")
    parts.append("\n## THINKING PATTERNS")
    for it in (syn.get("thinking_patterns") or []):
        parts.append(f"- {it.get('name','')}: {it.get('desc','')}")
    parts.append("\n## HARD LESSONS")
    for h in (syn.get("hard_lessons") or []):
        parts.append(f"- {h.get('title','')} -> {h.get('change','')}")
    parts.append("\n## REASONING FROM ATOMS")
    dec = [a for a in atoms if CUES.search(a.get("content", ""))]
    for a in dec[:90]:
        parts.append(f"- {a.get('content','')[:240]}")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--n", type=int, default=22)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bpath = BRAINS_DIR / args.brain / "brain.json"
    brain = json.loads(bpath.read_text())
    name = brain.get("name") or args.brain
    atoms = json.loads((BRAINS_DIR / args.brain / "pack" / "brain-atoms.json").read_text()).get("atoms", [])
    body = corpus(brain, atoms)

    step(f"decision-rules-gen — {name}, target {args.n} rules")
    if args.dry_run:
        print(body[:1500]); return
    if Anthropic is None:
        print("ERROR: anthropic not installed"); sys.exit(1)
    client = Anthropic(); tracker = CostTracker()
    res = call_claude(client, args.model, system=GEN_SYS.format(name=name, n=args.n),
                      messages=[{"role": "user", "content": "DOCUMENTED REASONING:\n\n" + body[:55000]}],
                      max_tokens=8000, parse_json=True, cost_tracker=tracker, label=f"rules:{args.brain}")
    rules = res["parsed"].get("decision_rules", [])
    rules = [r for r in rules if r.get("when") and r.get("then")]
    brain.setdefault("synthesis", {})["decision_rules"] = rules
    bpath.write_text(json.dumps(brain, indent=2))
    success(f"{args.brain}: wrote {len(rules)} decision_rules → brain.json  (${tracker.total_cost:.3f})")


if __name__ == "__main__":
    main()
