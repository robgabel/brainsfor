#!/usr/bin/env python3
"""Phase 3.5 — Synthesis Grounding & Sourcing.

Per SPEC-synthesis-grounding.md. For each synthesis principle, decide its
provenance instead of silently shipping confabulations as grounded:

  1. CORPUS CHECK   — is the principle supported by the brain's own corpus?
                      -> tag `grounded` (cite the atom evidence).
  2. DISCOVERY      — if not, search the web for the claim (Firecrawl search;
                      citations/URLs only, never the summarizer's prose).
  3. FETCH + VERIFY — scrape the candidate primary sources; ask the model for a
                      VERBATIM quote that supports the principle.
                      found -> mint a grounding atom (corpus GROWS), tag `sourced`.
  4. TRUTH-CHECK    — if still unsourced, ask (knowledge-based, SEPARATE from
                      sourcing) whether the person genuinely holds this view.
                      true -> tag `attributed` (keep + label, never delete).
                      false -> tag `dropped`.

Discovery is for FINDING, never for grounding — grounding always requires a
verbatim quote verified against fetched primary text. Output writes provenance
back into brain.json synthesis, appends sourced atoms to
research/sourced-atoms.json, and prints an honest scorecard:
  honest grounding = (grounded + sourced) / total.

Gate: if (attributed + dropped) / total > THIN_FLAG (0.30), the corpus is
undersampled for this subject — flagged for human review / more sources.

Usage:
  python3 scripts/ground-synthesis.py --brain elon-musk            # full run
  python3 scripts/ground-synthesis.py --brain elon-musk --dry-run  # no writes/web
  python3 scripts/ground-synthesis.py --brain elon-musk --limit 5  # first N ungrounded
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, uuid
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import importlib.util
import httpx

# Reuse corpus loading + principle collection + the Claude wrapper.
_fc = importlib.util.spec_from_file_location("factcheck", SCRIPT_DIR / "fact-check-brain.py")
fc = importlib.util.module_from_spec(_fc)
_fc.loader.exec_module(fc)

from auto_build_config import DEFAULT_MODEL, CostTracker, call_claude, step, success, warn, error  # noqa: E402

try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: pip install anthropic"); sys.exit(1)

BRAINS_DIR = ROOT / "brains"
FIRECRAWL_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
THIN_FLAG = 0.30
SCRAPE_MAX_CHARS = 12000


# ---------------------------------------------------------------------------
# Discovery + fetch (Firecrawl). Citations/URLs + primary text only.
# ---------------------------------------------------------------------------
def firecrawl_search(query: str, limit: int = 4) -> list[dict]:
    """Return candidate {url, title} for a claim. We use ONLY the URLs/titles —
    never any summarized answer text — so discovery can't launder confabulation.
    Retries on transient failure: a silently-swallowed blip would zero out sourcing
    for the whole principle (everything falls through to 'attributed')."""
    if not FIRECRAWL_KEY:
        return []
    for attempt in range(3):
        try:
            r = httpx.post(
                "https://api.firecrawl.dev/v1/search",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"},
                json={"query": query, "limit": limit},
                timeout=45,
            )
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(1.5 * (attempt + 1)); continue
            if r.status_code != 200:
                return []
            data = (r.json() or {}).get("data", [])
            return [{"url": d.get("url"), "title": d.get("title", "")} for d in data if d.get("url")]
        except Exception:
            time.sleep(1.0 * (attempt + 1))
    return []


def firecrawl_scrape(url: str) -> str:
    if not FIRECRAWL_KEY:
        return ""
    for attempt in range(3):
        try:
            r = httpx.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"},
                json={"url": url, "formats": ["markdown"]},
                timeout=60,
            )
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(1.5 * (attempt + 1)); continue
            if r.status_code != 200:
                return ""
            md = ((r.json() or {}).get("data") or {}).get("markdown", "") or ""
            return md[:SCRAPE_MAX_CHARS]
        except Exception:
            time.sleep(1.0 * (attempt + 1))
    return ""


# Prefer SCRAPEABLE primary text. Firecrawl returns markdown, so down-rank
# YouTube/video pages: Firecrawl can't extract transcripts from them (returns
# only page chrome), and the brain's own corpus already holds those transcripts.
# Discovery here should surface NEW scrapeable text (essays, interviews, articles).
PRIMARY_HINTS = ("transcript", "interview", "talk", "lecture", "podcast",
                 "speech", "essay", "blog", "article", "/20")
UNSCRAPEABLE = ("youtube.com", "youtu.be", "vimeo.com", "tiktok.com",
                "facebook.com", "instagram.com", "x.com/", "twitter.com")
THIRD_PARTY = ("wikipedia.org", "reddit.com", "quora.com", "medium.com/@", "pinterest.")


def rank_sources(cands: list[dict]) -> list[dict]:
    def score(c):
        u = (c.get("url") or "").lower()
        s = 0
        if any(h in u for h in PRIMARY_HINTS): s += 2
        if any(h in u for h in UNSCRAPEABLE): s -= 3   # Firecrawl can't extract video text
        if any(h in u for h in THIRD_PARTY): s -= 2
        return s
    return sorted(cands, key=score, reverse=True)


# ---------------------------------------------------------------------------
# LLM steps: verbatim verify + truth check
# ---------------------------------------------------------------------------
VERIFY_SYS = """You verify whether a SOURCE TEXT contains a VERBATIM quote that genuinely supports a PRINCIPLE attributed to a person.

Rules:
- The quote MUST appear verbatim (or near-verbatim, allowing minor transcription differences) in the SOURCE TEXT. Do NOT paraphrase or invent.
- It must actually support the principle, not just share a keyword.
- If no genuine supporting verbatim quote exists, say so. Never fabricate.

Return ONLY JSON: {"found": true|false, "quote": "<verbatim excerpt, or empty>", "why": "<one sentence>"}"""

TRUTH_SYS = """You judge whether a PRINCIPLE is genuinely held by a specific person, using your broad knowledge (this is NOT about any provided corpus).

Return ONLY JSON: {"true_to_person": true|false, "confidence": 0.0-1.0, "why": "<one sentence>"}
- true_to_person=true: this is a well-documented, accurate position the person actually holds.
- true_to_person=false: this misrepresents them, or is a generic claim they don't distinctively hold."""


def verify_quote(client, tracker, person, claim, source_text, model):
    msg = (f"PERSON: {person}\nPRINCIPLE: {claim}\n\nSOURCE TEXT:\n{source_text[:SCRAPE_MAX_CHARS]}")
    res = call_claude(client, model, messages=[{"role": "user", "content": msg}],
                      system=VERIFY_SYS, max_tokens=600, parse_json=True,
                      cost_tracker=tracker, label="grnd_verify")
    return res.get("parsed", {})


def truth_check(client, tracker, person, claim, model):
    msg = f"PERSON: {person}\nPRINCIPLE: {claim}"
    res = call_claude(client, model, messages=[{"role": "user", "content": msg}],
                      system=TRUTH_SYS, max_tokens=300, parse_json=True,
                      cost_tracker=tracker, label="grnd_truth")
    return res.get("parsed", {})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--dry-run", action="store_true", help="No web calls, no writes — show plan")
    ap.add_argument("--limit", type=int, default=0, help="Cap ungrounded principles processed (0=all)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--include-weak", action="store_true",
                    help="Also re-source 'weak' principles, not just 'ungrounded'")
    args = ap.parse_args()

    slug = args.brain
    bdir = BRAINS_DIR / slug
    bj_path = bdir / "brain.json"
    if not bj_path.exists():
        error(f"{slug}: brain.json not found"); sys.exit(1)
    brain = json.loads(bj_path.read_text())
    person = brain.get("brain_name", slug)

    principles = fc.collect_principles(brain)
    if not principles:
        warn(f"{slug}: no synthesis principles"); return
    step(f"{slug}: {len(principles)} synthesis principles · person={person}")

    # --- Step 1: corpus check (reuse fact-check judge) ---
    corpus = fc.load_source_corpus(slug)
    if corpus["n_videos"] == 0 and not corpus["atom_quotes"]:
        warn(f"{slug}: no corpus to ground against — every principle will need sourcing")
    client = Anthropic()
    tracker = CostTracker()
    corpus_text = fc.build_corpus_for_prompt(corpus)
    parsed = fc.call_fact_checker(client, person, principles, corpus_text, tracker, args.model)
    by_id = {r.get("principle_id"): r for r in parsed.get("results", [])}

    statuses = {}  # principle_id -> dict(provenance, evidence...)
    ungrounded = []
    for p in principles:
        pid = f"{p['section']}[{p['index']}]"
        st = (by_id.get(pid) or {}).get("status", "ungrounded")
        if st == "grounded":
            statuses[pid] = {"provenance": "grounded",
                             "evidence": (by_id.get(pid) or {}).get("evidence", [])[:1]}
        elif st == "weak" and not args.include_weak:
            statuses[pid] = {"provenance": "grounded", "note": "weak corpus support"}
        else:
            ungrounded.append(p)
    step(f"corpus check: {len(principles)-len(ungrounded)} grounded, {len(ungrounded)} need sourcing")

    if args.limit and len(ungrounded) > args.limit:
        warn(f"--limit {args.limit}: processing first {args.limit} of {len(ungrounded)} ungrounded")
        for p in ungrounded[args.limit:]:
            statuses[f"{p['section']}[{p['index']}]"] = {"provenance": "ungrounded", "note": "skipped by --limit"}
        ungrounded = ungrounded[:args.limit]

    if args.dry_run:
        step(f"[DRY RUN] would discover+verify {len(ungrounded)} principles via Firecrawl + verify/truth-check via {args.model}")
        for p in ungrounded[:8]:
            print(f"    - [{p['section']}] {p['title'][:70]}")
        return

    # --- Steps 2-4: discovery -> fetch -> verify -> mint / truth-check ---
    minted = []  # new sourced atoms
    for p in ungrounded:
        pid = f"{p['section']}[{p['index']}]"
        claim = p["claim"]
        query = f"{person} {p['title']}"
        cands = rank_sources(firecrawl_search(query, limit=6))
        sourced = False
        for c in cands[:5]:
            if any(h in (c["url"] or "").lower() for h in UNSCRAPEABLE):
                continue  # skip video/social — Firecrawl returns no usable text
            text = firecrawl_scrape(c["url"])
            if len(text) < 200:
                continue
            v = verify_quote(client, tracker, person, claim, text, args.model)
            if v.get("found") and (v.get("quote") or "").strip():
                quote = v["quote"].strip()
                atom = {
                    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, c["url"] + quote[:60])),
                    "content": p["title"],
                    "original_quote": quote,
                    "implication": p["desc"],
                    "cluster": "synthesis_sourced",
                    "topics": [],
                    "source_ref": c.get("title") or c["url"],
                    "source_url": c["url"],
                    "confidence": 0.85,
                    "confidence_tier": "high",
                }
                minted.append(atom)
                statuses[pid] = {"provenance": "sourced", "evidence": [{"quote": quote, "url": c["url"]}]}
                success(f"  sourced [{p['section']}] {p['title'][:55]}  <- {c['url'][:50]}")
                sourced = True
                break
            time.sleep(0.2)
        if sourced:
            continue
        # truth-check: real-but-unsourceable vs confabulated
        t = truth_check(client, tracker, person, claim, args.model)
        if t.get("true_to_person") and (t.get("confidence", 0) >= 0.6):
            statuses[pid] = {"provenance": "attributed", "note": t.get("why", "")[:120]}
            warn(f"  attributed (true, unsourced) [{p['section']}] {p['title'][:50]}")
        else:
            statuses[pid] = {"provenance": "dropped", "note": t.get("why", "")[:120]}
            warn(f"  DROPPED (not true-to-person) [{p['section']}] {p['title'][:50]}")

    # --- Write provenance back into brain.json synthesis ---
    syn = brain.get("synthesis", {})
    for p in principles:
        pid = f"{p['section']}[{p['index']}]"
        items = syn.get(p["section"]) or []
        if p["index"] < len(items):
            tag = statuses.get(pid, {"provenance": "ungrounded"})
            items[p["index"]]["provenance"] = tag["provenance"]
            if tag.get("evidence"):
                items[p["index"]]["evidence"] = tag["evidence"]
    bj_path.write_text(json.dumps(brain, indent=2))

    # --- Append minted sourced atoms ---
    if minted:
        sp = bdir / "research" / "sourced-atoms.json"
        existing = json.loads(sp.read_text()) if sp.exists() else []
        seen = {a["id"] for a in existing}
        existing += [a for a in minted if a["id"] not in seen]
        sp.write_text(json.dumps(existing, indent=2))
        success(f"wrote {len(minted)} sourced atoms -> {sp.relative_to(ROOT)}")

    # --- Scorecard + gate ---
    from collections import Counter
    counts = Counter(statuses.get(f"{p['section']}[{p['index']}]", {}).get("provenance", "ungrounded")
                     for p in principles)
    total = len(principles)
    honest = (counts.get("grounded", 0) + counts.get("sourced", 0)) / total if total else 0
    thin = (counts.get("attributed", 0) + counts.get("dropped", 0)) / total if total else 0
    print()
    success(f"{slug} grounding: {honest:.0%} honest "
            f"(grounded={counts.get('grounded',0)} sourced={counts.get('sourced',0)} "
            f"attributed={counts.get('attributed',0)} dropped={counts.get('dropped',0)} "
            f"ungrounded={counts.get('ungrounded',0)})  cost ${tracker.total_cost:.2f}")
    if thin > THIN_FLAG:
        warn(f"UNDERSAMPLED: {thin:.0%} of principles couldn't be sourced (> {THIN_FLAG:.0%}). "
             f"Add primary sources for {person} and re-run, or review the attributed/dropped tail.")


if __name__ == "__main__":
    main()
