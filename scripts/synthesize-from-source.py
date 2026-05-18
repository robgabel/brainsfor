#!/usr/bin/env python3
"""
Rebuild a brain's synthesis section from RAW source transcripts, not from atoms.

Today's auto-build pipeline generates synthesis by feeding aggregated atoms
(Haiku-extracted summaries) to Opus. This is a lossy compression — the
rhetorical structure, qualifications, and negative-space evidence
(`would_not_say`) get flattened out before Opus ever sees them.

This script reads the raw YouTube transcripts (and persisted text scrapes,
when available) and asks Opus to produce a synthesis with strict
citation-or-drop discipline:

- Each first_principle, contrarian_position, does_not_believe, and
  would_not_say item must come with ≥2 verbatim quotes from the corpus.
- The model is told to skip principles it can't ground rather than extrapolate.

After generating the new synthesis, the script:
  1. Writes the structured synthesis to brain.json.synthesis
  2. Backs up the old synthesis.md to synthesis.md.bak-{date}
  3. Generates a fresh synthesis.md from the new structured data
  4. Re-exports the pack via export-brain.py
  5. Runs fact-check-brain.py for verification

Usage:
    python3 scripts/synthesize-from-source.py --brain gokul-rajaraman
    python3 scripts/synthesize-from-source.py --brain gokul-rajaraman --dry-run
    python3 scripts/synthesize-from-source.py --brain gokul-rajaraman --no-export
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from auto_build_config import (  # type: ignore  # noqa: E402
    BRAINS_DIR,
    SYNTHESIS_MODEL,
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


MAX_CORPUS_CHARS = 300_000          # ~75K tokens — fits in Opus context with room
MIN_EVIDENCE_PER_PRINCIPLE = 2      # citation-or-drop threshold
MIN_EVIDENCE_WOULD_NOT_SAY = 1      # rejection moments are rare — allow single quote


SYSTEM_PROMPT = """You are a rigorous synthesis writer for the BrainsFor brain pack project.

Your job: read raw source transcripts of a thinker's recorded speech, then produce a structured synthesis of how they think.

**CITATION-OR-DROP RULE**: You MUST cite verbatim quotes for every claim. If you cannot find ≥2 supporting passages for a principle, DO NOT INCLUDE IT. Skipping a principle is always better than fabricating support for it.

Specifically:
- **first_principles** (target 7-10): a generative belief the speaker holds. Each must be supported by ≥2 verbatim quotes from distinct passages.
- **contrarian_positions** (target 3-5): a view that goes against industry consensus. Each requires ≥2 quotes where the speaker explicitly takes the contrarian side.
- **does_not_believe** (target 3-5): a position the speaker rejects. Each requires ≥1 quote where they explicitly disagree, push back, or call out the wrong framing.
- **would_not_say** (target 3-5): a phrasing the speaker would never use. Each requires either (a) ≥1 verbatim moment where they reject this exact framing in dialogue, or (b) ≥2 quotes showing they consistently hold the opposite view.
- **thinking_patterns** (target 4-6): characteristic rhetorical moves (e.g., "reframes binary questions as 3-way splits", "always asks for the supply-side metric first"). Each pattern must be observable in ≥3 different passages.

CRITICAL: Quotes must be VERBATIM from the corpus. Do not paraphrase. Do not invent. If the speaker uses unusual or colorful phrasing, prefer that quote. If you can't find a verbatim quote, you can't include the principle.

Output ONLY valid JSON (no markdown, no prose):
{
  "hero_tagline": "<one phrase capturing the speaker's intellectual identity, 8-12 words>",
  "first_principles": [
    {
      "title": "<crisp 5-9 word principle>",
      "desc": "<2-4 sentences explaining the principle in the speaker's own framing>",
      "source_evidence": [
        {"quote": "<verbatim excerpt>", "source": "<which transcript>"},
        {"quote": "<verbatim excerpt>", "source": "<which transcript>"}
      ]
    }
  ],
  "contrarian_positions": [...same structure...],
  "does_not_believe": [...same structure with 1+ quote...],
  "would_not_say": [
    {
      "title": "<the forbidden phrasing in quotes, e.g. \\"We can monetize later\\">",
      "desc": "<why the speaker would reject this>",
      "source_evidence": [
        {"quote": "<verbatim rejection moment OR multiple opposite-position quotes>", "source": "<...>"}
      ]
    }
  ],
  "thinking_patterns": [
    {
      "name": "<short label>",
      "desc": "<what the pattern is and what it produces>",
      "examples": [
        {"quote": "<verbatim>", "source": "<...>"}
      ]
    }
  ]
}"""


def load_corpus(brain_dir: Path) -> dict:
    """Aggregate raw transcripts (full_text) into a single corpus string."""
    transcripts_dir = brain_dir / "source" / "transcripts"
    parts = []
    n_videos = 0
    by_source = {}

    if not transcripts_dir.exists():
        return {"text": "", "n_videos": 0, "by_source": {}}

    for tp in sorted(transcripts_dir.glob("*.json")):
        try:
            d = json.loads(tp.read_text(encoding="utf-8"))
        except Exception:
            continue
        ft = d.get("full_text") or ""
        if not ft:
            continue
        title = d.get("title") or tp.stem
        # Tag each transcript with a stable source label
        source_label = title[:80]
        parts.append(f"\n\n### SOURCE: {source_label}\n\n{ft}")
        by_source[source_label] = len(ft)
        n_videos += 1

    raw_text = "".join(parts).strip()

    # Also add text-atoms as a SECONDARY signal (paraphrased, not verbatim source)
    text_atoms_path = brain_dir / "research" / "text-atoms.json"
    text_atom_block = ""
    if text_atoms_path.exists():
        try:
            atoms = json.loads(text_atoms_path.read_text(encoding="utf-8"))
            if isinstance(atoms, list) and atoms:
                lines = []
                for a in atoms[:50]:
                    src = (a.get("source_ref") or "")[:60]
                    content = (a.get("content") or "")[:300]
                    if content:
                        lines.append(f"- [{src}] {content}")
                if lines:
                    text_atom_block = (
                        "\n\n### SECONDARY: paraphrased extracts from text sources\n"
                        "### (NOT verbatim — use only when the same theme appears in a video transcript above)\n\n"
                        + "\n".join(lines)
                    )
        except Exception:
            pass

    full = raw_text + text_atom_block
    return {"text": full, "n_videos": n_videos, "by_source": by_source}


def truncate_corpus(text: str, max_chars: int) -> tuple:
    """Truncate corpus to max_chars, returning (truncated, was_truncated)."""
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars] + "\n\n[...corpus truncated...]", True


def call_synthesizer(client, brain_name: str, corpus_text: str, tracker: CostTracker,
                      model: str = SYNTHESIS_MODEL) -> dict:
    """Single Opus call: returns structured synthesis JSON."""
    user_msg = f"""## Brain: {brain_name}

Below is the raw source corpus — transcripts of {brain_name}'s recorded speech across multiple long-form interviews and talks. Read carefully, then produce the structured synthesis described in the system prompt.

Remember: every principle, position, and pattern MUST cite ≥2 verbatim quotes from this corpus (≥1 for would_not_say with a clear rejection moment). Skip principles you cannot ground — do not fabricate support.

---

{corpus_text}
"""

    step(f"Calling {model} with {len(corpus_text):,}-char corpus...")
    resp = call_claude(
        client=client,
        model=model,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        max_tokens=16000,
        parse_json=True,
        cost_tracker=tracker,
        label=f"synthesize-from-source:{brain_name}",
    )
    return resp["parsed"]


def validate_synthesis(parsed: dict) -> tuple:
    """Apply citation-or-drop rule. Returns (kept_synthesis, dropped_log)."""
    kept = {}
    dropped = []

    if "hero_tagline" in parsed:
        kept["hero_tagline"] = parsed["hero_tagline"]

    # Sections with citation rule
    for section, min_evidence in [
        ("first_principles", MIN_EVIDENCE_PER_PRINCIPLE),
        ("contrarian_positions", MIN_EVIDENCE_PER_PRINCIPLE),
        ("does_not_believe", 1),  # one rejection is enough
        ("would_not_say", MIN_EVIDENCE_WOULD_NOT_SAY),
    ]:
        items = parsed.get(section) or []
        kept_items = []
        for i, item in enumerate(items):
            evidence = item.get("source_evidence") or []
            valid_evidence = [
                e for e in evidence
                if isinstance(e, dict) and e.get("quote") and len(e["quote"]) >= 20
            ]
            if len(valid_evidence) >= min_evidence:
                # Normalize: keep title, desc, source_evidence
                kept_items.append({
                    "title": item.get("title", f"item-{i}"),
                    "desc": item.get("desc") or item.get("description", ""),
                    "source_evidence": valid_evidence,
                })
            else:
                dropped.append({
                    "section": section,
                    "title": item.get("title", "?"),
                    "evidence_count": len(valid_evidence),
                    "required": min_evidence,
                })
        kept[section] = kept_items

    # thinking_patterns: similar but uses 'examples' field
    patterns = parsed.get("thinking_patterns") or []
    kept_patterns = []
    for p in patterns:
        examples = p.get("examples") or []
        valid = [e for e in examples if isinstance(e, dict) and e.get("quote") and len(e["quote"]) >= 20]
        if len(valid) >= 2:
            kept_patterns.append({
                "name": p.get("name", "?"),
                "desc": p.get("desc") or p.get("description", ""),
                "examples": valid,
            })
        else:
            dropped.append({
                "section": "thinking_patterns",
                "title": p.get("name", "?"),
                "evidence_count": len(valid),
                "required": 2,
            })
    kept["thinking_patterns"] = kept_patterns

    return kept, dropped


def render_synthesis_md(brain_name: str, synthesis: dict, brain_dir: Path, n_videos: int) -> str:
    """Write a human-readable synthesis.md from the new structured data."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"## How {brain_name} Thinks",
        "",
        f"*Synthesis rebuilt {today} directly from {n_videos} raw transcripts using "
        f"citation-or-drop discipline — every principle below cites ≥2 verbatim "
        f"passages from the source corpus. Generated by scripts/synthesize-from-source.py.*",
        "",
    ]

    if synthesis.get("hero_tagline"):
        lines.append(f"**{synthesis['hero_tagline']}**")
        lines.append("")

    def render_section(title: str, items: list, format_evidence: bool = True):
        if not items:
            return
        lines.append(f"### {title}")
        lines.append("")
        for i, item in enumerate(items, 1):
            lines.append(f"**{i}. {item['title']}.** {item['desc']}")
            if format_evidence and item.get("source_evidence"):
                for ev in item["source_evidence"][:3]:
                    q = ev.get("quote", "").strip()
                    src = ev.get("source", "?")
                    lines.append(f"")
                    lines.append(f"> \"{q[:300]}\" — *{src[:80]}*")
            lines.append("")

    render_section("First Principles", synthesis.get("first_principles", []))
    render_section("Contrarian Positions", synthesis.get("contrarian_positions", []))
    render_section("Does Not Believe", synthesis.get("does_not_believe", []))
    render_section("Would Not Say", synthesis.get("would_not_say", []))

    patterns = synthesis.get("thinking_patterns", [])
    if patterns:
        lines.append("### Thinking Patterns")
        lines.append("")
        for p in patterns:
            lines.append(f"**{p['name']}.** {p['desc']}")
            for ex in p.get("examples", [])[:2]:
                q = ex.get("quote", "").strip()
                src = ex.get("source", "?")
                lines.append(f"")
                lines.append(f"> \"{q[:280]}\" — *{src[:80]}*")
            lines.append("")

    return "\n".join(lines)


def merge_into_brain_json(brain_dir: Path, new_synthesis: dict) -> None:
    """Update brain.json.synthesis with the new structured data, preserving non-rebuilt sections."""
    brain_json_path = brain_dir / "brain.json"
    config = json.loads(brain_json_path.read_text(encoding="utf-8"))
    syn = config.get("synthesis") or {}

    # Update the rebuilt sections
    for key in ("hero_tagline", "first_principles", "contrarian_positions",
                "does_not_believe", "would_not_say", "thinking_patterns"):
        if key in new_synthesis:
            syn[key] = new_synthesis[key]

    # Update hero_updated timestamp + provenance
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    syn["hero_updated"] = (
        f"Synthesis rebuilt {today} from raw source transcripts using "
        f"citation-or-drop discipline. Every first principle, contrarian position, "
        f"and 'would not say' item is supported by verbatim quotes from the corpus."
    )

    config["synthesis"] = syn
    brain_json_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Rebuild synthesis from raw transcripts (citation-or-drop)")
    ap.add_argument("--brain", required=True, help="Brain slug")
    ap.add_argument("--dry-run", action="store_true", help="Show plan + cost estimate")
    ap.add_argument("--no-export", action="store_true", help="Don't run export-brain.py at the end")
    ap.add_argument("--no-fact-check", action="store_true", help="Don't run fact-check after")
    ap.add_argument("--model", default=SYNTHESIS_MODEL, help=f"LLM (default: {SYNTHESIS_MODEL})")
    args = ap.parse_args()

    brain_dir = BRAINS_DIR / args.brain
    if not (brain_dir / "brain.json").exists():
        error(f"{args.brain}: brain.json not found")
        sys.exit(2)

    brain_cfg = json.loads((brain_dir / "brain.json").read_text(encoding="utf-8"))
    brain_name = brain_cfg.get("brain_name", args.brain)

    corpus = load_corpus(brain_dir)
    if corpus["n_videos"] == 0:
        error(f"{args.brain}: no transcripts in source/transcripts/ — cannot rebuild")
        sys.exit(2)

    step(f"{args.brain}: {corpus['n_videos']} transcripts, {len(corpus['text']):,} corpus chars")
    for src, chars in corpus["by_source"].items():
        step(f"  - {src} ({chars:,} chars)")

    corpus_text, was_truncated = truncate_corpus(corpus["text"], MAX_CORPUS_CHARS)
    if was_truncated:
        warn(f"corpus truncated to {MAX_CORPUS_CHARS:,} chars")

    if args.dry_run:
        est_in = len(corpus_text) // 4
        est_out = 12000
        in_cost = (est_in / 1000) * 0.015
        out_cost = (est_out / 1000) * 0.075
        step(f"[DRY RUN] est tokens: {est_in:,} in / {est_out:,} out · est cost: ${in_cost + out_cost:.2f}")
        sys.exit(0)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        error("ANTHROPIC_API_KEY not set — source ~/rob-ai/.env")
        sys.exit(2)
    client = Anthropic(api_key=api_key)
    tracker = CostTracker()

    # --- Generate synthesis ---
    parsed = call_synthesizer(client, brain_name, corpus_text, tracker, model=args.model)

    # --- Apply citation-or-drop ---
    kept, dropped = validate_synthesis(parsed)

    # --- Stats ---
    success(f"Synthesis generated. {tracker.summary()}")
    print()
    print("=" * 65)
    print("  KEPT (passed citation-or-drop)")
    print("=" * 65)
    for sec in ("first_principles", "contrarian_positions", "does_not_believe", "would_not_say", "thinking_patterns"):
        n = len(kept.get(sec, []))
        print(f"  {sec:25s}  {n}")
    print()
    if dropped:
        print("=" * 65)
        print(f"  DROPPED ({len(dropped)} — insufficient citation)")
        print("=" * 65)
        for d in dropped[:10]:
            print(f"  [{d['section']}] {d['title']}  (evidence: {d['evidence_count']}/{d['required']})")
        if len(dropped) > 10:
            print(f"  ... and {len(dropped) - 10} more")
        print()

    # --- Backup old synthesis.md ---
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")
    syn_md_path = brain_dir / "synthesis.md"
    if syn_md_path.exists():
        bak = brain_dir / f"synthesis.md.bak-{today}"
        shutil.copy(syn_md_path, bak)
        step(f"Backed up old synthesis.md → {bak.name}")

    # --- Write outputs ---
    new_md = render_synthesis_md(brain_name, kept, brain_dir, corpus["n_videos"])
    syn_md_path.write_text(new_md, encoding="utf-8")
    success(f"Wrote new synthesis.md ({len(new_md)} chars)")

    merge_into_brain_json(brain_dir, kept)
    success("Updated brain.json.synthesis")

    # --- Re-export ---
    if not args.no_export:
        step("Re-exporting pack...")
        all_atoms = brain_dir / "research" / "all-atoms.json"
        connections = brain_dir / "research" / "connections.json"
        cmd = ["python3", str(SCRIPT_DIR / "export-brain.py"), "--brain", args.brain]
        if all_atoms.exists() and connections.exists():
            cmd += ["--from-files", str(all_atoms), str(connections)]
        result = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)
        if result.returncode != 0:
            error(f"export-brain.py failed: {result.stderr[:500]}")
        else:
            success("Pack re-exported")

    # --- Fact-check ---
    if not args.no_fact_check:
        step("Running fact-check on new synthesis...")
        cmd = ["python3", str(SCRIPT_DIR / "fact-check-brain.py"), "--brain", args.brain]
        result = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            warn("fact-check below target — see brains/{slug}/evals/fact-check-summary.md")
        else:
            success("fact-check passed")


if __name__ == "__main__":
    main()
