#!/usr/bin/env python3
"""
Decision-benchmark GENERATOR — mine a brain's own corpus for held-out decision cases.

Hand-authoring 40 grounded decisions per person doesn't scale to a fleet. This
extracts them: it feeds the model the person's documented decisions (hard_lessons,
biography, and decision-flavored atoms) and asks for prediction cases in the exact
decision-bench schema, each grounded in the text, with auto-derived leak_markers.

Only emits a case when the corpus states BOTH the situation AND the actual choice —
no invented decisions. Prefers non-obvious / contrarian calls (the discriminating ones).

Usage:
  python3 scripts/decision-bench-gen.py --brain paul-graham --n 25          # write bench
  python3 scripts/decision-bench-gen.py --brain jesse-pujji --n 26 --merge  # add to existing
  python3 scripts/decision-bench-gen.py --brain sun-tzu --dry-run           # show corpus size
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_build_config import BRAINS_DIR, DEFAULT_MODEL, CostTracker, call_claude, step, success, warn  # noqa: E402

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

DECISION_CUES = re.compile(
    r"\b(chose|decided|refused|declined|turned down|instead of|rather than|shut down|"
    r"doubled down|walked away|bet on|hired|fired|raised|bootstrapp|quit|left|rejected|"
    r"picked|opted|insisted|pivot|acquir|sold|bought|launched|killed|passed on)\b", re.I)

GEN_SYS = """You build a DECISION PREDICTION BENCHMARK for {name}. Each case tests whether an AI can predict what {name} ACTUALLY did in a real situation — so the cases must be grounded in the documented record below, never invented.

Rules:
- Emit a case ONLY when the material states BOTH a real situation {name} faced AND the specific choice they actually made. If the choice isn't in the text, skip it.
- Prefer NON-OBVIOUS decisions: cases where a generic thoughtful person would plausibly guess a DIFFERENT option than {name} actually chose. These are the valuable ones. Mark obvious=true only if any sensible person would land on the same choice.
- 2-4 realistic options; exactly one matches what {name} really did; the others must be genuinely plausible, not strawmen.
- situation: written cold, second person ("You face..."), with NO hint of the answer.
- leak_markers: 4-10 specific substrings (names, numbers, distinctive nouns/verbs) that would reveal the answer if present in retrieved context. Be thorough — include the distinctive words from the actual_decision and reasoning.
- actual_reasoning: 1-2 sentences in {name}'s real logic.
- source: a short fingerprint (a few words) of the quote/passage it came from.

Return ONLY JSON: {{"cases": [{{"id": "<kebab-slug>", "obvious": <bool>, "situation": "...", "options": ["...","..."], "actual_decision": "...", "actual_reasoning": "...", "leak_markers": ["...","..."], "source": "..."}}]]}}

Aim for up to {n} high-quality cases. Fewer excellent grounded cases beat many thin ones."""


def decision_corpus(brain: dict, atoms: list) -> str:
    """Assemble the person's documented decisions for the generator to mine."""
    syn = brain.get("synthesis", {}) or {}
    parts = []
    hl = syn.get("hard_lessons") or []
    if hl:
        parts.append("## HARD LESSONS (mistake -> choice -> change)")
        for h in hl:
            rc = " ".join((r.get("quote") or "") for r in (h.get("receipts") or []))
            parts.append(f"- {h.get('title','')} | cost: {h.get('cost','')} | changed: {h.get('change','')} | {rc[:300]}")
    bio = syn.get("biography") or []
    if bio:
        parts.append("\n## BIOGRAPHY (dated moves + lessons)")
        for b in bio:
            parts.append(f"- {b.get('date','')}: {b.get('role','')} — {b.get('lesson','')}")
    # decision-flavored atoms
    dec_atoms = [a for a in atoms if DECISION_CUES.search(a.get("content", "") + " " + (a.get("original_quote") or ""))]
    if dec_atoms:
        parts.append("\n## DOCUMENTED CHOICES (from atoms)")
        for a in dec_atoms[:120]:
            line = f"- {a.get('content','')[:260]}"
            if a.get("original_quote"):
                line += f' | "{a["original_quote"][:180]}"'
            parts.append(line)
    return "\n".join(parts), len(dec_atoms)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--merge", action="store_true", help="merge into existing decision-bench.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bdir = BRAINS_DIR / args.brain
    brain = json.loads((bdir / "brain.json").read_text())
    name = brain.get("name") or args.brain
    atoms = json.loads((bdir / "pack" / "brain-atoms.json").read_text()).get("atoms", [])
    corpus, n_dec = decision_corpus(brain, atoms)

    step(f"Decision-bench-gen — {name}: {n_dec} decision-flavored atoms, target {args.n} cases")
    if args.dry_run:
        print(corpus[:2000]); return

    if Anthropic is None:
        print("ERROR: anthropic not installed"); sys.exit(1)
    client = Anthropic(); tracker = CostTracker()
    res = call_claude(client, args.model,
                      system=GEN_SYS.format(name=name, n=args.n),
                      messages=[{"role": "user", "content": "DOCUMENTED RECORD:\n\n" + corpus[:60000]}],
                      max_tokens=8000, parse_json=True, cost_tracker=tracker, label=f"gen:{args.brain}")
    new_cases = res["parsed"].get("cases", [])
    # de-dupe by id
    seen, clean = set(), []
    for c in new_cases:
        cid = c.get("id")
        if not cid or cid in seen or not c.get("actual_decision") or not c.get("options"):
            continue
        seen.add(cid); clean.append(c)

    path = bdir / "evals" / "decision-bench.json"
    if args.merge and path.exists():
        bench = json.loads(path.read_text())
        existing = {c["id"] for c in bench["cases"]}
        added = [c for c in clean if c["id"] not in existing]
        bench["cases"].extend(added)
        bench["version"] = bench.get("version", 1) + 1
        path.write_text(json.dumps(bench, indent=2))
        success(f"merged +{len(added)} cases → {len(bench['cases'])} total in {path}  (${tracker.total_cost:.3f})")
    else:
        bench = {"brain": args.brain, "person": name,
                 "purpose": "Auto-generated held-out decision benchmark (decision-bench-gen.py). Grounded in the brain's own corpus; spot-check before trusting fleet numbers.",
                 "version": 1, "generated": True, "cases": clean}
        path.write_text(json.dumps(bench, indent=2))
        success(f"wrote {len(clean)} cases → {path}  (${tracker.total_cost:.3f})")


if __name__ == "__main__":
    main()
