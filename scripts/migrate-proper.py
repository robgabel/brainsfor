#!/usr/bin/env python3
"""Proper OLD->NEW BrainsFor migration.

Reads rows from the OLD project via PostgREST (service key); writes to the NEW
project via direct psycopg (NEW_PW) so we can (a) add the missing PRIMARY KEY on
id and (b) load idempotently with ON CONFLICT DO NOTHING.

Atoms are copied WITHOUT `embedding` (prod routes use keyword scoring, not the
vector RPC). Order: atoms -> connections per brain, then shared tables.

Env: OLD_URL, OLD_KEY (service), NEW_DSN (full psycopg DSN).
"""
import os, sys, json, time
import httpx, psycopg

OLD_URL = os.environ["OLD_URL"].rstrip("/")
OLD_KEY = os.environ["OLD_KEY"]
NEW_DSN = os.environ["NEW_DSN"]

ATOM_COLS = ["id","content","original_quote","implication","cluster","topics",
             "source_ref","source_date","confidence","confidence_tier",
             "created_at","updated_at","source_url"]  # no embedding
CONN_COLS = ["id","atom_id_1","atom_id_2","relationship","confidence","created_at"]
PAGE = 1000


def api_hdr():
    return {"apikey": OLD_KEY, "Authorization": f"Bearer {OLD_KEY}"}


def fetch_all(table, cols):
    sel = ",".join(cols)
    out, off = [], 0
    while True:
        for attempt in range(4):
            try:
                r = httpx.get(f"{OLD_URL}/rest/v1/{table}?select={sel}&limit={PAGE}&offset={off}",
                              headers=api_hdr(), timeout=120)
                if r.status_code == 200:
                    rows = r.json(); break
                if r.status_code >= 500 or r.status_code == 429:
                    time.sleep(1.5*(attempt+1)); continue
                print(f"   ! read {table}@{off}: {r.status_code} {r.text[:100]}"); return out
            except Exception as e:
                time.sleep(1.0*(attempt+1)); rows = None
        if rows is None:
            print(f"   ! read {table}@{off}: exhausted retries"); return out
        out.extend(rows)
        if len(rows) < PAGE: break
        off += PAGE
    return out


def ensure_pk(cur, table):
    cur.execute("SELECT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid=%s::regclass AND contype='p')", (f"public.{table}",))
    if not cur.fetchone()[0]:
        cur.execute(f'ALTER TABLE public."{table}" ADD PRIMARY KEY (id)')
        return "added-pk"
    return "had-pk"


def load_table(conn, table, cols):
    # table existence + pk
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass(%s)", (f"public.{table}",))
        if cur.fetchone()[0] is None:
            print(f"  {table}: missing in NEW — skip"); return
        pk = ensure_pk(cur, table)
    conn.commit()

    rows = fetch_all(table, cols)
    if not rows:
        print(f"  {table}: 0 rows in OLD ({pk})"); return

    placeholders = "(" + ",".join(["%s"]*len(cols)) + ")"
    sql = f'INSERT INTO public."{table}" ({",".join(cols)}) VALUES {placeholders} ON CONFLICT (id) DO NOTHING'
    wrote = 0
    with conn.cursor() as cur:
        B = 500
        for i in range(0, len(rows), B):
            batch = rows[i:i+B]
            params = [[r.get(c) for c in cols] for r in batch]
            cur.executemany(sql, params)
            wrote += len(batch)
    conn.commit()
    with conn.cursor() as cur:
        cur.execute(f'SELECT count(*) FROM public."{table}"')
        cnt = cur.fetchone()[0]
    print(f"  {table}: read {len(rows)} → new total {cnt} ({pk})")


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only")+1].replace("-","_")
    idx = json.load(open(os.path.join(os.path.dirname(__file__),"..","brains","index.json")))
    slugs = [b["slug"].replace("-","_") for b in idx["brains"]]
    if only: slugs = [only]

    with psycopg.connect(NEW_DSN, connect_timeout=20) as conn:
        print(f"Connected NEW. Migrating {len(slugs)} brains.")
        for s in slugs:
            print(f"[{s}]")
            load_table(conn, f"{s}_atoms", ATOM_COLS)
            load_table(conn, f"{s}_connections", CONN_COLS)
        if not only:
            print("[shared]")
            # brain_metadata: dynamic cols
            load_meta(conn)


def load_meta(conn):
    # brain_metadata has a variable schema; copy all cols that exist in NEW.
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass('public.brain_metadata')")
        if cur.fetchone()[0] is None:
            print("  brain_metadata: missing in NEW — skip"); return
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='brain_metadata' ORDER BY ordinal_position")
        ncols = [r[0] for r in cur.fetchall()]
        ensure_pk(cur, "brain_metadata")
    conn.commit()
    rows = fetch_all("brain_metadata", ncols)
    if not rows:
        print("  brain_metadata: 0 rows"); return
    ph = "(" + ",".join(["%s"]*len(ncols)) + ")"
    sql = f'INSERT INTO public.brain_metadata ({",".join(ncols)}) VALUES {ph} ON CONFLICT (id) DO NOTHING'
    with conn.cursor() as cur:
        for i in range(0, len(rows), 200):
            batch = rows[i:i+200]
            cur.executemany(sql, [[r.get(c) for c in ncols] for r in batch])
    conn.commit()
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM public.brain_metadata"); print(f"  brain_metadata: {cur.fetchone()[0]} rows")


if __name__ == "__main__":
    main()
