#!/usr/bin/env python3
"""Provenance gate for voice enrichment — apply only corpus-verified quotes.

enrich-voice.py proposes original_quote values extracted by an LLM from fetched
source text. Even with the verbatim-only prompt, an LLM can paraphrase or stitch;
a quote that isn't verbatim in the local source corpus is a fabrication risk and
must not reach a pack (see CLAUDE.md: quote provenance / jesse-pujji lesson).

This script re-checks every proposed quote against the SAME corpus matcher the
structural audit uses (audit-brains.py: load_source_corpus + quote_signature),
then writes a filtered review file where unverified proposals are demoted to
status="rejected_provenance" (apply_enrichments skips non-"ok" entries).

Usage:
  python3 scripts/verify-enrichment.py --brain jesse-pujji
      # reads  brains/jesse-pujji/data/voice-enrichment-review.json
      # writes brains/jesse-pujji/data/voice-enrichment-verified.json
  python3 scripts/enrich-voice.py --brain jesse-pujji \
      --apply brains/jesse-pujji/data/voice-enrichment-verified.json

NOTE: fetch the brain's transcripts locally first (ingest-youtube.py
--from-sources) or real quotes will be rejected as unverifiable — the exact
false-alarm this gate exists to avoid firing in reverse.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
BRAINS_DIR = ROOT / "brains"

_spec = importlib.util.spec_from_file_location("audit", SCRIPT_DIR / "audit-brains.py")
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)


def main():
    ap = argparse.ArgumentParser(description="Filter voice-enrichment proposals to corpus-verified quotes")
    ap.add_argument("--brain", required=True)
    ap.add_argument("--review", default=None, help="Review JSON path (default: brains/<slug>/data/voice-enrichment-review.json)")
    args = ap.parse_args()

    bdir = BRAINS_DIR / args.brain
    review_path = Path(args.review) if args.review else bdir / "data" / "voice-enrichment-review.json"
    if not review_path.exists():
        print(f"ERROR: {review_path} not found — run enrich-voice.py first"); sys.exit(1)

    corpus = audit.load_source_corpus(bdir)
    print(f"corpus: {corpus['video_count']} transcripts ({len(corpus['youtube_text'])}ch), "
          f"{corpus['text_source_count']} raw md ({len(corpus['blog_podcast_text'])}ch)")
    if corpus["video_count"] == 0 and len(corpus["blog_podcast_text"]) < 5000:
        print("WARN: corpus is nearly empty — most proposals will be rejected. "
              "Fetch transcripts first: python3 scripts/ingest-youtube.py --brain "
              f"{args.brain} --from-sources")

    items = json.loads(review_path.read_text())
    verified = rejected = passthrough = 0
    for item in items:
        if item.get("status") != "ok" or not item.get("original_quote"):
            passthrough += 1
            continue
        sig = audit.quote_signature(item["original_quote"])
        if sig and sig in corpus["any_text"]:
            verified += 1
        else:
            item["status"] = "rejected_provenance"
            rejected += 1

    out = review_path.parent / "voice-enrichment-verified.json"
    out.write_text(json.dumps(items, indent=2))
    total_ok = verified + rejected
    pct = (100 * verified / total_ok) if total_ok else 0.0
    print(f"{args.brain}: {total_ok} proposed quotes → {verified} verified ({pct:.0f}%), "
          f"{rejected} rejected (not verbatim in corpus), {passthrough} skipped/failed")
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"apply: python3 scripts/enrich-voice.py --brain {args.brain} --apply {out}")


if __name__ == "__main__":
    main()
