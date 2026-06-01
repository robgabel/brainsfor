#!/usr/bin/env python3
"""Add a source_url column to every brain's atoms table and populate it from the
pack (the resolved clickable URL the citations UI needs). The Supabase schema only
had source_ref (often a title); source_url lived only in the pack JSON. Idempotent.

Usage: python3 scripts/backfill-source-url.py [--brain <slug>]
"""
import argparse, json, os, sys, time
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parent.parent
URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}


def us(slug): return slug.replace("-", "_")
def sq(v): return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"
def exec_sql(q):
    r = httpx.post(f"{URL}/rest/v1/rpc/exec_sql", headers=H, json={"query": q}, timeout=120)
    return r.status_code in (200, 201, 204), f"{r.status_code} {r.text[:120]}"


def backfill(slug):
    u = us(slug)
    pack = ROOT / "brains" / slug / "pack" / "brain-atoms.json"
    if not pack.exists():
        print(f"  {slug}: no pack, skip"); return
    atoms = json.loads(pack.read_text()).get("atoms", [])
    with_url = [a for a in atoms if a.get("source_url")]
    # 1. add column
    ok, msg = exec_sql(f"ALTER TABLE {u}_atoms ADD COLUMN IF NOT EXISTS source_url text;")
    if not ok:
        print(f"  {slug}: ALTER failed {msg}"); return
    # 2. populate in chunks via UPDATE ... FROM (VALUES ...)
    done = 0
    for i in range(0, len(with_url), 80):
        chunk = with_url[i:i + 80]
        vals = ",".join(f"('{a['id']}'::uuid,{sq(a['source_url'])})" for a in chunk)
        q = (f"UPDATE {u}_atoms AS t SET source_url = v.url "
             f"FROM (VALUES {vals}) AS v(id, url) WHERE t.id = v.id;")
        ok, msg = exec_sql(q)
        if ok: done += len(chunk)
        else: print(f"    chunk {i} failed: {msg}")
        time.sleep(0.2)
    print(f"  {slug}: source_url set on {done}/{len(with_url)} atoms (of {len(atoms)} total)")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--brain"); args = ap.parse_args()
    if args.brain:
        backfill(args.brain); return
    slugs = [b["slug"] for b in json.loads((ROOT / "brains" / "index.json").read_text())["brains"]
             if not b["slug"].endswith("-v2")]
    for s in slugs:
        backfill(s)


if __name__ == "__main__":
    main()
