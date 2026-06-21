#!/usr/bin/env python3
"""
auto-build-brain.py — Fully automated brain pack builder for BrainsFor.

Takes a person's name and produces a complete, shippable brain pack end-to-end
with ZERO manual approval gates. Replaces 6-12 hours of babysitting with
~60-90 minutes of unattended execution.

Usage:
    python scripts/auto-build-brain.py --person "Jensen Huang"
    python scripts/auto-build-brain.py --person "Kara Swisher" --dry-run
    python scripts/auto-build-brain.py --person "Jensen Huang" --resume
    python scripts/auto-build-brain.py --person "Jensen Huang" --resume-from 3

Pipeline:
    Phase 0: Source Discovery (web search → sources.json)
    Phase 1: Scaffolding (dirs, brain.json, Supabase tables, index.json)
    Phase 2: Content Ingestion (YouTube transcripts + deep research atoms)
    Phase 3: Synthesis (LLM-generated synthesis.md)
    Phase 4: Enrichment (voice + connections, auto-applied)
    Phase 5: Export & QA (pack generation + audit scoring)

Cost: ~$23-25 per brain | Time: ~45-90 minutes
"""

import argparse
import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# --- Paths ---
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
BRAINS_DIR = ROOT_DIR / "brains"
TEMPLATES_DIR = ROOT_DIR / "templates"

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR.parent / ".env")
except ImportError:
    pass

# Import config
sys.path.insert(0, str(SCRIPT_DIR))
from auto_build_config import (
    DEFAULT_MODEL, SYNTHESIS_MODEL, FAST_MODEL,
    TARGET_ATOMS, TARGET_CONNECTIONS, MIN_ATOMS_PER_CLUSTER,
    MIN_AUDIT_SCORE, MAX_REMEDIATION_CYCLES, PHASE_NAMES,
    MIN_BRAIN_ATOMS, MIN_QUOTE_PROVENANCE,
    MIN_VOICE_PCT, MIN_VIDEOS_EXPECT_TRANSCRIPTS,
    SCRAPE_MAX_CHARS, SCRAPE_MIN_CHARS, SCRAPE_TIMEOUT_SEC, SCRAPE_SKIP_DOMAINS,
    CostTracker, call_claude,
    phase_header, step, success, warn, error,
    get_search_queries,
    SOURCE_CLASSIFY_PROMPT, BRAIN_JSON_PROMPT,
    SYNTHESIS_PROMPT, SYNTHESIS_JSON_PROMPT,
    YOUTUBE_PARTNER_PROMPT,
    COLORS,
)

# Import existing scripts via importlib (hyphenated filenames)
build_brain = importlib.import_module("build-brain")

# Speaker diarization: attribute original_quote ONLY to the brain subject, never
# the interviewer/host. Shared by the text-source + transcript extraction paths.
from diarize import to_subject_text

# Optional imports
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from supabase import create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False


# =============================================================================
# SLACK NOTIFICATIONS (no-op if SLACK_BUILD_WEBHOOK unset)
# =============================================================================

def _gh_run_url() -> str:
    server = os.environ.get("GITHUB_SERVER_URL", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if server and repo and run_id:
        return f"{server}/{repo}/actions/runs/{run_id}"
    return ""


def post_slack(text: str, emoji: str = None):
    webhook = os.environ.get("SLACK_BUILD_WEBHOOK")
    if not webhook or not HAS_HTTPX:
        return
    try:
        run_url = _gh_run_url()
        suffix = f" · <{run_url}|run log>" if run_url else ""
        body = f"{emoji} {text}{suffix}" if emoji else f"{text}{suffix}"
        httpx.post(webhook, json={"text": body}, timeout=5.0)
    except Exception:
        pass


# =============================================================================
# PROGRESS TRACKING
# =============================================================================

def load_progress(brain_dir: Path) -> dict:
    """Load build progress from disk."""
    progress_path = brain_dir / "build-progress.json"
    if progress_path.exists():
        with open(progress_path) as f:
            return json.load(f)
    return None


def save_progress(brain_dir: Path, progress: dict):
    """Save build progress to disk."""
    brain_dir.mkdir(parents=True, exist_ok=True)
    progress_path = brain_dir / "build-progress.json"
    with open(progress_path, "w") as f:
        json.dump(progress, f, indent=2)


def init_progress(person_name: str, slug: str) -> dict:
    """Create initial progress structure."""
    return {
        "person": person_name,
        "slug": slug,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "phases": {str(i): {"status": "pending"} for i in range(6)},
        "total_cost_usd": 0.0,
    }


def mark_phase(progress: dict, phase: int, status: str, **extra):
    """Update a phase's status in the progress dict."""
    progress["phases"][str(phase)]["status"] = status
    if status == "complete":
        progress["phases"][str(phase)]["completed_at"] = datetime.now(timezone.utc).isoformat()
    for k, v in extra.items():
        progress["phases"][str(phase)][k] = v


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def slugify(name: str) -> str:
    """Convert a person's name to a brain slug."""
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s.strip("-")


def underscore_slug(slug: str) -> str:
    """Convert brain-slug to brain_slug for Supabase table names."""
    return slug.replace("-", "_")


# ── Per-brain emoji assignment ───────────────────────────────────────────────
# Every brain carries an `emoji` in index.json — the glanceable badge used by
# the /brain skill's session-tagging and the brainsforagents.com cards + pickers.
# New brains get one automatically: the LLM proposes one in brain.json, and
# registration validates + dedupes it (curated fallback pool, then 🧠).
_EMOJI_FALLBACK_POOL = [
    "🧠", "💭", "🔭", "🧩", "🗝️", "🎯", "🪄", "🛠️", "📐", "🔱",
    "🪶", "🧭", "🌱", "⚙️", "🪐", "🎲", "🧱", "🦉", "🐝", "🪁",
    "🧬", "📡", "🔆", "🌀", "🧲", "🪞", "🗺️", "🎼",
]


def _looks_like_emoji(s: str) -> bool:
    """Loose validity check. Accepts short ZWJ/variation sequences (👩‍💻, ⚔️);
    rejects empty strings and prose like 'the apple 🍎'."""
    s = (s or "").strip()
    if not s or len(s) > 8:
        return False
    return not any(c.isalnum() or c.isspace() for c in s)


def load_used_emojis() -> set:
    """Emojis already assigned in index.json (so new picks stay collision-free)."""
    index_path = BRAINS_DIR / "index.json"
    if not index_path.exists():
        return set()
    with open(index_path) as f:
        index = json.load(f)
    return {b.get("emoji") for b in index.get("brains", []) if b.get("emoji")}


def pick_brain_emoji(brain_json: dict, used_emojis: set) -> str:
    """Pick a distinct per-brain emoji: the LLM's brain.json proposal when it's
    a valid, unused single emoji; else the first unused curated emoji; 🧠 last."""
    proposed = (brain_json.get("emoji") or "").strip()
    if _looks_like_emoji(proposed) and proposed not in used_emojis:
        return proposed
    for e in _EMOJI_FALLBACK_POOL:
        if e not in used_emojis:
            return e
    return "🧠"


def get_supabase_client():
    """Create a Supabase client."""
    url = os.environ.get("SUPABASE_URL", "https://uzediwokyshjbsymevtp.supabase.co")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_KEY not set")
    return create_client(url, key)


def get_supabase_rest_headers() -> dict:
    """Get headers for direct Supabase REST API calls."""
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }


def get_supabase_url() -> str:
    return os.environ.get("SUPABASE_URL", "https://uzediwokyshjbsymevtp.supabase.co").rstrip("/")


def ensure_supabase_tables(slug: str, person_name: str, brain_json: dict) -> bool:
    """Create a brain's atoms/connections tables idempotently and verify they're live.

    Runs templates/create-brain-tables.sql (per-statement) through the service-role
    `exec_sql` RPC, reloads the PostgREST schema cache, then polls until both tables
    are queryable via REST (so the subsequent atom upload won't 404 on schema-cache lag).

    Returns True ONLY when both tables are verified visible. Returns False — honestly,
    with a real error — on any failure, instead of the old code's fake "Executed N
    statements" success. The pack still ships either way; Supabase is optional infra.
    """
    step("Creating + verifying Supabase tables...")
    us = underscore_slug(slug)
    url = get_supabase_url()
    headers = get_supabase_rest_headers()
    try:
        sql = (TEMPLATES_DIR / "create-brain-tables.sql").read_text()
        first_name = brain_json.get("brain_first_name", person_name.split()[0])
        last_name = brain_json.get("brain_last_name",
                                   person_name.split()[-1] if " " in person_name else "")
        possessive = brain_json.get("brain_possessive", "their")
        sql = (sql.replace("{{SLUG}}", us).replace("{{NAME}}", person_name)
                  .replace("{{FIRST_NAME}}", first_name).replace("{{LAST_NAME}}", last_name)
                  .replace("{{POSSESSIVE}}", possessive))

        # Split into single statements (template has no function bodies / DO blocks),
        # stripping comment-only lines so exec_sql gets clean SQL.
        def _clean(stmt: str) -> str:
            return "\n".join(l for l in stmt.splitlines()
                             if not l.strip().startswith("--")).strip()
        statements = [_clean(s) for s in sql.split(";")]
        statements = [s for s in statements if s]

        failures = []
        for stmt in statements:
            resp = httpx.post(f"{url}/rest/v1/rpc/exec_sql", headers=headers,
                              json={"query": stmt}, timeout=60)
            if resp.status_code not in (200, 201, 204):
                failures.append(f"HTTP {resp.status_code}: {resp.text[:140]} :: {stmt[:70]}")
        if failures:
            warn(f"Table creation failed ({len(failures)} statement(s)):")
            for f in failures[:6]:
                warn(f"  {f}")
            return False

        # Force PostgREST to pick up the new tables immediately.
        httpx.post(f"{url}/rest/v1/rpc/exec_sql", headers=headers,
                   json={"query": "NOTIFY pgrst, 'reload schema'"}, timeout=30)

        # Poll until both tables answer a REST query (defeats schema-cache lag —
        # the exact bug that silently orphaned every recent build).
        for _ in range(6):
            time.sleep(1.5)
            a = httpx.get(f"{url}/rest/v1/{us}_atoms?select=id&limit=0",
                          headers=headers, timeout=30).status_code
            c = httpx.get(f"{url}/rest/v1/{us}_connections?select=id&limit=0",
                          headers=headers, timeout=30).status_code
            if a == 200 and c == 200:
                success(f"Supabase tables ready: {us}_atoms, {us}_connections")
                return True
        warn(f"Tables created but {us}_atoms not visible to PostgREST after retries")
        return False
    except Exception as e:
        warn(f"Supabase table creation failed: {e}")
        return False


# =============================================================================
# PHASE 0: SOURCE DISCOVERY
# =============================================================================

def seed_from_wikipedia(person_name: str) -> list[dict]:
    """Seed candidate URLs from Wikipedia: the article itself + external links.

    Wikipedia gives biographical scaffolding and — more importantly — a curated
    external-links section that often surfaces personal sites, podcast pages,
    and bibliographies the bare web search misses. Returns [{url, title, description}].
    Silent failure: any error returns [] so we never block Phase 0 on Wikipedia.
    """
    WIKI_API = "https://en.wikipedia.org/w/api.php"
    WIKI_HEADERS = {"User-Agent": "BrainsFor/1.0 (https://brainsforagents.com; rob@brainsforagents.com)"}
    candidates: list[dict] = []

    try:
        # 1. Find the right page via search (handles "Jensen Huang" → "Jensen Huang" page)
        search = httpx.get(
            WIKI_API,
            params={"action": "query", "list": "search", "srsearch": person_name,
                    "srlimit": 1, "format": "json"},
            headers=WIKI_HEADERS, timeout=15,
        )
        if search.status_code != 200:
            return []
        hits = search.json().get("query", {}).get("search", [])
        if not hits:
            return []
        page_title = hits[0]["title"]

        # 2. Add the Wikipedia article itself as an essential bio source
        wiki_url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
        candidates.append({
            "url": wiki_url,
            "title": f"Wikipedia: {page_title}",
            "description": "Biographical overview from Wikipedia",
        })

        # 3. Pull external links from the article
        ext = httpx.get(
            WIKI_API,
            params={"action": "parse", "page": page_title, "prop": "externallinks",
                    "format": "json"},
            headers=WIKI_HEADERS, timeout=15,
        )
        if ext.status_code == 200:
            links = ext.json().get("parse", {}).get("externallinks", [])
            # Skip noise: Wikipedia internals, archive duplicates, citations databases
            skip_domains = (
                "archive.org", "web.archive.org", "doi.org", "worldcat.org",
                "viaf.org", "isni.org", "id.loc.gov", "d-nb.info", "wikidata.org",
                "wikipedia.org", "wikimedia.org", "google.com/books",
                "ncbi.nlm.nih.gov", "jstor.org", "semanticscholar.org",
            )
            seen = set()
            for link in links:
                if not link or not link.startswith(("http://", "https://")):
                    continue
                if any(d in link for d in skip_domains):
                    continue
                if link in seen:
                    continue
                seen.add(link)
                candidates.append({
                    "url": link,
                    "title": "",  # let LLM classifier infer from URL
                    "description": "External link from Wikipedia article",
                })

        return candidates
    except Exception:
        return []


def discover_youtube_videos(
    person_name: str,
    client: "anthropic.Anthropic",
    cost_tracker: "CostTracker",
    max_base: int = 20,
    max_per_partner: int = 2,
) -> list[dict]:
    """Hybrid yt-dlp YouTube discovery — two passes, zero identity confusion.

    Pass A: ytsearch{max_base}:{person_name}
        Full-name anchor — YouTube's own ranking, high recall, no hallucination.

    Pass B: curated partner queries with QUOTED name strings
        LLM generates high-confidence partner/event names.
        Each query: ytsearch2:"Person Name" "Partner Name"
        Quoted strings prevent 'Annie → Annie Jacobsen' style identity confusion.

    Results are deduped by video ID. yt-dlp must be installed (brew install yt-dlp).
    """
    yt_dlp_bin = shutil.which("yt-dlp")
    if not yt_dlp_bin:
        warn("yt-dlp not installed — skipping YouTube discovery (brew install yt-dlp)")
        return []

    seen_ids: set[str] = set()
    videos: list[dict] = []

    def _run_ytsearch(query: str, limit: int) -> list[dict]:
        try:
            result = subprocess.run(
                [yt_dlp_bin, f"ytsearch{limit}:{query}",
                 "--print", "%(id)s\t%(title)s",
                 "--no-playlist", "--no-warnings"],
                capture_output=True, text=True, timeout=45,
            )
            items = []
            for line in result.stdout.strip().splitlines():
                if "\t" not in line:
                    continue
                vid_id, title = line.split("\t", 1)
                vid_id, title = vid_id.strip(), title.strip()
                if vid_id and title:
                    items.append({
                        "youtube_id": vid_id,
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={vid_id}",
                    })
            return items
        except Exception as e:
            warn(f"yt-dlp error for {query!r}: {e}")
            return []

    # --- Pass A: base search ---
    step(f"YouTube [A]: ytsearch{max_base}:{person_name!r}...")
    for v in _run_ytsearch(person_name, max_base):
        if v["youtube_id"] not in seen_ids:
            seen_ids.add(v["youtube_id"])
            videos.append(v)
    success(f"YouTube [A]: {len(videos)} videos")

    # --- Pass B: curated partner queries ---
    step("YouTube [B]: generating partner list via LLM...")
    try:
        partner_result = call_claude(
            client, FAST_MODEL,
            messages=[{"role": "user", "content": YOUTUBE_PARTNER_PROMPT.format(person_name=person_name)}],
            max_tokens=512,
            parse_json=True,
            cost_tracker=cost_tracker,
            label="youtube_partners",
        )
        partners = partner_result.get("parsed", {}).get("partners", [])
        if not isinstance(partners, list):
            partners = []
    except Exception as e:
        warn(f"Partner LLM call failed: {e}")
        partners = []

    success(f"YouTube [B]: {len(partners)} partner candidates from LLM")

    new_b = 0
    for partner in partners[:12]:
        query = f'"{person_name}" "{partner}"'
        for v in _run_ytsearch(query, max_per_partner):
            if v["youtube_id"] not in seen_ids:
                seen_ids.add(v["youtube_id"])
                videos.append(v)
                new_b += 1

    success(f"YouTube [B]: +{new_b} unique videos from partner queries")
    success(f"YouTube total: {len(videos)} unique videos discovered")
    return videos


def phase_0_discover_sources(
    person_name: str,
    slug: str,
    brain_dir: Path,
    client: "anthropic.Anthropic",
    cost_tracker: CostTracker,
    max_sources: int = 15,
    dry_run: bool = False,
) -> dict:
    """Discover source material via web search + LLM classification."""
    phase_header(0)

    sources_path = brain_dir / "source" / "sources.json"
    if sources_path.exists():
        with open(sources_path) as f:
            existing = json.load(f)
        source_count = len(existing.get("sources", []))
        if source_count > 0:
            success(f"sources.json already exists ({source_count} sources) — skipping discovery")
            return existing
        else:
            warn("Existing sources.json is empty — re-running discovery")

    if dry_run:
        step("[DRY RUN] Would run 4 Firecrawl web searches + yt-dlp YouTube discovery + LLM classify")
        return {"sources": []}

    # --- YouTube discovery via yt-dlp (independent of Firecrawl) ---
    yt_videos = discover_youtube_videos(person_name, client, cost_tracker)

    # --- Web search via Firecrawl (TEXT sources only — YouTube handled above) ---
    firecrawl_key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not firecrawl_key:
        warn("FIRECRAWL_API_KEY not set — skipping text source search. YouTube videos still discovered.")

    all_urls = []
    seen_urls = set()

    if firecrawl_key:
        # --- Wikipedia seed (free, no API key) ---
        step("Seeding from Wikipedia...")
        wiki_candidates = seed_from_wikipedia(person_name)
        # Cap Wikipedia external links to 30 to limit biographical noise —
        # the article itself is always first, so we keep it + up to 29 links.
        wiki_candidates = wiki_candidates[:30]
        for c in wiki_candidates:
            if c["url"] not in seen_urls:
                seen_urls.add(c["url"])
                all_urls.append(c)
        if wiki_candidates:
            success(f"Wikipedia seeded {len(wiki_candidates)} URLs (article + external links, capped at 30)")
        else:
            warn("Wikipedia returned no usable seeds — continuing with web search only")

        queries = get_search_queries(person_name)

        for query in queries:
            step(f"Searching: {query}")
            try:
                resp = httpx.post(
                    "https://api.firecrawl.dev/v1/search",
                    headers={"Authorization": f"Bearer {firecrawl_key}", "Content-Type": "application/json"},
                    json={"query": query, "limit": 10},
                    timeout=30,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("data", [])
                    for r in results:
                        url = r.get("url", "")
                        # Skip YouTube URLs — those come from yt-dlp, not Firecrawl
                        if url and url not in seen_urls and "youtube.com" not in url and "youtu.be" not in url:
                            seen_urls.add(url)
                            all_urls.append({
                                "url": url,
                                "title": r.get("title", ""),
                                "description": r.get("description", ""),
                            })
                    success(f"Found {len(results)} results")
                else:
                    warn(f"Search returned {resp.status_code}: {resp.text[:200]}")
                time.sleep(1)
            except Exception as e:
                warn(f"Search error: {e}")

    if not all_urls and not yt_videos:
        warn("No search results found. Create sources.json manually.")
        return {"sources": []}

    # --- Classify TEXT results with LLM ---
    step(f"Classifying {len(all_urls)} text URLs with LLM...")

    def _clean_title(t: str) -> str:
        if not t:
            return ""
        cleaned = t.replace("\n", " ").replace("\r", " ").replace('"', "'")
        cleaned = "".join(ch for ch in cleaned if ch.isprintable())
        return cleaned[:120].strip()
    urls_json = json.dumps([{"url": u["url"], "title": _clean_title(u["title"])} for u in all_urls[:50]], indent=2)
    prompt = SOURCE_CLASSIFY_PROMPT.format(person_name=person_name, urls_json=urls_json)

    result = call_claude(
        client, FAST_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8192,
        parse_json=True,
        cost_tracker=cost_tracker,
        label="source_classify",
    )

    classified = result.get("parsed", []) if all_urls else []

    # Build text sources from LLM classification (skip any YouTube URLs that
    # slipped through — they'd be duplicates of what yt-dlp already found)
    sources = []
    for item in classified[:max_sources]:
        url = item.get("url", "")
        if "youtube.com" in url or "youtu.be" in url:
            continue  # YouTube handled by yt-dlp path
        source = {
            "title": item.get("title", "Unknown"),
            "type": item.get("type", "other"),
            "priority": item.get("priority", "medium"),
            "url": url,
        }
        sources.append(source)

    # --- Merge YouTube videos from yt-dlp (always essential — they have transcripts) ---
    for v in yt_videos:
        sources.append({
            "title": v["title"],
            "type": "video",
            "priority": "high",
            "url": v["url"],
            "youtube_id": v["youtube_id"],
        })

    sources_data = {
        "description": f"Source material for the {person_name} brain pack — text via Firecrawl, video via yt-dlp.",
        "brain_slug": slug,
        "brain_name": person_name,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
    }

    # Save
    source_dir = brain_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    with open(sources_path, "w") as f:
        json.dump(sources_data, f, indent=2)

    essential = sum(1 for s in sources if s.get("priority") == "essential")
    n_videos = sum(1 for s in sources if s.get("youtube_id"))
    n_text = len(sources) - n_videos
    success(f"Discovered {len(sources)} sources: {n_text} text + {n_videos} YouTube videos ({essential} essential)")

    return sources_data


# =============================================================================
# PHASE 1: SCAFFOLDING
# =============================================================================

def phase_1_scaffold(
    person_name: str,
    slug: str,
    brain_dir: Path,
    sources_data: dict,
    client: "anthropic.Anthropic",
    cost_tracker: CostTracker,
    reference_slug: str = "scott-belsky",
    model: str = DEFAULT_MODEL,
    dry_run: bool = False,
) -> dict:
    """Create directories, brain.json, Supabase tables, and index entry."""
    phase_header(1)

    # 1.1 Create directories
    step("Creating directory structure...")
    for subdir in ["source", "research", "data", "pack"]:
        (brain_dir / subdir).mkdir(parents=True, exist_ok=True)
    success("Directories created")

    # 1.2 Generate brain.json
    brain_json_path = brain_dir / "brain.json"
    if brain_json_path.exists():
        step("brain.json already exists — loading")
        with open(brain_json_path) as f:
            brain_json = json.load(f)
    else:
        step(f"Generating brain.json via {model}...")
        if dry_run:
            step("[DRY RUN] Would generate brain.json")
            return {}

        # Load exemplar
        exemplar_path = BRAINS_DIR / reference_slug / "brain.json"
        with open(exemplar_path) as f:
            exemplar = json.load(f)

        # Prepare sources summary. Includes URLs (domain context disambiguates
        # common names — e.g. paypal.com vs holosync.com for "Bill Harris") and
        # the sources_data description (often hand-written disambiguation).
        sources_list = sources_data.get("sources", [])
        sources_lines = []
        description = sources_data.get("description", "").strip()
        if description:
            sources_lines.append(f"DESCRIPTION: {description}\n")
        sources_lines.append("SOURCES:")
        for s in sources_list:
            line = f"- [{s.get('priority', 'medium')}] {s.get('title', 'Unknown')} ({s.get('type', 'unknown')})"
            url = s.get("url", "")
            if url:
                line += f" — {url}"
            sources_lines.append(line)
        sources_summary = "\n".join(sources_lines) if sources_list else "No sources discovered yet."

        us = underscore_slug(slug)
        used_emojis = load_used_emojis()
        prompt = BRAIN_JSON_PROMPT.format(
            person_name=person_name,
            slug=slug,
            exemplar_json=json.dumps(exemplar, indent=2),
            sources_summary=sources_summary,
            atoms_table=f"{us}_atoms",
            connections_table=f"{us}_connections",
            used_emojis=", ".join(sorted(used_emojis)) or "(none yet)",
        )

        result = call_claude(
            client, model,
            messages=[{"role": "user", "content": prompt}],
            # 8192 truncated brain.json mid-string for richer thinkers (charlie-munger,
            # jensen-huang failed at ~char 34900 == the 8192-token ceiling), producing
            # invalid JSON. The synthesis section (first_principles, contrarian_positions,
            # etc.) can run large — give it headroom.
            max_tokens=16384,
            parse_json=True,
            cost_tracker=cost_tracker,
            label="brain_json_gen",
        )

        brain_json = result["parsed"]

        # Validate required keys
        required_keys = ["brain_name", "brain_slug", "brain_first_name", "clusters", "supabase"]
        missing = [k for k in required_keys if k not in brain_json]
        if missing:
            warn(f"Generated brain.json missing keys: {missing} — adding defaults")
            brain_json.setdefault("brain_slug", slug)
            brain_json.setdefault("brain_name", person_name)
            parts = person_name.split()
            brain_json.setdefault("brain_first_name", parts[0])
            brain_json.setdefault("brain_last_name", parts[-1] if len(parts) > 1 else "")

        # Ensure Supabase config
        us = underscore_slug(slug)
        brain_json.setdefault("supabase", {})
        brain_json["supabase"]["project_id"] = "uzediwokyshjbsymevtp"
        brain_json["supabase"]["atoms_table"] = f"{us}_atoms"
        brain_json["supabase"]["connections_table"] = f"{us}_connections"

        with open(brain_json_path, "w") as f:
            json.dump(brain_json, f, indent=2)
        success(f"brain.json generated ({len(brain_json.get('clusters', {}))} clusters)")

    # 1.3 Create Supabase tables (verified — see ensure_supabase_tables)
    if dry_run:
        step("[DRY RUN] Would create + verify Supabase tables")
    else:
        tables_ready = ensure_supabase_tables(slug, person_name, brain_json)
        brain_json["_supabase_tables_ready"] = tables_ready
        if not tables_ready:
            warn("Supabase tables NOT ready — atoms/connections upload will be skipped. "
                 "Pack still ships, but Supabase-backed connection enrichment is disabled "
                 "for this brain until the tables exist.")

    # 1.4 Register in index.json
    step("Registering in index.json...")
    if not dry_run:
        index_path = BRAINS_DIR / "index.json"
        if index_path.exists():
            with open(index_path) as f:
                index = json.load(f)
        else:
            index = {"brains": []}

        # Pick a distinct emoji (LLM proposal in brain.json, deduped against
        # those already in use; falls back to a curated pool, then 🧠). This is
        # the per-brain badge read by the /brain skill + the website.
        used_emojis = {b.get("emoji") for b in index["brains"] if b.get("emoji")}
        existing_entry = next((b for b in index["brains"] if b["slug"] == slug), None)
        if existing_entry is None:
            emoji = pick_brain_emoji(brain_json, used_emojis)
            index["brains"].append({
                "slug": slug,
                "emoji": emoji,
                "name": person_name,
                "source": brain_json.get("brain_source_detail", brain_json.get("brain_source_description", "")),
                "atom_count": 0,
                "connection_count": 0,
                "status": "scaffolded",
                "pack_path": f"brains/{slug}/pack/",
            })
            with open(index_path, "w") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
            success(f"Registered in index.json ({emoji})")
        elif not existing_entry.get("emoji"):
            # Backfill on a brain registered before emojis existed (or mid-resume).
            existing_entry["emoji"] = pick_brain_emoji(brain_json, used_emojis)
            with open(index_path, "w") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
            success(f"Already registered — added emoji ({existing_entry['emoji']})")
        else:
            success(f"Already registered in index.json ({existing_entry['emoji']})")

    return brain_json


# =============================================================================
# PHASE 2: CONTENT INGESTION
# =============================================================================

def extract_atoms_from_text(
    brain_json: dict,
    source: dict,
    content: str,
    client: "anthropic.Anthropic",
    cost_tracker: CostTracker,
    model: str,
) -> list:
    """Use Claude to extract atoms from a single scraped text source."""
    brain_name = brain_json["brain_name"]
    first_name = brain_json["brain_first_name"]
    clusters = brain_json.get("clusters", {})
    cluster_list = "\n".join(f"- {k}: {v.get('name', '')}" for k, v in clusters.items())

    src_type = source.get("type", "article")
    src_title = source.get("title", "")
    src_url = source.get("url", "")

    # Diarization: for interview/podcast sources, keep ONLY the subject's spoken
    # turns so original_quote can never be attributed to the interviewer. Named
    # labels are parsed for free; unlabeled interview transcripts are split by a
    # fast model; audio URLs use STT if ASSEMBLYAI_API_KEY is set. Essays and
    # single-author sources pass through unchanged (back-compatible).
    diar = to_subject_text(
        raw_text=content,
        audio_url=source.get("audio_url"),
        subject_name=brain_name,
        subject_first=first_name,
        src_type=src_type,
        client=client,
        model=FAST_MODEL,
        assemblyai_key=os.environ.get("ASSEMBLYAI_API_KEY"),
    )
    content = diar["text"]
    diar_note = ""
    if diar["diarized"]:
        turn_info = (
            f" ({diar['subject_turns']} of {diar['subject_turns'] + diar['other_turns']} turns kept)"
            if diar.get("subject_turns") is not None else ""
        )
        diar_note = (
            f"\nIMPORTANT — SPEAKER ATTRIBUTION: This CONTENT has already been filtered "
            f"to ONLY {first_name}'s own spoken turns (diarization method: {diar['method']}{turn_info}); "
            f"the interviewer/host words were removed. Every \"original_quote\" is therefore "
            f"{first_name} speaking — never attribute the interviewer's questions or commentary to {first_name}.\n"
        )
    # Source publication date — required for /evolve to work. We accept several
    # shapes (`date`, `published`, `year`) and fall back to null if none exist.
    src_date = (
        source.get("date")
        or source.get("published")
        or source.get("year")
        or None
    )
    src_date_str = str(src_date) if src_date else ""
    src_date_line = f"PUBLISHED: {src_date_str}\n" if src_date_str else ""
    src_date_rule = (
        f'5b. "source_date" MUST be set to "{src_date_str}" on every atom (the source\'s publication date — verbatim, no inference). This is required for the /evolve skill.\n'
        if src_date_str
        else '5b. "source_date" — omit this field. The source has no known publication date.\n'
    )
    src_date_example = (
        f'"source_date": "{src_date_str}",\n    '
        if src_date_str
        else ""
    )

    prompt = f"""Extract atomic insights from this content about {brain_name}.

SOURCE: {src_title} ({src_type})
URL: {src_url}
{src_date_line}
CONTENT:
{content}
{diar_note}
YOUR TASK: Extract 8-15 high-quality atoms — discrete units of knowledge — from this source. Each atom should capture a distinct insight, story, framework, or position from {first_name}.

RULES:
1. Every atom MUST be grounded in the actual content above. Do NOT invent.
2. "original_quote" must be {first_name}'s ACTUAL words from the content (verbatim or near-verbatim). If only paraphrased in the source, use the closest direct quote you can find. If nothing direct exists, omit the field rather than fabricate.
3. "content" is your distilled 2-4 sentence statement of the insight.
4. "implication" is the "so what" — what this means for builders/creators/leaders today.
5. "source_ref" should reference the source title.
{src_date_rule}6. "source_type" should be: {src_type}
7. Set confidence: 0.95 for direct quotes, 0.85 for clear positions, 0.75 for inferred views.
8. Assign 2-5 topic tags per atom.
9. Pick the best-fit cluster from the list below.
10. If the content is too thin, off-topic, or not actually about {first_name}, return [].

AVAILABLE CLUSTERS:
{cluster_list}

OUTPUT FORMAT — Return ONLY a JSON array:
[
  {{
    "content": "Distilled 2-4 sentence insight...",
    "original_quote": "{first_name}'s actual documented words from the source...",
    "implication": "What this means for builders/leaders today...",
    "cluster": "cluster_key",
    "topics": ["topic1", "topic2"],
    "confidence": 0.92,
    "source_type": "{src_type}",
    "source_ref": "{src_title}",
    {src_date_example}"source_url": "{src_url}"
  }}
]

Return ONLY the JSON array."""

    try:
        result = call_claude(
            client, model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8000,
            parse_json=True,
            cost_tracker=cost_tracker,
            label=f"text_atoms_{src_type}",
        )
    except Exception as e:
        warn(f"Atom extraction failed for {src_title[:40]}: {e}")
        return []

    atoms = result.get("parsed", [])
    if not isinstance(atoms, list):
        return []
    # Stamp the source URL on each atom
    for a in atoms:
        a.setdefault("source_url", src_url)
    return atoms


def raw_source_filename(source: dict) -> str:
    """Stable filename for source/raw/ entries: slug(title)_sha8(url).md.
    Stable across re-runs so backfill + builds don't duplicate."""
    title = source.get("title", "untitled")
    url = source.get("url", "")
    title_slug = slugify(title)[:60] or "untitled"
    url_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{title_slug}_{url_hash}.md"


def persist_raw_text(
    brain_dir: Path, source: dict, markdown: str, scraped_at: Optional[str] = None
) -> Path:
    """Write raw scraped markdown to source/raw/ and append to _index.json.
    Idempotent — same source URL maps to same filename.
    Returns the path written.
    """
    raw_dir = brain_dir / "source" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    filename = raw_source_filename(source)
    fp = raw_dir / filename
    fp.write_text(markdown, encoding="utf-8")

    index_path = raw_dir / "_index.json"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    except Exception:
        index = {}
    index[source.get("url", "")] = {
        "filename": filename,
        "title": source.get("title", ""),
        "type": source.get("type", ""),
        "priority": source.get("priority", ""),
        "scraped_at": scraped_at or datetime.now(timezone.utc).isoformat(),
        "char_count": len(markdown),
    }
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
    return fp


def scrape_text_sources(
    brain_json: dict,
    brain_dir: Path,
    sources_json: dict,
    client: "anthropic.Anthropic",
    cost_tracker: CostTracker,
    model: str = DEFAULT_MODEL,
    dry_run: bool = False,
) -> int:
    """Scrape text URLs (essays, articles, interviews, profiles, podcasts) via Firecrawl
    and extract atoms with Claude. Returns count of atoms generated. Idempotent: skips
    if research/text-atoms.json already exists."""
    research_dir = brain_dir / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    text_atoms_path = research_dir / "text-atoms.json"

    # Idempotent skip
    if text_atoms_path.exists():
        with open(text_atoms_path) as f:
            existing = json.load(f)
        success(f"text-atoms.json exists ({len(existing)} atoms) — skipping scrape")
        return len(existing)

    # Filter scrapeable sources
    text_sources = []
    for s in sources_json.get("sources", []):
        if s.get("youtube_id"):
            continue
        url = s.get("url", "")
        if not url.startswith("http"):
            continue
        if any(d in url for d in SCRAPE_SKIP_DOMAINS):
            continue
        text_sources.append(s)

    if not text_sources:
        step("No text sources to scrape")
        return 0

    if dry_run:
        step(f"[DRY RUN] Would scrape {len(text_sources)} text sources via Firecrawl")
        return 0

    firecrawl_key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not firecrawl_key:
        warn("FIRECRAWL_API_KEY not set — skipping text source scraping")
        return 0

    step(f"Scraping {len(text_sources)} text sources via Firecrawl (5 workers)...")
    all_atoms = []
    scraped_count = 0
    skipped_thin = 0
    failed_scrape = 0

    def _process_one(i_source):
        """Scrape one URL + persist raw + extract atoms. Returns a tuple the
        outer loop can fold back into counters. Runs in a worker thread."""
        i, source = i_source
        url = source["url"]
        title = source.get("title", "")[:60]

        try:
            resp = httpx.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {firecrawl_key}",
                    "Content-Type": "application/json",
                },
                json={"url": url, "formats": ["markdown"]},
                timeout=SCRAPE_TIMEOUT_SEC,
            )
            if resp.status_code != 200:
                return i, "failed", title, [], f"scrape failed ({resp.status_code})"

            data = resp.json()
            markdown = (data.get("data") or {}).get("markdown", "")
            if not markdown or len(markdown) < SCRAPE_MIN_CHARS:
                return i, "thin", title, [], f"too thin ({len(markdown)} chars)"

            if len(markdown) > SCRAPE_MAX_CHARS:
                markdown = markdown[:SCRAPE_MAX_CHARS] + "\n\n[...truncated]"

            # Persist truncated markdown to source/raw/ for audit corpus +
            # reproducibility. The provenance verifier (Phase 2.3b) reads
            # from here, so this MUST happen before atom extraction.
            try:
                persist_raw_text(brain_dir, source, markdown)
            except Exception as e:
                warn(f"persist_raw_text failed for {url}: {e}")

            atoms = extract_atoms_from_text(
                brain_json, source, markdown, client, cost_tracker, model
            )
            return i, "ok", title, atoms, f"{len(atoms)} atoms"

        except Exception as e:
            return i, "failed", title, [], f"error: {e}"

    from concurrent.futures import ThreadPoolExecutor, as_completed

    completed = 0
    results = []  # (i, atoms) for status=="ok"; sorted later to preserve source order
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_process_one, (i, s)): i for i, s in enumerate(text_sources, 1)}
        for fut in as_completed(futures):
            i, status, title, atoms, msg = fut.result()
            completed += 1
            print(f"  [{completed}/{len(text_sources)}] {title}... {msg}", flush=True)
            if status == "ok":
                scraped_count += 1
                results.append((i, atoms))
            elif status == "thin":
                skipped_thin += 1
            else:
                failed_scrape += 1

    # Preserve original source order in the saved atoms file so manual review +
    # downstream tooling (e.g. extract-by-source dashboards) stay stable.
    results.sort(key=lambda x: x[0])
    for _, atoms in results:
        all_atoms.extend(atoms)

    if all_atoms:
        with open(text_atoms_path, "w") as f:
            json.dump(all_atoms, f, indent=2)
        success(
            f"Saved {len(all_atoms)} atoms from {scraped_count}/{len(text_sources)} text sources"
            f" (thin: {skipped_thin}, failed: {failed_scrape})"
        )
    else:
        warn(
            f"No atoms extracted from {len(text_sources)} text sources"
            f" (thin: {skipped_thin}, failed: {failed_scrape})"
        )

    return len(all_atoms)


# =============================================================================
# QUOTE VERIFIER (corpus grounding)
# =============================================================================

# Mirrors audit-brains.py: lowercase + whitespace collapse + 35-char signature
# Use the same algorithm so verifier-passes == audit-passes.
_QUOTE_SIG_LEN = 35


def _normalize_corpus_text(s: str) -> str:
    """Match audit-brains.normalize_text exactly so substrings line up."""
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _quote_signature(quote: str) -> str:
    """Match audit-brains.quote_signature exactly: middle 35-char substring."""
    n = _normalize_corpus_text(quote)
    if len(n) <= _QUOTE_SIG_LEN:
        return n
    return n[10 : 10 + _QUOTE_SIG_LEN]


def _load_verification_corpus(brain_dir: Path) -> str:
    """Concat YouTube transcripts + scraped raw text into one normalized blob.

    Same sources audit-brains uses for provenance scoring, so the verifier and
    the auditor agree on what counts as grounded. Atom-pool fallback is NOT
    included on purpose — round-trip self-grounding would defeat the check.
    """
    parts = []

    transcripts_dir = brain_dir / "source" / "transcripts"
    if transcripts_dir.exists():
        for tp in sorted(transcripts_dir.glob("*.json")):
            try:
                d = json.loads(tp.read_text(encoding="utf-8"))
            except Exception:
                continue
            ft = d.get("full_text") or ""
            if ft:
                parts.append(ft)

    raw_dir = brain_dir / "source" / "raw"
    if raw_dir.exists():
        for rp in sorted(raw_dir.glob("*.md")):
            try:
                parts.append(rp.read_text(encoding="utf-8"))
            except Exception:
                continue

    return _normalize_corpus_text(" ".join(parts))


def verify_quotes_against_corpus(brain_dir: Path) -> dict:
    """Strip unverified original_quote values from research/all-atoms.json.

    Each atom's quote is substring-matched against the merged corpus (YouTube
    transcripts + Firecrawl-scraped markdown). Quotes that don't match are
    set to None in-place. Atoms keep their content + implication regardless —
    only the unfounded voice attribution is removed.

    Returns: {"checked": N, "kept": K, "stripped": S, "no_quote": Q}.
    Safe no-op if all-atoms.json doesn't exist (e.g., dry-run, early failure).
    """
    atoms_path = brain_dir / "research" / "all-atoms.json"
    if not atoms_path.exists():
        return {"checked": 0, "kept": 0, "stripped": 0, "no_quote": 0}

    try:
        atoms = json.loads(atoms_path.read_text(encoding="utf-8"))
    except Exception as e:
        warn(f"Quote verifier could not parse all-atoms.json: {e}")
        return {"checked": 0, "kept": 0, "stripped": 0, "no_quote": 0}

    corpus = _load_verification_corpus(brain_dir)
    if not corpus:
        # No corpus to verify against — strip all quotes; we cannot prove any.
        # Better to ship with no quotes than fabricated ones.
        stripped = 0
        no_quote = 0
        for a in atoms:
            if a.get("original_quote"):
                a["original_quote"] = None
                stripped += 1
            else:
                no_quote += 1
        atoms_path.write_text(json.dumps(atoms, indent=2), encoding="utf-8")
        warn(f"No source corpus found — stripped all {stripped} quotes")
        return {"checked": len(atoms), "kept": 0, "stripped": stripped, "no_quote": no_quote}

    kept = 0
    stripped = 0
    no_quote = 0
    for a in atoms:
        q = a.get("original_quote")
        if not q:
            no_quote += 1
            continue
        sig = _quote_signature(q)
        if sig and sig in corpus:
            kept += 1
        else:
            a["original_quote"] = None
            stripped += 1

    atoms_path.write_text(json.dumps(atoms, indent=2), encoding="utf-8")
    return {
        "checked": len(atoms),
        "kept": kept,
        "stripped": stripped,
        "no_quote": no_quote,
    }


def phase_2_ingest(
    brain_json: dict,
    brain_dir: Path,
    slug: str,
    client: "anthropic.Anthropic",
    cost_tracker: CostTracker,
    reference_slug: str = "scott-belsky",
    model: str = DEFAULT_MODEL,
    target_atoms: int = TARGET_ATOMS,
    dry_run: bool = False,
) -> dict:
    """Download transcripts, scrape articles, generate atoms, upload to Supabase."""
    phase_header(2)

    research_dir = brain_dir / "research"
    research_dir.mkdir(parents=True, exist_ok=True)

    # --- 2.1 YouTube transcripts ---
    step("Ingesting YouTube transcripts...")
    sources_path = brain_dir / "source" / "sources.json"
    sources_json = {}
    if sources_path.exists():
        with open(sources_path) as f:
            sources_json = json.load(f)

    videos = [s for s in sources_json.get("sources", []) if s.get("youtube_id")]
    if videos and not dry_run:
        # Use build-brain's stage_youtube directly
        yt_result = build_brain.stage_youtube(brain_json, brain_dir, model, dry_run=dry_run)
        if yt_result:
            success("YouTube transcripts processed")
        else:
            warn("YouTube stage returned False — some transcripts may have failed")
    elif videos:
        step(f"[DRY RUN] Would process {len(videos)} YouTube videos")
    else:
        step("No YouTube sources found — skipping")

    # --- 2.2 Text source scraping (essays, profiles, interviews, podcast pages) ---
    step("Scraping text sources via Firecrawl...")
    scrape_text_sources(
        brain_json, brain_dir, sources_json, client, cost_tracker, model, dry_run=dry_run
    )

    # --- 2.3 Deep research atoms ---
    step("Generating deep research atoms...")
    if not dry_run:
        gen_result = build_brain.stage_generate(
            brain_json, brain_dir, reference_slug, model, dry_run=dry_run
        )
        if gen_result:
            success("Deep research atoms generated")
        else:
            warn("Atom generation had issues")
    else:
        clusters = brain_json.get("clusters", {})
        step(f"[DRY RUN] Would generate atoms for {len(clusters)} clusters")

    # --- 2.3 Merge ---
    step("Merging all atoms...")
    if not dry_run:
        merge_result = build_brain.stage_merge(brain_json, brain_dir, dry_run=dry_run)
    else:
        step("[DRY RUN] Would merge all atom files")

    # --- 2.3b Verify quotes against source corpus ---
    # Strips original_quote values that aren't substring-grounded in scraped MD
    # or YouTube transcripts. Prevents Phase 3 synthesis (and Supabase upload
    # below) from ever seeing fabricated quotes.
    if not dry_run:
        step("Verifying quote provenance against source corpus...")
        vr = verify_quotes_against_corpus(brain_dir)
        if vr["checked"] == 0:
            warn("No atoms to verify (skipped)")
        else:
            kept_pct = round(100 * vr["kept"] / max(vr["checked"], 1), 1)
            success(
                f"Quote verifier: kept {vr['kept']} / stripped {vr['stripped']} "
                f"/ no-quote {vr['no_quote']} of {vr['checked']} atoms ({kept_pct}% have verified quotes)"
            )
            if vr["stripped"]:
                step(
                    f"Stripped quotes are fabrications — kept the atoms (content + implication)"
                )
    else:
        step("[DRY RUN] Would verify quote provenance against corpus")

    # --- 2.4 Upload to Supabase ---
    all_atoms_path = research_dir / "all-atoms.json"
    # Self-heal: if Phase 1 ran before the table-creation fix (or tables got dropped),
    # ensure tables exist now rather than silently 404-ing every batch.
    if all_atoms_path.exists() and not dry_run and not brain_json.get("_supabase_tables_ready"):
        if ensure_supabase_tables(slug, brain_json.get("brain_name", slug), brain_json):
            brain_json["_supabase_tables_ready"] = True
    if all_atoms_path.exists() and not dry_run and brain_json.get("_supabase_tables_ready"):
        step("Uploading atoms to Supabase...")
        try:
            with open(all_atoms_path) as f:
                atoms = json.load(f)

            us = underscore_slug(slug)
            table = f"{us}_atoms"
            url = get_supabase_url()
            headers = get_supabase_rest_headers()

            # Map atoms to DB schema (reuses upload-atoms.py logic)
            rows = []
            for a in atoms:
                row = {
                    "content": a["content"],
                    "original_quote": a.get("original_quote"),
                    "implication": a.get("implication"),
                    "cluster": a.get("cluster"),
                    "topics": a.get("topics", []),
                    "source_ref": a.get("source_ref"),
                    "confidence": a.get("confidence", 0.8),
                    "confidence_tier": a.get("confidence_tier", "medium"),
                }
                sd = a.get("source_date")
                row["source_date"] = None
                if sd:
                    sd_str = str(sd).strip()
                    if len(sd_str) == 4 and sd_str.isdigit():
                        row["source_date"] = f"{sd_str}-01-01T00:00:00Z"
                    elif len(sd_str) == 7 and sd_str[4] == "-" and sd_str[:4].isdigit() and sd_str[5:7].isdigit():
                        row["source_date"] = f"{sd_str}-01T00:00:00Z"
                    elif len(sd_str) == 10 and sd_str[4] == "-" and sd_str[7] == "-":
                        row["source_date"] = f"{sd_str}T00:00:00Z"
                    elif "T" in sd_str:
                        row["source_date"] = sd_str
                rows.append(row)

            batch_size = 50
            uploaded = 0
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                resp = httpx.post(
                    f"{url}/rest/v1/{table}",
                    headers=headers,
                    json=batch,
                    timeout=30,
                )
                if resp.status_code in (200, 201):
                    uploaded += len(batch)
                else:
                    warn(f"Upload batch error: {resp.status_code} {resp.text[:200]}")

            if uploaded == len(rows):
                success(f"Uploaded {uploaded}/{len(rows)} atoms to {table}")
            elif uploaded == 0:
                warn(f"ORPHANED: 0/{len(rows)} atoms reached {table} — brain is NOT in Supabase")
                brain_json["_supabase_tables_ready"] = False
            else:
                warn(f"PARTIAL: only {uploaded}/{len(rows)} atoms reached {table}")
        except Exception as e:
            warn(f"Supabase upload failed: {e}")
            warn("Atoms are saved locally — you can upload manually later")
    elif all_atoms_path.exists() and not dry_run:
        warn(f"Skipped atom upload — Supabase tables for {slug} are not ready (pack still ships)")

    # --- 2.5 Gap check ---
    if all_atoms_path.exists() and not dry_run:
        with open(all_atoms_path) as f:
            atoms = json.load(f)

        cluster_counts = Counter(a.get("cluster", "unknown") for a in atoms)
        thin_clusters = [c for c, n in cluster_counts.items() if n < MIN_ATOMS_PER_CLUSTER]

        if thin_clusters:
            warn(f"{len(thin_clusters)} thin clusters (<{MIN_ATOMS_PER_CLUSTER} atoms): {thin_clusters}")
            step("Running supplemental research on thin clusters...")
            exemplars = build_brain.load_exemplar_atoms(reference_slug)
            for cluster_key in thin_clusters:
                cluster_info = brain_json.get("clusters", {}).get(cluster_key)
                if not cluster_info:
                    continue
                try:
                    step(f"  Supplementing {cluster_key}...")
                    new_atoms = build_brain.generate_cluster_atoms(
                        brain_json, cluster_key, cluster_info, exemplars, sources_json, model
                    )
                    # Save supplemental atoms
                    supp_path = research_dir / f"{cluster_key.replace('_', '-')}-supplemental-atoms.json"
                    with open(supp_path, "w") as f:
                        json.dump(new_atoms, f, indent=2)
                    success(f"  +{len(new_atoms)} atoms for {cluster_key}")
                    time.sleep(2)
                except Exception as e:
                    warn(f"  Supplemental generation failed for {cluster_key}: {e}")

            # Re-merge after supplemental
            step("Re-merging with supplemental atoms...")
            build_brain.stage_merge(brain_json, brain_dir)

        # Reload after potential supplemental + remerge
        with open(all_atoms_path) as f:
            atoms = json.load(f)
        atom_count = len(atoms)
        step(f"Total atoms: {atom_count} (target: {target_atoms})")
    else:
        atom_count = 0

    return {"atom_count": atom_count}


# =============================================================================
# PHASE 3: SYNTHESIS
# =============================================================================

# Stable template — 8 skill names + canonical titles + descriptions used across all
# brains (matches scott-belsky and the 9 customer-facing skill files in pack/skills/).
# Only the per-brain "example" is dynamic: pulled from brain_json["skill_examples"].
SKILL_TEMPLATE = [
    ("advise",   "Strategic Counsel",            "Get advice on decisions grounded in this brain's frameworks."),
    ("teach",    "Learn Through Their Lens",     "Explain a concept using this brain's actual vocabulary and mental models."),
    ("debate",   "Steel-Man Both Sides",         "Present a position or pit two ideas against each other; brain argues the counterpoint."),
    ("connect",  "Bridge Ideas",                 "Find unexpected connections between concepts or synthesize multiple ideas into something new."),
    ("evolve",   "Intellectual Evolution",       "Trace how this brain's thinking on a topic developed over time."),
    ("surprise", "Show Me Something Unexpected", "Random high-quality atom for daily inspiration."),
    ("coach",    "Socratic Questions",           "No answers — just the questions this thinker would ask you."),
    ("predict",  "Implication Chains",           "Trace the second and third-order effects of a trend or decision."),
]


def build_synthesis_skills(brain_json: dict) -> list:
    """Build the synthesis.skills array programmatically from skill_examples.
    Skills are template-able — only the example string varies per brain."""
    examples = brain_json.get("skill_examples", {}) or {}
    skills = []
    for name, title, desc in SKILL_TEMPLATE:
        ex = examples.get(name, "").strip()
        if name == "surprise":
            # /surprise takes no args. Even if skill_examples[surprise] has a hint
            # like "No input needed", we don't render it as a fake argument.
            ex_str = "/surprise"
        elif ex.startswith("/"):
            ex_str = ex
        elif ex:
            ex_str = f'/{name} "{ex}"'
        else:
            ex_str = f"/{name}"
        skills.append({
            "name": name,
            "title": title,
            "desc": desc,
            "example": ex_str,
        })
    return skills


def phase_3_synthesize(
    brain_json: dict,
    brain_dir: Path,
    person_name: str,
    client: "anthropic.Anthropic",
    cost_tracker: CostTracker,
    reference_slug: str = "scott-belsky",
    model: str = SYNTHESIS_MODEL,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    """Generate synthesis.md and update brain.json synthesis section."""
    phase_header(3)

    synthesis_path = brain_dir / "synthesis.md"
    all_atoms_path = brain_dir / "research" / "all-atoms.json"

    if synthesis_path.exists() and not force:
        success(f"synthesis.md already exists ({synthesis_path})")
        return {"synthesis_exists": True}
    elif synthesis_path.exists() and force:
        backup_path = synthesis_path.with_suffix(".md.bak")
        shutil.copy2(synthesis_path, backup_path)
        step(f"Backed up existing synthesis.md to {backup_path.name}")

    if not all_atoms_path.exists():
        error("all-atoms.json not found — run Phase 2 first")
        return {"error": "no atoms"}

    if dry_run:
        step("[DRY RUN] Would generate synthesis.md via LLM")
        return {}

    # Load atoms
    with open(all_atoms_path) as f:
        atoms = json.load(f)

    # Group by cluster and format
    by_cluster = defaultdict(list)
    for atom in atoms:
        by_cluster[atom.get("cluster", "unknown")].append(atom)

    atoms_text_parts = []
    for cluster, cluster_atoms in sorted(by_cluster.items()):
        cluster_name = brain_json.get("clusters", {}).get(cluster, {}).get("name", cluster)
        atoms_text_parts.append(f"\n### {cluster_name} ({len(cluster_atoms)} atoms)")
        # Include top atoms per cluster (by confidence)
        sorted_atoms = sorted(cluster_atoms, key=lambda a: a.get("confidence", 0.8), reverse=True)
        for a in sorted_atoms[:20]:  # Cap per cluster to fit context
            content = a.get("content", "")
            quote = a.get("original_quote", "")
            atoms_text_parts.append(f"- {content}")
            if quote:
                atoms_text_parts.append(f"  > \"{quote}\"")

    atoms_by_cluster = "\n".join(atoms_text_parts)

    # Load exemplar synthesis
    exemplar_path = BRAINS_DIR / reference_slug / "synthesis.md"
    exemplar_synthesis = ""
    if exemplar_path.exists():
        with open(exemplar_path) as f:
            exemplar_synthesis = f.read()

    # Draft synthesis from brain.json
    draft = json.dumps(brain_json.get("synthesis", {}), indent=2)

    # --- Generate synthesis.md ---
    step(f"Generating synthesis.md via {model} ({len(atoms)} atoms as context)...")

    prompt = SYNTHESIS_PROMPT.format(
        person_name=person_name,
        atom_count=len(atoms),
        exemplar_synthesis=exemplar_synthesis[:6000],  # Trim to fit context
        draft_synthesis=draft[:3000],
        atoms_by_cluster=atoms_by_cluster[:40000],  # Large context
    )

    result = call_claude(
        client, model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8192,
        cost_tracker=cost_tracker,
        label="synthesis_gen",
    )

    synthesis_md = result["content"]
    with open(synthesis_path, "w") as f:
        f.write(synthesis_md)
    success(f"synthesis.md written ({len(synthesis_md)} chars)")

    # --- Update brain.json synthesis section ---
    step("Extracting structured synthesis for brain.json...")

    json_prompt = SYNTHESIS_JSON_PROMPT.format(
        person_name=person_name,
        synthesis_md=synthesis_md[:10000],
    )

    json_result = call_claude(
        client, DEFAULT_MODEL,
        messages=[{"role": "user", "content": json_prompt}],
        max_tokens=6144,
        parse_json=True,
        cost_tracker=cost_tracker,
        label="synthesis_json",
    )

    if json_result.get("parsed"):
        synthesis_data = json_result["parsed"]
        # Skills are template-able — generate programmatically from skill_examples
        # rather than relying on the LLM (which used to copy the empty existing array).
        synthesis_data["skills"] = build_synthesis_skills(brain_json)
        brain_json["synthesis"] = synthesis_data

        brain_json_path = brain_dir / "brain.json"
        with open(brain_json_path, "w") as f:
            json.dump(brain_json, f, indent=2)
        success(f"brain.json synthesis section updated ({len(synthesis_data['skills'])} skills)")

    return {"synthesis_written": True}


# =============================================================================
# PHASE 4: ENRICHMENT
# =============================================================================

def phase_4_enrich(
    brain_json: dict,
    brain_dir: Path,
    slug: str,
    client: "anthropic.Anthropic",
    cost_tracker: CostTracker,
    model: str = DEFAULT_MODEL,
    dry_run: bool = False,
) -> dict:
    """Voice enrichment + connection discovery, all auto-applied."""
    phase_header(4)

    # --- 4.1 Connection discovery (local, then LLM) ---
    step("Discovering connections...")
    if not dry_run:
        conn_result = build_brain.stage_connections(brain_json, brain_dir, model, dry_run=dry_run)
        if conn_result:
            success("Connections discovered")
        else:
            warn("Connection discovery had issues")
    else:
        step("[DRY RUN] Would discover connections")

    # --- 4.2 Upload connections to Supabase ---
    connections_path = brain_dir / "research" / "connections.json"
    if connections_path.exists() and not dry_run:
        step("Uploading connections to Supabase...")
        try:
            with open(connections_path) as f:
                connections = json.load(f)

            # We need atom IDs that exist in Supabase. Since we uploaded atoms
            # in Phase 2, we need to map local UUIDs to Supabase UUIDs.
            # The simplest approach: fetch atom IDs from Supabase by content hash.
            us = underscore_slug(slug)
            table = f"{us}_connections"
            url = get_supabase_url()
            headers = get_supabase_rest_headers()

            # First, get atom ID mapping from Supabase
            atoms_table = f"{us}_atoms"
            resp = httpx.get(
                f"{url}/rest/v1/{atoms_table}?select=id,content",
                headers={
                    "apikey": os.environ.get("SUPABASE_SERVICE_KEY", ""),
                    "Authorization": f"Bearer {os.environ.get('SUPABASE_SERVICE_KEY', '')}",
                },
                timeout=30,
            )

            if resp.status_code == 200:
                db_atoms = resp.json()
                # Map content → DB id for matching
                content_to_db_id = {}
                for a in db_atoms:
                    # Use first 100 chars of content as key
                    key = a["content"][:100]
                    content_to_db_id[key] = a["id"]

                # Load local atoms to map local ID → content
                all_atoms_path = brain_dir / "research" / "all-atoms.json"
                if all_atoms_path.exists():
                    with open(all_atoms_path) as f:
                        local_atoms = json.load(f)
                    local_id_to_content = {a["id"]: a["content"][:100] for a in local_atoms}

                    # Build local ID → DB ID mapping
                    local_to_db = {}
                    for local_id, content_key in local_id_to_content.items():
                        if content_key in content_to_db_id:
                            local_to_db[local_id] = content_to_db_id[content_key]

                    # Map connections to DB IDs
                    db_connections = []
                    for c in connections:
                        db_id_1 = local_to_db.get(c["atom_id_1"])
                        db_id_2 = local_to_db.get(c["atom_id_2"])
                        if db_id_1 and db_id_2:
                            db_connections.append({
                                "atom_id_1": db_id_1,
                                "atom_id_2": db_id_2,
                                "relationship": c["relationship"],
                                "confidence": c.get("confidence", 0.8),
                            })

                    # Upload in batches
                    uploaded = 0
                    for i in range(0, len(db_connections), 50):
                        batch = db_connections[i:i + 50]
                        resp = httpx.post(
                            f"{url}/rest/v1/{table}",
                            headers=headers,
                            json=batch,
                            timeout=30,
                        )
                        if resp.status_code in (200, 201):
                            uploaded += len(batch)
                        # Ignore conflicts (duplicates)

                    success(f"Uploaded {uploaded}/{len(db_connections)} connections to {table}")
                else:
                    warn("Cannot map connections — all-atoms.json not found")
            else:
                warn(f"Cannot fetch atom IDs from Supabase: {resp.status_code}")
        except Exception as e:
            warn(f"Connection upload failed: {e}")

    # Count results
    all_atoms_path = brain_dir / "research" / "all-atoms.json"
    atom_count = 0
    connection_count = 0
    if all_atoms_path.exists():
        with open(all_atoms_path) as f:
            atom_count = len(json.load(f))
    if connections_path.exists():
        with open(connections_path) as f:
            connection_count = len(json.load(f))

    step(f"Result: {atom_count} atoms, {connection_count} connections")
    return {"atom_count": atom_count, "connection_count": connection_count}


# =============================================================================
# PHASE 5: EXPORT & QA
# =============================================================================

def embed_and_check_parity(slug: str, brain_dir: Path) -> dict:
    """Phase-5 finalizer: generate embeddings (non-destructive fill) and assert
    pack<->Supabase parity.

    Addresses two audit defects:
      - "embeddings are never generated" — loops the embed-brain edge function so
        every uploaded atom gets a 1536-dim vector (semantic search / board RPC).
      - "pack <-> Supabase divergence" — compares pack atom count to the live DB
        count and flags loudly when the two sources of truth disagree.

    Best-effort and never raises: embeddings depend on an external API, so a blip
    must not fail an otherwise-good build. The hard backstop is the taste gate —
    builds stay 'hidden' until a human promotes, so a parity warning is seen
    before anything goes live. Run finalize-supabase.py to reconcile a mismatch.
    """
    us = underscore_slug(slug)
    url = get_supabase_url()
    headers = get_supabase_rest_headers()
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    pack = brain_dir / "pack" / "brain-atoms.json"
    pack_count = len(json.loads(pack.read_text()).get("atoms", [])) if pack.exists() else 0

    embedded_total = 0
    try:
        step("Generating embeddings (embed-brain)...")
        for _ in range(60):
            r = httpx.post(f"{url}/functions/v1/embed-brain",
                           headers={"Authorization": f"Bearer {key}", "apikey": key,
                                    "Content-Type": "application/json"},
                           json={"table": f"{us}_atoms", "limit": 200}, timeout=300)
            if r.status_code != 200:
                warn(f"embed-brain HTTP {r.status_code}: {r.text[:120]} — embeddings incomplete")
                break
            n = r.json().get("embedded", 0)
            embedded_total += n
            if n == 0:
                break
            time.sleep(1)
    except Exception as e:
        warn(f"embedding step failed (non-fatal): {e}")

    db_count = -1
    try:
        r = httpx.get(f"{url}/rest/v1/{us}_atoms?select=id",
                      headers={**headers, "Prefer": "count=exact", "Range": "0-0"}, timeout=60)
        db_count = int(r.headers.get("content-range", "*/0").split("/")[-1])
    except Exception as e:
        warn(f"parity check failed: {e}")

    parity_ok = (db_count == pack_count and pack_count > 0)
    if not parity_ok:
        warn(f"PACK<->DB PARITY MISMATCH: pack={pack_count}, db={db_count} ({us}_atoms). "
             f"Two sources of truth disagree — run: "
             f"python3 scripts/finalize-supabase.py --brain {slug}")
    else:
        success(f"pack<->DB parity OK ({pack_count} atoms); embeddings filled (+{embedded_total})")
    return {"embedded": embedded_total, "db_atoms": db_count,
            "pack_atoms": pack_count, "parity_ok": parity_ok}


def phase_5_export_qa(
    brain_json: dict,
    brain_dir: Path,
    slug: str,
    dry_run: bool = False,
    client=None,
    cost_tracker: "CostTracker" = None,
) -> dict:
    """Export pack, run audit, remediate if needed."""
    phase_header(5)

    if dry_run:
        step("[DRY RUN] Would run export + audit + semantic fact-check")
        return {"score": 0}

    # --- 5.1 Generate synthesis.md from brain.json if not exists ---
    # (stage_synthesis just writes the .md from brain.json data)
    build_brain.stage_synthesis(brain_json, brain_dir, dry_run=dry_run)

    # --- 5.2 Export ---
    step("Running export pipeline...")
    export_ok = build_brain.stage_export(brain_json, brain_dir, dry_run=dry_run)
    if export_ok:
        success("Pack exported")
    else:
        error("Export failed")
        return {"score": 0, "error": "export_failed"}

    # --- 5.3 Update index ---
    build_brain.stage_update_index(brain_json, brain_dir, dry_run=dry_run)

    # --- 5.3.5 Semantic fact-check (authoritative synthesis grounding) ---
    # Runs BEFORE the audit so audit-brains.check_synthesis_grounding picks up the
    # fact-check JSON and reports the semantic score instead of the lexical fallback.
    # Non-fatal: a fact-check failure must not block a build (the lexical fallback
    # still produces a usable score).
    if client is not None and cost_tracker is not None:
        step("Running semantic fact-check (synthesis grounding)...")
        try:
            fact_check = importlib.import_module("fact-check-brain")
            sc = fact_check.fact_check_brain(slug, client, cost_tracker)
            if sc:
                totals = sc.get("totals", {})
                success(f"Fact-check grounding: {sc.get('grounding_pct', 0)}% "
                        f"({totals.get('grounded', 0)}/{totals.get('total', 0)} grounded, "
                        f"{totals.get('weak', 0)} weak)")
            else:
                warn("Fact-check produced no scorecard (no corpus or no principles) "
                     "— audit will use lexical grounding fallback")
        except Exception as e:
            warn(f"Fact-check failed (non-fatal): {e} — audit will use lexical fallback")
    else:
        warn("Fact-check skipped — no Anthropic client passed to phase 5")

    # --- 5.4 Audit ---
    step("Running quality audit...")
    try:
        audit_brains = importlib.import_module("audit-brains")
        index_path = BRAINS_DIR / "index.json"
        with open(index_path) as f:
            index_data = json.load(f)

        audit = audit_brains.audit_brain(slug, index_data)
        score = audit.completeness_score

        c = COLORS
        grade_color = c["green"] if score >= 70 else c["yellow"] if score >= 50 else c["red"]
        print(f"\n  {c['bold']}Audit Score: {grade_color}{score}/100{c['reset']}")

        if audit.errors:
            print(f"  Errors: {len(audit.errors)}")
            for issue in audit.errors[:5]:
                print(f"    {c['red']}{issue.message}{c['reset']}")
        if audit.warnings:
            print(f"  Warnings: {len(audit.warnings)}")
            for issue in audit.warnings[:5]:
                print(f"    {c['yellow']}{issue.message}{c['reset']}")

        # --- 5.5 Remediation loop ---
        cycles = 0
        while score < MIN_AUDIT_SCORE and cycles < MAX_REMEDIATION_CYCLES:
            cycles += 1
            warn(f"Score {score} < {MIN_AUDIT_SCORE} — remediation cycle {cycles}/{MAX_REMEDIATION_CYCLES}")

            # Re-export (sometimes fixes structural issues)
            build_brain.stage_export(brain_json, brain_dir)
            build_brain.stage_update_index(brain_json, brain_dir)

            # Re-audit
            audit = audit_brains.audit_brain(slug, index_data)
            score = audit.completeness_score
            step(f"Post-remediation score: {score}/100")

        # --- 5.6 Quote-provenance guardrail ---
        # If quote provenance is below the floor, re-run the verifier (catches
        # any quotes added between Phase 2 and Phase 5, e.g. by synthesis or
        # manual edits), re-export, re-audit. Then enforce the floor.
        provenance_pct = audit.stats.get("provenance_pct", 0.0) if hasattr(audit, "stats") else 0.0
        quoted_atoms = audit.stats.get("quoted_atoms", 0) if hasattr(audit, "stats") else 0

        if quoted_atoms > 0 and provenance_pct < MIN_QUOTE_PROVENANCE:
            warn(
                f"Quote provenance {provenance_pct}% < {MIN_QUOTE_PROVENANCE}% floor "
                f"({quoted_atoms} quoted atoms) — re-running verifier"
            )
            vr = verify_quotes_against_corpus(brain_dir)
            step(
                f"Verifier stripped {vr['stripped']} unverified quotes "
                f"(kept {vr['kept']}, no-quote {vr['no_quote']})"
            )
            # Re-export so pack/brain-atoms.json reflects the strip, then re-audit.
            build_brain.stage_export(brain_json, brain_dir)
            build_brain.stage_update_index(brain_json, brain_dir)
            audit = audit_brains.audit_brain(slug, index_data)
            score = audit.completeness_score
            provenance_pct = audit.stats.get("provenance_pct", 0.0) if hasattr(audit, "stats") else 0.0
            step(f"Post-verifier score: {score}/100, provenance: {provenance_pct}%")

            # Hard abort if structural score collapsed (e.g. voice enrichment
            # killed by mass strip) OR provenance still under floor (corpus
            # is so thin that even the verifier can't find matches).
            if score < MIN_AUDIT_SCORE or (
                audit.stats.get("quoted_atoms", 0) > 0
                and provenance_pct < MIN_QUOTE_PROVENANCE
            ):
                error(
                    "Brain build BLOCKED — quote provenance cannot meet floor.\n"
                    f"  Score: {score}/100 (floor: {MIN_AUDIT_SCORE})\n"
                    f"  Provenance: {provenance_pct}% (floor: {MIN_QUOTE_PROVENANCE}%)\n"
                    "  Fix: add more source coverage (YouTube videos, essays, "
                    "interview transcripts) to brain.json and re-run with "
                    "--resume-from 2. Better to ship a thinner brain with real "
                    "voice than a fat one with fabricated quotes."
                )

        # --- 5.7 Embeddings + pack<->DB parity (audit defects #2, #3) ---
        fin = embed_and_check_parity(slug, brain_dir)

        return {
            "score": score,
            "errors": len(audit.errors),
            "warnings": len(audit.warnings),
            "provenance_pct": provenance_pct,
            "embedded": fin["embedded"],
            "db_atoms": fin["db_atoms"],
            "pack_atoms": fin["pack_atoms"],
            "parity_ok": fin["parity_ok"],
        }

    except Exception as e:
        warn(f"Audit failed: {e}")
        return {"score": -1, "error": str(e)}


# =============================================================================
# DRY RUN COST ESTIMATE
# =============================================================================

def print_dry_run_estimate(person_name: str, slug: str, brain_dir: Path):
    """Print cost and time estimates without executing."""
    c = COLORS
    print(f"\n{c['bold']}{'=' * 60}")
    print(f"  DRY RUN: {person_name} ({slug})")
    print(f"{'=' * 60}{c['reset']}\n")

    has_sources = (brain_dir / "source" / "sources.json").exists()
    has_brain_json = (brain_dir / "brain.json").exists()
    has_atoms = (brain_dir / "research" / "all-atoms.json").exists()
    has_synthesis = (brain_dir / "synthesis.md").exists()
    has_pack = (brain_dir / "pack" / "brain-atoms.json").exists()

    rows = [
        ("Phase", "Status", "Est. Cost", "Est. Time"),
        ("─" * 25, "─" * 12, "─" * 10, "─" * 12),
        ("0: Source Discovery", "SKIP" if has_sources else "RUN", "$0.05", "30-60s"),
        ("1: Scaffolding", "SKIP" if has_brain_json else "RUN", "$0.40", "2-3 min"),
        ("2: Content Ingestion", "SKIP" if has_atoms else "RUN", "$6.00", "15-30 min"),
        ("3: Synthesis", "SKIP" if has_synthesis else "RUN", "$2.00", "3-5 min"),
        ("4: Enrichment", "RUN", "$15.00", "20-40 min"),
        ("5: Export & QA", "SKIP" if has_pack else "RUN", "$0.00", "2-5 min"),
    ]

    for row in rows:
        print(f"  {row[0]:<25} {row[1]:<12} {row[2]:<10} {row[3]}")

    total_cost = sum(
        float(r[2].replace("$", ""))
        for r in rows[2:]
        if r[1] == "RUN"
    )
    print(f"\n  {c['bold']}Estimated total: ${total_cost:.2f} | ~45-90 minutes{c['reset']}")
    print(f"\n  Existing artifacts:")
    print(f"    sources.json: {'yes' if has_sources else 'no'}")
    print(f"    brain.json:   {'yes' if has_brain_json else 'no'}")
    print(f"    all-atoms:    {'yes' if has_atoms else 'no'}")
    print(f"    synthesis.md: {'yes' if has_synthesis else 'no'}")
    print(f"    pack/:        {'yes' if has_pack else 'no'}")


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fully automated brain pack builder — zero approval gates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/auto-build-brain.py --person "Jensen Huang"
  python scripts/auto-build-brain.py --person "Kara Swisher" --dry-run
  python scripts/auto-build-brain.py --person "Jensen Huang" --resume
  python scripts/auto-build-brain.py --person "Jensen Huang" --resume-from 3

Cost: ~$23-25 per brain | Time: ~45-90 minutes
        """,
    )
    parser.add_argument("--person", required=True, help="Person's full name (e.g., 'Jensen Huang')")
    parser.add_argument("--slug", help="Brain slug (default: derived from name)")
    parser.add_argument("--reference", default="scott-belsky", help="Reference brain for exemplars")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model for generation (default: {DEFAULT_MODEL})")
    parser.add_argument("--synthesis-model", default=SYNTHESIS_MODEL, help=f"Model for synthesis (default: {SYNTHESIS_MODEL})")
    parser.add_argument("--skip-phase", type=int, action="append", default=[], help="Skip a phase (can repeat)")
    parser.add_argument("--resume", action="store_true", help="Resume from last completed phase")
    parser.add_argument("--resume-from", type=int, help="Resume from specific phase number")
    parser.add_argument("--dry-run", action="store_true", help="Show cost estimate without executing")
    parser.add_argument("--max-sources", type=int, default=15, help="Max sources to discover")
    parser.add_argument("--target-atoms", type=int, default=TARGET_ATOMS, help=f"Target atom count (default: {TARGET_ATOMS})")
    parser.add_argument("--min-atoms", type=int, default=MIN_BRAIN_ATOMS, help=f"Hard floor — build halts after Phase 2 if below this (default: {MIN_BRAIN_ATOMS})")
    parser.add_argument("--allow-thin-pack", action="store_true", help="Bypass the min-atoms floor and allow shipping a thin brain")
    parser.add_argument("--force-synthesis", action="store_true", help="Regenerate synthesis.md even if it already exists (backs up existing to .bak)")
    parser.add_argument("--skip-grounding", action="store_true", help="Skip Phase 3.5 synthesis grounding/sourcing")
    parser.add_argument("--skip-hard-lessons", action="store_true", help="Skip Phase 3.6 hard-lessons + receipts mining")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    # Derive slug
    slug = args.slug or slugify(args.person)
    brain_dir = BRAINS_DIR / slug

    # --- Dry run ---
    if args.dry_run:
        print_dry_run_estimate(args.person, slug, brain_dir)
        # Still run phases in dry_run mode to show what would happen
        # but return after estimate for now
        return

    # --- Preflight checks ---
    c = COLORS
    print(f"\n{c['bold']}{'#' * 60}")
    print(f"#  AUTO-BUILD BRAIN: {args.person}")
    print(f"#  Slug: {slug}")
    print(f"#  Model: {args.model}")
    print(f"#  Synthesis model: {args.synthesis_model}")
    print(f"{'#' * 60}{c['reset']}\n")

    # Check API keys
    if not os.environ.get("ANTHROPIC_API_KEY"):
        error("ANTHROPIC_API_KEY not set. Required for LLM calls.")
        sys.exit(1)

    if not HAS_ANTHROPIC:
        error("anthropic SDK not installed: pip install anthropic")
        sys.exit(1)

    if not HAS_HTTPX:
        error("httpx not installed: pip install httpx")
        sys.exit(1)

    # Initialize
    client = anthropic.Anthropic()
    cost_tracker = CostTracker()
    start_time = time.time()

    # --- Resume logic ---
    progress = load_progress(brain_dir)
    start_phase = 0

    if args.resume_from is not None:
        start_phase = args.resume_from
        # Force re-run: clear "complete" status for the explicit resume target AND all
        # subsequent phases so the loop body re-runs them. Re-running Phase 2 with new
        # sources should also re-run Phase 3/4/5 — otherwise synthesis + pack reflect
        # the old (smaller) atom set.
        if not progress:
            # No build-progress.json (e.g. a fresh checkout, or it was never
            # committed). Initialize so --resume-from doesn't crash on None.
            progress = init_progress(args.person, slug)
        for i in range(start_phase, 6):
            if str(i) in progress["phases"]:
                progress["phases"][str(i)] = {"status": "pending"}
        save_progress(brain_dir, progress)
        step(f"Resuming from Phase {start_phase} (forced re-run, cascades to later phases)")
    elif args.resume and progress:
        # Find first non-complete phase
        for i in range(6):
            if progress["phases"].get(str(i), {}).get("status") != "complete":
                start_phase = i
                break
        step(f"Resuming from Phase {start_phase} (last progress loaded)")
    else:
        progress = init_progress(args.person, slug)

    # --- Notify build start ---
    start_label = f"resume from Phase {start_phase}" if start_phase > 0 else "fresh build"
    post_slack(f"Starting brain build: *{args.person}* (`{slug}`) — {start_label}", ":brain:")

    # --- Execute phases ---
    brain_json = None
    sources_data = {}

    for phase_num in range(start_phase, 6):
        if phase_num in args.skip_phase:
            step(f"Skipping Phase {phase_num} (--skip-phase)")
            mark_phase(progress, phase_num, "skipped")
            save_progress(brain_dir, progress)
            continue

        # Check if already complete (for resume)
        if progress["phases"].get(str(phase_num), {}).get("status") == "complete":
            step(f"Phase {phase_num} already complete — skipping")
            continue

        mark_phase(progress, phase_num, "running")
        save_progress(brain_dir, progress)
        post_slack(f"`{slug}` · Phase {phase_num}: {PHASE_NAMES[phase_num]} — running")

        try:
            if phase_num == 0:
                sources_data = phase_0_discover_sources(
                    args.person, slug, brain_dir, client, cost_tracker,
                    max_sources=args.max_sources,
                )
                source_count = len(sources_data.get("sources", []))
                if source_count > 0:
                    mark_phase(progress, 0, "complete", sources_found=source_count)
                else:
                    mark_phase(progress, 0, "failed",
                               sources_found=0,
                               reason="0 sources found — create sources.json manually or check FIRECRAWL_API_KEY")
                    save_progress(brain_dir, progress)
                    error("Phase 0 produced 0 sources. Cannot continue.")
                    sys.exit(1)

            elif phase_num == 1:
                brain_json = phase_1_scaffold(
                    args.person, slug, brain_dir, sources_data, client, cost_tracker,
                    reference_slug=args.reference, model=args.model,
                )
                mark_phase(progress, 1, "complete",
                           clusters=len(brain_json.get("clusters", {})))

            elif phase_num == 2:
                # Ensure brain.json is loaded
                if brain_json is None:
                    bjp = brain_dir / "brain.json"
                    if bjp.exists():
                        with open(bjp) as f:
                            brain_json = json.load(f)
                    else:
                        error("brain.json not found — cannot run Phase 2")
                        break

                result = phase_2_ingest(
                    brain_json, brain_dir, slug, client, cost_tracker,
                    reference_slug=args.reference, model=args.model,
                    target_atoms=args.target_atoms,
                )
                atom_count = result.get("atom_count", 0)

                if atom_count == 0:
                    mark_phase(progress, 2, "failed",
                               atoms=0,
                               reason="0 atoms produced — check source content and ingestion logs")
                    save_progress(brain_dir, progress)
                    error("Phase 2 produced 0 atoms. Cannot continue.")
                    break

                # Hard floor — halt before spending on synthesis/enrichment if pack is too thin
                if atom_count < args.min_atoms and not args.allow_thin_pack:
                    error(
                        f"Atom floor not met: {atom_count} < {args.min_atoms}. "
                        f"Add more sources to brain.json or sources.json and resume, "
                        f"or pass --allow-thin-pack to ship anyway."
                    )
                    mark_phase(progress, 2, "blocked",
                               atoms=atom_count,
                               reason=f"below min-atoms floor ({atom_count}/{args.min_atoms})")
                    save_progress(brain_dir, progress)
                    break

                # Voice floor — catch the "transcripts silently failed" failure mode
                # (e.g. YouTube blocks CI/cloud IPs). Text scraping can clear the atom
                # floor while the brain ships near-quoteless and ungrounded. Measure
                # what actually landed rather than trusting the atom count.
                if not args.allow_thin_pack:
                    n_videos = 0
                    sj = brain_dir / "source" / "sources.json"
                    if sj.exists():
                        try:
                            sjd = json.loads(sj.read_text())
                            n_videos = sum(1 for s in sjd.get("sources", []) if s.get("youtube_id"))
                        except Exception:
                            pass
                    n_transcripts = len(list((brain_dir / "source" / "transcripts").glob("*.json"))) \
                        if (brain_dir / "source" / "transcripts").exists() else 0
                    voice_pct = 0.0
                    aap = brain_dir / "research" / "all-atoms.json"
                    if aap.exists():
                        try:
                            _atoms = json.loads(aap.read_text())
                            if _atoms:
                                voice_pct = sum(1 for a in _atoms if (a.get("original_quote") or "").strip()) / len(_atoms)
                        except Exception:
                            pass

                    transcript_fail = (n_videos >= MIN_VIDEOS_EXPECT_TRANSCRIPTS and n_transcripts == 0)
                    if transcript_fail and atom_count < MIN_BRAIN_ATOMS and not args.allow_thin_pack:
                        # TRULY HOLLOW: videos were an expected source AND the text
                        # corpus is below the atom floor. Continuing would spend ~$15
                        # of synthesis+enrichment on a quote-less brain. Halt as a cost
                        # guard — re-run locally / add a proxy, or pass --allow-thin-pack.
                        error(f"Transcript fetch failed: {n_videos} videos discovered, 0 transcripts "
                              f"fetched (likely IP block — YouTube blocks cloud/CI IPs), and only "
                              f"{atom_count} text atoms (< floor {MIN_BRAIN_ATOMS}). The brain would "
                              f"ship hollow. Build locally / add a proxy and --resume, or pass "
                              f"--allow-thin-pack to ship anyway.")
                        mark_phase(progress, 2, "blocked", atoms=atom_count,
                                   reason=f"transcript fetch failed: 0/{n_videos} transcripts, atoms {atom_count} < floor")
                        save_progress(brain_dir, progress)
                        break
                    if transcript_fail:
                        # Transcripts failed (IP block) BUT the text/other sources already
                        # cleared the atom floor — the brain is NOT hollow. Don't halt: the
                        # cost-guard rationale only applies to a thin brain. Continue and
                        # ship HIDDEN + flagged so a human can add the video voice later
                        # (locally / via proxy). Mirrors the low-voice degrade path below.
                        warn(f"Transcript fetch failed ({n_transcripts}/{n_videos}) — but {atom_count} "
                             f"atoms from text sources clear the floor ({MIN_BRAIN_ATOMS}). Continuing; "
                             f"brain ships HIDDEN + flagged for missing video voice (re-run locally / "
                             f"add a proxy to enrich the spoken voice).")
                        progress["transcript_fetch_failed"] = f"{n_transcripts}/{n_videos}"
                    if voice_pct < MIN_VOICE_PCT:
                        # QUALITY, not fatal: real but thin voice. Builds-should-not-fail —
                        # finish the build and ship HIDDEN + flagged (the no-auto-promote
                        # default keeps it off the live site). A human decides whether to
                        # promote or re-mine for voice. Does NOT abort.
                        warn(f"Voice below floor: {voice_pct:.0%} < {MIN_VOICE_PCT:.0%} "
                             f"({n_transcripts}/{n_videos} transcripts). Build CONTINUES; brain ships "
                             f"HIDDEN + flagged low-voice for human review (not aborted).")
                        progress["low_voice_flag"] = round(voice_pct, 3)

                mark_phase(progress, 2, "complete",
                           atoms=atom_count,
                           voice_pct=round(voice_pct, 3) if not args.allow_thin_pack else None)

            elif phase_num == 3:
                if brain_json is None:
                    bjp = brain_dir / "brain.json"
                    if bjp.exists():
                        with open(bjp) as f:
                            brain_json = json.load(f)

                phase_3_synthesize(
                    brain_json, brain_dir, args.person, client, cost_tracker,
                    reference_slug=args.reference, model=args.synthesis_model,
                    force=args.force_synthesis,
                )

                # --- Phase 3.5: ground/source the synthesis (SPEC-synthesis-grounding.md) ---
                # Tags every principle grounded|sourced|attributed|dropped, mints sourced
                # atoms from primary material for real-but-uncaptured principles, and flags
                # if the corpus is too thin. Non-fatal; merges sourced atoms into the
                # pipeline so they reach the pack + Supabase + enrichment.
                if not args.dry_run and not args.skip_grounding:
                    step("Phase 3.5: grounding synthesis (discover + verify primary sources)...")
                    gr = subprocess.run(
                        ["python3", str(SCRIPT_DIR / "ground-synthesis.py"), "--brain", slug],
                        cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=2400,
                    )
                    for line in gr.stdout.strip().splitlines()[-3:]:
                        print(f"  {line}")
                    if gr.returncode != 0:
                        warn(f"synthesis grounding exited {gr.returncode} (non-fatal): {gr.stderr[-200:]}")
                    # Merge minted sourced atoms into all-atoms.json so they export + load.
                    sp = brain_dir / "research" / "sourced-atoms.json"
                    ap = brain_dir / "research" / "all-atoms.json"
                    if sp.exists() and ap.exists():
                        try:
                            sourced = json.loads(sp.read_text())
                            allat = json.loads(ap.read_text())
                            seen = {a.get("id") for a in allat}
                            new = [a for a in sourced if a.get("id") not in seen]
                            if new:
                                allat.extend(new)
                                ap.write_text(json.dumps(allat, indent=2))
                                success(f"merged {len(new)} sourced atoms into all-atoms.json")
                        except Exception as e:
                            warn(f"could not merge sourced atoms: {e}")
                    # Reload brain.json — grounding wrote provenance tags into it.
                    bjp2 = brain_dir / "brain.json"
                    if bjp2.exists():
                        with open(bjp2) as f:
                            brain_json = json.load(f)

                # --- Phase 3.6: mine Hard Lessons + receipts from the corpus ---
                # Auto-generates synthesis.hard_lessons (mistake -> cost -> change with
                # verbatim receipts) from the brain's OWN diarized atoms, enforcing the
                # real-cost rubric. An empty result is correct for a sanitized corpus — a
                # QA signal, not a hole to fill. Runs after grounding so the pool includes
                # any minted sourced atoms. Non-fatal.
                if not args.dry_run and not args.skip_hard_lessons:
                    step("Phase 3.6: mining hard lessons + receipts...")
                    hl = subprocess.run(
                        ["python3", str(SCRIPT_DIR / "mine-hard-lessons.py"),
                         "--brain", slug, "--force"],
                        cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=900,
                    )
                    for line in hl.stdout.strip().splitlines()[-4:]:
                        print(f"  {line}")
                    if hl.returncode != 0:
                        warn(f"hard-lessons mining exited {hl.returncode} (non-fatal): {hl.stderr[-200:]}")
                    # Reload brain.json — the miner wrote synthesis.hard_lessons into it.
                    bjp3 = brain_dir / "brain.json"
                    if bjp3.exists():
                        with open(bjp3) as f:
                            brain_json = json.load(f)

                mark_phase(progress, 3, "complete")

            elif phase_num == 4:
                if brain_json is None:
                    bjp = brain_dir / "brain.json"
                    if bjp.exists():
                        with open(bjp) as f:
                            brain_json = json.load(f)

                result = phase_4_enrich(
                    brain_json, brain_dir, slug, client, cost_tracker,
                    model=args.model,
                )
                mark_phase(progress, 4, "complete",
                           connections=result.get("connection_count", 0))

            elif phase_num == 5:
                if brain_json is None:
                    bjp = brain_dir / "brain.json"
                    if bjp.exists():
                        with open(bjp) as f:
                            brain_json = json.load(f)

                result = phase_5_export_qa(brain_json, brain_dir, slug,
                                           client=client, cost_tracker=cost_tracker)
                mark_phase(progress, 5, "complete",
                           audit_score=result.get("score", 0))

        except KeyboardInterrupt:
            warn(f"\nInterrupted at Phase {phase_num}. Use --resume to continue.")
            mark_phase(progress, phase_num, "interrupted")
            save_progress(brain_dir, progress)
            sys.exit(1)

        except Exception as e:
            error(f"Phase {phase_num} failed: {e}")
            tb_str = traceback.format_exc()
            print(tb_str)
            mark_phase(progress, phase_num, "failed", error=str(e), traceback=tb_str)
            save_progress(brain_dir, progress)
            post_slack(f"`{slug}` · FAILED at Phase {phase_num}: {e}", ":x:")
            warn("Use --resume to retry from this phase.")
            sys.exit(1)

        progress["total_cost_usd"] = cost_tracker.total_cost
        save_progress(brain_dir, progress)

    # --- Check for skipped/failed phases ---
    skipped_phases = [
        i for i in range(6)
        if progress["phases"].get(str(i), {}).get("status") == "skipped"
    ]
    failed_phases = [
        i for i in range(6)
        if progress["phases"].get(str(i), {}).get("status") in ("failed", "blocked")
    ]

    if 5 in skipped_phases:
        print(f"\n{c['yellow']}{c['bold']}{'!' * 60}")
        print(f"  WARNING: Phase 5 (Export & QA) was skipped")
        print(f"  Brain pack NOT generated. Run with --resume to complete.")
        print(f"{'!' * 60}{c['reset']}")
    if 4 in skipped_phases:
        warn("Phase 4 (Enrichment) was skipped — connections not generated")

    # --- Final report ---
    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    build_incomplete = failed_phases or 5 in skipped_phases
    if build_incomplete:
        print(f"\n{c['bold']}{c['yellow']}{'=' * 60}")
        print(f"  BUILD INCOMPLETE: {args.person}")
        print(f"{'=' * 60}{c['reset']}\n")
    else:
        print(f"\n{c['bold']}{c['green']}{'=' * 60}")
        print(f"  BUILD COMPLETE: {args.person}")
        print(f"{'=' * 60}{c['reset']}\n")
    print(f"  Slug:        {slug}")
    print(f"  Time:        {mins}m {secs}s")
    print(f"  {cost_tracker.summary()}")

    # Show what was produced
    pack_dir = brain_dir / "pack"
    if pack_dir.exists():
        pack_files = list(pack_dir.rglob("*"))
        print(f"  Pack files:  {len([f for f in pack_files if f.is_file()])}")

    all_atoms = brain_dir / "research" / "all-atoms.json"
    connections = brain_dir / "research" / "connections.json"
    if all_atoms.exists():
        with open(all_atoms) as f:
            print(f"  Atoms:       {len(json.load(f))}")
    if connections.exists():
        with open(connections) as f:
            print(f"  Connections: {len(json.load(f))}")

    print(f"\n  {c['bold']}Next steps:{c['reset']}")
    print(f"    1. Open brains/{slug}/pack/explore.html in your browser")
    print(f"    2. Try: /brain {slug} then /advise or /surprise")
    print(f"    3. Run: python scripts/audit-brains.py --brain {slug}")
    print()

    # Final Slack ping with audit score if Phase 5 ran
    audit_score = progress["phases"].get("5", {}).get("audit_score")
    score_note = f" · audit {audit_score}" if audit_score is not None else ""
    post_slack(
        f"`{slug}` · Build complete — {args.person}{score_note} · {cost_tracker.summary()} · {mins}m {secs}s",
        ":white_check_mark:",
    )

    # --- Sync ~/rob-ai/CLAUDE.md from brains/index.json so new brains never drift ---
    if not build_incomplete:
        try:
            sync_script = SCRIPT_DIR / "sync-claude-md-brains.py"
            if sync_script.exists():
                result = subprocess.run(
                    [sys.executable, str(sync_script)],
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0:
                    print(f"  CLAUDE.md: {result.stdout.strip()}")
                else:
                    warn(f"sync-claude-md-brains.py failed (rc={result.returncode}): "
                         f"{result.stderr.strip() or result.stdout.strip()}")
            else:
                warn(f"sync-claude-md-brains.py not found at {sync_script}")
        except Exception as e:
            warn(f"CLAUDE.md sync raised: {e}")


if __name__ == "__main__":
    main()
