#!/usr/bin/env python3
"""Bulk-load a brain's missing atoms + connections into Supabase via the exec_sql
RPC (server-side multi-row INSERT), bypassing the PostgREST per-row rate ceiling
that capped the REST loader at ~480 rows/process.

Each exec_sql call inserts up to CHUNK rows in ONE request (ON CONFLICT DO NOTHING,
so it's idempotent and only fills gaps). Then embeds via the embed-brain edge fn.

Usage: python3 scripts/load-via-execsql.py --brain sun-tzu [--no-embed]
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parent.parent
URL = os.environ.get("SUPABASE_URL", "https://uzediwokyshjbsymevtp.supabase.co").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
CHUNK = 80


def us(slug): return slug.replace("-", "_")
def sq(v):
    if v is None: return "NULL"
    return "'" + str(v).replace("'", "''") + "'"
def arr(lst):
    if not lst: return "'{}'::text[]"
    return "ARRAY[" + ",".join(sq(x) for x in lst) + "]::text[]"


def exec_sql(query):
    r = httpx.post(f"{URL}/rest/v1/rpc/exec_sql", headers=H, json={"query": query}, timeout=120)
    return r.status_code in (200, 201, 204), f"{r.status_code} {r.text[:120]}"


def table_count(t):
    r = httpx.get(f"{URL}/rest/v1/{t}?select=id", headers={**H, "Prefer": "count=exact", "Range": "0-0"}, timeout=30)
    return int(r.headers.get("content-range", "*/0").split("/")[-1])


def existing_ids(t):
    ids, start = set(), 0
    while True:
        r = httpx.get(f"{URL}/rest/v1/{t}?select=id", headers={**H, "Range": f"{start}-{start+999}"}, timeout=60)
        if r.status_code not in (200, 206): break
        rows = r.json(); ids.update(x["id"] for x in rows)
        if len(rows) < 1000: break
        start += 1000
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--no-embed", action="store_true")
    args = ap.parse_args()
    slug = args.brain; u = us(slug)
    pack = json.loads((ROOT / "brains" / slug / "pack" / "brain-atoms.json").read_text())
    atoms = pack.get("atoms", [])
    aid = {a["id"] for a in atoms}
    conns = [c for c in pack.get("connections", []) if c.get("atom_id_1") in aid and c.get("atom_id_2") in aid]

    # --- atoms ---
    have = existing_ids(f"{u}_atoms")
    missing = [a for a in atoms if a["id"] not in have]
    print(f"  {slug}: {len(have)}/{len(atoms)} atoms present, {len(missing)} to load")
    for i in range(0, len(missing), CHUNK):
        rows = missing[i:i + CHUNK]
        vals = ",".join(
            f"('{a['id']}'::uuid,{sq(a.get('content'))},{sq(a.get('original_quote'))},"
            f"{sq(a.get('implication'))},{sq(a.get('cluster'))},{arr(a.get('topics'))},"
            f"{sq(a.get('source_ref'))},{sq(a.get('source_url'))},{a.get('confidence',0.8) or 0.8},"
            f"{sq(a.get('confidence_tier') or 'medium')})"
            for a in rows)
        q = (f"INSERT INTO {u}_atoms (id,content,original_quote,implication,cluster,topics,"
             f"source_ref,source_url,confidence,confidence_tier) VALUES {vals} ON CONFLICT (id) DO NOTHING;")
        ok, msg = exec_sql(q)
        if not ok: print(f"    atom chunk {i} FAILED: {msg}")
        time.sleep(0.3)
    ac = table_count(f"{u}_atoms")
    print(f"  atoms now: {ac}/{len(atoms)}")

    # --- connections ---
    chave = existing_ids(f"{u}_connections")
    cmiss = [c for c in conns if c.get("id") not in chave]
    for i in range(0, len(cmiss), CHUNK):
        rows = cmiss[i:i + CHUNK]
        vals = ",".join(
            f"('{c['id']}'::uuid,'{c['atom_id_1']}'::uuid,'{c['atom_id_2']}'::uuid,"
            f"{sq(c.get('relationship','related'))},{c.get('confidence',0.8) or 0.8})"
            for c in rows)
        q = (f"INSERT INTO {u}_connections (id,atom_id_1,atom_id_2,relationship,confidence) "
             f"VALUES {vals} ON CONFLICT (id) DO NOTHING;")
        ok, msg = exec_sql(q)
        if not ok: print(f"    conn chunk {i} FAILED: {msg}")
        time.sleep(0.3)
    cc = table_count(f"{u}_connections")
    print(f"  connections now: {cc}/{len(conns)}")

    # --- embeddings ---
    if not args.no_embed:
        emb = 0
        for _ in range(60):
            r = httpx.post(f"{URL}/functions/v1/embed-brain",
                           headers={"Authorization": f"Bearer {KEY}", "apikey": KEY, "Content-Type": "application/json"},
                           json={"table": f"{u}_atoms", "limit": 200}, timeout=300)
            if r.status_code != 200: print(f"    embed HTTP {r.status_code}"); break
            n = r.json().get("embedded", 0); emb += n
            if n == 0: break
            time.sleep(1)
        print(f"  embedded +{emb}")
    print(f"  DONE {slug}: {table_count(f'{u}_atoms')} atoms / {table_count(f'{u}_connections')} conns")


if __name__ == "__main__":
    main()
