#!/usr/bin/env python3
"""
enrich-voice-local.py — LOCAL-FIRST voice enrichment.

Fills empty `original_quote` on a brain's LOCAL pack (pack/brain-atoms.json) using
VERBATIM quotes drawn ONLY from diarized, subject-attributed transcripts under
source/transcripts/*.json (diarized=True, produced by ingest-transcript-pages.py).

WHY LOCAL-FIRST
---------------
The Supabase-backed enrich-voice.py reads/writes the build DB and would CLOBBER
local audit work — e.g. elon-musk's nulled source_refs from the #50 attribution
audit live only in the pack. This script reads and writes the shipped pack, so it
composes with that audit instead of overwriting it.

SAFETY CONTRACT
---------------
1. Candidate passages come ONLY from `diarized: true` transcripts (subject's own
   turns; interviewer/host words were dropped at ingest). So any substring is
   speaker-safe by construction.
2. The chosen quote MUST be an exact (whitespace-normalized) substring of a
   candidate passage — no paraphrase, no fabrication.
3. Haiku returns null when no candidate genuinely expresses the atom, so we never
   force a wrong quote onto an atom (the deep-research grounding failure mode).
4. Quote<->citation consistency: when a quote is attached, source_ref/url/date are
   set to THAT transcript. This fixes (never introduces) quote-source mismatch —
   the core defect the whole misattribution effort targets.

USAGE
    export ANTHROPIC_API_KEY=...
    python3 scripts/enrich-voice-local.py --brain elon-musk --dry-run        # preview + stats, no writes
    python3 scripts/enrich-voice-local.py --brain elon-musk --apply          # write quotes into the pack
    python3 scripts/enrich-voice-local.py --brain elon-musk --apply --limit 40 --workers 8
"""
import argparse
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import auto_build_config as cfg  # noqa: E402

try:
    import anthropic
except ImportError:
    sys.exit("ERROR: pip install anthropic")

STOP = set("""a an the and or but if then else of to in on at for from by with as is are was were be been being
this that these those it its it's their they them we you your our i he she his her not no do does did will would
can could should may might must have has had how what when where who why which about into over under out up down
so than too very just also more most some any all one two like get got make made really thing things kind sort
he's she's i'm you're we're there here yeah know think going want said say says because been""".split())

MIN_QUOTE, MAX_QUOTE = 40, 420
TOP_K = 5
MIN_OVERLAP = 3  # atoms with <3 shared content-words to every passage get null (no call)

_lock = threading.Lock()

SYS = """You attach a VERBATIM quote to a knowledge atom about {name}.

You are given the atom (a distilled insight) and up to 5 candidate passages. Every
passage is {name}'s OWN speech, transcribed verbatim from a real interview.

Your job: pick the ONE candidate passage that most directly expresses the atom's
core idea in {name}'s voice, and return the exact span to quote.

HARD RULES
- The quote MUST be copied EXACTLY from one candidate — character for character.
  Do not paraphrase, correct, trim mid-word, or stitch across passages.
- Quote a self-contained span (roughly one to four sentences).
- Return null if NO candidate genuinely expresses this atom's idea. A loose topical
  overlap is NOT enough — the passage must actually say what the atom claims. When
  unsure, return null. A missing quote is fine; a quote that misrepresents the atom
  is a failure.

Return ONLY JSON: {{"candidate": <1-5 or 0>, "quote": "<verbatim span, or empty if 0>"}}"""


def brain_dir(slug):
    d = ROOT / "brains" / slug
    if not d.exists():
        sys.exit(f"ERROR: no brain at {d}")
    return d


def subject_name(slug):
    bj = brain_dir(slug) / "brain.json"
    if bj.exists():
        try:
            data = json.loads(bj.read_text())
            for k in ("name", "person", "thinker", "full_name"):
                if data.get(k):
                    return data[k]
        except Exception:
            pass
    return slug.replace("-", " ").title()


_word = re.compile(r"[a-z0-9]+")


def toks(text):
    return {w for w in _word.findall(text.lower()) if w not in STOP and len(w) > 2}


def norm_ws(s):
    return re.sub(r"\s+", " ", s).strip()


def split_passages(text, url, ref, date, vid):
    """Turn -> citation-sized passages. Long turns split on sentence boundaries."""
    out = []
    for turn in text.split("\n\n"):
        turn = norm_ws(turn)
        if len(turn) < MIN_QUOTE:
            continue
        if len(turn) <= 700:
            out.append(turn)
        else:
            sents = re.split(r"(?<=[.!?])\s+", turn)
            buf = ""
            for s in sents:
                if len(buf) + len(s) > 600 and buf:
                    out.append(buf.strip())
                    buf = s
                else:
                    buf = (buf + " " + s).strip()
            if buf:
                out.append(buf.strip())
    return [{"text": p, "toks": toks(p), "url": url, "ref": ref, "date": date, "vid": vid} for p in out]


def load_passages(slug):
    passages = []
    tdir = brain_dir(slug) / "source" / "transcripts"
    for f in sorted(tdir.glob("*.json")) if tdir.exists() else []:
        d = json.loads(f.read_text())
        if not d.get("diarized"):
            continue
        passages += split_passages(
            d.get("full_text", ""), d.get("source_url", ""),
            d.get("title", ""), d.get("source_date", ""), d.get("video_id", ""),
        )
    return passages


def candidates(atom, passages):
    at = toks((atom.get("content") or "") + " " + (atom.get("implication") or ""))
    scored = []
    for p in passages:
        ov = len(at & p["toks"])
        if ov >= MIN_OVERLAP:
            scored.append((ov, p))
    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:TOP_K]]


def find_verbatim(quote, cands):
    """Return (exact_text, passage) if quote is a real substring of a candidate."""
    nq = norm_ws(quote)
    if not (MIN_QUOTE <= len(nq) <= MAX_QUOTE + 120):
        return None
    for p in cands:
        np = norm_ws(p["text"])
        if nq in np:
            return nq, p
    return None


def enrich_one(client, name, atom, passages, cost):
    cands = candidates(atom, passages)
    if not cands:
        return None
    numbered = "\n\n".join(f"[{i+1}] {c['text']}" for i, c in enumerate(cands))
    user = (
        f"ATOM (insight):\n{atom.get('content','')}\n\n"
        f"IMPLICATION:\n{atom.get('implication','')}\n\n"
        f"CANDIDATE PASSAGES ({name}'s own words):\n{numbered}"
    )
    try:
        r = cfg.call_claude(
            client, cfg.FAST_MODEL,
            [{"role": "user", "content": user}],
            system=SYS.format(name=name), max_tokens=600,
            parse_json=True, cost_tracker=cost, label="voice-local",
        )
    except Exception:
        return None
    parsed = r.get("parsed") or {}
    if isinstance(parsed, list):
        parsed = parsed[0] if parsed and isinstance(parsed[0], dict) else {}
    if not isinstance(parsed, dict):
        return None
    n = parsed.get("candidate") or 0
    quote = (parsed.get("quote") or "").strip()
    if not n or not quote:
        return None
    hit = find_verbatim(quote, cands)
    if not hit:
        return None
    exact, p = hit
    return {"quote": exact, "url": p["url"], "ref": p["ref"], "date": p["date"], "vid": p["vid"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--apply", action="store_true", help="write quotes into the pack (default: dry-run)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    slug = args.brain
    name = subject_name(slug)
    pack = brain_dir(slug) / "pack" / "brain-atoms.json"
    data = json.loads(pack.read_text())
    atoms = data["atoms"] if isinstance(data, dict) else data

    passages = load_passages(slug)
    if not passages:
        sys.exit("ERROR: no diarized transcripts found — run ingest-transcript-pages.py first")
    targets = [a for a in atoms if not (a.get("original_quote") or "").strip()]
    if args.limit:
        targets = targets[: args.limit]
    print(f"{name}: {len(atoms)} atoms · {len(targets)} quote-less to attempt · "
          f"{len(passages)} diarized passages · mode={'APPLY' if apply else 'DRY-RUN'}")

    # Explicit socket timeout: without it a hung HTTP connection stalls a worker
    # forever and as_completed() waits on it indefinitely (a dead run once idled
    # 18h at ~0 CPU). 60s/call + call_claude's bounded retries = fail-fast to None.
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=60.0, max_retries=1)
    cost = cfg.CostTracker() if hasattr(cfg, "CostTracker") else None

    results = {}
    done = 0
    # generous overall ceiling: ~1.5s/atom of wall-clock budget, floor 300s.
    budget = max(300, int(len(targets) * 1.5))
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(enrich_one, client, name, a, passages, cost): a for a in targets}
        try:
            for fut in as_completed(futs, timeout=budget):
                a = futs[fut]
                try:
                    res = fut.result()
                except Exception:
                    res = None
                done += 1
                if res:
                    results[a["id"]] = res
                if done % 25 == 0:
                    print(f"  {done}/{len(targets)} processed · {len(results)} quotes found", flush=True)
        except TimeoutError:
            print(f"  WARN: hit {budget}s budget with {done}/{len(targets)} done — proceeding with partial results", flush=True)
            for fut in futs:
                fut.cancel()

    print(f"\nAttached-able quotes: {len(results)}/{len(targets)} "
          f"({100*len(results)//max(1,len(targets))}% of quote-less atoms)")
    if cost:
        try:
            print(f"Cost: ${cost.total_cost:.2f}" if hasattr(cost, "total_cost") else "")
        except Exception:
            pass

    # sample for review
    sample = list(results.items())[:4]
    for aid, r in sample:
        atom = next(a for a in atoms if a["id"] == aid)
        print(f"\n  · atom: {atom['content'][:95]}...")
        print(f"    quote: “{r['quote'][:150]}”")
        print(f"    from:  {r['ref'][:60]}")

    if not apply:
        print("\n(dry-run — no writes. Re-run with --apply to attach.)")
        return

    n_recite = 0
    for a in atoms:
        r = results.get(a["id"])
        if not r:
            continue
        a["original_quote"] = r["quote"]
        # quote<->citation consistency: cite the transcript the quote is from
        if r["ref"]:
            a["source_ref"] = r["ref"]
        if r["url"]:
            a["source_url"] = r["url"]
        if r["date"]:
            a["source_date"] = r["date"]
        a["voice_enriched"] = "diarized-transcript-2026-07-05"
        n_recite += 1
    # match export-brain.py's canonical format (indent=2, ensure_ascii=True) so the
    # diff is limited to changed atoms — not a whole-file unicode re-escape.
    pack.write_text(json.dumps(data, indent=2) + "\n")
    print(f"\nAPPLIED: {n_recite} atoms now carry a verbatim, speaker-safe quote. Pack written.")
    print("Next: python3 scripts/audit-brains.py --brain " + slug + "  (voice coverage should rise)")


if __name__ == "__main__":
    main()
