#!/usr/bin/env python3
"""
extract-atoms-local.py — extract NEW atoms from diarized transcripts into the LOCAL pack.

Companion to enrich-voice-local.py (which attaches quotes to EXISTING atoms). This
one ADDS atoms — used to raise a brain's COVERAGE from a source the pack doesn't yet
represent. Built for Elon Part-1 A: the "mess corpus" (crisis/failure/conflict in his
own words) the persona panel flagged as missing ("the id is laundered out").

Reads diarized, subject-only transcripts (ingest-transcript-pages.py output), extracts
atoms via Sonnet under an ANTI-VINDICATION rubric (capture the mess honestly — the
combativeness, the volatility, the defensiveness — not the flattering gloss), and
appends them to pack/brain-atoms.json with a verbatim original_quote (exact substring
of the subject's own speech), cluster, topics, and epistemic defaults.

Safety: original_quote must be an exact substring of the diarized (subject-only) text,
so quotes are speaker-safe by construction. Atoms whose quote can't be verified are
dropped. Does NOT touch Supabase; re-export with export-brain.py --from-files after.

USAGE
    export ANTHROPIC_API_KEY=...
    python3 scripts/extract-atoms-local.py --brain elon-musk --transcripts dealbook-2023 --dry-run
    python3 scripts/extract-atoms-local.py --brain elon-musk --transcripts dealbook-2023 --apply
"""
import argparse
import json
import os
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import auto_build_config as cfg  # noqa: E402
try:
    import anthropic
except ImportError:
    sys.exit("ERROR: pip install anthropic")

CHUNK = 9000  # chars of transcript per extraction call

SYS = """You extract knowledge atoms from a verbatim transcript of {name} speaking.

This is a MESS-CORPUS pass. The goal is to capture {name} as they ACTUALLY are in this
moment — including the parts a flattering profile leaves out: combativeness, emotional
volatility, defensiveness, contradiction, the unguarded id. Do NOT sanitize, redeem, or
add a vindicating gloss. If {name} says something petty, reckless, or self-contradicting,
capture THAT — faithfully, in their own frame.

For each substantive idea {name} expresses, emit one atom:
- content: the distilled insight or stance, stated plainly and honestly (include the mess;
  do not launder it into something wiser than what was said).
- original_quote: {name}'s EXACT words — copied character-for-character from the passage,
  a self-contained span (~1-3 sentences). This must be a verbatim substring of the text.
- implication: the "so what" for someone modeling {name}'s thinking (may be uncomfortable).
- cluster: ONE of: {clusters}.
- topics: 2-5 lowercase snake_case tags.
- claim_type: "opinion" (a stance), "fact" (a discrete checkable claim), or "prediction".

Skip filler, pleasantries, and interviewer setup. Aim for the 4-8 strongest atoms per
passage. Return ONLY JSON: {{"atoms": [ {{...}}, ... ]}}."""


def brain_dir(slug):
    d = ROOT / "brains" / slug
    if not d.exists():
        sys.exit(f"ERROR: no brain at {d}")
    return d


def brain_meta(slug):
    b = json.loads((brain_dir(slug) / "brain.json").read_text())
    name = b.get("name") or slug.replace("-", " ").title()
    clusters = b.get("clusters") or {}
    keys = list(clusters.keys()) if isinstance(clusters, dict) else [c if isinstance(c, str) else c.get("key") for c in clusters]
    return name, keys


def norm_ws(s):
    return re.sub(r"\s+", " ", s).strip()


def chunk_text(text):
    text = norm_ws(text)
    out, buf = [], ""
    for sent in re.split(r"(?<=[.!?])\s+", text):
        if len(buf) + len(sent) > CHUNK and buf:
            out.append(buf.strip()); buf = sent
        else:
            buf = (buf + " " + sent).strip()
    if buf:
        out.append(buf.strip())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--transcripts", nargs="+", required=True,
                    help="transcript video_id(s)/filename stem(s) under source/transcripts/")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-per-transcript", type=int, default=40)
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    slug = args.brain
    name, clusters = brain_meta(slug)
    tdir = brain_dir(slug) / "source" / "transcripts"
    pack_path = brain_dir(slug) / "pack" / "brain-atoms.json"
    pack = json.loads(pack_path.read_text())
    existing_quotes = {norm_ws(a.get("original_quote") or "") for a in pack["atoms"] if a.get("original_quote")}

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=90.0, max_retries=2)
    cost = cfg.CostTracker()
    system = SYS.format(name=name, clusters=", ".join(clusters))

    new_atoms = []
    for stem in args.transcripts:
        f = tdir / f"{stem}.json"
        if not f.exists():
            print(f"  SKIP {stem}: not found"); continue
        d = json.loads(f.read_text())
        if not d.get("diarized"):
            print(f"  SKIP {stem}: not diarized (unsafe)"); continue
        body = d["full_text"]
        src_ref, src_url, src_date = d.get("title", ""), d.get("source_url", ""), d.get("source_date", "")
        chunks = chunk_text(body)
        got = 0
        print(f"  {stem}: {len(body):,} chars -> {len(chunks)} chunks")
        for ci, ch in enumerate(chunks):
            if got >= args.max_per_transcript:
                break
            try:
                r = cfg.call_claude(client, cfg.DEFAULT_MODEL,
                                    [{"role": "user", "content": f"PASSAGE:\n{ch}"}],
                                    system=system, max_tokens=4000, parse_json=True,
                                    cost_tracker=cost, label=f"mess:{stem}")
            except Exception as e:
                print(f"    chunk {ci} failed: {e}"); continue
            parsed = r.get("parsed") or {}
            atoms = parsed.get("atoms", []) if isinstance(parsed, dict) else (parsed if isinstance(parsed, list) else [])
            for a in atoms:
                q = norm_ws(a.get("original_quote") or "")
                # verbatim + dedup guards
                if not q or len(q) < 25:
                    continue
                if q not in norm_ws(ch) and q not in norm_ws(body):
                    continue  # not a real substring -> drop (no fabrication)
                if q in existing_quotes:
                    continue
                cl = a.get("cluster")
                if cl not in clusters:
                    cl = "media_and_communication"  # safe default for mess material
                new_atoms.append({
                    "id": str(uuid.uuid4()),
                    "content": (a.get("content") or "").strip(),
                    "cluster": cl,
                    "topics": [t for t in (a.get("topics") or []) if isinstance(t, str)][:5],
                    "source_ref": src_ref,
                    "source_url": src_url,
                    "source_date": (src_date or "")[:10] if src_date else None,
                    "confidence": 0.7,
                    "confidence_tier": "medium",
                    "claim_type": a.get("claim_type") if a.get("claim_type") in ("opinion", "fact", "prediction") else "opinion",
                    "verification": "unverified",
                    "implication": (a.get("implication") or "").strip(),
                    "original_quote": q,
                    "source_pass": "mess-corpus-2026-07-08",
                })
                existing_quotes.add(q)
                got += 1
        print(f"    -> {got} atoms")

    print(f"\nExtracted {len(new_atoms)} new mess atoms across {len(args.transcripts)} transcript(s). Cost ${cost.total_cost:.2f}")
    for a in new_atoms[:5]:
        print(f"\n  · [{a['cluster']}] {a['content'][:95]}")
        print(f"    “{a['original_quote'][:130]}”")

    if not apply:
        print("\n(dry-run — no writes. Re-run with --apply to append.)")
        return

    pack["atoms"].extend(new_atoms)
    if isinstance(pack.get("brain"), dict):
        pack["brain"]["atom_count"] = len(pack["atoms"])
    pack_path.write_text(json.dumps(pack, indent=2) + "\n")
    print(f"\nAPPLIED: pack now has {len(pack['atoms'])} atoms (+{len(new_atoms)} mess).")
    print(f"Next: export-brain.py --from-files (regen context+website) then re-gate.")


if __name__ == "__main__":
    main()
