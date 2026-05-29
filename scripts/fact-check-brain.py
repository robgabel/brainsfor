#!/usr/bin/env python3
"""
Independent fact-check pass for a BrainsFor brain pack.

For each principle in brain.json.synthesis (first_principles, contrarian_positions,
does_not_believe, would_not_say), ask Sonnet to find supporting verbatim quotes
in the source corpus (YouTube transcripts + extracted atom quotes).

Output:
  - brains/{slug}/evals/fact-check-{YYYY-MM-DD}.json — per-principle results
  - brains/{slug}/evals/fact-check-summary.md — human-readable scorecard
  - Stdout: per-section grounding %, top 3 ungrounded principles

This complements audit-brains.py's `check_synthesis_grounding` (a fast lexical
check). The fact-check pass is semantic — Sonnet can identify paraphrased
support that a string match misses, and conversely can flag principles whose
key phrases match but whose meaning isn't actually present in the corpus.

Usage:
    python3 scripts/fact-check-brain.py --brain gokul-rajaraman
    python3 scripts/fact-check-brain.py --brain gokul-rajaraman --dry-run
    python3 scripts/fact-check-brain.py --all  # cross-brain summary

Exit code: 0 if grounding >= GROUNDING_TARGET, 1 otherwise.
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Match auto_build_config's path discovery
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from auto_build_config import (  # type: ignore  # noqa: E402
    BRAINS_DIR,
    DEFAULT_MODEL,
    CostTracker,
    call_claude,
    step,
    success,
    warn,
    error,
)

try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: anthropic package required. pip install anthropic")
    sys.exit(1)


GROUNDING_TARGET = 0.70  # 70% of principles should be grounded
SECTIONS = ("first_principles", "contrarian_positions", "does_not_believe", "would_not_say")
MAX_CORPUS_CHARS = 200_000  # ~50K tokens — leaves room for system + response


# ---------------------------------------------------------------------------
# Source corpus loading
# ---------------------------------------------------------------------------

def load_source_corpus(slug: str) -> dict:
    """Aggregate YouTube transcripts + atom-pool quotes for a brain.

    Returns dict with:
      youtube_text: raw transcripts concatenated
      atom_quotes: list of (quote, source_ref) from video/text atoms
      total_chars: corpus size
      n_videos: transcript count
    """
    brain_dir = BRAINS_DIR / slug
    transcripts_dir = brain_dir / "source" / "transcripts"

    yt_parts = []
    n_videos = 0
    if transcripts_dir.exists():
        for tp in sorted(transcripts_dir.glob("*.json")):
            try:
                d = json.loads(tp.read_text(encoding="utf-8"))
            except Exception:
                continue
            ft = d.get("full_text") or ""
            title = d.get("title") or tp.stem
            if ft:
                yt_parts.append(f"### {title}\n{ft}")
                n_videos += 1
    youtube_text = "\n\n---\n\n".join(yt_parts)

    # Pull verbatim source quotes from every research atom file. New brains use
    # video-atoms.json / text-atoms.json; older back-catalog brains (built before
    # the YouTube-first pipeline) store them in all-atoms.json or per-cluster files
    # (book-atoms.json, interview-atoms.json, batch1-atoms.json, ...). Glob covers
    # all of them so the back catalog gets a real corpus for grounding instead of
    # falling through to "no corpus". connections.json is not matched by *-atoms.json.
    # Verbatim only (original_quote) — never the distilled `content` field, which
    # would make grounding circular.
    atom_quotes = []
    seen_quotes = set()
    research_dir = brain_dir / "research"
    if research_dir.exists():
        for fp in sorted(research_dir.glob("*-atoms.json")):
            try:
                atoms = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(atoms, list):
                continue
            for a in atoms:
                q = a.get("original_quote") or ""
                src = a.get("source_ref") or "unknown"
                if q and len(q) > 20:
                    key = q.strip().lower()
                    if key in seen_quotes:
                        continue
                    seen_quotes.add(key)
                    atom_quotes.append((q, src))

    return {
        "youtube_text": youtube_text,
        "atom_quotes": atom_quotes,
        "total_chars": len(youtube_text) + sum(len(q) for q, _ in atom_quotes),
        "n_videos": n_videos,
    }


def build_corpus_for_prompt(corpus: dict, max_chars: int = MAX_CORPUS_CHARS) -> str:
    """Produce a single corpus string for the fact-check prompt.

    YouTube text first (highest signal), then atom quotes if room remains.
    Truncates if necessary, marking the truncation point.
    """
    yt = corpus["youtube_text"]
    if len(yt) > max_chars:
        return yt[:max_chars] + "\n\n[...truncated...]"

    remaining = max_chars - len(yt)
    quote_lines = []
    for q, src in corpus["atom_quotes"]:
        line = f"- [{src[:60]}] {q}"
        if len(line) > remaining:
            break
        quote_lines.append(line)
        remaining -= len(line) + 1

    if not quote_lines:
        return yt

    return yt + "\n\n## ATOM QUOTES (paraphrased from text sources)\n\n" + "\n".join(quote_lines)


# ---------------------------------------------------------------------------
# Principle extraction
# ---------------------------------------------------------------------------

def collect_principles(brain_cfg: dict) -> list:
    """Pull principles from synthesis into a flat list of probe records."""
    syn = brain_cfg.get("synthesis", {}) or {}
    out = []
    for section in SECTIONS:
        items = syn.get(section) or []
        for i, item in enumerate(items):
            title = item.get("title") or item.get("name") or f"item-{i}"
            desc = item.get("desc") or item.get("description") or ""
            out.append({
                "section": section,
                "index": i,
                "title": title,
                "desc": desc,
                "claim": f"{title}. {desc}".strip(),
            })
    return out


# ---------------------------------------------------------------------------
# Fact-check LLM call
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a rigorous fact-checker for a BrainsFor brain pack.

Your job: for each PRINCIPLE attributed to a thinker, determine whether the SOURCE CORPUS (transcripts of the thinker's own speech + paraphrased atom quotes) actually supports the principle.

For each principle, output one of three statuses:
- "grounded": You found ≥2 distinct passages in the corpus that clearly support the principle (paraphrase or verbatim).
- "weak": You found exactly 1 supporting passage, OR multiple passages that only tangentially relate.
- "ungrounded": You found no supporting passages. The principle appears to be an extrapolation or hallucination — the thinker does not say this in the source material.

Quote excerpts verbatim from the corpus. If you cannot quote it, it is not grounded.

Return ONLY valid JSON in this shape (no markdown, no prose):
{
  "results": [
    {
      "principle_id": "<as given>",
      "status": "grounded" | "weak" | "ungrounded",
      "evidence": [
        {"quote": "<verbatim excerpt>", "relation": "<paraphrase|verbatim|partial>"},
        ...
      ],
      "rationale": "<one sentence explaining the status decision>"
    },
    ...
  ]
}"""


def call_fact_checker(client, brain_name: str, principles: list, corpus_text: str,
                      tracker: CostTracker, model: str = DEFAULT_MODEL) -> dict:
    """Single Sonnet call: returns dict with per-principle grounding results."""

    # Build the principle list as a numbered enumeration
    principle_block = []
    for p in principles:
        pid = f"{p['section']}[{p['index']}]"
        principle_block.append(f"{pid}: {p['claim'][:500]}")
    principles_text = "\n\n".join(principle_block)

    user = f"""## Brain: {brain_name}

## SOURCE CORPUS

{corpus_text}

## PRINCIPLES TO FACT-CHECK

{principles_text}

For each principle above, search the SOURCE CORPUS and return your verdict.
Use the principle_id format I gave you (e.g., "first_principles[0]").
"""

    step(f"Fact-checking {len(principles)} principles against {len(corpus_text):,}-char corpus...")

    resp = call_claude(
        client=client,
        model=model,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
        max_tokens=8000,
        parse_json=True,
        cost_tracker=tracker,
        label=f"fact-check:{brain_name}",
    )
    return resp["parsed"]


# ---------------------------------------------------------------------------
# Scorecard
# ---------------------------------------------------------------------------

def score_results(principles: list, results_by_id: dict) -> dict:
    """Aggregate per-section scores from fact-check results."""
    by_section = {s: {"grounded": 0, "weak": 0, "ungrounded": 0, "total": 0} for s in SECTIONS}
    ungrounded_examples = []
    weak_examples = []

    for p in principles:
        pid = f"{p['section']}[{p['index']}]"
        result = results_by_id.get(pid)
        section_stats = by_section[p["section"]]
        section_stats["total"] += 1
        if not result:
            section_stats["ungrounded"] += 1
            continue
        status = result.get("status", "ungrounded")
        if status not in section_stats:
            status = "ungrounded"
        section_stats[status] += 1
        if status == "ungrounded" and len(ungrounded_examples) < 5:
            ungrounded_examples.append({
                "id": pid,
                "title": p["title"],
                "rationale": result.get("rationale", ""),
            })
        elif status == "weak" and len(weak_examples) < 5:
            weak_examples.append({
                "id": pid,
                "title": p["title"],
                "rationale": result.get("rationale", ""),
            })

    total_g = sum(s["grounded"] for s in by_section.values())
    total_w = sum(s["weak"] for s in by_section.values())
    total_u = sum(s["ungrounded"] for s in by_section.values())
    total = total_g + total_w + total_u

    grounding_pct = (total_g + 0.5 * total_w) / total if total else 0.0

    return {
        "by_section": by_section,
        "totals": {"grounded": total_g, "weak": total_w, "ungrounded": total_u, "total": total},
        "grounding_pct": round(grounding_pct * 100, 1),
        "ungrounded_examples": ungrounded_examples,
        "weak_examples": weak_examples,
    }


def write_outputs(slug: str, scorecard: dict, principles: list,
                   results_by_id: dict, corpus: dict, model: str) -> tuple:
    """Write JSON results + summary.md. Returns (json_path, summary_path)."""
    evals_dir = BRAINS_DIR / slug / "evals"
    evals_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_path = evals_dir / f"fact-check-{today}.json"
    summary_path = evals_dir / "fact-check-summary.md"

    # Full JSON
    full = {
        "brain_slug": slug,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "corpus": {
            "n_videos": corpus["n_videos"],
            "youtube_chars": len(corpus["youtube_text"]),
            "atom_quote_count": len(corpus["atom_quotes"]),
            "total_chars": corpus["total_chars"],
        },
        "scorecard": scorecard,
        "results": [
            {
                "principle_id": f"{p['section']}[{p['index']}]",
                "section": p["section"],
                "title": p["title"],
                "claim": p["claim"],
                **(results_by_id.get(f"{p['section']}[{p['index']}]") or {"status": "missing"}),
            }
            for p in principles
        ],
    }
    with open(json_path, "w") as f:
        json.dump(full, f, indent=2)

    # Summary markdown
    lines = [
        f"# Fact-Check — {slug}",
        f"",
        f"- Run: {datetime.now(timezone.utc).isoformat()}",
        f"- Model: {model}",
        f"- Corpus: {corpus['n_videos']} YouTube transcripts ({len(corpus['youtube_text']):,} chars) + {len(corpus['atom_quotes'])} atom quotes",
        f"- **Grounding score: {scorecard['grounding_pct']}%** (grounded = 1pt, weak = 0.5pt)",
        f"",
        f"## By section",
        f"",
        f"| Section | Grounded | Weak | Ungrounded | Total |",
        f"|---|---|---|---|---|",
    ]
    for sec, s in scorecard["by_section"].items():
        lines.append(f"| {sec} | {s['grounded']} | {s['weak']} | {s['ungrounded']} | {s['total']} |")

    if scorecard["ungrounded_examples"]:
        lines.append("")
        lines.append("## Worst-grounded principles (sample)")
        lines.append("")
        for ex in scorecard["ungrounded_examples"]:
            lines.append(f"### {ex['id']} — {ex['title']}")
            lines.append(f"")
            lines.append(f"_{ex['rationale']}_")
            lines.append("")

    summary_path.write_text("\n".join(lines), encoding="utf-8")

    return json_path, summary_path


# ---------------------------------------------------------------------------
# Per-brain orchestration
# ---------------------------------------------------------------------------

def fact_check_brain(slug: str, client, tracker: CostTracker, dry_run: bool = False,
                     model: str = DEFAULT_MODEL) -> dict:
    """Run fact-check on a single brain. Returns scorecard dict."""
    brain_dir = BRAINS_DIR / slug
    brain_json_path = brain_dir / "brain.json"
    if not brain_json_path.exists():
        error(f"{slug}: brain.json not found")
        return {}

    brain_cfg = json.loads(brain_json_path.read_text(encoding="utf-8"))
    brain_name = brain_cfg.get("brain_name", slug)

    principles = collect_principles(brain_cfg)
    if not principles:
        warn(f"{slug}: no principles in synthesis sections — nothing to fact-check")
        return {}

    corpus = load_source_corpus(slug)
    if corpus["n_videos"] == 0 and not corpus["atom_quotes"]:
        warn(f"{slug}: no source corpus (no transcripts, no atom quotes) — cannot fact-check")
        return {}

    step(f"{slug}: {len(principles)} principles · {corpus['n_videos']} transcripts · {corpus['total_chars']:,} corpus chars")

    if dry_run:
        # Estimate cost: ~1.2x corpus tokens at Sonnet input rate
        est_input_tokens = corpus["total_chars"] // 4 + sum(len(p["claim"]) // 4 for p in principles)
        est_input_cost = (est_input_tokens / 1000) * 0.003
        est_output_cost = (8000 / 1000) * 0.015
        est_total = est_input_cost + est_output_cost
        step(f"  [DRY RUN] est tokens: ~{est_input_tokens:,} in, ~8000 out · est cost: ${est_total:.2f}")
        return {}

    corpus_text = build_corpus_for_prompt(corpus)
    parsed = call_fact_checker(client, brain_name, principles, corpus_text, tracker, model)

    results_by_id = {}
    for r in parsed.get("results", []):
        pid = r.get("principle_id")
        if pid:
            results_by_id[pid] = r

    scorecard = score_results(principles, results_by_id)
    json_path, summary_path = write_outputs(slug, scorecard, principles, results_by_id, corpus, model)

    success(f"{slug}: grounding {scorecard['grounding_pct']}% — wrote {json_path.relative_to(ROOT_DIR)}")
    return scorecard


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Independent fact-check pass for BrainsFor brains")
    ap.add_argument("--brain", help="Brain slug (else --all)")
    ap.add_argument("--all", action="store_true", help="Fact-check every brain in index.json")
    ap.add_argument("--dry-run", action="store_true", help="Show cost estimate only")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"LLM (default: {DEFAULT_MODEL})")
    args = ap.parse_args()

    if not args.brain and not args.all:
        ap.error("Must specify --brain <slug> or --all")

    # Build target list
    if args.brain:
        slugs = [args.brain]
    else:
        index_path = BRAINS_DIR / "index.json"
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        slugs = [b["slug"] for b in idx.get("brains", []) if b.get("status") != "hidden"]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        error("ANTHROPIC_API_KEY not set — source ~/rob-ai/.env")
        sys.exit(2)
    client = Anthropic(api_key=api_key)
    tracker = CostTracker()

    scores = {}
    for slug in slugs:
        sc = fact_check_brain(slug, client, tracker, dry_run=args.dry_run, model=args.model)
        if sc:
            scores[slug] = sc

    print()
    print("=" * 65)
    print("  FACT-CHECK SCORECARD")
    print("=" * 65)
    print()
    print(f"  {'Brain':<25} {'Grounding':>10} {'Grounded':>9} {'Weak':>6} {'Ungrd':>6}")
    print(f"  {'-'*25} {'-'*10} {'-'*9} {'-'*6} {'-'*6}")
    for slug, sc in scores.items():
        t = sc["totals"]
        print(f"  {slug:<25} {sc['grounding_pct']:>9.1f}% {t['grounded']:>9} {t['weak']:>6} {t['ungrounded']:>6}")
    print()
    print(f"  {tracker.summary()}")
    print()

    if scores:
        avg = sum(s["grounding_pct"] for s in scores.values()) / len(scores)
        below = [s for s, sc in scores.items() if sc["grounding_pct"] < GROUNDING_TARGET * 100]
        print(f"  Average grounding: {avg:.1f}%   |   Target: {GROUNDING_TARGET * 100:.0f}%")
        if below:
            print(f"  Below target: {', '.join(below)}")
            sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
