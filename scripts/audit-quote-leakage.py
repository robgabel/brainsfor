#!/usr/bin/env python3
"""
audit-quote-leakage.py — flag interviewer/host text that leaked into a brain's
`original_quote` atoms.

Zero-cost, deterministic, no API calls. Reads the shipped pack
(`brains/<slug>/pack/brain-atoms.json`) and scores each `original_quote` against
host-phrasing heuristics. A subject's quote should be THEIR insight — not the
interviewer's question or framing. This tells you, for ~$0, whether a brain is
actually carrying leaked interviewer text (→ worth a diarized rebuild) or just
has the occasional legitimate rhetorical question (→ leave it alone).

Severity:
  HOST     — strong interviewer tell ("welcome to", "tell me about", "how did
             you get into", "thanks for joining"...). Very likely leakage.
  QUESTION — a bare question with no host tell. Possible leakage, but the
             subject may simply be asking rhetorically. Eyeball before acting.

Usage:
  python3 scripts/audit-quote-leakage.py                      # ranked summary, all brains
  python3 scripts/audit-quote-leakage.py --brain scott-belsky # one brain
  python3 scripts/audit-quote-leakage.py --show               # print the flagged quotes
  python3 scripts/audit-quote-leakage.py --show --host-only   # only strong (HOST) hits
  python3 scripts/audit-quote-leakage.py --limit 10           # cap printed quotes per brain
  python3 scripts/audit-quote-leakage.py --json               # machine-readable
  python3 scripts/audit-quote-leakage.py --source research    # scan research/all-atoms.json instead
"""

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- Strong interviewer/host tells. A match here is very likely NOT the subject. ---
HOST_PATTERNS = [
    r"\bwelcome (back )?to\b",
    r"\bthank(s| you)( so much)? for (coming|joining|being here|having me)\b",
    r"\b(joining (me|us)( today| now| is)?|our guest( today)?|here with (me|us)|with us (today|now))\b",
    r"\b(let me ask you|i (just )?(want|wanted|have|need) to ask|my (next|first|last|second) question|let'?s (start|begin|talk|dive|get) (with|into|about))\b",
    r"\b(tell me (about|a little|more)|tell us (about|more)|walk me through|walk us through|can you (talk|tell|explain|describe|walk|share|give) (me|us)\b)",
    r"\b(how did you (get|start|begin|come|decide|end up|first)|what (made|got|led|drew) you|when did you (first|realize|know|start)|why did you (decide|choose|start))\b",
    r"\b(before we (go|wrap|start|begin|move on|finish)|last question|one (more|last) (thing|question)|as we wrap|in the time we have)\b",
    r"\b(for (our|the|my) (listeners|audience|viewers|readers)|on (this|the|our) (show|podcast|episode|program))\b",
    r"\b(i'?m here with|today (i'?m|we'?re|my guest)|so glad (you|to have)|great to have you)\b",
]
HOST_RE = re.compile("|".join(HOST_PATTERNS), re.I)

# A "question" cue: ends with ? OR opens with an interrogative aimed at the speaker.
INTERROGATIVE_OPEN = re.compile(
    r"^\s*(what|why|how|when|where|who|which|do you|did you|are you|have you|"
    r"would you|could you|can you|is it|was it|tell me|talk to me)\b", re.I)

# Real interviewer text addresses the subject in 2nd person ("how did YOU...").
# First-person statements ("Today WE'RE announcing", "I have looked in the mirror")
# that merely brush a host phrase are the SUBJECT talking — not leakage.
SECOND_PERSON = re.compile(r"\b(you|your|you're|you've|you'd|you'll)\b", re.I)
FIRST_PERSON = re.compile(r"\b(i|i'm|i've|i'd|we|we're|we've|my|our|us|me)\b", re.I)


def classify(quote: str):
    """Return 'host', 'question', or None for a single original_quote string."""
    q = (quote or "").strip()
    if not q:
        return None
    if HOST_RE.search(q):
        # Only treat as interviewer text if it addresses the subject (2nd person)
        # or carries no 1st-person subject markers. This suppresses the common
        # false positive of a subject's own announcement/anecdote.
        if SECOND_PERSON.search(q) or not FIRST_PERSON.search(q):
            return "host"
    if q.rstrip().endswith("?") or INTERROGATIVE_OPEN.match(q):
        return "question"
    return None


def load_atoms(slug: str, source: str) -> list:
    if source == "research":
        p = ROOT / "brains" / slug / "research" / "all-atoms.json"
    else:
        p = ROOT / "brains" / slug / "pack" / "brain-atoms.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except Exception:
        return []
    return data.get("atoms", data) if isinstance(data, dict) else data


def audit_brain(slug: str, source: str) -> dict:
    atoms = load_atoms(slug, source)
    quoted = [a for a in atoms if (a.get("original_quote") or "").strip()]
    flags = []
    for a in quoted:
        sev = classify(a.get("original_quote"))
        if sev:
            flags.append({
                "id": a.get("id", ""),
                "severity": sev,
                "cluster": a.get("cluster", ""),
                "quote": (a.get("original_quote") or "").strip(),
            })
    n_host = sum(1 for f in flags if f["severity"] == "host")
    n_q = sum(1 for f in flags if f["severity"] == "question")
    return {
        "slug": slug,
        "quoted": len(quoted),
        "host": n_host,
        "question": n_q,
        "flagged": len(flags),
        "pct": round(100 * len(flags) / len(quoted), 1) if quoted else 0.0,
        "host_pct": round(100 * n_host / len(quoted), 1) if quoted else 0.0,
        "flags": flags,
    }


def discover_slugs() -> list:
    out = []
    for p in sorted(glob.glob(str(ROOT / "brains" / "*" / "pack" / "brain-atoms.json"))):
        out.append(Path(p).parts[-3])
    return out


def main():
    ap = argparse.ArgumentParser(description="Flag interviewer text leaked into original_quote atoms.")
    ap.add_argument("--brain", help="Single brain slug (default: all)")
    ap.add_argument("--source", choices=["pack", "research"], default="pack",
                    help="Which atoms to scan (default: shipped pack)")
    ap.add_argument("--show", action="store_true", help="Print the flagged quote strings")
    ap.add_argument("--host-only", action="store_true", help="Only HOST-severity (strong) hits")
    ap.add_argument("--limit", type=int, default=15, help="Max quotes printed per brain with --show")
    ap.add_argument("--json", action="store_true", help="Machine-readable output")
    args = ap.parse_args()

    slugs = [args.brain] if args.brain else discover_slugs()
    results = [audit_brain(s, args.source) for s in slugs]
    results = [r for r in results if r["quoted"] > 0]
    results.sort(key=lambda r: (-r["host_pct"], -r["pct"]))

    if args.json:
        print(json.dumps(results, indent=2))
        return

    # Summary table
    print(f"\n  Quote-leakage audit ({args.source})  —  HOST = strong tell, QUESTION = possible\n")
    print(f"  {'brain':22}{'quoted':>7}{'HOST':>6}{'QUEST':>7}{'host%':>7}{'flag%':>7}")
    print("  " + "-" * 56)
    tot_q = tot_h = tot_f = 0
    for r in results:
        tot_q += r["quoted"]; tot_h += r["host"]; tot_f += r["flagged"]
        mark = "  <== review" if r["host"] >= 3 else ""
        print(f"  {r['slug']:22}{r['quoted']:7}{r['host']:6}{r['question']:7}"
              f"{r['host_pct']:6}%{r['pct']:6}%{mark}")
    print("  " + "-" * 56)
    hp = round(100 * tot_h / tot_q, 1) if tot_q else 0
    fp = round(100 * tot_f / tot_q, 1) if tot_q else 0
    print(f"  {'TOTAL':22}{tot_q:7}{tot_h:6}{'':7}{hp:6}%{fp:6}%")
    print(f"\n  HOST hits are the strong signal — a brain with several is a real diarized-rebuild")
    print(f"  candidate. QUESTION-only hits are often legitimate rhetorical questions; use --show")
    print(f"  to eyeball before deciding.\n")

    if args.show:
        for r in results:
            shown = [f for f in r["flags"] if (f["severity"] == "host" or not args.host_only)]
            if not shown:
                continue
            shown.sort(key=lambda f: 0 if f["severity"] == "host" else 1)
            print(f"\n  === {r['slug']} ({len(shown)} flagged) ===")
            for f in shown[:args.limit]:
                tag = "HOST" if f["severity"] == "host" else "q?  "
                q = f["quote"]
                q = q if len(q) <= 160 else q[:157] + "..."
                print(f"   [{tag}] {q}")
            if len(shown) > args.limit:
                print(f"   ... +{len(shown) - args.limit} more (raise --limit)")


if __name__ == "__main__":
    main()
