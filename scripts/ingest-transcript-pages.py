#!/usr/bin/env python3
"""
ingest-transcript-pages.py — fetch PUBLISHED transcript pages (Lex Fridman, TED,
Happy Scribe, etc.) via Firecrawl and DIARIZE them down to the brain subject's
own turns, writing speaker-safe transcripts the voice-enrichment pipeline can use.

WHY THIS EXISTS
---------------
YouTube hard-blocks caption fetches from datacenter/cloud IPs (AWS/GCP/Azure and
CI), so `ingest-youtube.py --from-sources` returns 0 transcripts from any non-
residential environment — the wall that stalled the Elon voice work. But the same
conversations are published as HTML transcript pages that Firecrawl CAN scrape from
a cloud IP. Most of those pages are SPEAKER-LABELED ("Elon Musk[(00:31)](url) …"),
which is the *ideal* case for the misattribution safeguard: we keep only the
subject's turns, so an interviewer's words can never leak into `original_quote`.

This is the "named" diarization tier (parse `Name:` / `Name (ts)` labels) from
scripts/diarize.py, applied at ingestion time, before any atom extraction.

INPUT   sources.json entries with a `transcript_url` (and the brain subject name).
OUTPUT  brains/<slug>/source/transcripts/<id>.json  ({video_id,title,full_text,
        source_url,diarized,turns_kept,turns_dropped}) — full_text is SUBJECT-ONLY.

USAGE
    export FIRECRAWL_API_KEY=...
    python3 scripts/ingest-transcript-pages.py --brain elon-musk            # all transcript_url sources
    python3 scripts/ingest-transcript-pages.py --brain elon-musk --url https://lexfridman.com/elon-musk-4-transcript/ --title "Lex #400" --id JN3KPFbWCy8
    python3 scripts/ingest-transcript-pages.py --brain elon-musk --dry-run  # show what would be fetched
    python3 scripts/ingest-transcript-pages.py --brain elon-musk --from-cache <file.txt> --id JN3KPFbWCy8 --title "Lex #400"  # diarize an already-scraped page
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIRECRAWL_API = "https://api.firecrawl.dev/v2/scrape"


def brain_dir(slug: str) -> Path:
    d = ROOT / "brains" / slug
    if not d.exists():
        sys.exit(f"ERROR: no brain at {d}")
    return d


def subject_name(slug: str) -> str:
    """Full display name of the brain subject, from brain.json (fallback: slug)."""
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


def firecrawl_scrape(url: str) -> str:
    """Scrape a URL to markdown via Firecrawl v2. Returns markdown text."""
    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        sys.exit("ERROR: FIRECRAWL_API_KEY not set (needed to scrape transcript pages)")
    body = json.dumps({"url": url, "formats": ["markdown"], "onlyMainContent": True}).encode()
    req = urllib.request.Request(
        FIRECRAWL_API, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode())
            md = (data.get("data") or {}).get("markdown") or ""
            if md:
                return md
            raise RuntimeError(f"empty markdown ({json.dumps(data)[:200]})")
        except Exception as e:
            if attempt == 2:
                raise
            wait = 10 * (attempt + 1)
            print(f"    scrape retry in {wait}s ({e})")
            time.sleep(wait)
    return ""


# --- Diarization: keep only the subject's turns ------------------------------
# Two label formats cover ~all published transcripts we've seen:
#   Lex/Happy Scribe markdown:  Name[(00:31)](https://…)Their words…
#   Plain labeled:              Name (00:31)  Their words…   OR   Name:  Their words…

def _speaker_variants(name: str) -> list:
    """Accepted spellings of the subject label (first+last, last-name-only, etc.)."""
    parts = name.split()
    variants = {name}
    if len(parts) >= 2:
        variants.add(f"{parts[0]} {parts[-1]}")  # drop middle names
    return [re.escape(v) for v in variants]


def diarize(md: str, subject: str) -> dict:
    """Split a labeled transcript into turns; return subject-only text + stats.

    Recognizes ANY `Name[(ts)](url)` or `Name (ts)`/`Name:` label as a turn
    boundary (so we detect every speaker, not just the subject), then keeps only
    turns whose speaker matches the subject. Unlabeled pages return diarized=False
    and the raw text (caller decides whether to trust it)."""
    md = md.replace("\\n", "\n")
    subj_alt = "|".join(_speaker_variants(subject))
    # A speaker label = 1-4 capitalized words, then a timestamp/colon marker. Covers:
    #   Lex/HappyScribe:  Name[(ts)](url)text
    #   rev.com:          Name ( [ts](url) ): text
    #   plain labeled:    Name (ts) text   |   Name: text
    ts = r'\d{1,2}:\d{2}(?::\d{2})?'
    label = re.compile(
        r'(?:^|\n|\s)([A-Z][A-Za-z.\'-]+(?:\s+[A-Z][A-Za-z.\'-]+){0,3})'
        r'(?:'
        r'\[\(' + ts + r'\)\]\([^)]+\)'                 # Lex
        r'|\s*\(\s*\[' + ts + r'\]\([^)]+\)\s*\)\s*:'   # rev.com
        r'|\s*\(' + ts + r'\)'                          # plain (ts)
        r'|\s*:'                                        # plain colon
        r')\s*'
    )
    matches = list(label.finditer(md))
    if len(matches) < 8:
        return {"diarized": False, "full_text": md.strip(), "turns_kept": 0, "turns_dropped": 0}

    subj_re = re.compile(rf'^(?:{subj_alt})$', re.IGNORECASE)
    kept, dropped = [], 0
    for i, m in enumerate(matches):
        speaker = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        text = md[start:end].strip()
        if not text:
            continue
        if subj_re.match(speaker):
            kept.append(text)
        else:
            dropped += 1
    return {
        "diarized": True,
        "full_text": "\n\n".join(kept),
        "turns_kept": len(kept),
        "turns_dropped": dropped,
    }


def process(slug: str, url: str, vid: str, title: str, cache: str = None) -> dict:
    subject = subject_name(slug)
    if cache:
        md = Path(cache).read_text()
    else:
        print(f"  scraping {url}")
        md = firecrawl_scrape(url)
    dia = diarize(md, subject)
    out = {
        "video_id": vid,
        "title": title,
        "source_url": url,
        "diarized": dia["diarized"],
        "turns_kept": dia["turns_kept"],
        "turns_dropped": dia["turns_dropped"],
        "full_text": dia["full_text"],
        "char_count": len(dia["full_text"]),
    }
    tdir = brain_dir(slug) / "source" / "transcripts"
    tdir.mkdir(parents=True, exist_ok=True)
    dest = tdir / f"{vid or re.sub(r'[^a-z0-9]+','-',title.lower())}.json"
    dest.write_text(json.dumps(out, indent=2))
    flag = "diarized" if dia["diarized"] else "RAW (no labels found)"
    print(f"    -> {dest.name}  [{flag}]  kept {dia['turns_kept']} / dropped {dia['turns_dropped']}  · {out['char_count']:,} chars")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--url", help="single transcript page URL")
    ap.add_argument("--id", default="", help="video_id for the single URL")
    ap.add_argument("--title", default="", help="title for the single URL")
    ap.add_argument("--from-cache", help="path to an already-scraped markdown/txt file (skips Firecrawl)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.url or args.from_cache:
        process(args.brain, args.url or "(cache)", args.id, args.title or "(untitled)", cache=args.from_cache)
        return

    # batch: every source with a transcript_url
    src = brain_dir(args.brain) / "source" / "sources.json"
    if not src.exists():
        sys.exit(f"ERROR: {src} not found")
    sources = json.loads(src.read_text())
    items = sources if isinstance(sources, list) else sources.get("sources", [])
    targets = [s for s in items if s.get("transcript_url")]
    if not targets:
        print(f"No sources with a transcript_url in {src}. Add transcript_url fields first.")
        return
    print(f"{len(targets)} transcript_url source(s) for {args.brain}:")
    for s in targets:
        vid = s.get("youtube_id") or s.get("id") or ""
        title = s.get("title", "(untitled)")
        if args.dry_run:
            print(f"  would fetch: {title}  <- {s['transcript_url']}")
            continue
        try:
            process(args.brain, s["transcript_url"], vid, title)
        except Exception as e:
            print(f"  FAILED {title}: {e}")


if __name__ == "__main__":
    main()
