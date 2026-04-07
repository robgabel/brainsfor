#!/usr/bin/env python3
"""
Connection enrichment for brain atoms (generic — works with any brain).

Discovers new connections between atoms using:
1. Topic overlap (Jaccard similarity) — within AND across clusters
2. Temporal proximity — atoms published within 7 days with shared topics
3. LLM-assisted analysis — contradicts, extends, inspired_by (within + cross-cluster)

Usage:
  python scripts/enrich-connections.py --brain scott-belsky --discover
  python scripts/enrich-connections.py --brain scott-belsky --discover --llm
  python scripts/enrich-connections.py --brain scott-belsky --discover --llm --auto-apply
  python scripts/enrich-connections.py --brain scott-belsky --apply FILE
  python scripts/enrich-connections.py --brain scott-belsky --stats

Requires: SUPABASE_URL + SUPABASE_SERVICE_KEY (in .env), ANTHROPIC_API_KEY (for --llm)
"""

import argparse
import json
import os
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass

try:
    from supabase import create_client
except ImportError:
    print("pip install supabase python-dotenv")
    sys.exit(1)

# --- Paths ---
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
BRAINS_DIR = ROOT_DIR / "brains"

# --- Config ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://uzediwokyshjbsymevtp.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# LLM model — Sonnet for quality contradiction detection
LLM_MODEL = "claude-3-haiku-20240307"


def load_brain_config(slug: str) -> dict:
    """Load brain config from brains/{slug}/brain.json"""
    config_path = BRAINS_DIR / slug / "brain.json"
    if not config_path.exists():
        print(f"ERROR: Brain config not found: {config_path}")
        sys.exit(1)
    with open(config_path) as f:
        return json.load(f)


def fetch_all_data(supabase, atoms_table: str, connections_table: str):
    """Fetch all atoms and existing connections."""
    atoms_resp = supabase.table(atoms_table).select(
        "id, content, cluster, topics, source_date, confidence"
    ).execute()

    conn_resp = supabase.table(connections_table).select(
        "atom_id_1, atom_id_2, relationship"
    ).execute()

    atoms = atoms_resp.data
    connections = conn_resp.data

    existing = set()
    for c in connections:
        pair = tuple(sorted([c["atom_id_1"], c["atom_id_2"]]))
        existing.add(pair)

    return atoms, connections, existing


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def discover_topic_overlap(atoms: list, existing: set, threshold: float = 0.3, cross_cluster: bool = True) -> list:
    """Find candidate connections via topic overlap.

    When cross_cluster=True (default), also discovers connections between atoms
    in different clusters using a higher threshold (0.5) to reduce noise.
    """
    candidates = []
    clusters = defaultdict(list)
    for atom in atoms:
        clusters[atom.get("cluster", "unknown")].append(atom)

    # Within-cluster: use standard threshold
    within_count = 0
    for cluster_key, cluster_atoms in clusters.items():
        for a, b in combinations(cluster_atoms, 2):
            pair = tuple(sorted([a["id"], b["id"]]))
            if pair in existing:
                continue

            topics_a = set(a.get("topics") or [])
            topics_b = set(b.get("topics") or [])
            sim = jaccard_similarity(topics_a, topics_b)

            if sim >= threshold:
                candidates.append({
                    "atom_id_1": a["id"],
                    "atom_id_2": b["id"],
                    "relationship": "related",
                    "confidence": round(min(sim, 0.90), 2),
                    "method": "topic_overlap",
                    "cluster": cluster_key,
                    "similarity": round(sim, 3),
                    "content_1": a["content"][:100],
                    "content_2": b["content"][:100],
                    "shared_topics": list(topics_a & topics_b)
                })
                within_count += 1

    # Cross-cluster: higher threshold to keep quality high
    cross_count = 0
    if cross_cluster:
        cross_threshold = max(threshold, 0.5)  # At least 0.5 for cross-cluster
        cluster_keys = sorted(clusters.keys())
        for ci in range(len(cluster_keys)):
            for cj in range(ci + 1, len(cluster_keys)):
                atoms_ci = clusters[cluster_keys[ci]]
                atoms_cj = clusters[cluster_keys[cj]]
                for a in atoms_ci:
                    for b in atoms_cj:
                        pair = tuple(sorted([a["id"], b["id"]]))
                        if pair in existing:
                            continue

                        topics_a = set(a.get("topics") or [])
                        topics_b = set(b.get("topics") or [])
                        sim = jaccard_similarity(topics_a, topics_b)

                        if sim >= cross_threshold:
                            candidates.append({
                                "atom_id_1": a["id"],
                                "atom_id_2": b["id"],
                                "relationship": "related",
                                "confidence": round(min(sim, 0.85), 2),  # Slightly lower cap for cross-cluster
                                "method": "topic_overlap_cross_cluster",
                                "cluster": f"{cluster_keys[ci]} ↔ {cluster_keys[cj]}",
                                "similarity": round(sim, 3),
                                "content_1": a["content"][:100],
                                "content_2": b["content"][:100],
                                "shared_topics": list(topics_a & topics_b)
                            })
                            cross_count += 1

    print(f"    Within-cluster: {within_count}, Cross-cluster: {cross_count}")
    candidates.sort(key=lambda c: c["similarity"], reverse=True)
    return candidates


def discover_temporal(atoms: list, existing: set) -> list:
    """Find candidate 'extends' connections between atoms published within 7 days with overlapping topics."""
    candidates = []
    dated = [a for a in atoms if a.get("source_date")]
    dated.sort(key=lambda a: a["source_date"])

    for i, a in enumerate(dated):
        for j in range(i + 1, len(dated)):
            b = dated[j]
            date_a = a["source_date"][:10]
            date_b = b["source_date"][:10]

            try:
                da = datetime.strptime(date_a, "%Y-%m-%d")
                db = datetime.strptime(date_b, "%Y-%m-%d")
                if abs((db - da).days) > 7:
                    break
            except ValueError:
                continue

            pair = tuple(sorted([a["id"], b["id"]]))
            if pair in existing:
                continue

            topics_a = set(a.get("topics") or [])
            topics_b = set(b.get("topics") or [])
            overlap = topics_a & topics_b

            if len(overlap) >= 2:
                candidates.append({
                    "atom_id_1": a["id"],
                    "atom_id_2": b["id"],
                    "relationship": "extends",
                    "confidence": 0.80,
                    "method": "temporal_proximity",
                    "cluster": a.get("cluster"),
                    "shared_topics": list(overlap),
                    "content_1": a["content"][:100],
                    "content_2": b["content"][:100]
                })

    return candidates


def discover_llm_connections(atoms: list, existing: set, brain_name: str, source_desc: str, cross_cluster: bool = True) -> list:
    """Use LLM to find contradicts, extends, inspired_by within and across clusters."""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    candidates = []

    clusters = defaultdict(list)
    for atom in atoms:
        clusters[atom.get("cluster", "unknown")].append(atom)

    # --- Within-cluster analysis ---
    within_prompt = """Analyze these knowledge atoms from {brain_name}'s {source_desc}. All are in the "{cluster}" cluster.

Find connections between atoms. Focus ESPECIALLY on:
1. **contradicts** — Where {brain_name} contradicts themselves, holds tension between opposing ideas, or where two atoms pull in different directions. These are the MOST VALUABLE. Be aggressive — intellectual tension is the point.
2. **extends** — Where one atom builds on, deepens, or evolves another
3. **inspired_by** — Where one idea clearly led to or motivated another

Return a JSON array. Each item: {{"atom_1_index": N, "atom_2_index": M, "relationship": "contradicts|extends|inspired_by", "confidence": 0.70-0.95, "rationale": "one sentence why"}}

If no connections found, return [].

ATOMS:
{atoms_text}"""

    cluster_keys = sorted(clusters.keys())
    total_steps = len([k for k in cluster_keys if len(clusters[k]) >= 3])
    if cross_cluster:
        total_steps += len(cluster_keys) * (len(cluster_keys) - 1) // 2
    step = 0

    for cluster_key in cluster_keys:
        cluster_atoms = clusters[cluster_key]
        if len(cluster_atoms) < 3:
            continue

        step += 1
        print(f"  [{step}/{total_steps}] LLM within-cluster: {cluster_key} ({len(cluster_atoms)} atoms)...")

        atoms_text = ""
        for i, atom in enumerate(cluster_atoms):
            date = (atom.get("source_date") or "")[:10]
            atoms_text += f"\n[{i}] ({date}) {atom['content']}\n"

        prompt = within_prompt.format(
            brain_name=brain_name,
            source_desc=source_desc,
            cluster=cluster_key,
            atoms_text=atoms_text
        )

        new = _call_llm_for_connections(client, prompt, cluster_atoms, existing, cluster_key)
        candidates.extend(new)
        time.sleep(0.5)

    # --- Cross-cluster analysis ---
    if cross_cluster:
        cross_prompt = """Analyze these knowledge atoms from {brain_name}'s {source_desc}. They come from TWO DIFFERENT topic clusters: "{cluster_a}" and "{cluster_b}".

Find CROSS-CLUSTER connections — ideas that bridge these domains. Focus on:
1. **contradicts** — Where an idea in one domain contradicts or creates tension with an idea in another domain. MOST VALUABLE.
2. **extends** — Where an idea in one domain deepens or builds on an idea from the other
3. **inspired_by** — Where thinking in one domain clearly influenced the other

These cross-cluster connections are especially valuable because they reveal how {brain_name}'s thinking connects across different domains.

Return a JSON array. Each item: {{"atom_1_index": N, "atom_2_index": M, "relationship": "contradicts|extends|inspired_by", "confidence": 0.70-0.95, "rationale": "one sentence why"}}

Atom indices 0-{last_a} are from "{cluster_a}", indices {first_b}-{last_b} are from "{cluster_b}".

If no cross-cluster connections found, return [].

ATOMS:
{atoms_text}"""

        for ci in range(len(cluster_keys)):
            for cj in range(ci + 1, len(cluster_keys)):
                ca = cluster_keys[ci]
                cb = cluster_keys[cj]
                atoms_a = clusters[ca]
                atoms_b = clusters[cb]

                # Skip if either cluster is too small
                if len(atoms_a) < 2 or len(atoms_b) < 2:
                    continue

                # For large cluster pairs, sample to keep context manageable
                max_per_cluster = 15
                sample_a = atoms_a[:max_per_cluster] if len(atoms_a) > max_per_cluster else atoms_a
                sample_b = atoms_b[:max_per_cluster] if len(atoms_b) > max_per_cluster else atoms_b

                combined = sample_a + sample_b

                step += 1
                print(f"  [{step}/{total_steps}] LLM cross-cluster: {ca} ↔ {cb} ({len(sample_a)}+{len(sample_b)} atoms)...")

                atoms_text = ""
                for i, atom in enumerate(combined):
                    date = (atom.get("source_date") or "")[:10]
                    label = ca if i < len(sample_a) else cb
                    atoms_text += f"\n[{i}] [{label}] ({date}) {atom['content']}\n"

                prompt = cross_prompt.format(
                    brain_name=brain_name,
                    source_desc=source_desc,
                    cluster_a=ca,
                    cluster_b=cb,
                    last_a=len(sample_a) - 1,
                    first_b=len(sample_a),
                    last_b=len(combined) - 1,
                    atoms_text=atoms_text
                )

                new = _call_llm_for_connections(client, prompt, combined, existing, f"{ca} ↔ {cb}")
                candidates.extend(new)
                time.sleep(0.5)

    return candidates


def _call_llm_for_connections(client, prompt: str, atoms_list: list, existing: set, cluster_label: str) -> list:
    """Call LLM and parse connection candidates. Shared by within/cross-cluster analysis."""
    candidates = []
    try:
        message = client.messages.create(
            model=LLM_MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = message.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        # Try to extract JSON array from response (handles prose wrappers)
        import re
        if not text.startswith("["):
            match = re.search(r'\[[\s\S]*\]', text)
            if match:
                text = match.group(0)

        found = json.loads(text)

        # Deduplicate by atom pair within this batch
        seen_pairs = set()
        for item in found:
            idx_a = item.get("atom_1_index", -1)
            idx_b = item.get("atom_2_index", -1)
            if idx_a < 0 or idx_b < 0 or idx_a >= len(atoms_list) or idx_b >= len(atoms_list):
                continue

            a = atoms_list[idx_a]
            b = atoms_list[idx_b]
            pair = tuple(sorted([a["id"], b["id"]]))

            if pair in existing or pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            rel = item.get("relationship", "related")
            if rel not in ("contradicts", "extends", "inspired_by", "related"):
                rel = "related"

            candidates.append({
                "atom_id_1": a["id"],
                "atom_id_2": b["id"],
                "relationship": rel,
                "confidence": item.get("confidence", 0.80),
                "method": "llm_analysis",
                "cluster": cluster_label,
                "rationale": item.get("rationale", ""),
                "content_1": a["content"][:100],
                "content_2": b["content"][:100]
            })
            existing.add(pair)

        rel_breakdown = defaultdict(int)
        for c in candidates:
            rel_breakdown[c["relationship"]] += 1
        if candidates:
            print(f"    Found {len(candidates)}: {dict(rel_breakdown)}")

    except (json.JSONDecodeError, KeyError) as e:
        print(f"    Parse error for {cluster_label}: {e}")
    except Exception as e:
        print(f"    Error for {cluster_label}: {e}")

    return candidates


def print_stats(atoms: list, connections: list, existing: set):
    """Print connection stats."""
    conn_counts = defaultdict(int)
    for a in atoms:
        conn_counts[a["id"]] = 0

    rel_counts = defaultdict(int)
    for c in connections:
        conn_counts[c["atom_id_1"]] += 1
        conn_counts[c["atom_id_2"]] += 1
        rel_counts[c["relationship"]] += 1

    orphans = sum(1 for v in conn_counts.values() if v == 0)
    total = len(connections)
    avg = total * 2 / len(atoms) if atoms else 0

    print(f"\n--- Connection Stats ---")
    print(f"Total atoms: {len(atoms)}")
    print(f"Total connections: {total}")
    print(f"Avg connections per atom: {avg:.1f}")
    print(f"Orphan atoms (0 connections): {orphans}")
    print(f"\nBy type:")
    for rel, count in sorted(rel_counts.items(), key=lambda x: -x[1]):
        print(f"  {rel}: {count}")

    # Quality assessment
    contradicts = rel_counts.get("contradicts", 0)
    inspired = rel_counts.get("inspired_by", 0)
    print(f"\n--- Quality Assessment ---")
    if contradicts < 5:
        print(f"  ⚠️  contradicts: {contradicts} (target: 30+) — run with --llm to add")
    elif contradicts < 30:
        print(f"  🔶 contradicts: {contradicts} (target: 30+)")
    else:
        print(f"  ✅ contradicts: {contradicts} (target: 30+)")

    if inspired < 10:
        print(f"  ⚠️  inspired_by: {inspired} (target: 20+) — run with --llm to add")
    else:
        print(f"  ✅ inspired_by: {inspired} (target: 20+)")

    if orphans > 0:
        print(f"  ⚠️  orphans: {orphans} (target: 0)")
    else:
        print(f"  ✅ orphans: 0")

    print(f"\nTarget: 800+ connections, 30+ contradicts, 20+ inspired_by, 0 orphans")


def apply_connections(supabase, connections_table: str, filepath: str):
    """Write approved connections to Supabase."""
    with open(filepath) as f:
        candidates = json.load(f)

    applied = 0
    skipped = 0
    errors = 0
    for item in candidates:
        if item.get("_skip"):
            skipped += 1
            continue

        row = {
            "id": str(uuid.uuid4()),
            "atom_id_1": item["atom_id_1"],
            "atom_id_2": item["atom_id_2"],
            "relationship": item["relationship"],
            "confidence": item.get("confidence", 0.80)
        }

        try:
            supabase.table(connections_table).insert(row).execute()
            applied += 1
        except Exception as e:
            errors += 1
            print(f"  Error inserting: {e}")

    print(f"\nApplied {applied} new connections (skipped {skipped}, errors {errors})")


def main():
    parser = argparse.ArgumentParser(description="Enrich brain connections")
    parser.add_argument("--brain", required=True, help="Brain slug (matches brains/{slug}/brain.json)")
    parser.add_argument("--discover", action="store_true", help="Find candidate connections")
    parser.add_argument("--llm", action="store_true", help="Include LLM-assisted discovery (slower, better)")
    parser.add_argument("--cross-cluster", action="store_true", default=True,
                        help="Include cross-cluster connections (default: true)")
    parser.add_argument("--no-cross-cluster", action="store_true", help="Skip cross-cluster connections")
    parser.add_argument("--auto-apply", action="store_true",
                        help="Automatically apply discovered connections to Supabase (no review step)")
    parser.add_argument("--apply", metavar="FILE", help="Write approved connections from review file to Supabase")
    parser.add_argument("--stats", action="store_true", help="Show current connection stats")
    parser.add_argument("--threshold", type=float, default=0.3, help="Jaccard threshold (default: 0.3)")
    args = parser.parse_args()

    if args.no_cross_cluster:
        args.cross_cluster = False

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

    brain_name = config["brain_name"]
    source_desc = config.get("brain_source_description", "published content")

    print(f"Brain: {brain_name} ({args.brain})")
    print(f"Tables: {atoms_table}, {connections_table}")
    print(f"LLM model: {LLM_MODEL}")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Output dir for review files
    output_dir = BRAINS_DIR / config["brain_slug"] / "data"

    print("Fetching all atoms and connections...")
    atoms, connections, existing = fetch_all_data(supabase, atoms_table, connections_table)
    print(f"  {len(atoms)} atoms, {len(connections)} existing connections")

    if args.stats:
        print_stats(atoms, connections, existing)
        return

    if args.apply:
        print(f"Applying connections from {args.apply}...")
        apply_connections(supabase, connections_table, args.apply)
        return

    if args.discover:
        all_candidates = []
        start_time = time.time()

        print(f"\nDiscovering topic overlap connections (cross-cluster: {args.cross_cluster})...")
        topic_candidates = discover_topic_overlap(atoms, existing, args.threshold, cross_cluster=args.cross_cluster)
        print(f"  Found {len(topic_candidates)} candidates via topic overlap")
        all_candidates.extend(topic_candidates)

        for c in topic_candidates:
            pair = tuple(sorted([c["atom_id_1"], c["atom_id_2"]]))
            existing.add(pair)

        print("\nDiscovering temporal proximity connections...")
        temporal_candidates = discover_temporal(atoms, existing)
        print(f"  Found {len(temporal_candidates)} candidates via temporal proximity")
        all_candidates.extend(temporal_candidates)

        for c in temporal_candidates:
            pair = tuple(sorted([c["atom_id_1"], c["atom_id_2"]]))
            existing.add(pair)

        if args.llm:
            if not ANTHROPIC_KEY:
                print("ERROR: Set ANTHROPIC_API_KEY for --llm mode")
                sys.exit(1)
            print(f"\nDiscovering LLM-assisted connections (cross-cluster: {args.cross_cluster})...")
            llm_candidates = discover_llm_connections(
                atoms, existing, brain_name, source_desc,
                cross_cluster=args.cross_cluster
            )
            print(f"  Found {len(llm_candidates)} candidates via LLM analysis")
            all_candidates.extend(llm_candidates)

        elapsed = time.time() - start_time
        rel_summary = defaultdict(int)
        method_summary = defaultdict(int)
        for c in all_candidates:
            rel_summary[c["relationship"]] += 1
            method_summary[c["method"]] += 1

        print(f"\n--- Discovery Summary ({elapsed:.0f}s) ---")
        print(f"Total candidates: {len(all_candidates)}")
        print(f"By relationship: {dict(rel_summary)}")
        print(f"By method: {dict(method_summary)}")
        print(f"Would bring total to: {len(connections) + len(all_candidates)}")

        if args.auto_apply and all_candidates:
            print(f"\n--- Auto-applying {len(all_candidates)} connections ---")
            output_dir.mkdir(exist_ok=True)
            temp_file = output_dir / "connection-candidates-autoapply.json"
            with open(temp_file, "w") as f:
                json.dump(all_candidates, f, indent=2)
            apply_connections(supabase, connections_table, str(temp_file))
            print("Done. Re-export the brain pack to update brain-atoms.json.")
        elif all_candidates:
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / "connection-candidates.json"
            with open(output_file, "w") as f:
                json.dump(all_candidates, f, indent=2)
            print(f"\nReview file: {output_file}")
            print(f"To apply: python scripts/enrich-connections.py --brain {args.brain} --apply {output_file}")
            print(f"To auto-apply: add --auto-apply flag to skip review")
        else:
            print("\nNo new candidates found.")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
