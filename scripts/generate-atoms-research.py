#!/usr/bin/env python3
"""
Deep-research atom generation for BrainsForSale.

For subjects where direct content ingestion isn't possible (deceased figures,
pre-blogging era thinkers), this script uses Claude with web search to generate
high-quality atoms based on exemplar atoms from an existing brain.

Strategy:
1. Load exemplar atoms from a reference brain (e.g., scott-belsky) to show format/quality
2. Load the target brain's brain.json for clusters, synthesis, and identity
3. Generate atoms cluster-by-cluster using Claude, grounded in publicly documented
   speeches, interviews, and writings

Usage:
    # Generate atoms for all clusters (full run)
    python scripts/generate-atoms-research.py --brain steve-jobs --reference scott-belsky

    # Generate atoms for specific clusters only
    python scripts/generate-atoms-research.py --brain steve-jobs --reference scott-belsky \
        --clusters product_design taste_craft focus_strategy

    # Dry run — show prompts without calling API
    python scripts/generate-atoms-research.py --brain steve-jobs --reference scott-belsky --dry-run

    # Use a specific model
    python scripts/generate-atoms-research.py --brain steve-jobs --reference scott-belsky --model claude-sonnet-4-20250514
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def load_exemplar_atoms(reference_slug: str, n_per_cluster: int = 3) -> list:
    """Load a diverse sample of atoms from a reference brain as format exemplars."""
    research_dir = Path(f"brains/{reference_slug}/research")
    pack_dir = Path(f"brains/{reference_slug}/pack")

    atoms = []

    # Try research files first (they have the right format)
    for f in sorted(research_dir.glob("*-atoms.json")) if research_dir.exists() else []:
        with open(f) as fh:
            atoms.extend(json.load(fh))

    # Fall back to pack/brain-atoms.json
    if not atoms:
        brain_atoms_path = pack_dir / "brain-atoms.json"
        if brain_atoms_path.exists():
            with open(brain_atoms_path) as fh:
                data = json.load(fh)
                atoms = data.get("atoms", [])

    if not atoms:
        print(f"WARNING: No exemplar atoms found for {reference_slug}")
        return []

    # Sample diverse atoms: pick top-confidence ones from different clusters
    by_cluster = {}
    for atom in atoms:
        cluster = atom.get("cluster", "unknown")
        by_cluster.setdefault(cluster, []).append(atom)

    exemplars = []
    for cluster, cluster_atoms in by_cluster.items():
        # Sort by confidence descending
        sorted_atoms = sorted(cluster_atoms, key=lambda a: a.get("confidence", 0.8), reverse=True)
        exemplars.extend(sorted_atoms[:n_per_cluster])

    return exemplars[:15]  # Cap at 15 exemplars to keep prompt manageable


def generate_cluster_atoms(
    brain_json: dict,
    cluster_key: str,
    cluster_info: dict,
    exemplar_atoms: list,
    sources_json: dict,
    model: str = "claude-sonnet-4-20250514",
) -> list:
    """Generate atoms for a single cluster using Claude."""
    if not HAS_ANTHROPIC:
        print("ERROR: anthropic SDK not installed")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    brain_name = brain_json["brain_name"]
    first_name = brain_json["brain_first_name"]
    date_range = brain_json.get("date_range", "unknown")

    # Format exemplars
    exemplar_text = json.dumps(exemplar_atoms[:5], indent=2)

    # Format synthesis context
    synthesis = brain_json.get("synthesis", {})
    first_principles = synthesis.get("first_principles", [])
    fp_text = "\n".join(f"- {fp['title']}: {fp['desc']}" for fp in first_principles)

    contrarian = synthesis.get("contrarian_positions", [])
    contrarian_text = "\n".join(f"- {c['title']}: {c['desc']}" for c in contrarian)

    thinking_patterns = synthesis.get("thinking_patterns", [])
    tp_text = "\n".join(f"- {t['name']}: {t['desc']}" for t in thinking_patterns)

    # Format source list for grounding
    source_titles = "\n".join(
        f"- {s['title']} ({s['date']}): {s['description']}"
        for s in sources_json.get("sources", [])
        if s.get("priority") in ("essential", "high")
    )

    # All clusters for reference
    all_clusters = "\n".join(
        f"- {k}: {v['name']}" for k, v in brain_json.get("clusters", {}).items()
    )

    prompt = f"""You are a research assistant generating "atoms" — discrete units of knowledge — for a
brain pack about {brain_name} ({date_range}).

YOUR TASK: Generate 15-25 high-quality atoms for the cluster "{cluster_info['name']}".

CLUSTER DESCRIPTION: {cluster_info['description']}

IMPORTANT RULES:
1. Every atom must be grounded in {first_name}'s ACTUAL documented statements, speeches,
   interviews, or publicly known positions. Do NOT invent or speculate.
2. "original_quote" must be {first_name}'s REAL words — actual quotes from speeches, interviews,
   or documented conversations. If you cannot find a real quote, omit the field rather than fabricate.
3. "content" is your distilled 2-4 sentence statement of the insight.
4. "implication" is the "so what" — what this means for builders, creators, and leaders today.
5. "source_ref" should reference the specific speech, interview, or appearance.
6. "source_date" should be as precise as possible (YYYY-MM-DD or YYYY).
7. Set confidence: 0.95 for direct quotes, 0.85 for well-documented positions, 0.75 for reasonable inferences.
8. Assign 2-5 topic tags per atom.

{first_name.upper()}'S FIRST PRINCIPLES (for context):
{fp_text}

{first_name.upper()}'S THINKING PATTERNS:
{tp_text}

{first_name.upper()}'S CONTRARIAN POSITIONS:
{contrarian_text}

KEY SOURCES TO DRAW FROM:
{source_titles}

ALL AVAILABLE CLUSTERS (for reference — assign to "{cluster_key}" unless a different one fits better):
{all_clusters}

EXEMPLAR ATOMS (from another brain pack — match this format and quality):
{exemplar_text}

OUTPUT FORMAT — Return ONLY a JSON array:
[
  {{
    "content": "Distilled 2-4 sentence insight...",
    "original_quote": "{first_name}'s actual documented words...",
    "implication": "What this means for builders/leaders today...",
    "cluster": "{cluster_key}",
    "topics": ["topic1", "topic2", "topic3"],
    "confidence": 0.92,
    "source_type": "video",
    "source_ref": "Stanford commencement speech, 2005",
    "source_date": "2005-06-12"
  }}
]

Generate 15-25 atoms. Prioritize {first_name}'s most provocative, original, and timeless ideas.
Avoid generic observations. Every atom should make a reader think "I didn't know he said/thought that"
or "that reframes how I think about this."

Return ONLY the JSON array."""

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=12000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)

    atoms = json.loads(text)
    return atoms


def main():
    parser = argparse.ArgumentParser(description="Deep-research atom generation for BrainsForSale")
    parser.add_argument("--brain", required=True, help="Target brain slug")
    parser.add_argument("--reference", default="scott-belsky",
                        help="Reference brain slug for exemplar atoms (default: scott-belsky)")
    parser.add_argument("--clusters", nargs="+", help="Specific clusters to generate (default: all)")
    parser.add_argument("--model", default="claude-sonnet-4-20250514", help="Claude model to use")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--atoms-per-cluster", type=int, default=20,
                        help="Target atoms per cluster (guidance, not enforced)")
    args = parser.parse_args()

    # Load target brain config
    brain_path = Path(f"brains/{args.brain}/brain.json")
    if not brain_path.exists():
        print(f"ERROR: {brain_path} not found")
        sys.exit(1)
    with open(brain_path) as f:
        brain_json = json.load(f)

    # Load sources
    sources_path = Path(f"brains/{args.brain}/source/sources.json")
    sources_json = {}
    if sources_path.exists():
        with open(sources_path) as f:
            sources_json = json.load(f)

    # Load exemplar atoms from reference brain
    print(f"Loading exemplar atoms from {args.reference}...")
    exemplars = load_exemplar_atoms(args.reference)
    print(f"  Loaded {len(exemplars)} exemplar atoms")

    # Determine clusters to process
    clusters = brain_json.get("clusters", {})
    if args.clusters:
        clusters = {k: v for k, v in clusters.items() if k in args.clusters}

    print(f"\nGenerating atoms for {brain_json['brain_name']}")
    print(f"Clusters: {len(clusters)}")
    print(f"Model: {args.model}")
    print(f"Reference: {args.reference}")
    print()

    all_atoms = []
    for i, (cluster_key, cluster_info) in enumerate(clusters.items()):
        print(f"[{i+1}/{len(clusters)}] {cluster_info['name']}...")

        if args.dry_run:
            print(f"  [DRY RUN] Would generate ~{args.atoms_per_cluster} atoms")
            continue

        try:
            atoms = generate_cluster_atoms(
                brain_json, cluster_key, cluster_info,
                exemplars, sources_json, args.model
            )
            print(f"  Generated {len(atoms)} atoms")
            all_atoms.extend(atoms)

            # Rate limiting — be gentle with the API
            if i < len(clusters) - 1:
                time.sleep(2)

        except json.JSONDecodeError as e:
            print(f"  ERROR: Failed to parse response as JSON: {e}")
        except Exception as e:
            print(f"  ERROR: {e}")

    if all_atoms and not args.dry_run:
        output_path = Path(f"brains/{args.brain}/research/deep-research-atoms.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(all_atoms, f, indent=2)

        # Stats
        cluster_counts = {}
        for atom in all_atoms:
            c = atom.get("cluster", "unknown")
            cluster_counts[c] = cluster_counts.get(c, 0) + 1

        print(f"\n{'='*60}")
        print(f"TOTAL: {len(all_atoms)} atoms saved to {output_path}")
        print(f"\nBy cluster:")
        for c, count in sorted(cluster_counts.items(), key=lambda x: -x[1]):
            name = clusters.get(c, {}).get("name", c)
            print(f"  {name}: {count}")
        print(f"\nNext steps:")
        print(f"  1. Review and curate: brains/{args.brain}/research/deep-research-atoms.json")
        print(f"  2. Add YouTube transcript atoms: python scripts/ingest-youtube.py --brain {args.brain} --decompose")
        print(f"  3. Merge all atom sources into a single file")
        print(f"  4. Load into Supabase")
        print(f"  5. Run connections: python scripts/enrich-connections.py --brain {args.brain} --discover --llm")
        print(f"  6. Export: python scripts/export-brain.py --brain {args.brain} --from-files ...")


if __name__ == "__main__":
    main()
