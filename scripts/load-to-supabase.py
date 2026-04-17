#!/usr/bin/env python3
"""
Load local brain atoms + connections into Supabase tables.

Usage:
  python scripts/load-to-supabase.py --brain charlie-munger --atoms --connections
  python scripts/load-to-supabase.py --brain peter-zeihan --connections
  python scripts/load-to-supabase.py --brain charlie-munger --atoms --dry-run

Requires: SUPABASE_URL + SUPABASE_SERVICE_KEY (in .env)
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    # Try website env first (has working anon key), then root env
    load_dotenv(Path(__file__).resolve().parent.parent / "website" / ".env.local", override=True)
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
except ImportError:
    pass

try:
    from supabase import create_client
except ImportError:
    print("pip install supabase python-dotenv")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
BRAINS_DIR = ROOT_DIR / "brains"

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL", "https://uzediwokyshjbsymevtp.supabase.co")

# Prefer service key if it looks valid (3-part JWT), else fall back to anon key
_svc = os.environ.get("SUPABASE_SERVICE_KEY", "")
_anon = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
SUPABASE_KEY = _svc if _svc.count(".") == 2 else _anon


def load_brain_config(slug: str) -> dict:
    config_path = BRAINS_DIR / slug / "brain.json"
    if not config_path.exists():
        print(f"ERROR: Brain config not found: {config_path}")
        sys.exit(1)
    with open(config_path) as f:
        return json.load(f)


def load_atoms(supabase, atoms_table: str, atoms_file: Path, dry_run: bool = False):
    """Load atoms from local JSON into Supabase."""
    with open(atoms_file) as f:
        atoms = json.load(f)

    print(f"Loading {len(atoms)} atoms into {atoms_table}...")

    if dry_run:
        print(f"  [DRY RUN] Would insert {len(atoms)} atoms")
        return

    batch_size = 50
    loaded = 0
    for i in range(0, len(atoms), batch_size):
        batch = atoms[i:i + batch_size]
        rows = []
        for atom in batch:
            row = {
                "id": atom["id"],
                "content": atom["content"],
                "cluster": atom.get("cluster"),
                "topics": atom.get("topics", []),
                "source_ref": atom.get("source_ref"),
                "confidence": atom.get("confidence"),
                "confidence_tier": atom.get("confidence_tier"),
                "original_quote": atom.get("original_quote"),
                "implication": atom.get("implication"),
            }
            sd = atom.get("source_date")
            if sd:
                import re
                sd = str(sd).strip()
                if sd in ("unknown", "n/a", ""):
                    pass  # skip
                elif re.match(r'^\d{4}-\d{4}$', sd):  # date range like "2022-2023"
                    sd = f"{sd[:4]}-01-01"
                    row["source_date"] = sd
                elif re.match(r'^\d{4}$', sd):
                    row["source_date"] = f"{sd}-01-01"
                elif re.match(r'^\d{4}-\d{2}$', sd):
                    row["source_date"] = f"{sd}-01"
                else:
                    row["source_date"] = sd
            rows.append(row)

        supabase.table(atoms_table).upsert(rows).execute()
        loaded += len(batch)
        print(f"  Loaded {loaded}/{len(atoms)} atoms")

    print(f"  Done: {loaded} atoms loaded into {atoms_table}")


def load_connections(supabase, connections_table: str, connections_file: Path, dry_run: bool = False):
    """Load connections from local JSON into Supabase."""
    with open(connections_file) as f:
        connections = json.load(f)

    print(f"Loading {len(connections)} connections into {connections_table}...")

    if dry_run:
        print(f"  [DRY RUN] Would insert {len(connections)} connections")
        return

    batch_size = 50
    loaded = 0
    for i in range(0, len(connections), batch_size):
        batch = connections[i:i + batch_size]
        rows = []
        for conn in batch:
            row = {
                "atom_id_1": conn["atom_id_1"],
                "atom_id_2": conn["atom_id_2"],
                "relationship": conn.get("relationship", "related"),
                "confidence": conn.get("confidence", 0.8),
            }
            if conn.get("id"):
                row["id"] = conn["id"]
            rows.append(row)

        supabase.table(connections_table).upsert(rows).execute()
        loaded += len(batch)
        print(f"  Loaded {loaded}/{len(connections)} connections")

    print(f"  Done: {loaded} connections loaded into {connections_table}")


def main():
    parser = argparse.ArgumentParser(description="Load local brain data into Supabase")
    parser.add_argument("--brain", required=True, help="Brain slug")
    parser.add_argument("--atoms", action="store_true", help="Load atoms")
    parser.add_argument("--connections", action="store_true", help="Load connections")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    if not SUPABASE_KEY:
        print("ERROR: Set SUPABASE_SERVICE_KEY in .env")
        sys.exit(1)

    if not args.atoms and not args.connections:
        print("ERROR: Specify --atoms and/or --connections")
        sys.exit(1)

    config = load_brain_config(args.brain)
    atoms_table = config["supabase"]["atoms_table"]
    connections_table = config["supabase"]["connections_table"]
    research_dir = BRAINS_DIR / config["brain_slug"] / "research"

    print(f"Brain: {config['brain_name']} ({args.brain})")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    if args.atoms:
        atoms_file = research_dir / "all-atoms.json"
        if not atoms_file.exists():
            print(f"ERROR: {atoms_file} not found")
            sys.exit(1)
        load_atoms(supabase, atoms_table, atoms_file, args.dry_run)

    if args.connections:
        connections_file = research_dir / "connections.json"
        if not connections_file.exists():
            print(f"ERROR: {connections_file} not found")
            sys.exit(1)
        load_connections(supabase, connections_table, connections_file, args.dry_run)

    print("\nDone!")


if __name__ == "__main__":
    main()
