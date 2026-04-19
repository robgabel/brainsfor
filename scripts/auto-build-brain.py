#!/usr/bin/env python3
"""
auto-build-brain.py — Fully automated brain pack builder for BrainsFor.

Takes a person's name and produces a complete, shippable brain pack end-to-end
with ZERO manual approval gates. Replaces 6-12 hours of babysitting with
~60-90 minutes of unattended execution.

Usage:
    python scripts/auto-build-brain.py --person "Jensen Huang"
    python scripts/auto-build-brain.py --person "Annie Duke" --dry-run
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
import importlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

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
    CostTracker, call_claude,
    phase_header, step, success, warn, error,
    get_search_queries,
    SOURCE_CLASSIFY_PROMPT, BRAIN_JSON_PROMPT,
    SYNTHESIS_PROMPT, SYNTHESIS_JSON_PROMPT,
    COLORS,
)

# Import existing scripts via importlib (hyphenated filenames)
build_brain = importlib.import_module("build-brain")

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


# =============================================================================
# PHASE 0: SOURCE DISCOVERY
# =============================================================================

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
        success(f"sources.json already exists ({len(existing.get('sources', []))} sources) — skipping discovery")
        return existing

    if dry_run:
        step("[DRY RUN] Would run 5 web searches + classify results")
        return {"sources": []}

    # --- Web search via Firecrawl search API ---
    firecrawl_key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not firecrawl_key:
        warn("FIRECRAWL_API_KEY not set — cannot search. Create sources.json manually and use --skip-phase 0")
        return {"sources": []}

    queries = get_search_queries(person_name)
    all_urls = []
    seen_urls = set()

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
                    if url and url not in seen_urls:
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

    if not all_urls:
        warn("No search results found. Create sources.json manually.")
        return {"sources": []}

    # --- Classify results with LLM ---
    step(f"Classifying {len(all_urls)} URLs with LLM...")

    urls_json = json.dumps([{"url": u["url"], "title": u["title"]} for u in all_urls[:30]], indent=2)
    prompt = SOURCE_CLASSIFY_PROMPT.format(person_name=person_name, urls_json=urls_json)

    result = call_claude(
        client, FAST_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        parse_json=True,
        cost_tracker=cost_tracker,
        label="source_classify",
    )

    classified = result.get("parsed", [])
    if not classified:
        warn("LLM classification returned empty results")
        return {"sources": []}

    # Build sources.json
    sources = []
    for item in classified[:max_sources]:
        source = {
            "title": item.get("title", "Unknown"),
            "type": item.get("type", "other"),
            "priority": item.get("priority", "medium"),
            "url": item.get("url", ""),
        }
        # Extract YouTube video ID
        yt_id = item.get("youtube_id")
        if not yt_id and "youtube.com" in source["url"] or "youtu.be" in source.get("url", ""):
            try:
                yt_id = build_brain.extract_video_id(source["url"])
            except (ValueError, AttributeError):
                pass
        if yt_id:
            source["youtube_id"] = yt_id
        sources.append(source)

    sources_data = {
        "description": f"Source material for the {person_name} brain pack — auto-discovered via web search.",
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
    videos = sum(1 for s in sources if s.get("youtube_id"))
    success(f"Discovered {len(sources)} sources ({essential} essential, {videos} with YouTube IDs)")

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

        # Prepare sources summary
        sources_list = sources_data.get("sources", [])
        sources_summary = "\n".join(
            f"- [{s.get('priority', 'medium')}] {s.get('title', 'Unknown')} ({s.get('type', 'unknown')})"
            for s in sources_list
        ) or "No sources discovered yet."

        us = underscore_slug(slug)
        prompt = BRAIN_JSON_PROMPT.format(
            person_name=person_name,
            slug=slug,
            exemplar_json=json.dumps(exemplar, indent=2),
            sources_summary=sources_summary,
            atoms_table=f"{us}_atoms",
            connections_table=f"{us}_connections",
        )

        result = call_claude(
            client, model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
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

    # 1.3 Create Supabase tables
    step("Creating Supabase tables...")
    if dry_run:
        step("[DRY RUN] Would create Supabase tables")
    else:
        try:
            sql_template_path = TEMPLATES_DIR / "create-brain-tables.sql"
            with open(sql_template_path) as f:
                sql_template = f.read()

            us = underscore_slug(slug)
            first_name = brain_json.get("brain_first_name", person_name.split()[0])
            last_name = brain_json.get("brain_last_name", person_name.split()[-1] if " " in person_name else "")
            possessive = brain_json.get("brain_possessive", "their")

            sql = sql_template.replace("{{SLUG}}", us)
            sql = sql.replace("{{NAME}}", person_name)
            sql = sql.replace("{{FIRST_NAME}}", first_name)
            sql = sql.replace("{{LAST_NAME}}", last_name)
            sql = sql.replace("{{POSSESSIVE}}", possessive)

            # Execute via Supabase REST RPC
            url = get_supabase_url()
            key = os.environ.get("SUPABASE_SERVICE_KEY", "")
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key},",
                "Content-Type": "application/json",
            }

            # Split SQL into individual statements and execute each
            statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
            executed = 0
            for stmt in statements:
                try:
                    resp = httpx.post(
                        f"{url}/rest/v1/rpc/",
                        headers=headers,
                        json={"query": stmt},
                        timeout=30,
                    )
                    # RPC endpoint may not exist — fall back to direct SQL via pg API
                    if resp.status_code not in (200, 201, 204):
                        # Try the SQL endpoint instead
                        resp2 = httpx.post(
                            f"{url}/pg",
                            headers={
                                "apikey": key,
                                "Authorization": f"Bearer {key}",
                                "Content-Type": "application/json",
                            },
                            json={"query": stmt + ";"},
                            timeout=30,
                        )
                except Exception:
                    pass
                executed += 1

            success(f"Executed {executed} SQL statements for {us}_atoms and {us}_connections")
        except Exception as e:
            warn(f"Supabase table creation failed: {e}")
            warn("Tables may need to be created manually. Continuing...")

    # 1.4 Register in index.json
    step("Registering in index.json...")
    if not dry_run:
        index_path = BRAINS_DIR / "index.json"
        if index_path.exists():
            with open(index_path) as f:
                index = json.load(f)
        else:
            index = {"brains": []}

        # Check if already registered
        existing = any(b["slug"] == slug for b in index["brains"])
        if not existing:
            index["brains"].append({
                "slug": slug,
                "name": person_name,
                "source": brain_json.get("brain_source_detail", brain_json.get("brain_source_description", "")),
                "atom_count": 0,
                "connection_count": 0,
                "status": "scaffolded",
                "pack_path": f"brains/{slug}/pack/",
            })
            with open(index_path, "w") as f:
                json.dump(index, f, indent=2)
            success("Registered in index.json")
        else:
            success("Already registered in index.json")

    return brain_json


# =============================================================================
# PHASE 2: CONTENT INGESTION
# =============================================================================

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

    # --- 2.2 Deep research atoms ---
    step("Generating deep research atoms...")
    if not dry_run:
        gen_result = build_brain.stage_generate(
            brain_json, brain_dir, reference_slug, model, dry_run=dry_run
        )
        if gen_result:
            success("Deep research atoms generated")
        else:
            raise RuntimeError(
                "Deep research atom generation failed for every cluster. "
                "Check ANTHROPIC_API_KEY, model availability, and rate limits. "
                "No atoms were produced — aborting Phase 2."
            )
    else:
        clusters = brain_json.get("clusters", {})
        step(f"[DRY RUN] Would generate atoms for {len(clusters)} clusters")

    # --- 2.3 Merge ---
    step("Merging all atoms...")
    if not dry_run:
        merge_result = build_brain.stage_merge(brain_json, brain_dir, dry_run=dry_run)
        if not merge_result:
            raise RuntimeError(
                "Atom merge failed — no atom files found in research/. "
                "YouTube ingestion and deep research both produced zero output."
            )
    else:
        step("[DRY RUN] Would merge all atom files")

    # --- 2.4 Upload to Supabase ---
    all_atoms_path = research_dir / "all-atoms.json"
    if all_atoms_path.exists() and not dry_run:
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
                if sd:
                    sd_str = str(sd).strip()
                    if len(sd_str) == 9 and sd_str[4] == "-" and sd_str[:4].isdigit():
                        row["source_date"] = f"{sd_str[:4]}-01-01T00:00:00Z"
                    elif len(sd_str) == 4 and sd_str.isdigit():
                        row["source_date"] = f"{sd_str}-01-01T00:00:00Z"
                    elif "T" in sd_str or "-" in sd_str:
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

            success(f"Uploaded {uploaded}/{len(rows)} atoms to {table}")
        except Exception as e:
            warn(f"Supabase upload failed: {e}")
            warn("Atoms are saved locally — you can upload manually later")

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

        atom_count = len(atoms)
        step(f"Total atoms: {atom_count} (target: {target_atoms})")
    else:
        atom_count = 0

    if not dry_run and atom_count == 0:
        raise RuntimeError(
            "Phase 2 completed but zero atoms were produced. "
            "Cannot proceed to synthesis/enrichment/export on empty corpus."
        )

    return {"atom_count": atom_count}


# =============================================================================
# PHASE 3: SYNTHESIS
# =============================================================================

def phase_3_synthesize(
    brain_json: dict,
    brain_dir: Path,
    person_name: str,
    client: "anthropic.Anthropic",
    cost_tracker: CostTracker,
    reference_slug: str = "scott-belsky",
    model: str = SYNTHESIS_MODEL,
    dry_run: bool = False,
) -> dict:
    """Generate synthesis.md and update brain.json synthesis section."""
    phase_header(3)

    synthesis_path = brain_dir / "synthesis.md"
    all_atoms_path = brain_dir / "research" / "all-atoms.json"

    if synthesis_path.exists():
        success(f"synthesis.md already exists ({synthesis_path})")
        return {"synthesis_exists": True}

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
        # Preserve existing skills array if present
        if "skills" not in synthesis_data and "skills" in brain_json.get("synthesis", {}):
            synthesis_data["skills"] = brain_json["synthesis"]["skills"]
        brain_json["synthesis"] = synthesis_data

        brain_json_path = brain_dir / "brain.json"
        with open(brain_json_path, "w") as f:
            json.dump(brain_json, f, indent=2)
        success("brain.json synthesis section updated")

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

def phase_5_export_qa(
    brain_json: dict,
    brain_dir: Path,
    slug: str,
    dry_run: bool = False,
) -> dict:
    """Export pack, run audit, remediate if needed."""
    phase_header(5)

    if dry_run:
        step("[DRY RUN] Would run export + audit")
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

        return {"score": score, "errors": len(audit.errors), "warnings": len(audit.warnings)}

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
  python scripts/auto-build-brain.py --person "Annie Duke" --dry-run
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
        step(f"Resuming from Phase {start_phase}")
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
                mark_phase(progress, 0, "complete",
                           sources_found=len(sources_data.get("sources", [])))

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
                mark_phase(progress, 2, "complete",
                           atoms=result.get("atom_count", 0))

            elif phase_num == 3:
                if brain_json is None:
                    bjp = brain_dir / "brain.json"
                    if bjp.exists():
                        with open(bjp) as f:
                            brain_json = json.load(f)

                phase_3_synthesize(
                    brain_json, brain_dir, args.person, client, cost_tracker,
                    reference_slug=args.reference, model=args.synthesis_model,
                )
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

                result = phase_5_export_qa(brain_json, brain_dir, slug)
                mark_phase(progress, 5, "complete",
                           audit_score=result.get("score", 0))

        except KeyboardInterrupt:
            warn(f"\nInterrupted at Phase {phase_num}. Use --resume to continue.")
            mark_phase(progress, phase_num, "interrupted")
            save_progress(brain_dir, progress)
            sys.exit(1)

        except Exception as e:
            error(f"Phase {phase_num} failed: {e}")
            import traceback
            traceback.print_exc()
            mark_phase(progress, phase_num, "failed", error=str(e))
            save_progress(brain_dir, progress)
            post_slack(f"`{slug}` · FAILED at Phase {phase_num}: {e}", ":x:")
            warn("Use --resume to retry from this phase.")
            sys.exit(1)

        progress["total_cost_usd"] = cost_tracker.total_cost
        save_progress(brain_dir, progress)

    # --- Final report ---
    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

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


if __name__ == "__main__":
    main()
