#!/usr/bin/env python3
"""Numeric-claims verifier — catch hard figures the brain gets wrong.

Every "hard number" a brain asserts about its human (revenue, users, raise, exit,
multiples, dates) is a fidelity liability. The classic defect: the brain says
"Ampush revenue ~$10M" while the corpus says "$30M". A string-match audit can't
catch it (both are grounded *somewhere*); only checking each figure for a
LARGER/NEWER corpus value does.

Pipeline:
  1. Scan the brain's ASSERTIONS — synthesis (first_principles, contrarian_positions,
     does_not_believe, would_not_say, biography, hero_tagline) + hard_lessons
     (title/cost/change). Receipts are verbatim corpus, so they're skipped.
  2. Regex-detect figure-bearing sentences (money, "N figures", counts, %, Nx, years).
  3. ONE LLM pass: given the corpus of the person's own words, classify each figure
     claim as grounded | superseded | ungrounded | unverifiable, returning the
     corpus value + a verbatim evidence quote when a larger/newer figure exists.
  4. Emit a defect list with severity + a fidelity penalty the persona-QA panel reads.

Output:
  brains/<slug>/evals/numeric-claims-<YYYY-MM-DD>.json  (machine-readable; panel input)
  stdout scorecard.

Exit code: 0 if no high-severity defects, 1 otherwise (ship-gate signal).

Usage:
  python3 scripts/verify-claims.py --brain jesse-pujji
  python3 scripts/verify-claims.py --brain jesse-pujji --dry-run   # list figure claims, no API
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import importlib.util

# Reuse corpus loading from fact-check-brain (hyphenated filename -> importlib).
_fc = importlib.util.spec_from_file_location("factcheck", SCRIPT_DIR / "fact-check-brain.py")
fc = importlib.util.module_from_spec(_fc)
_fc.loader.exec_module(fc)

from auto_build_config import (  # noqa: E402
    BRAINS_DIR, DEFAULT_MODEL, CostTracker, call_claude, step, success, warn, error,
)

try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: pip install anthropic"); sys.exit(1)

# Sections whose text we treat as the brain's assertions about the person.
ASSERTION_SECTIONS = (
    "first_principles", "thinking_patterns", "contrarian_positions",
    "does_not_believe", "would_not_say", "biography",
)

# Figure detectors. Each match marks the containing sentence as a numeric claim.
FIGURE_PATTERNS = [
    r"\$\s?\d[\d,]*\.?\d*\s?(?:[KMB]\b|thousand|million|billion|trillion|bn|k\b|m\b)?",  # $30M, $60,000
    r"\b(?:single|double|triple|four|five|six|seven|eight|nine|ten)[\s-]?figures?\b",     # nine figures
    r"\b\d\s?figures?\b",                                                                  # 8 figures
    r"\b(?:hundreds?|thousands?|millions?|billions?)\s+of\s+(?:dollars|users|customers|people|downloads|views|followers|subscribers)\b",
    r"\b\d[\d,]*\.?\d*\s?(?:%|percent)\b",                                                 # 30%
    r"\b\d+(?:\.\d+)?\s?x\b",                                                              # 5x, 10x
    r"\b\d[\d,]{2,}\+?\s?(?:users|customers|employees|people|companies|deals|subscribers|followers|stores|clients|countries|downloads|views|episodes|patients)\b",
    r"\b(?:19|20)\d{2}\b",                                                                 # years
    r"\b(?:ten|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion)\s+(?:thousand|million|billion|dollars|grand)\b",
]
FIGURE_RE = re.compile("|".join(f"(?:{p})" for p in FIGURE_PATTERNS), re.IGNORECASE)

# Bare 4-digit years are common and low-risk; only flag a year claim if it sits next
# to a life-event verb (founded/sold/raised/launched/exited) — those are the dates
# that matter and that the corpus can contradict.
YEAR_ONLY_RE = re.compile(r"^\D*\b(?:19|20)\d{2}\b\D*$")
EVENT_NEAR_YEAR = re.compile(r"\b(found|launch|start|sold|sell|rais|exit|acqui|ipo|merg|join|left|quit|born|graduat)", re.IGNORECASE)

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9$])")


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return []
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


def collect_claims(brain: dict) -> list[dict]:
    """Collect figure-bearing sentences from the brain's assertions."""
    syn = brain.get("synthesis", {}) or {}
    claims = []

    def add_from(text: str, where: str):
        for sent in split_sentences(text):
            figs = FIGURE_RE.findall(sent)
            figs = [f for f in (m if isinstance(m, str) else "".join(m) for m in figs) if f.strip()]
            if not figs:
                continue
            # Drop incidental bare-year sentences with no life-event verb.
            if YEAR_ONLY_RE.match(sent) and not EVENT_NEAR_YEAR.search(sent):
                continue
            claims.append({"where": where, "text": sent, "figures": sorted(set(figs))})

    if syn.get("hero_tagline"):
        add_from(syn["hero_tagline"], "hero_tagline")
    for section in ASSERTION_SECTIONS:
        for i, it in enumerate(syn.get(section) or []):
            for field in ("title", "name", "desc", "description", "role", "lesson"):
                if it.get(field):
                    add_from(it[field], f"{section}[{i}].{field}")
    for i, hl in enumerate(syn.get("hard_lessons") or []):
        for field in ("title", "cost", "change"):
            if hl.get(field):
                add_from(hl[field], f"hard_lessons[{i}].{field}")
    return claims


VERIFY_SYS = """You are a numeric fact-checker for a knowledge "brain pack" about a real person.

You are given (a) a CORPUS of the person's own words (verbatim interview/essay quotes) and (b) NUMERIC CLAIMS the brain asserts about them — each containing a hard figure (money, user/customer counts, multiples, percentages, an exit/raise size, or a life-event year).

For EACH claim, decide its status against the CORPUS:
- "grounded": the corpus supports this figure (same metric, same or equivalent value).
- "superseded": the corpus contains a LARGER or MORE RECENT value for the SAME metric/entity. THIS IS THE IMPORTANT ONE — e.g. claim says "$10M revenue" but the corpus says "$30M". Return the corpus value and a verbatim quote.
- "ungrounded": no figure for this metric appears anywhere in the corpus (possible fabrication).
- "unverifiable": the corpus is silent and the figure is plausible/common-knowledge (e.g. a founding year); not a defect, just unconfirmed.

Match on METRIC, not just number: "$30M revenue" and "$30M ad spend" are different metrics — don't cross them. A bigger number for a DIFFERENT metric is NOT superseded.

severity: "high" = a materially wrong figure (superseded by a much larger/newer value, or an ungrounded hard money/exit/user figure presented as fact). "medium" = ungrounded but minor, or a date that conflicts. "low" = rounding, approximation, or unverifiable-but-plausible.

Quote evidence VERBATIM from the corpus. If you can't quote it, you can't call it grounded or superseded.

Return ONLY JSON, no markdown:
{"results": [{"claim_id": <int>, "status": "grounded|superseded|ungrounded|unverifiable", "corpus_value": "<the corpus figure, or empty>", "evidence_quote": "<verbatim corpus quote, or empty>", "severity": "high|medium|low", "why": "<one sentence>"}]}"""


def main():
    ap = argparse.ArgumentParser(description="Verify a brain's hard numbers against its corpus")
    ap.add_argument("--brain", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true", help="List figure claims, no API call")
    ap.add_argument("--date", default=None, help="Override output date stamp (YYYY-MM-DD); avoids Date.now in callers")
    args = ap.parse_args()

    slug = args.brain
    bdir = BRAINS_DIR / slug
    bj = bdir / "brain.json"
    if not bj.exists():
        error(f"{slug}: brain.json not found"); sys.exit(1)
    brain = json.loads(bj.read_text())
    person = brain.get("brain_name", slug)

    claims = collect_claims(brain)
    if not claims:
        success(f"{slug}: no hard-figure claims in synthesis/hard_lessons — nothing to verify")
        _write_report(bdir, slug, person, [], [], args.date)
        return

    step(f"{slug}: {len(claims)} figure-bearing claims · person={person}")
    if args.dry_run:
        for i, c in enumerate(claims):
            print(f"  [{i}] ({c['where']}) figs={c['figures']}")
            print(f"       {c['text'][:130]}")
        return

    corpus = fc.load_source_corpus(slug)
    corpus_text = fc.build_corpus_for_prompt(corpus)
    if len(corpus_text) < 200:
        warn(f"{slug}: corpus is nearly empty — every figure will be unverifiable, not a defect")

    claim_block = "\n".join(f"{i}: {c['text']}" for i, c in enumerate(claims))
    user = (f"## Person: {person}\n\n## CORPUS (their own words)\n\n{corpus_text}\n\n"
            f"## NUMERIC CLAIMS TO VERIFY\n\n{claim_block}\n\n"
            f"Verify each claim by its id against the corpus.")

    client = Anthropic()
    tracker = CostTracker()
    res = call_claude(client, args.model,
                      messages=[{"role": "user", "content": user}],
                      system=VERIFY_SYS, max_tokens=4000, parse_json=True,
                      cost_tracker=tracker, label=f"verify-claims:{slug}")
    results = (res.get("parsed", {}) or {}).get("results", [])
    by_id = {r.get("claim_id"): r for r in results if isinstance(r, dict)}

    # --- Assemble defects ---
    defects = []
    counts = {"grounded": 0, "superseded": 0, "ungrounded": 0, "unverifiable": 0}
    for i, c in enumerate(claims):
        r = by_id.get(i, {"status": "unverifiable", "severity": "low", "why": "no verdict returned"})
        status = r.get("status", "unverifiable")
        counts[status] = counts.get(status, 0) + 1
        if status in ("superseded", "ungrounded"):
            defects.append({
                "where": c["where"], "claim": c["text"], "figures": c["figures"],
                "status": status, "severity": r.get("severity", "medium"),
                "corpus_value": r.get("corpus_value", ""), "evidence_quote": r.get("evidence_quote", ""),
                "why": r.get("why", ""),
            })

    high = [d for d in defects if d["severity"] == "high"]
    defects.sort(key=lambda d: {"high": 0, "medium": 1, "low": 2}.get(d["severity"], 3))

    print()
    success(f"{slug} numeric verify: {len(claims)} claims · "
            f"grounded={counts['grounded']} superseded={counts['superseded']} "
            f"ungrounded={counts['ungrounded']} unverifiable={counts['unverifiable']} · "
            f"{len(high)} high-severity · cost ${tracker.total_cost:.2f}")
    for d in defects[:12]:
        tag = "‼" if d["severity"] == "high" else ("!" if d["severity"] == "medium" else "·")
        print(f"  {tag} [{d['severity']}/{d['status']}] ({d['where']}) {d['claim'][:90]}")
        if d["corpus_value"]:
            print(f"      corpus says: {d['corpus_value']}  ← {d['evidence_quote'][:80]}")
        elif d["why"]:
            print(f"      {d['why'][:110]}")

    _write_report(bdir, slug, person, claims, defects, args.date, counts, tracker.total_cost)
    sys.exit(1 if high else 0)


def _write_report(bdir: Path, slug: str, person: str, claims: list, defects: list,
                  date_override: str | None, counts: dict = None, cost: float = 0.0):
    date = date_override or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    evals = bdir / "evals"
    evals.mkdir(exist_ok=True)
    high = sum(1 for d in defects if d.get("severity") == "high")
    # Fidelity penalty: persona-QA subtracts this from the fidelity dimension.
    # High defects are disqualifying for the ship-gate (zero unverified hard numbers).
    penalty = min(100, high * 25 + sum(1 for d in defects if d.get("severity") == "medium") * 8)
    report = {
        "slug": slug, "person": person, "date": date,
        "total_claims": len(claims), "counts": counts or {},
        "defect_count": len(defects), "high_severity_count": high,
        "fidelity_penalty": penalty, "cost": round(cost, 4),
        "defects": defects,
    }
    out = evals / f"numeric-claims-{date}.json"
    out.write_text(json.dumps(report, indent=2))
    success(f"wrote {out.relative_to(ROOT)} (penalty {penalty}, {high} high-severity)")


if __name__ == "__main__":
    main()
