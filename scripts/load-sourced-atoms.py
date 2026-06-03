#!/usr/bin/env python3
"""Load Phase 3.5 sourced atoms (research/sourced-atoms.json) into a project's
<slug>_atoms table. Idempotent (ON CONFLICT (id) DO NOTHING).

Env: NEW_DSN (psycopg DSN).
Usage: python3 load-sourced-atoms.py [--only slug]
"""
import os, sys, json, glob
import psycopg

NEW_DSN = os.environ["NEW_DSN"]
COLS = ["id","content","original_quote","implication","cluster","topics",
        "source_ref","source_url","confidence","confidence_tier"]


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only")+1]
    root = os.path.join(os.path.dirname(__file__), "..", "brains")
    paths = sorted(glob.glob(os.path.join(root, "*", "research", "sourced-atoms.json")))
    with psycopg.connect(NEW_DSN, connect_timeout=20) as conn:
        for p in paths:
            slug = p.split("/brains/")[1].split("/")[0]
            if only and slug != only:
                continue
            atoms = json.load(open(p))
            if not atoms:
                continue
            table = slug.replace("-", "_") + "_atoms"
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass(%s)", (f"public.{table}",))
                if cur.fetchone()[0] is None:
                    print(f"  {table}: missing — skip"); continue
                ph = "(" + ",".join(["%s"]*len(COLS)) + ")"
                sql = f'INSERT INTO public."{table}" ({",".join(COLS)}) VALUES {ph} ON CONFLICT (id) DO NOTHING'
                params = [[a.get(c) for c in COLS] for a in atoms]
                cur.executemany(sql, params)
                cur.execute(f"SELECT count(*) FROM public.\"{table}\" WHERE cluster='synthesis_sourced'")
                n = cur.fetchone()[0]
            conn.commit()
            print(f"  {slug}: loaded {len(atoms)} sourced → {n} synthesis_sourced in table")


if __name__ == "__main__":
    main()
