#!/usr/bin/env python3
"""Copy BrainsFor tables from the OLD shared project to the NEW dedicated project
via PostgREST (service keys), no DB password needed.

- Atoms are copied WITHOUT the `embedding` column (both prod routes use keyword
  scoring on fetched atoms, not the vector RPC). Embeddings can be backfilled
  later via the embed-brain edge function if semantic search is wanted.
- Upserts on primary key (Prefer: resolution=merge-duplicates) so it is re-runnable.

Env: OLD_URL, OLD_KEY, NEW_URL, NEW_KEY  (service keys for both).
Usage: python3 migrate-via-api.py [--only slug] [--tables atoms|connections|all]
"""
import os, sys, json, time, argparse
import httpx

OLD_URL = os.environ["OLD_URL"].rstrip("/")
OLD_KEY = os.environ["OLD_KEY"]
NEW_URL = os.environ["NEW_URL"].rstrip("/")
NEW_KEY = os.environ["NEW_KEY"]

PAGE = 1000
POST_BATCH = 400


def hdr(key, extra=None):
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h


def get_cols(url, key, table):
    """Column names from one row, or [] if table empty/missing."""
    r = httpx.get(f"{url}/rest/v1/{table}?select=*&limit=1", headers=hdr(key), timeout=30)
    if r.status_code != 200:
        return None
    data = r.json()
    if not data:
        return "EMPTY"
    return list(data[0].keys())


def fetch_all(url, key, table, cols):
    sel = ",".join(cols)
    out = []
    off = 0
    while True:
        r = httpx.get(f"{url}/rest/v1/{table}?select={sel}&limit={PAGE}&offset={off}",
                      headers=hdr(key), timeout=120)
        if r.status_code != 200:
            print(f"   ! read err {table} @{off}: {r.status_code} {r.text[:120]}")
            break
        rows = r.json()
        out.extend(rows)
        if len(rows) < PAGE:
            break
        off += PAGE
    return out


def upsert(url, key, table, rows):
    if not rows:
        return 0
    done = 0
    for i in range(0, len(rows), POST_BATCH):
        batch = rows[i:i + POST_BATCH]
        for attempt in range(4):
            try:
                r = httpx.post(f"{url}/rest/v1/{table}",
                               headers=hdr(key, {"Prefer": "resolution=merge-duplicates,return=minimal"}),
                               json=batch, timeout=120)
                if r.status_code in (200, 201, 204):
                    done += len(batch); break
                if r.status_code in (429,) or r.status_code >= 500:
                    time.sleep(1.5 * (attempt + 1)); continue
                print(f"   ! write err {table} batch {i}: {r.status_code} {r.text[:160]}")
                break
            except Exception as e:
                print(f"   ! write exc {table} batch {i}: {e}"); time.sleep(1.0 * (attempt + 1))
    return done


def copy_table(table, drop_embedding=True):
    cols = get_cols(OLD_URL, OLD_KEY, table)
    if cols is None:
        print(f"  {table}: missing in OLD — skip"); return
    if cols == "EMPTY":
        print(f"  {table}: empty in OLD — skip"); return
    if drop_embedding and "embedding" in cols:
        cols = [c for c in cols if c != "embedding"]
    # confirm NEW has the table
    ncols = get_cols(NEW_URL, NEW_KEY, table)
    if ncols is None:
        print(f"  {table}: missing in NEW — skip"); return
    rows = fetch_all(OLD_URL, OLD_KEY, table, cols)
    n = upsert(NEW_URL, NEW_KEY, table, rows)
    # verify count in new
    r = httpx.get(f"{NEW_URL}/rest/v1/{table}?select=id", headers=hdr(NEW_KEY, {"Prefer": "count=exact", "Range": "0-0"}), timeout=30)
    cr = r.headers.get("content-range", "?")
    print(f"  {table}: read {len(rows)} → wrote {n} | NEW count-range {cr}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="single brain slug (underscored)")
    ap.add_argument("--tables", default="all", choices=["atoms", "connections", "all", "meta"])
    args = ap.parse_args()

    idx = json.load(open(os.path.join(os.path.dirname(__file__), "..", "brains", "index.json")))
    slugs = [b["slug"].replace("-", "_") for b in idx.get("brains", idx if isinstance(idx, list) else [])]
    if args.only:
        slugs = [args.only.replace("-", "_")]

    print(f"Migrating {len(slugs)} brains | tables={args.tables}")
    for s in slugs:
        print(f"[{s}]")
        if args.tables in ("atoms", "all"):
            copy_table(f"{s}_atoms")
        if args.tables in ("connections", "all"):
            copy_table(f"{s}_connections", drop_embedding=False)
    if args.tables in ("meta", "all") and not args.only:
        print("[shared]")
        copy_table("brain_metadata", drop_embedding=False)
        copy_table("cross_connections", drop_embedding=False)


if __name__ == "__main__":
    main()
