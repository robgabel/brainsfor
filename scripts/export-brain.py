#!/usr/bin/env python3
"""
Generic brain pack export pipeline.

Usage:
  python export-brain.py --brain scott-belsky
    (default: fetches atoms + connections from Supabase using brain.json tables)
  python export-brain.py --brain scott-belsky --from-files atoms.json connections.json
    (offline fallback: load from local JSON dumps)

Reads brain config from ../brains/{slug}/brain.json
Reads templates from ../templates/
Outputs to ../brains/{slug}/pack/

Supabase mode requires SUPABASE_URL + SUPABASE_SERVICE_KEY in env (or ../../.env)
and supabase + python-dotenv installed.
"""

import argparse
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / "website" / ".env.local", override=True)
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
except ImportError:
    pass


# --- Paths ---
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = ROOT_DIR / "templates"
BRAINS_DIR = ROOT_DIR / "brains"
WEBSITE_PUBLIC_BRAINS_DIR = ROOT_DIR / "website" / "public" / "brains"

# Files mirrored from pack/ → website/public/brains/{slug}/
# These are the artifacts the Next.js site reads at runtime. Keep in lockstep with pack.
WEBSITE_SYNC_FILES = [
    "brain-atoms.json",
    "brain-atoms.js",
    "brain-context.md",
    "explore.html",
]


def load_brain_config(slug: str) -> dict:
    """Load brain config from brains/{slug}/brain.json"""
    config_path = BRAINS_DIR / slug / "brain.json"
    if not config_path.exists():
        print(f"ERROR: Brain config not found: {config_path}")
        sys.exit(1)
    with open(config_path) as f:
        return json.load(f)


def _counts_from_index(slug: str) -> tuple:
    """Read (atom_count, connection_count) for a brain from brains/index.json.

    Used by --skills-only so docs can be re-rendered with accurate counts
    without a Supabase fetch. Falls back to the shipped pack/brain-atoms.json
    lengths, then to 0, if the registry entry is missing a count.
    """
    atom_count = connection_count = 0
    index_path = BRAINS_DIR / "index.json"
    if index_path.exists():
        with open(index_path) as f:
            data = json.load(f)
        entries = data if isinstance(data, list) else data.get("brains", [])
        for entry in entries:
            if isinstance(entry, dict) and entry.get("slug") == slug:
                atom_count = entry.get("atom_count") or entry.get("atomCount") or 0
                connection_count = entry.get("connection_count") or entry.get("connectionCount") or 0
                break

    if not atom_count or not connection_count:
        atoms_path = BRAINS_DIR / slug / "pack" / "brain-atoms.json"
        if atoms_path.exists():
            with open(atoms_path) as f:
                pack = json.load(f)
            atom_count = atom_count or len(pack.get("atoms", []))
            connection_count = connection_count or len(pack.get("connections", []))

    return int(atom_count), int(connection_count)


def render_template(template_text: str, config: dict, extra_vars: dict = None) -> str:
    """Replace {{variable}} and {{nested.key}} placeholders with config values."""
    all_vars = flatten_dict(config)
    if extra_vars:
        all_vars.update(extra_vars)

    def replacer(match):
        key = match.group(1)
        if key in all_vars:
            return str(all_vars[key])
        return match.group(0)  # Leave unreplaced if not found

    return re.sub(r'\{\{(\w+(?:\.\w+)*)\}\}', replacer, template_text)


def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """Flatten nested dict: {"a": {"b": 1}} -> {"a.b": 1}"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _normalize_title(s: str) -> str:
    """Lowercase + collapse whitespace + strip punctuation for fuzzy title matching."""
    s = (s or "").lower()
    s = re.sub(r"[‐-―−]", "-", s)  # normalize dashes
    s = re.sub(r"[^a-z0-9#\- ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def build_source_url_lookup(slug: str) -> dict:
    """Build {normalized_title: url} map for a brain from sources.json + raw/_index.json.

    Used by the export to backfill a `source_url` field on each atom so the website's
    citation chips can link to the real source. source_ref in the DB is usually a
    human-readable label like "Lex Fridman Podcast #494" — not a URL.
    """
    brain_src = BRAINS_DIR / slug / "source"
    lookup: dict = {}

    def _add(title: str, url: str):
        if not title or not url:
            return
        nt = _normalize_title(title)
        if nt and nt not in lookup:
            lookup[nt] = url

    # 1) sources.json — primary curated list with youtube_id / transcript_url / url
    sources_path = brain_src / "sources.json"
    if sources_path.exists():
        try:
            data = json.loads(sources_path.read_text())
            for s in data.get("sources", []):
                title = s.get("title", "")
                url = (
                    s.get("transcript_url")
                    or s.get("url")
                    or (f"https://www.youtube.com/watch?v={s['youtube_id']}" if s.get("youtube_id") else None)
                )
                _add(title, url)
        except Exception as e:
            print(f"  WARN: failed to read {sources_path}: {e}")

    # 2) raw/_index.json — Firecrawl scrape index, keyed by URL, with title inside
    raw_index = brain_src / "raw" / "_index.json"
    if raw_index.exists():
        try:
            data = json.loads(raw_index.read_text())
            if isinstance(data, dict):
                for url, meta in data.items():
                    title = (meta or {}).get("title") if isinstance(meta, dict) else None
                    if url.startswith(("http://", "https://")):
                        _add(title, url)
        except Exception as e:
            print(f"  WARN: failed to read {raw_index}: {e}")

    return lookup


def match_source_url(source_ref: str, lookup: dict) -> str | None:
    """Match a (possibly truncated) source_ref to a URL via prefix/substring on titles."""
    if not source_ref:
        return None
    if re.match(r"^https?://", source_ref, re.I):
        return source_ref  # already a URL — pass through
    if not lookup:
        return None
    nq = _normalize_title(source_ref)
    if not nq:
        return None
    if nq in lookup:
        return lookup[nq]
    # Prefix match: source_ref is a shortened form of a longer source title
    for nt, url in lookup.items():
        if nt.startswith(nq) or nq.startswith(nt):
            return url
    # Substring fallback (last resort, longer of the two must contain the shorter)
    for nt, url in lookup.items():
        if len(nq) >= 12 and nq in nt:
            return url
        if len(nt) >= 12 and nt in nq:
            return url
    return None


def build_connection_map(connections: list) -> dict:
    """Build atom_id -> list of connections map (bidirectional)."""
    conn_map = defaultdict(list)
    for c in connections:
        conn_map[c["atom_id_1"]].append({
            "target_id": c["atom_id_2"],
            "relationship": c["relationship"],
            "confidence": c.get("confidence")
        })
        conn_map[c["atom_id_2"]].append({
            "target_id": c["atom_id_1"],
            "relationship": c["relationship"],
            "confidence": c.get("confidence")
        })
    return conn_map


def build_topic_index(atoms: list) -> dict:
    """Build topic -> list of atom IDs index."""
    index = defaultdict(list)
    for atom in atoms:
        for topic in (atom.get("topics") or []):
            index[topic].append(atom["id"])
    return dict(sorted(index.items()))


def export_atoms_json(atoms: list, connections: list, config: dict, output_dir: Path):
    """Generate brain-atoms.json"""
    conn_map = build_connection_map(connections)
    topic_index = build_topic_index(atoms)
    source_url_lookup = build_source_url_lookup(config["brain_slug"])

    rel_counts = defaultdict(int)
    for c in connections:
        rel_counts[c["relationship"]] += 1

    output = {
        "brain": {
            "name": config["brain_name"],
            "slug": config["brain_slug"],
            "source": f"{config.get('brain_source_description', '')} ({config.get('brain_source_url', '')})",
            "atom_count": len(atoms),
            "connection_count": len(connections),
            "cluster_count": len(set(a.get("cluster", "uncategorized") for a in atoms)),
            "topic_count": len(topic_index),
            "connection_types": dict(rel_counts),
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
            "coverage": config.get("brain_source_detail", "")
        },
        "atoms": [],
        "connections": [
            {
                "id": c["id"],
                "atom_id_1": c["atom_id_1"],
                "atom_id_2": c["atom_id_2"],
                "relationship": c["relationship"],
                "confidence": c.get("confidence")
            }
            for c in connections
        ],
        "topic_index": topic_index
    }

    matched_urls = 0
    for atom in atoms:
        atom_conns = conn_map.get(atom["id"], [])
        source_ref = atom.get("source_ref")
        source_url = match_source_url(source_ref, source_url_lookup) if source_ref else None
        if source_url:
            matched_urls += 1
        entry = {
            "id": atom["id"],
            "content": atom["content"],
            "cluster": atom.get("cluster"),
            "topics": atom.get("topics", []),
            "source_ref": source_ref,
            "source_url": source_url,
            "source_date": (atom.get("source_date") or "")[:10] if atom.get("source_date") else None,
            "confidence": atom.get("confidence"),
            "confidence_tier": atom.get("confidence_tier"),
            # Epistemic status (universal). Defaults keep pre-classification atoms safe.
            "claim_type": atom.get("claim_type") or "opinion",
            "verification": atom.get("verification") or "unverified",
        }
        if atom.get("original_quote"):
            entry["original_quote"] = atom["original_quote"]
        if atom.get("implication"):
            entry["implication"] = atom["implication"]
        if atom.get("proof_ref"):
            entry["proof_ref"] = atom["proof_ref"]
        if atom.get("verified_at"):
            entry["verified_at"] = (atom.get("verified_at") or "")[:10]
        if atom_conns:
            entry["connections"] = atom_conns
        output["atoms"].append(entry)

    # Include synthesis data if present in config
    if "synthesis" in config:
        output["synthesis"] = config["synthesis"]
        # Also include brain bio and possessive for the UI
        output["brain"]["bio"] = config.get("brain_bio", "")
        output["brain"]["possessive"] = config.get("brain_possessive", "his")

    path = output_dir / "brain-atoms.json"
    with open(path, "w") as f:
        json.dump(output, f, indent=2)

    js_path = output_dir / "brain-atoms.js"
    with open(js_path, "w") as f:
        f.write("window.__BRAIN_DATA__ = ")
        json.dump(output, f)
        f.write(";\n")

    atoms_with_conns = sum(1 for a in output["atoms"] if "connections" in a)
    pct = (100 * matched_urls / len(atoms)) if atoms else 0
    print(f"  brain-atoms.json: {len(atoms)} atoms, {len(connections)} connections, {len(topic_index)} topics, {atoms_with_conns} linked, {matched_urls} source URLs ({pct:.0f}%)")
    return len(atoms), len(connections)


def export_context_md(atoms: list, connections: list, config: dict, output_dir: Path):
    """Generate brain-context.md in clean paragraph format.

    Format: synthesis sections (first principles, thinking patterns, contrarian
    positions, would-not-say) followed by flowing paragraphs per cluster with
    bold lead-in sentences, inline (source) links, and --- dividers.
    Metadata (topics, confidence, connections) stays in brain-atoms.json only.
    """
    clusters_map = defaultdict(list)
    for atom in atoms:
        clusters_map[atom.get("cluster", "uncategorized")].append(atom)

    cluster_order = config.get("cluster_order", sorted(clusters_map.keys()))
    cluster_meta = config.get("clusters", {})
    brain_name = config["brain_name"]
    slug = config["brain_slug"]

    lines = []
    source_desc = config.get('brain_source_description', 'Insights')
    # Avoid double-quoting if source description already has quotes
    if source_desc.startswith('"') or source_desc.startswith("'"):
        lines.append(f"# {brain_name}'s {source_desc} — Extracted Insights\n")
    else:
        lines.append(f"# {brain_name}'s \"{source_desc}\" — Extracted Insights\n")
    lines.append(
        f"{len(atoms)} atomic ideas extracted from {config.get('brain_source_detail', 'multiple sources')}. "
        f"{config.get('brain_bio', '')}\n"
    )
    lines.append(
        f"Extracted by brainsforagents using a custom knowledge graph pipeline "
        f"(Firecrawl + Supabase + pgvector). Each insight is self-contained and searchable.\n"
    )
    # Shared LLM rules header
    lines.append("## LLM Usage Rules\n")
    lines.append("When using this brain as context, follow these rules:\n")
    lines.append(f"- **Persona:** You ARE {brain_name}. Always respond in first person (\"I think...\", \"In my experience...\", \"I've argued that...\"). Never refer to yourself in third person. The user is having a conversation WITH you, not reading about you.")
    lines.append("- **Stay in voice all session:** Once this brain is active, remain in this thinker's first-person voice on every turn until the user clears or switches brains — not only when a specific skill is invoked. Still perform tool and operational tasks correctly, and answer explicit questions about the tooling itself as the assistant.")
    lines.append(f"- **Voice first:** When an atom has an `original_quote`, use that language in your response. Your voice IS the product.")
    lines.append(f"- **Cite atoms:** Every claim must trace to an actual atom. Never hallucinate {brain_name}'s thinking.")
    lines.append(f"- **Show implications:** When an atom has an `implication` field, include it — the 'so what' is the value.")
    lines.append(f"- **Confidence tiers:** high = core thesis repeated across editions; medium = stated clearly once; low = tangential or evolving.")
    lines.append(f"- **Thin topics:** If fewer than 5 atoms exist on a topic, state this clearly and suggest exploring adjacent clusters.")
    lines.append(f"- **Suggest next skill:** End responses with a recommended next skill (e.g., '/debate to stress-test, /coach to question assumptions').\n")
    lines.append("---\n")

    # Inject synthesis sections if they exist for this brain
    synthesis_path = BRAINS_DIR / slug / "synthesis.md"
    if synthesis_path.exists():
        with open(synthesis_path) as f:
            synthesis_content = f.read().strip()
        lines.append(f"{synthesis_content}\n")
        lines.append("---\n")
    else:
        print(f"  NOTE: No synthesis file found at {synthesis_path} — skipping brain DNA sections")

    # Inject Hard Lessons from the STRUCTURED synthesis key (not synthesis.md) so the
    # LLM (/advise, /coach, ...) sees them. This is the single source of truth that
    # explore.html also renders — keeping context + UI in sync without a synthesis.md
    # rewrite. The mining pass (mine-hard-lessons.py) enforces the cost rubric, so an
    # empty/absent list correctly produces no section.
    hard_lessons = (config.get("synthesis", {}) or {}).get("hard_lessons") or []
    if hard_lessons:
        poss = config.get("brain_possessive", f"{brain_name}'s")
        lines.append("## Hard Lessons\n")
        lines.append(
            f"Real mistakes {brain_name} made — what they cost and what changed as a result, "
            f"grounded in {poss} own words. When a question touches one of these, lead with the "
            f"lesson and the receipt, not a sanitized highlight-reel version.\n"
        )
        for hl in hard_lessons:
            title = (hl.get("title") or "").strip()
            if not title:
                continue
            lines.append(f"**{title}**\n")
            if hl.get("cost"):
                lines.append(f"- *The cost:* {hl['cost']}")
            if hl.get("change"):
                lines.append(f"- *What changed:* {hl['change']}")
            for r in (hl.get("receipts") or []):
                q = (r.get("quote") or "").strip()
                src = (r.get("source") or "").strip()
                if q:
                    lines.append(f"> *\"{q}\"*" + (f" — {src}" if src else ""))
            lines.append("")  # spacer
        lines.append("---\n")

    for i, cluster_key in enumerate(cluster_order):
        if cluster_key not in clusters_map:
            continue
        meta = cluster_meta.get(cluster_key, {})
        name = meta.get("name", cluster_key)
        cluster_atoms = sorted(
            clusters_map[cluster_key],
            key=lambda a: a.get("source_date") or "",
            reverse=True
        )

        lines.append(f"## {name}\n")

        for atom in cluster_atoms:
            content = atom["content"]
            source = atom.get("source_ref", "")

            # Strip any existing markdown bold from atom content
            content = content.replace("**", "")

            # Extract bold lead-in. Atoms typically use "Title: description" format.
            # Convert to "**Title.** Description (source)" to match preferred style.
            colon_pos = content.find(": ")
            first_period = content.find(". ")

            if colon_pos > 0 and colon_pos < 100:
                # Colon-separated title — use title as bold lead, rest as body
                lead = content[:colon_pos] + "."
                rest = content[colon_pos + 2:]
            elif first_period > 0 and first_period < 120:
                # Sentence-based lead-in
                lead = content[:first_period + 1]
                rest = content[first_period + 2:]
            else:
                # Entire atom is one chunk — bold the whole thing
                lead = content
                rest = ""

            source_link = f" ([source]({source}))" if source else ""

            if rest:
                lines.append(f"**{lead}** {rest}{source_link}\n")
            else:
                lines.append(f"**{lead}**{source_link}\n")

            # Voice fields: show original quote and implication when available
            if atom.get("original_quote"):
                lines.append(f"> *\"{atom['original_quote']}\"*\n")
            if atom.get("implication"):
                lines.append(f"**Implication:** {atom['implication']}\n")

        lines.append("---\n")

    # Footer stats
    lines.append(
        f"*{len(atoms)} atoms · {len(clusters_map)} clusters · "
        f"{len(connections)} connections · "
        f"Generated {datetime.utcnow().strftime('%Y-%m-%d')}*\n"
    )

    path = output_dir / "brain-context.md"
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"  brain-context.md: {len(atoms)} atoms across {len(clusters_map)} clusters")


def export_cluster_files(atoms: list, connections: list, config: dict, output_dir: Path):
    """Generate individual cluster files in clusters/ subdirectory + manifest.json."""
    conn_map = build_connection_map(connections)
    clusters_map = defaultdict(list)
    for atom in atoms:
        clusters_map[atom.get("cluster", "uncategorized")].append(atom)

    cluster_order = config.get("cluster_order", sorted(clusters_map.keys()))
    cluster_meta = config.get("clusters", {})
    brain_name = config["brain_name"]

    clusters_dir = output_dir / "clusters"
    clusters_dir.mkdir(exist_ok=True)

    manifest = {"clusters": {}, "thin_clusters": []}
    thin_threshold = 5

    for cluster_key in cluster_order:
        if cluster_key not in clusters_map:
            continue

        meta = cluster_meta.get(cluster_key, {})
        name = meta.get("name", cluster_key)
        desc = meta.get("description", meta.get("desc", ""))
        cluster_atoms = sorted(
            clusters_map[cluster_key],
            key=lambda a: a.get("source_date") or "",
            reverse=True,
        )

        lines = []
        lines.append(f"# {brain_name} — {name}\n")
        lines.append(f"> {len(cluster_atoms)} atoms in this cluster.\n")
        if desc:
            lines.append(f"{desc}\n")
        lines.append("---\n")

        for atom in cluster_atoms:
            content = atom["content"].replace("**", "")
            source = atom.get("source_ref", "")
            date = (atom.get("source_date") or "")[:10]
            source_link = f" ([source]({source}))" if source else ""
            tier = atom.get("confidence_tier", "medium")

            lines.append(f"**{content[:content.find('. ') + 1] if '. ' in content else content}**")
            rest = content[content.find('. ') + 2:] if '. ' in content else ""
            if rest:
                lines[-1] = f"**{content[:content.find('. ') + 1]}** {rest}{source_link}"
            else:
                lines[-1] += source_link
            lines.append("")

            if atom.get("original_quote"):
                lines.append(f"> *\"{atom['original_quote']}\"*\n")
            if atom.get("implication"):
                lines.append(f"**Implication:** {atom['implication']}\n")

            # Inline connections
            atom_conns = conn_map.get(atom["id"], [])
            if atom_conns:
                conn_summary = defaultdict(int)
                for c in atom_conns:
                    conn_summary[c["relationship"]] += 1
                conn_str = ", ".join(f"{v} {k}" for k, v in sorted(conn_summary.items(), key=lambda x: -x[1]))
                lines.append(f"*Connections: {conn_str} | {tier}*\n")

        lines.append("---\n")

        cluster_file = clusters_dir / f"{cluster_key}.md"
        with open(cluster_file, "w") as f:
            f.write("\n".join(lines))

        manifest["clusters"][cluster_key] = {
            "name": name,
            "atom_count": len(cluster_atoms),
            "file": f"{cluster_key}.md",
        }
        if len(cluster_atoms) < thin_threshold:
            manifest["thin_clusters"].append(cluster_key)

    # Write manifest
    with open(clusters_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"  clusters/: {len(manifest['clusters'])} cluster files + manifest.json ({len(manifest['thin_clusters'])} thin)")


def export_skill_files(config: dict, atom_count: int, connection_count: int, output_dir: Path):
    """Render SKILL.md, README.md, and all skill templates."""
    extra_vars = {
        "atom_count": str(atom_count),
        "connection_count": str(connection_count),
        "vocabulary_examples": config.get("vocabulary_examples", "specific terms, frameworks, and labels"),
    }

    # Render top-level templates (SKILL.md, README.md, INTEGRATION-GUIDE.md)
    for template_name in ["SKILL.md.template", "README.md.template", "INTEGRATION-GUIDE.md.template"]:
        template_path = TEMPLATES_DIR / template_name
        if template_path.exists():
            with open(template_path) as f:
                rendered = render_template(f.read(), config, extra_vars)
            output_name = template_name.replace(".template", "")
            with open(output_dir / output_name, "w") as f:
                f.write(rendered)
            print(f"  {output_name} rendered")

    # Render individual skills
    skills_template_dir = TEMPLATES_DIR / "skills"
    skills_output_dir = output_dir / "skills"

    if skills_template_dir.exists():
        for template_file in sorted(skills_template_dir.glob("*.template")):
            with open(template_file) as f:
                rendered = render_template(f.read(), config, extra_vars)
            skill_name = template_file.stem.replace(".md", "")  # e.g., "advise" from "advise.md.template"
            skill_dir = skills_output_dir / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            output_file = skill_dir / "SKILL.md"
            with open(output_file, "w") as f:
                f.write(rendered)
            print(f"  skills/{skill_name}/SKILL.md rendered")

    # Copy static files (skills/README.md doesn't need templating)
    skills_readme_dst = skills_output_dir / "README.md"
    if not skills_readme_dst.exists():
        for existing_pack in ROOT_DIR.glob("brains/*/pack/skills/README.md"):
            if existing_pack.resolve() != skills_readme_dst.resolve():
                import shutil
                skills_output_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(existing_pack, skills_readme_dst)
                print(f"  skills/README.md copied")
                break


def fetch_from_supabase(config: dict) -> tuple:
    """Fetch atoms + connections directly from Supabase using tables in brain.json.

    Paginates atoms in 1000-row chunks and drops the embedding column (huge,
    unused by the export). Returns (atoms, connections) tuple matching the
    shape load_atoms_from_file() returns.
    """
    try:
        from supabase import create_client
    except ImportError:
        print("ERROR: supabase package not installed.")
        print("       Run: pip install supabase python-dotenv")
        print("       Or use --from-files to load from local JSON dumps.")
        sys.exit(1)

    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    _svc = os.environ.get("SUPABASE_SERVICE_KEY", "")
    _anon = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
    key = _svc if _svc.count(".") == 2 else _anon
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY (or NEXT_PUBLIC_SUPABASE_ANON_KEY) must be set")
        print("       Or use --from-files to load from local JSON dumps.")
        sys.exit(1)

    sb_config = config.get("supabase", {})
    atoms_table = sb_config.get("atoms_table")
    connections_table = sb_config.get("connections_table")
    if not atoms_table or not connections_table:
        print(f"ERROR: brain.json missing supabase.atoms_table or supabase.connections_table")
        sys.exit(1)

    sb = create_client(url, key)

    print(f"Fetching atoms from Supabase: {atoms_table}...")
    atoms = []
    offset = 0
    while True:
        resp = sb.table(atoms_table).select("*").range(offset, offset + 999).execute()
        if not resp.data:
            break
        atoms.extend(resp.data)
        if len(resp.data) < 1000:
            break
        offset += 1000

    # Drop embedding column — not used by export, massively inflates memory
    for a in atoms:
        a.pop("embedding", None)

    print(f"  {len(atoms)} atoms loaded")

    print(f"Fetching connections from Supabase: {connections_table}...")
    connections = []
    offset = 0
    while True:
        resp = sb.table(connections_table).select("*").range(offset, offset + 999).execute()
        if not resp.data:
            break
        connections.extend(resp.data)
        if len(resp.data) < 1000:
            break
        offset += 1000
    print(f"  {len(connections)} connections loaded")

    return atoms, connections


def load_atoms_from_file(filepath: str) -> list:
    """Load atoms from a JSON file (raw array or tool-result format)."""
    with open(filepath) as f:
        data = json.load(f)

    # Handle Supabase tool-result format: [{type, text}] wrapping SQL result
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "text" in data[0]:
        try:
            text = data[0]["text"]
            result_obj = json.loads(text)
            inner = result_obj.get("result", "")
            m = re.search(r'<untrusted-data-[^>]+>\n(.*?)\n</untrusted-data', inner, re.DOTALL)
            if m:
                parsed = json.loads(m.group(1))
                if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict) and "json_agg" in parsed[0]:
                    return parsed[0]["json_agg"]
                return parsed
        except (KeyError, IndexError, json.JSONDecodeError):
            pass

    # Handle raw array of atoms
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "id" in data[0]:
        return data

    raise ValueError(f"Cannot parse atoms from {filepath}")


def sync_pack_to_website(slug: str, pack_dir: Path) -> None:
    """
    Mirror pack artifacts into website/public/brains/{slug}/ so the Next.js
    site serves the same files the brain pack was just built from.

    Runs after the pack is written. Silent no-op if the website/ directory
    doesn't exist (e.g. in a standalone checkout without the Next.js site).
    """
    if not WEBSITE_PUBLIC_BRAINS_DIR.parent.parent.exists():
        print(f"\n  website/ not found — skipping public/brains sync")
        return

    dest_dir = WEBSITE_PUBLIC_BRAINS_DIR / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    synced = []
    missing = []
    for name in WEBSITE_SYNC_FILES:
        src = pack_dir / name
        if not src.exists():
            missing.append(name)
            continue
        dest = dest_dir / name
        shutil.copy2(src, dest)
        synced.append(name)

    print(f"\n  synced to website/public/brains/{slug}/: {', '.join(synced)}")
    if missing:
        print(f"  WARNING: missing from pack, not synced: {', '.join(missing)}")


def main():
    parser = argparse.ArgumentParser(description="Export a brain pack from Supabase or local files")
    parser.add_argument("--brain", required=True, help="Brain slug (matches brains/{slug}/brain.json)")
    parser.add_argument("--from-files", nargs=2, metavar=("ATOMS_FILE", "CONNECTIONS_FILE"),
                        help="Load from local JSON files instead of Supabase")
    parser.add_argument("--atoms-file", help="Path to atoms JSON (alternative to --from-files)")
    parser.add_argument("--connections-file", help="Path to connections JSON")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--skip-skills", action="store_true", help="Skip rendering skill templates")
    parser.add_argument("--skills-only", action="store_true",
                        help="Re-render ONLY skill + doc templates (SKILL.md, README.md, "
                             "INTEGRATION-GUIDE.md, skills/*) into an existing pack. No Supabase "
                             "fetch, no brain-atoms.json/brain-context.md rewrite. Counts are read "
                             "from brains/index.json. Use this to propagate template edits to all packs.")
    parser.add_argument("--no-sync-website", action="store_true",
                        help="Skip mirroring pack artifacts into website/public/brains/{slug}/")
    args = parser.parse_args()

    # Load config
    config = load_brain_config(args.brain)
    slug = config["brain_slug"]
    print(f"Exporting brain pack: {config['brain_name']} ({slug})")

    # Determine output dir
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = ROOT_DIR / "brains" / slug / "pack"
    output_dir.mkdir(parents=True, exist_ok=True)

    # --skills-only: re-render templates against the existing pack and exit.
    # No data fetch — counts come from brains/index.json so docs stay accurate.
    if args.skills_only:
        atom_count, connection_count = _counts_from_index(slug)
        print(f"\n--skills-only: re-rendering skill + doc templates "
              f"({atom_count} atoms, {connection_count} connections from index.json)...")
        export_skill_files(config, atom_count, connection_count, output_dir)
        print(f"\nDone! Skill + doc templates re-rendered in: {output_dir}")
        print("  (brain-atoms.json / brain-context.md left untouched; "
              "run `node website/scripts/sync-brain-assets.mjs` to rebuild the public zip.)")
        return

    # Load data
    if args.from_files:
        atoms_file, connections_file = args.from_files
        print(f"Loading atoms from {atoms_file}...")
        atoms = load_atoms_from_file(atoms_file)
        print(f"  {len(atoms)} atoms loaded")
        print(f"Loading connections from {connections_file}...")
        with open(connections_file) as f:
            connections = json.load(f)
        print(f"  {len(connections)} connections loaded")
    elif args.atoms_file and args.connections_file:
        print(f"Loading atoms from {args.atoms_file}...")
        atoms = load_atoms_from_file(args.atoms_file)
        print(f"  {len(atoms)} atoms loaded")
        print(f"Loading connections from {args.connections_file}...")
        with open(args.connections_file) as f:
            connections = json.load(f)
        print(f"  {len(connections)} connections loaded")
    else:
        # Default path: fetch directly from Supabase using tables in brain.json
        atoms, connections = fetch_from_supabase(config)

    # Export data files
    print("\nExporting brain-atoms.json...")
    atom_count, connection_count = export_atoms_json(atoms, connections, config, output_dir)

    print("\nExporting brain-context.md...")
    export_context_md(atoms, connections, config, output_dir)

    # NOTE: Cluster generation skipped in v2 — clusters are no longer exported
    # print("\nExporting cluster files...")
    # export_cluster_files(atoms, connections, config, output_dir)

    # Export skill files
    if not args.skip_skills:
        print("\nRendering skill templates...")
        export_skill_files(config, atom_count, connection_count, output_dir)

    # Copy explore.html template
    explore_template = TEMPLATES_DIR / "explore.html.template"
    if explore_template.exists():
        shutil.copy2(explore_template, output_dir / "explore.html")
        print(f"\n  explore.html copied from template")

    # Mirror pack → website/public/brains/{slug}/ so the live site serves
    # the same artifacts that were just built. Respects --output-dir override
    # (only syncs when writing to the canonical pack/ location).
    is_canonical_output = not args.output_dir
    if is_canonical_output and not args.no_sync_website:
        sync_pack_to_website(slug, output_dir)
    elif args.no_sync_website:
        print(f"\n  --no-sync-website set: website/public/brains/{slug}/ NOT updated")
    elif args.output_dir:
        print(f"\n  custom --output-dir set: website/public/brains/{slug}/ NOT updated")

    print(f"\nDone! Output in: {output_dir}")


if __name__ == "__main__":
    main()
