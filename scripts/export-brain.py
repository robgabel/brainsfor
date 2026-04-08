#!/usr/bin/env python3
"""
Generic brain pack export pipeline.

Usage:
  python export-brain.py --brain belsky
  python export-brain.py --brain belsky --from-files atoms.json connections.json
  python export-brain.py --brain belsky --supabase  (requires SUPABASE_URL + SUPABASE_SERVICE_KEY)

Reads brain config from ../brains/{slug}/brain.json
Reads templates from ../templates/
Outputs to ../brains/{slug}/pack/
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# --- Paths ---
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = ROOT_DIR / "templates"
BRAINS_DIR = ROOT_DIR / "brains"


def load_brain_config(slug: str) -> dict:
    """Load brain config from brains/{slug}/brain.json"""
    config_path = BRAINS_DIR / slug / "brain.json"
    if not config_path.exists():
        print(f"ERROR: Brain config not found: {config_path}")
        sys.exit(1)
    with open(config_path) as f:
        return json.load(f)


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

    for atom in atoms:
        atom_conns = conn_map.get(atom["id"], [])
        entry = {
            "id": atom["id"],
            "content": atom["content"],
            "cluster": atom.get("cluster"),
            "topics": atom.get("topics", []),
            "source_ref": atom.get("source_ref"),
            "source_date": (atom.get("source_date") or "")[:10] if atom.get("source_date") else None,
            "confidence": atom.get("confidence"),
            "confidence_tier": atom.get("confidence_tier"),
        }
        if atom.get("original_quote"):
            entry["original_quote"] = atom["original_quote"]
        if atom.get("implication"):
            entry["implication"] = atom["implication"]
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

    atoms_with_conns = sum(1 for a in output["atoms"] if "connections" in a)
    print(f"  brain-atoms.json: {len(atoms)} atoms, {len(connections)} connections, {len(topic_index)} topics, {atoms_with_conns} linked")
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
        f"Extracted by Rob Gabel using a custom knowledge graph pipeline "
        f"(Firecrawl + Supabase + pgvector). Each insight is self-contained and searchable.\n"
    )
    # Shared LLM rules header
    lines.append("## LLM Usage Rules\n")
    lines.append("When using this brain as context, follow these rules:\n")
    lines.append(f"- **Persona:** You ARE {brain_name}. Always respond in first person (\"I think...\", \"In my experience...\", \"I've argued that...\"). Never refer to yourself in third person. The user is having a conversation WITH you, not reading about you.")
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


def _to_first_person(text: str, last_name: str = "") -> str:
    """Convert third-person references to first person for skill persona consistency.

    Handles common patterns like 'He believes' -> 'I believe',
    'Belsky argues' -> 'I argue', etc.
    """
    import re as _re

    def _deconj(verb):
        """Convert third-person singular verb to first-person."""
        verb_map = {
            "believes": "believe", "argues": "argue", "warns": "warn",
            "insists": "insist", "thinks": "think", "says": "say",
            "advocates": "advocate", "emphasizes": "emphasize",
        }
        return verb_map.get(verb, verb.rstrip("s") if verb.endswith("s") and not verb.endswith("ss") else verb)

    def _fix_pronoun_verb(m):
        word = m.group(1)
        # Check if this is an adverb (ends in -ly) followed by a verb
        rest = m.string[m.end():]
        adv_match = _re.match(r"^(\w+ly)\s+(\w+)", word + rest) if word.endswith("ly") else None
        if adv_match and word.endswith("ly"):
            # "He actively argues" -> need to also fix the next word
            # But regex already consumed; handle via second pass below
            pass
        return f"I {_deconj(word.lower())}"

    # "He's" / "She's" -> "I'm"
    text = _re.sub(r"\bHe's\b", "I'm", text)
    text = _re.sub(r"\bShe's\b", "I'm", text)
    # "He verb" / "She verb" patterns
    text = _re.sub(r"\bHe (\w+)", _fix_pronoun_verb, text)
    text = _re.sub(r"\bShe (\w+)", _fix_pronoun_verb, text)
    # Brain last name references (e.g., "Belsky believes" -> "I believe")
    if last_name:
        text = _re.sub(rf"\b{re.escape(last_name)}'s\b", "my", text)
        text = _re.sub(rf"\b{re.escape(last_name)} (\w+)", _fix_pronoun_verb, text)
    # Second pass: fix "I adverb verb-s" patterns (e.g., "I actively argues" -> "I actively argue")
    def _fix_adverb_verb(m):
        adv, verb = m.group(1), m.group(2)
        return f"I {adv} {_deconj(verb.lower())}"
    text = _re.sub(r"\bI (\w+ly) (\w+s)\b", _fix_adverb_verb, text)
    return text


def compute_skill_variables(atoms: list, connections: list, config: dict) -> dict:
    """Pre-compute template variables for skill files from brain data.

    Returns a dict of template variables that skills can reference via {{name}}.
    Each variable is a pre-rendered markdown block ready for inline insertion.
    """
    synthesis = config.get("synthesis", {})
    cluster_meta = config.get("clusters", {})
    last_name = config.get("brain_last_name", "")
    vars = {}

    # --- Guardrails block (for advise, teach, coach, predict) ---
    guardrail_lines = []
    does_not = synthesis.get("does_not_believe", [])
    if does_not:
        guardrail_lines.append("If the user's question assumes any of these, I disagree — lead with my actual position:\n")
        for item in does_not:
            guardrail_lines.append(f"- **{item['title']}** {item['desc']}")
    would_not = synthesis.get("would_not_say", [])
    if would_not:
        guardrail_lines.append("\nThings I would never say:\n")
        for item in would_not:
            guardrail_lines.append(f"- **{item['title']}** {item['desc']}")
    vars["guardrails_block"] = _to_first_person("\n".join(guardrail_lines), last_name) if guardrail_lines else ""

    # --- Coverage map (for advise, teach) ---
    cluster_counts = defaultdict(int)
    for atom in atoms:
        cluster_counts[atom.get("cluster", "uncategorized")] += 1
    deep, moderate, thin = [], [], []
    for key, count in sorted(cluster_counts.items(), key=lambda x: -x[1]):
        name = cluster_meta.get(key, {}).get("name", key)
        entry = f"- {name} ({count} atoms)"
        if count >= 20:
            deep.append(entry)
        elif count >= 10:
            moderate.append(entry)
        else:
            thin.append(entry)
    coverage_lines = []
    if deep:
        coverage_lines.append("I have deep expertise here (20+ atoms):\n" + "\n".join(deep))
    if moderate:
        coverage_lines.append("\nI've explored these (10-19 atoms):\n" + "\n".join(moderate))
    if thin:
        coverage_lines.append("\nI have less to say here (<10 atoms):\n" + "\n".join(thin))
    coverage_lines.append("\nIf the topic falls in a thin area, say so honestly. Bridge from adjacent deep areas if possible. Never fake depth I don't have.")
    vars["coverage_map"] = "\n".join(coverage_lines)

    # --- Voice anchors (for advise, teach, debate, coach, predict) ---
    # High-confidence atoms with original_quote, grouped by cluster
    voice_candidates = [
        a for a in atoms
        if a.get("original_quote") and a.get("confidence_tier") in ("high", "medium")
    ]
    # Sort: high confidence first, then by quote length (prefer punchy quotes)
    voice_candidates.sort(key=lambda a: (
        0 if a.get("confidence_tier") == "high" else 1,
        len(a.get("original_quote", ""))
    ))
    # Take up to 10, spread across clusters
    voice_lines = []
    cluster_used = defaultdict(int)
    for a in voice_candidates:
        cl = a.get("cluster", "uncategorized")
        if cluster_used[cl] >= 2:
            continue
        quote = a["original_quote"]
        if len(quote) > 200:
            quote = quote[:197] + "..."
        cl_name = cluster_meta.get(cl, {}).get("name", cl)
        voice_lines.append(f"- \"{quote}\" — *{cl_name}*")
        cluster_used[cl] += 1
        if len(voice_lines) >= 10:
            break
    vars["voice_anchors"] = "\n".join(voice_lines) if voice_lines else "Use the vocabulary and framing from brain-context.md."

    # --- Debate positions (for debate — guardrails reframed as ammunition) ---
    debate_lines = []
    contrarian = synthesis.get("contrarian_positions", [])
    if contrarian:
        debate_lines.append("Positions I hold strongly and will argue for:\n")
        for item in contrarian:
            debate_lines.append(f"- **{item['title']}** {item['desc']}")
    if does_not:
        debate_lines.append("\nPositions I reject — if the user argues FOR these, push back hard:\n")
        for item in does_not:
            debate_lines.append(f"- **{item['title']}** {item['desc']}")
    if would_not:
        debate_lines.append("\nEven when steel-manning the other side, never put these words in my mouth:\n")
        for item in would_not:
            debate_lines.append(f"- {item['title']}")
    vars["debate_positions"] = _to_first_person("\n".join(debate_lines), last_name)

    # --- Temporal map (for evolve) ---
    cluster_dates = defaultdict(list)
    for atom in atoms:
        date = atom.get("source_date")
        if date:
            cluster_dates[atom.get("cluster", "uncategorized")].append(str(date)[:10])
    good_evo, snapshot = [], []
    for cluster, dates in sorted(cluster_dates.items(), key=lambda x: -len(x[1])):
        name = cluster_meta.get(cluster, {}).get("name", cluster)
        dates_sorted = sorted(dates)
        if len(dates) >= 3:
            earliest, latest = dates_sorted[0][:4], dates_sorted[-1][:4]
            try:
                span = int(latest) - int(earliest)
            except ValueError:
                span = 0
            if span >= 2:
                good_evo.append(f"- {name}: {len(dates)} atoms spanning {earliest}-{latest} ({span}+ years)")
            else:
                snapshot.append(f"- {name}: {len(dates)} atoms, mostly from {earliest}")
        elif dates:
            snapshot.append(f"- {name}: only {len(dates)} dated atom(s)")
    temporal_lines = []
    if good_evo:
        temporal_lines.append("Topics where I can trace real evolution (multi-year span):\n" + "\n".join(good_evo))
    if snapshot:
        temporal_lines.append("\nTopics where I only have a snapshot (limited evolution tracking):\n" + "\n".join(snapshot))
    temporal_lines.append("\nFor snapshot topics, be honest: \"I can share my current position, but I don't have enough dated material to show how it evolved.\"")
    vars["temporal_map"] = "\n".join(temporal_lines)

    # --- Highlight reel (for surprise — top atoms ranked by richness) ---
    def atom_richness(atom):
        s = 0
        if atom.get("confidence_tier") == "high":
            s += 3
        elif atom.get("confidence_tier") == "medium":
            s += 1
        if atom.get("original_quote"):
            s += 2
        if atom.get("implication"):
            s += 1
        return s
    ranked = sorted(atoms, key=atom_richness, reverse=True)
    highlight_lines = []
    for i, atom in enumerate(ranked[:25], 1):
        quote = atom.get("original_quote", atom["content"])
        if len(quote) > 200:
            quote = quote[:197] + "..."
        cl = atom.get("cluster", "uncategorized")
        cl_name = cluster_meta.get(cl, {}).get("name", cl)
        tier = atom.get("confidence_tier", "medium")
        highlight_lines.append(f"{i}. \"{quote}\" — *{cl_name}, {tier}*")
    vars["highlight_reel"] = "\n".join(highlight_lines)

    # --- Bridge examples (for connect — cross-cluster connections) ---
    atom_map = {a["id"]: a for a in atoms}
    cross_cluster = []
    for c in connections:
        a1 = atom_map.get(c.get("atom_id_1"))
        a2 = atom_map.get(c.get("atom_id_2"))
        if a1 and a2 and a1.get("cluster") != a2.get("cluster"):
            cross_cluster.append({
                "c1": cluster_meta.get(a1.get("cluster", ""), {}).get("name", a1.get("cluster", "")),
                "c2": cluster_meta.get(a2.get("cluster", ""), {}).get("name", a2.get("cluster", "")),
                "s1": a1["content"][:100],
                "s2": a2["content"][:100],
                "rel": c.get("relationship", "related"),
            })
    # Prioritize contradicts and extends over supports/related
    rel_priority = {"contradicts": 3, "extends": 2, "related": 1, "supports": 0}
    cross_cluster.sort(key=lambda x: rel_priority.get(x["rel"], 0), reverse=True)
    bridge_lines = []
    seen_pairs = set()
    for cc in cross_cluster:
        pair = tuple(sorted([cc["c1"], cc["c2"]]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        bridge_lines.append(f"- **{cc['c1']} <> {cc['c2']}** ({cc['rel']}): \"{cc['s1']}\" connects to \"{cc['s2']}\"")
        if len(bridge_lines) >= 8:
            break
    vars["bridge_examples"] = "\n".join(bridge_lines) if bridge_lines else "No cross-cluster connections available yet."

    # --- Chain examples (for predict — atoms showing cascading logic) ---
    chain_atoms = [
        a for a in atoms
        if a.get("confidence_tier") in ("high", "medium")
        and any(marker in (a.get("content", "") + a.get("original_quote", ""))
                for marker in ["\u2192", "leads to", "which means", "second-order", "third-order", "cascade"])
    ]
    chain_lines = []
    patterns = synthesis.get("thinking_patterns", [])
    chain_pattern = next((p for p in patterns if "chain" in p.get("name", "").lower()
                          or "implication" in p.get("name", "").lower()), None)
    if chain_pattern:
        chain_lines.append(f"My signature move: {chain_pattern['desc']}\n")
    if chain_atoms:
        chain_lines.append("Examples of my cascading logic (match this style):\n")
        for a in chain_atoms[:5]:
            quote = a.get("original_quote", a["content"])
            if len(quote) > 250:
                quote = quote[:247] + "..."
            chain_lines.append(f"- \"{quote}\"")
    vars["chain_examples"] = "\n".join(chain_lines) if chain_lines else ""

    return vars


def export_skill_files(config: dict, atoms: list, connections: list, output_dir: Path):
    """Render SKILL.md, README.md, and all skill templates with pre-computed variables."""
    skill_vars = compute_skill_variables(atoms, connections, config)
    extra_vars = {
        "atom_count": str(len(atoms)),
        "connection_count": str(len(connections)),
        "vocabulary_examples": config.get("vocabulary_examples", "specific terms, frameworks, and labels"),
    }
    extra_vars.update(skill_vars)

    # Render top-level templates (SKILL.md, README.md)
    for template_name in ["SKILL.md.template", "README.md.template"]:
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


def main():
    parser = argparse.ArgumentParser(description="Export a brain pack from Supabase or local files")
    parser.add_argument("--brain", required=True, help="Brain slug (matches brains/{slug}/brain.json)")
    parser.add_argument("--from-files", nargs=2, metavar=("ATOMS_FILE", "CONNECTIONS_FILE"),
                        help="Load from local JSON files instead of Supabase")
    parser.add_argument("--atoms-file", help="Path to atoms JSON (alternative to --from-files)")
    parser.add_argument("--connections-file", help="Path to connections JSON")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--skip-skills", action="store_true", help="Skip rendering skill templates")
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
        print("ERROR: Provide --from-files or --atoms-file + --connections-file")
        print("       (Supabase direct fetch requires SUPABASE_URL + SUPABASE_SERVICE_KEY — not yet implemented)")
        sys.exit(1)

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
        export_skill_files(config, atoms, connections, output_dir)

    # Copy explore.html template
    explore_template = TEMPLATES_DIR / "explore.html.template"
    if explore_template.exists():
        import shutil
        shutil.copy2(explore_template, output_dir / "explore.html")
        print(f"\n  explore.html copied from template")

    print(f"\nDone! Output in: {output_dir}")


if __name__ == "__main__":
    main()
