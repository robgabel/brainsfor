#!/usr/bin/env python3
"""
Voice enrichment for brain atoms (generic — works with any brain).

Fetches original source content, extracts the thinker's actual voice/framing
and the "implication" (the "so what") for each atom.

Usage:
  python scripts/enrich-voice.py --brain scott-belsky                    # Process top 80 atoms
  python scripts/enrich-voice.py --brain scott-belsky --limit 20         # Process top 20 atoms
  python scripts/enrich-voice.py --brain scott-belsky --apply review.json # Write approved enrichments
  python scripts/enrich-voice.py --brain scott-belsky --dry-run           # Show what would be processed

Requires: ANTHROPIC_API_KEY, SUPABASE_URL + SUPABASE_SERVICE_KEY (in .env)
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

try:
    from dotenv import load_dotenv
    # Fill gaps only (override=False): real shell env wins, then website/.env.local,
    # then ~/rob-ai/.env. Mirrors the export-brain.py fix — the old override=True let
    # website/.env.local's NEXT_PUBLIC_SUPABASE_URL (the paused auth-only project)
    # clobber the factory project and enrichment dialed a dead host.
    load_dotenv(Path(__file__).resolve().parent.parent / "website" / ".env.local", override=False)
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
except ImportError:
    pass

try:
    import anthropic
    from supabase import create_client
except ImportError:
    print("pip install anthropic supabase python-dotenv")
    sys.exit(1)

# --- Paths ---
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
BRAINS_DIR = ROOT_DIR / "brains"

# Canonical model strings — source of truth is auto_build_config.py
sys.path.insert(0, str(SCRIPT_DIR))
from auto_build_config import FAST_MODEL

# --- Config ---
SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL", "https://uzediwokyshjbsymevtp.supabase.co")
_svc = os.environ.get("SUPABASE_SERVICE_KEY", "")
_anon = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
SUPABASE_KEY = _svc if _svc.count(".") == 2 else _anon
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def load_brain_config(slug: str) -> dict:
    """Load brain config from brains/{slug}/brain.json"""
    config_path = BRAINS_DIR / slug / "brain.json"
    if not config_path.exists():
        print(f"ERROR: Brain config not found: {config_path}")
        sys.exit(1)
    with open(config_path) as f:
        return json.load(f)


def get_extraction_prompt(config: dict) -> str:
    """Build the extraction prompt from brain config."""
    name = config["brain_name"]
    source_desc = config.get("brain_source_description", "published content")
    return f"""You are extracting the original voice and implications from {name}'s {source_desc}.

You will receive:
1. An ATOM — a distilled insight previously extracted from {name}'s writing
2. The FULL TEXT of the source content where this atom came from

Your job:

**original_quote**: Find the passage in the source that this atom was extracted from and quote it VERBATIM — 1-3 contiguous sentences copied exactly from the source text (their provocative framing, specific metaphors, stories, emotional weight). Do NOT paraphrase, do NOT stitch fragments from different passages, and do NOT compose words {name} did not say — a synthesized "quote" is a fabrication and will be rejected by provenance QA. If no contiguous passage in the source expresses this atom, return null.

**implication**: What is the "so what"? What does this insight MEAN for someone making decisions? Write 1-2 sentences in {name}'s style about what this means for builders, leaders, or practitioners. If {name} explicitly states the implication, use their words. If not, write one faithful to their voice and thinking patterns.

Return ONLY valid JSON:
{{
  "original_quote": "...",
  "implication": "..."
}}

If you cannot find the relevant passage in the source text, return:
{{
  "original_quote": null,
  "implication": null,
  "reason": "Could not locate the source passage"
}}"""


def fetch_top_atoms(supabase, atoms_table: str, connections_table: str, limit: int = 80) -> list:
    """Fetch atoms most worth enriching: highest confidence + most connected."""
    conn_resp = supabase.table(connections_table).select("atom_id_1, atom_id_2").execute()
    conn_counts = defaultdict(int)
    for c in conn_resp.data:
        conn_counts[c["atom_id_1"]] += 1
        conn_counts[c["atom_id_2"]] += 1

    atoms_resp = supabase.table(atoms_table).select(
        "id, content, source_ref, source_date, cluster, confidence, confidence_tier, original_quote"
    ).is_("original_quote", "null").order("confidence", desc=True).execute()

    atoms = atoms_resp.data

    for atom in atoms:
        atom["_conn_count"] = conn_counts.get(atom["id"], 0)
        atom["_score"] = (atom.get("confidence") or 0.8) * 100 + atom["_conn_count"] * 10

    atoms.sort(key=lambda a: a["_score"], reverse=True)
    return atoms[:limit]


def _norm_title(s: str) -> str:
    """Normalize a title/ref for fuzzy matching (mirrors export-brain's approach)."""
    import re as _re
    s = (s or "").lower().replace("_", " ").replace("-", " ")
    s = _re.sub(r"[^a-z0-9# ]+", " ", s)
    return _re.sub(r"\s+", " ", s).strip()


def build_local_source_index(slug: str) -> dict:
    """Map normalized source refs → LOCAL text (transcripts + scraped raw md).

    Atoms carry source_ref as a TITLE or a youtube:<id>/<slug> token, not a URL.
    The corpus for those refs usually already sits on disk:
      brains/<slug>/source/transcripts/*.json  (full_text, title, video_id)
      brains/<slug>/source/raw/*.md            (via raw/_index.json: url → title/filename)
    Using local text avoids re-fetching the internet for content we have, and is
    the ONLY path that works for youtube: refs (fetching a YouTube page returns
    player HTML, not the transcript). HTTP fetch remains the fallback.
    Values are lazy: (kind, path) tuples; text loaded on first use.
    """
    index = {}
    bdir = BRAINS_DIR / slug / "source"

    tdir = bdir / "transcripts"
    if tdir.exists():
        for tp in sorted(tdir.glob("*.json")):
            try:
                d = json.loads(tp.read_text())
            except Exception:
                continue
            keys = {_norm_title(d.get("title", "")), _norm_title(tp.stem)}
            vid = d.get("video_id")
            if vid:
                keys.add(f"youtube:{vid}".lower())
                keys.add(vid.lower())
            for k in keys:
                if k and k not in index:
                    index[k] = ("transcript", tp)

    raw_index = bdir / "raw" / "_index.json"
    if raw_index.exists():
        try:
            data = json.loads(raw_index.read_text())
        except Exception:
            data = {}
        for url, meta in (data.items() if isinstance(data, dict) else []):
            if not isinstance(meta, dict):
                continue
            fp = bdir / "raw" / meta.get("filename", "")
            if not fp.exists():
                continue
            for k in (_norm_title(meta.get("title", "")), url.lower()):
                if k and k not in index:
                    index[k] = ("raw", fp)
    return index


def resolve_local_source(ref: str, local_index: dict) -> str | None:
    """Return local source text for a ref, or None. Exact then fuzzy title match."""
    if not ref or not local_index:
        return None
    candidates = [ref.lower(), _norm_title(ref)]
    # youtube:Named_Slug refs: also try the slug body as a title
    if ref.lower().startswith("youtube:"):
        candidates.append(_norm_title(ref.split(":", 1)[1]))
    hit = None
    for c in candidates:
        if c in local_index:
            hit = local_index[c]
            break
    if hit is None:
        # prefix/substring fuzzy match on normalized titles (min length guard)
        nq = _norm_title(ref.split(":", 1)[1] if ref.lower().startswith("youtube:") else ref)
        if len(nq) >= 12:
            for k, v in local_index.items():
                if k.startswith(nq) or nq.startswith(k) or (len(nq) >= 16 and nq in k):
                    hit = v
                    break
    if hit is None:
        return None
    kind, path = hit
    try:
        if kind == "transcript":
            return (json.loads(path.read_text()).get("full_text") or "")[:100000]
        return path.read_text()[:100000]
    except Exception:
        return None


def fetch_source_content(url: str) -> str:
    """Fetch source text from URL using httpx."""
    import httpx

    try:
        resp = httpx.get(url, follow_redirects=True, timeout=30,
                         headers={"User-Agent": "Mozilla/5.0 (research bot)"})
        resp.raise_for_status()
        html = resp.text

        import re
        html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")

        return text[:50000]
    except Exception as e:
        return f"ERROR: Could not fetch {url}: {e}"


def extract_voice(client: anthropic.Anthropic, atom_content: str, source_text: str, prompt: str) -> dict:
    """Use Claude to extract original voice + implication."""
    message = client.messages.create(
        model=FAST_MODEL,
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"{prompt}\n\n---\n\nATOM:\n{atom_content}\n\n---\n\nFULL SOURCE TEXT:\n{source_text}"
        }]
    )

    try:
        text = message.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        return {"original_quote": None, "implication": None, "reason": f"Parse error: {message.content[0].text[:100]}"}


def process_atoms(atoms: list, extraction_prompt: str, dry_run: bool = False, title_to_url: dict = None, local_index: dict = None) -> list:
    """Process atoms: fetch source, extract voice, return enrichments.

    Atoms generated by the auto-build pipeline have ``source_ref`` set to the
    source TITLE (not URL). title_to_url maps those titles to fetchable URLs
    using the brain's sources.json. Falls through to source_ref unchanged if no
    map is provided or no match is found (for atoms whose source_ref is already
    a URL — e.g. youtube:VIDEO_ID via older ingestion paths)."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    results = []
    url_cache = {}
    title_to_url = title_to_url or {}
    local_index = local_index or {}

    for i, atom in enumerate(atoms):
        ref = atom.get("source_ref", "")
        url = title_to_url.get(ref, ref)
        # Local corpus first — the ref usually names a transcript/raw file we
        # already have on disk (and youtube: refs are ONLY resolvable locally).
        if not dry_run and url not in url_cache:
            local_text = resolve_local_source(ref, local_index)
            if local_text:
                url_cache[url] = local_text
        atom_id = atom["id"]
        content = atom["content"]

        print(f"[{i+1}/{len(atoms)}] {content[:80]}...")

        if dry_run:
            results.append({
                "id": atom_id,
                "content": content,
                "source_ref": url,
                "cluster": atom.get("cluster"),
                "confidence_tier": atom.get("confidence_tier"),
                "status": "would_process"
            })
            continue

        if not url:
            results.append({
                "id": atom_id,
                "content": content,
                "source_ref": url,
                "original_quote": None,
                "implication": None,
                "status": "no_source_url"
            })
            continue

        if url not in url_cache:
            print(f"  Fetching: {url}")
            url_cache[url] = fetch_source_content(url)
            time.sleep(0.5)

        source_text = url_cache[url]
        if source_text.startswith("ERROR:"):
            results.append({
                "id": atom_id,
                "content": content,
                "source_ref": url,
                "original_quote": None,
                "implication": None,
                "status": source_text
            })
            continue

        extraction = extract_voice(client, content, source_text, extraction_prompt)
        results.append({
            "id": atom_id,
            "content": content,
            "source_ref": url,
            "cluster": atom.get("cluster"),
            "confidence_tier": atom.get("confidence_tier"),
            "original_quote": extraction.get("original_quote"),
            "implication": extraction.get("implication"),
            "status": "ok" if extraction.get("original_quote") else "extraction_failed",
            "reason": extraction.get("reason")
        })

        time.sleep(0.3)

    return results


def apply_enrichments(supabase, atoms_table: str, filepath: str):
    """Write approved enrichments from review JSON back to Supabase."""
    with open(filepath) as f:
        enrichments = json.load(f)

    applied = 0
    skipped = 0
    for item in enrichments:
        if item.get("status") != "ok":
            skipped += 1
            continue
        if not item.get("original_quote"):
            skipped += 1
            continue

        update = {"original_quote": item["original_quote"]}
        if item.get("implication"):
            update["implication"] = item["implication"]

        supabase.table(atoms_table).update(update).eq("id", item["id"]).execute()
        applied += 1
        print(f"  Updated atom {item['id'][:8]}...")

    print(f"\nApplied: {applied}, Skipped: {skipped}")


def main():
    parser = argparse.ArgumentParser(description="Enrich brain atoms with original voice + implications")
    parser.add_argument("--brain", required=True, help="Brain slug (matches brains/{slug}/brain.json)")
    parser.add_argument("--limit", type=int, default=80, help="Number of atoms to process (default: 80)")
    parser.add_argument("--apply", metavar="FILE", help="Apply enrichments from review JSON to Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without fetching")
    args = parser.parse_args()

    if not SUPABASE_KEY:
        print("ERROR: Set SUPABASE_SERVICE_KEY in .env")
        sys.exit(1)

    # Load brain config
    config = load_brain_config(args.brain)
    atoms_table = config.get("supabase", {}).get("atoms_table")
    connections_table = config.get("supabase", {}).get("connections_table")

    if not atoms_table or not connections_table:
        print(f"ERROR: brain.json missing supabase.atoms_table or supabase.connections_table")
        sys.exit(1)

    print(f"Brain: {config['brain_name']} ({args.brain})")
    print(f"Tables: {atoms_table}, {connections_table}")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Output dir for review files
    output_dir = BRAINS_DIR / config["brain_slug"] / "data"

    if args.apply:
        print(f"Applying enrichments from {args.apply}...")
        apply_enrichments(supabase, atoms_table, args.apply)
        return

    if not ANTHROPIC_KEY and not args.dry_run:
        print("ERROR: Set ANTHROPIC_API_KEY env var")
        sys.exit(1)

    print(f"Fetching top {args.limit} atoms for voice enrichment...")
    atoms = fetch_top_atoms(supabase, atoms_table, connections_table, args.limit)
    print(f"  Found {len(atoms)} atoms to enrich")

    if not atoms:
        print("  All atoms already have original_quote. Nothing to do.")
        return

    urls = defaultdict(int)
    for a in atoms:
        urls[a.get("source_ref", "no_url")] += 1
    print(f"  Spanning {len(urls)} unique source URLs")

    extraction_prompt = get_extraction_prompt(config)

    # Build title -> URL map from sources.json (atoms store source_ref as title,
    # not URL, after the auto-build pipeline).
    title_to_url = {}
    sources_path = BRAINS_DIR / config["brain_slug"] / "source" / "sources.json"
    if sources_path.exists():
        try:
            with open(sources_path) as f:
                sd = json.load(f)
            for s in sd.get("sources", []):
                t = s.get("title")
                u = s.get("url")
                if t and u:
                    title_to_url[t] = u
            print(f"  Loaded {len(title_to_url)} title->URL mappings from sources.json")
        except Exception as e:
            print(f"  WARN: Could not load sources.json: {e}")

    local_index = build_local_source_index(config["brain_slug"])
    print(f"  Local source index: {len(local_index)} keys (transcripts + raw md)")

    results = process_atoms(atoms, extraction_prompt, dry_run=args.dry_run, title_to_url=title_to_url, local_index=local_index)

    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "voice-enrichment-review.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    ok = sum(1 for r in results if r["status"] == "ok")
    failed = sum(1 for r in results if r["status"] != "ok" and r["status"] != "would_process")
    print(f"\nResults: {ok} enriched, {failed} failed")
    print(f"Review file: {output_file}")
    print(f"\nNext step: Review the JSON, then run:")
    print(f"  python scripts/enrich-voice.py --brain {args.brain} --apply {output_file}")


if __name__ == "__main__":
    main()
