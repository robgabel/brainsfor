#!/usr/bin/env python3
"""Fix the two tables that the main migration skipped:
  - scott_belsky_atoms: legacy schema → migrate the old∩new column intersection.
  - brain_metadata: wrap JSONB columns with psycopg Json().

Env: OLD_URL, OLD_KEY (service), NEW_DSN.
"""
import os, json, time
import httpx, psycopg
from psycopg.types.json import Json

OLD_URL = os.environ["OLD_URL"].rstrip("/")
OLD_KEY = os.environ["OLD_KEY"]
NEW_DSN = os.environ["NEW_DSN"]
PAGE = 1000


def api_hdr():
    return {"apikey": OLD_KEY, "Authorization": f"Bearer {OLD_KEY}"}


def old_cols(table):
    r = httpx.get(f"{OLD_URL}/rest/v1/{table}?select=*&limit=1", headers=api_hdr(), timeout=30)
    return list(r.json()[0].keys()) if r.status_code == 200 and r.json() else []


def fetch_all(table, cols):
    sel = ",".join(cols); out, off = [], 0
    while True:
        r = httpx.get(f"{OLD_URL}/rest/v1/{table}?select={sel}&limit={PAGE}&offset={off}", headers=api_hdr(), timeout=120)
        if r.status_code != 200:
            print(f"   ! {table}@{off}: {r.status_code} {r.text[:120]}"); break
        rows = r.json(); out.extend(rows)
        if len(rows) < PAGE: break
        off += PAGE
    return out


def new_meta(conn, table):
    with conn.cursor() as cur:
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name=%s", (table,))
        return {r[0]: r[1] for r in cur.fetchall()}


def ensure_pk(conn, table):
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid=%s::regclass AND contype='p')", (f"public.{table}",))
        if not cur.fetchone()[0]:
            cur.execute(f'ALTER TABLE public."{table}" ADD PRIMARY KEY (id)')
    conn.commit()


def migrate(conn, table, batch=400):
    nmeta = new_meta(conn, table)
    if not nmeta:
        print(f"  {table}: missing in NEW — skip"); return
    ocols = old_cols(table)
    cols = [c for c in ocols if c in nmeta and c != "embedding"]
    jsonb = {c for c in cols if nmeta[c] in ("jsonb", "json")}
    ensure_pk(conn, table)
    rows = fetch_all(table, cols)
    if not rows:
        print(f"  {table}: 0 rows in OLD"); return
    ph = "(" + ",".join(["%s"]*len(cols)) + ")"
    sql = f'INSERT INTO public."{table}" ({",".join(cols)}) VALUES {ph} ON CONFLICT (id) DO NOTHING'
    with conn.cursor() as cur:
        for i in range(0, len(rows), batch):
            params = []
            for r in rows[i:i+batch]:
                params.append([Json(r.get(c)) if (c in jsonb and r.get(c) is not None) else r.get(c) for c in cols])
            cur.executemany(sql, params)
    conn.commit()
    with conn.cursor() as cur:
        cur.execute(f'SELECT count(*) FROM public."{table}"'); n = cur.fetchone()[0]
    print(f"  {table}: read {len(rows)} ({len(cols)} cols, {len(jsonb)} jsonb) → new total {n}")


def main():
    with psycopg.connect(NEW_DSN, connect_timeout=20) as conn:
        print("Fixing scott_belsky_atoms + brain_metadata")
        migrate(conn, "scott_belsky_atoms")
        migrate(conn, "brain_metadata")


if __name__ == "__main__":
    main()
