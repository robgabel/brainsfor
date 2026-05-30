#!/usr/bin/env python3
"""Make a brain's Supabase tables an exact, embedded mirror of its shipped pack.

Fixes the two issues behind the "pack and Supabase are different brains" bug:
  1. Consistency — loads the PACK's atoms/connections (what actually ships) into
     <slug>_atoms/<slug>_connections, preserving pack ids so connections resolve.
     Skips the reload when Supabase already matches the pack (count + id set).
  2. Embeddings — calls the embed-brain edge function (OpenAI key lives in Supabase
     secrets) in a loop until every atom has a 1536-dim embedding, so semantic
     search / search_brain_atoms / board Layer-2 work.

cross_connections (Rob<->thinker links) FK-references scott_belsky_atoms only.
A scott-belsky reload first clears the stale cross_connections rows (they point at
atom ids that die in the rebuild); regenerate those links separately afterward.

Usage:
  python3 scripts/finalize-supabase.py --brain reshma-saujani
  python3 scripts/finalize-supabase.py --brain scott-belsky        # handles cross_connections
  python3 scripts/finalize-supabase.py --brain reshma-saujani --embed-only
  python3 scripts/finalize-supabase.py --brain reshma-saujani --dry-run

Requires SUPABASE_URL + SUPABASE_SERVICE_KEY in env.
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path
import importlib.util
import httpx

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

_spec = importlib.util.spec_from_file_location("abb", SCRIPTS / "auto-build-brain.py")
_abb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_abb)
ensure_supabase_tables = _abb.ensure_supabase_tables
get_supabase_url = _abb.get_supabase_url
get_supabase_rest_headers = _abb.get_supabase_rest_headers
underscore_slug = _abb.underscore_slug


def say(tag, msg): print(f"  {tag} {msg}")


def exec_sql(url, headers, query):
    r = httpx.post(f"{url}/rest/v1/rpc/exec_sql", headers=headers, json={"query": query}, timeout=60)
    return r.status_code in (200, 201, 204), f"HTTP {r.status_code} {r.text[:120]}"


def atom_row(a):
    row = {
        "id": a["id"],
        "content": a.get("content"),
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
        s = str(sd).strip()
        if len(s) == 4 and s.isdigit(): row["source_date"] = f"{s}-01-01T00:00:00Z"
        elif len(s) == 7: row["source_date"] = f"{s}-01T00:00:00Z"
        elif len(s) == 10: row["source_date"] = f"{s}T00:00:00Z"
        elif "T" in s: row["source_date"] = s
    return row


def table_count(url, headers, table):
    r = httpx.get(f"{url}/rest/v1/{table}?select=id",
                  headers={**headers, "Prefer": "count=exact", "Range": "0-0"}, timeout=60)
    try:
        return int(r.headers.get("content-range", "*/0").split("/")[-1])
    except Exception:
        return -1


def insert_batches(url, headers, table, rows, label, passes=10):
    """Idempotently upsert rows until the table count reaches len(rows).

    Supabase's REST API starts rejecting after ~400 rows POSTed back-to-back in a
    single process (rate/connection pressure), which silently left tables half
    loaded — atoms stalled at ~400/1086 and every downstream connection failed its
    FK check. Fix: small batches (40) with a brief inter-batch sleep, and re-pass
    the whole set (merge-duplicates makes it an idempotent upsert) until the live
    count matches the target or we run out of passes. Heals partial loads instead
    of trusting a single pass.
    """
    target = len(rows)
    for p in range(passes):
        for i in range(0, target, 40):
            batch = rows[i:i + 40]
            try:
                httpx.post(f"{url}/rest/v1/{table}", headers=headers, json=batch, timeout=60)
            except Exception:
                pass
            time.sleep(0.2)
        c = table_count(url, headers, table)
        if c >= target:
            say("OK", f"loaded {c}/{target} {label} (pass {p + 1})")
            return c
        say("i", f"  {label} pass {p + 1}: {c}/{target} — re-passing")
    c = table_count(url, headers, table)
    say("WARN" if c < target else "OK", f"loaded {c}/{target} {label}")
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--embed-only", action="store_true", help="Skip reload; only generate embeddings")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    slug = args.brain
    us = underscore_slug(slug)
    brain_dir = ROOT / "brains" / slug
    pack = brain_dir / "pack" / "brain-atoms.json"
    if not pack.exists():
        say("ERR", f"no pack at {pack}"); sys.exit(1)
    data = json.loads(pack.read_text())
    atoms = data.get("atoms", [])
    atom_ids = {a["id"] for a in atoms}
    # Only load connections whose BOTH endpoints exist in the pack's atom set.
    # A dangling connection (atom filtered out post-enrichment) would fail its FK
    # forever and stall the loop-until-count pass.
    all_conns = data.get("connections", [])
    conns = [c for c in all_conns if c.get("atom_id_1") in atom_ids and c.get("atom_id_2") in atom_ids]
    dangling = len(all_conns) - len(conns)
    say("i", f"{slug}: pack has {len(atoms)} atoms, {len(conns)} connections"
             + (f" ({dangling} dangling skipped)" if dangling else ""))

    url = get_supabase_url()
    headers = get_supabase_rest_headers()
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")

    if args.dry_run:
        say("DRY", f"would mirror {len(atoms)} atoms + {len(conns)} conns into {us}_* and embed all")
        return

    # Load brain.json so ensure_supabase_tables can fill brain_metadata.
    bj = json.loads((brain_dir / "brain.json").read_text()) if (brain_dir / "brain.json").exists() else {}
    if not ensure_supabase_tables(slug, bj.get("brain_name", slug), bj):
        say("ERR", "tables not ready"); sys.exit(1)

    if not args.embed_only:
        # Is Supabase already consistent with the pack (same id set)?
        r = httpx.get(f"{url}/rest/v1/{us}_atoms?select=id", headers=headers, timeout=60)
        db_ids = {row["id"] for row in r.json()} if r.status_code == 200 else set()
        pack_ids = {a["id"] for a in atoms}
        if db_ids == pack_ids and db_ids:
            say("OK", f"Supabase already matches pack ({len(db_ids)} atoms) — skipping reload")
        else:
            say("i", f"reloading (db={len(db_ids)} vs pack={len(pack_ids)} atoms)")
            # cross_connections FK-references scott_belsky_atoms only.
            if us == "scott_belsky":
                ok, msg = exec_sql(url, headers,
                    "DELETE FROM cross_connections WHERE belsky_atom_id IN "
                    "(SELECT id FROM scott_belsky_atoms)")
                say("OK" if ok else "WARN", f"cleared stale Belsky cross_connections: {msg}")
            ok, msg = exec_sql(url, headers,
                f"TRUNCATE TABLE {us}_connections, {us}_atoms CASCADE")
            say("OK" if ok else "WARN", f"truncate {us}_*: {msg}")
            insert_batches(url, headers, f"{us}_atoms", [atom_row(a) for a in atoms], "atoms")
            crows = [{"id": c.get("id"), "atom_id_1": c["atom_id_1"], "atom_id_2": c["atom_id_2"],
                      "relationship": c.get("relationship", "related"),
                      "confidence": c.get("confidence", 0.8)} for c in conns]
            insert_batches(url, headers, f"{us}_connections", crows, "connections")

    # --- Embeddings: loop embed-brain until none remain ---
    say("i", "generating embeddings via embed-brain edge function...")
    total_embedded = 0
    for _ in range(60):  # cap iterations
        resp = httpx.post(f"{url}/functions/v1/embed-brain",
                          headers={"Authorization": f"Bearer {key}", "apikey": key,
                                   "Content-Type": "application/json"},
                          json={"table": f"{us}_atoms", "limit": 200}, timeout=300)
        if resp.status_code != 200:
            say("WARN", f"embed-brain HTTP {resp.status_code}: {resp.text[:160]}"); break
        body = resp.json()
        n = body.get("embedded", 0)
        total_embedded += n
        if n == 0:
            break
        say("i", f"  embedded {n} (running total {total_embedded})")
        time.sleep(1)

    # --- Verify ---
    r = httpx.get(f"{url}/rest/v1/{us}_atoms?select=id&embedding=not.is.null",
                  headers={**headers, "Prefer": "count=exact", "Range": "0-0"}, timeout=60)
    embedded_count = r.headers.get("content-range", "*/?").split("/")[-1]
    r2 = httpx.get(f"{url}/rest/v1/{us}_atoms?select=id",
                   headers={**headers, "Prefer": "count=exact", "Range": "0-0"}, timeout=60)
    total_count = r2.headers.get("content-range", "*/?").split("/")[-1]
    say("DONE", f"{us}_atoms: {total_count} atoms, {embedded_count} embedded (pack has {len(atoms)})")


if __name__ == "__main__":
    main()
