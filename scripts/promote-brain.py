#!/usr/bin/env python3
"""Promote a factory-rebuilt staging brain (<slug>-v2) over its live counterpart.

The staged-slug rebuild pattern (auto-build-brain.py --slug <slug>-v2) keeps the
live brain serving while a fresh, higher-quality version is built alongside. This
script swaps the staging brain into the canonical slug once it's validated:

  1. Safety gates: staging build Phase 5 complete, audit >= live audit (unless --force).
  2. Replace brains/<slug>/ with brains/<slug>-v2/ content (data/ nesting-safe).
  3. Fix brain.json slug + supabase table refs (<slug>-v2 -> <slug>).
  4. Re-export the pack from local files so every shipped file carries the right slug.
  5. Restore the live brain's curated pack/intro.md if the staging build lacks one.
  6. index.json: <slug> entry <- staging metadata; remove the <slug>-v2 entry.
  7. Re-sync website/public via the website prebuild; remove public/<slug>-v2.
  8. Drop the orphaned <slug>_v2 Supabase tables.

NOT done automatically (needs a human decision):
  - Reloading <slug>_atoms in Supabase with the new atoms. cross_connections
    FK-references existing atom ids (Rob's curated cross-brain links); replacing
    them needs care. /board reads packs (Path B), so the live promotion is complete
    without it. Use --reload-supabase to attempt it (truncates with CASCADE — will
    drop dependent cross_connections rows; refuses unless --yes-drop-cross-connections).

Usage:
  python3 scripts/promote-brain.py --slug steve-jobs
  python3 scripts/promote-brain.py --slug steve-jobs --dry-run
  python3 scripts/promote-brain.py --slug steve-jobs --force   # skip audit gate
  git add -A && git commit  (this script does NOT commit — review the diff first)

Requires SUPABASE_URL + SUPABASE_SERVICE_KEY in env (for dropping v2 tables).
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
BRAINS = ROOT / "brains"
WEBSITE = ROOT / "website"


def underscore_slug(slug: str) -> str:
    return slug.replace("-", "_")


def say(tag, msg):
    print(f"  {tag} {msg}")


def audit_score(slug: str) -> int | None:
    try:
        out = subprocess.run(
            ["python3", str(ROOT / "scripts" / "audit-brains.py"), "--brain", slug, "--json"],
            capture_output=True, text=True, cwd=ROOT,
        ).stdout
        return json.loads(out)["brains"][0]["completeness_score"]
    except Exception:
        return None


def persona_gate(slug: str) -> tuple[bool | None, str]:
    """Read the latest persona-QA scorecard for a brain. Returns (pass, detail).
    pass is None if no persona-QA has been run (gate can't be evaluated)."""
    import glob
    files = sorted(glob.glob(str(BRAINS / slug / "evals" / "persona-qa-*.json")))
    if not files:
        return None, "no persona-qa-*.json (run scripts/brain-qa.py --brain %s)" % slug
    try:
        sc = json.loads(Path(files[-1]).read_text())
        detail = (f"score={sc.get('persona_qa_score')} high-numeric-defects="
                  f"{sc.get('high_severity_numeric_defects')} ({Path(files[-1]).name})")
        return bool(sc.get("pass")), detail
    except Exception as e:
        return None, f"unreadable persona-qa json: {e}"


def supabase_exec(query: str) -> tuple[bool, str]:
    url = os.environ.get("SUPABASE_URL", "https://uzediwokyshjbsymevtp.supabase.co").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not key:
        return False, "SUPABASE_SERVICE_KEY not set"
    try:
        r = httpx.post(f"{url}/rest/v1/rpc/exec_sql",
                       headers={"apikey": key, "Authorization": f"Bearer {key}",
                                "Content-Type": "application/json"},
                       json={"query": query}, timeout=60)
        return (r.status_code in (200, 201, 204)), f"HTTP {r.status_code} {r.text[:120]}"
    except Exception as e:
        return False, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True, help="Canonical (live) slug, e.g. steve-jobs")
    ap.add_argument("--staging-slug", help="Staging slug (default: <slug>-v2)")
    ap.add_argument("--force", action="store_true", help="Skip the audit >= live gate")
    ap.add_argument("--persona-gate", action="store_true",
                    help="Also require the staging brain to PASS its persona-QA ship-gate "
                         "(brains/<stage>/evals/persona-qa-*.json pass=true). Off by default.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-finalize", action="store_true",
                    help="Skip the post-swap finalize-supabase (load pack + embed)")
    args = ap.parse_args()

    base = args.slug
    stage = args.staging_slug or f"{base}-v2"
    base_dir = BRAINS / base
    stage_dir = BRAINS / stage
    base_us, stage_us = underscore_slug(base), underscore_slug(stage)

    # --- Safety gates ------------------------------------------------------
    if not stage_dir.exists():
        say("ERR", f"staging dir {stage_dir} not found"); sys.exit(1)
    prog = stage_dir / "build-progress.json"
    if prog.exists():
        ph = json.loads(prog.read_text())["phases"]
        if ph.get("5", {}).get("status") != "complete":
            say("ERR", f"{stage} build not complete (phase 5 = {ph.get('5', {}).get('status')})")
            sys.exit(1)
    stage_pack = stage_dir / "pack" / "brain-atoms.json"
    if not stage_pack.exists():
        say("ERR", f"{stage} has no pack/brain-atoms.json"); sys.exit(1)

    stage_score = audit_score(stage)
    base_score = audit_score(base) if base_dir.exists() else None
    say("i", f"audit: {base} = {base_score}, {stage} = {stage_score}")
    if not args.force and base_score is not None and stage_score is not None and stage_score < base_score:
        say("ERR", f"{stage} ({stage_score}) scores below live {base} ({base_score}). Use --force to override.")
        sys.exit(1)

    # Optional persona-QA ship-gate: promotion publishes a brain, so honor the same
    # gate that governs hidden->live. Off by default (existing promotions unaffected);
    # --force bypasses it like the audit gate.
    if args.persona_gate and not args.force:
        ppass, pdetail = persona_gate(stage)
        say("i", f"persona-gate ({stage}): {pdetail}")
        if ppass is None:
            say("ERR", f"--persona-gate set but no persona-QA result for {stage}. "
                       f"Run: python3 scripts/brain-qa.py --brain {stage}")
            sys.exit(1)
        if not ppass:
            say("ERR", f"{stage} fails its persona-QA ship-gate ({pdetail}). Fix + re-run brain-qa, or --force.")
            sys.exit(1)

    n_atoms = len(json.loads(stage_pack.read_text()).get("atoms", []))
    n_conn = len(json.loads(stage_pack.read_text()).get("connections", []))
    say("i", f"{stage}: {n_atoms} atoms, {n_conn} connections")

    if args.dry_run:
        say("DRY", f"would promote {stage} -> {base} (drop {stage_us}_* tables, remove {stage} entry)")
        return

    # --- 1. Preserve live intro.md ----------------------------------------
    saved_intro = None
    live_intro = base_dir / "pack" / "intro.md"
    if live_intro.exists():
        saved_intro = live_intro.read_text()

    # --- 2. Nesting-safe dir swap (rm live entirely, then move staging in) --
    with tempfile.TemporaryDirectory() as td:
        holding = Path(td) / "staging"
        shutil.move(str(stage_dir), str(holding))
        if base_dir.exists():
            shutil.rmtree(base_dir)          # removes gitignored data/ too
        shutil.move(str(holding), str(base_dir))
    say("OK", f"moved {stage} -> brains/{base}/")
    # drop the staging build's progress marker
    (base_dir / "build-progress.json").unlink(missing_ok=True)

    # --- 3. Fix brain.json slug + supabase refs ---------------------------
    bj_path = base_dir / "brain.json"
    bj = bj_path.read_text().replace(stage, base).replace(stage_us, base_us)
    bj_path.write_text(bj)
    say("OK", "brain.json slug + supabase refs corrected")

    # --- 4. Re-export pack from local files (clean slug everywhere) --------
    atoms_f = base_dir / "research" / "all-atoms.json"
    conns_f = base_dir / "research" / "connections.json"
    r = subprocess.run(["python3", str(ROOT / "scripts" / "export-brain.py"),
                        "--brain", base, "--from-files", str(atoms_f), str(conns_f)],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        say("ERR", f"export failed:\n{r.stdout[-800:]}\n{r.stderr[-400:]}"); sys.exit(1)
    say("OK", "pack re-exported from local files")

    # --- 5. Restore curated intro.md --------------------------------------
    if saved_intro and not (base_dir / "pack" / "intro.md").exists():
        (base_dir / "pack" / "intro.md").write_text(saved_intro)
        say("OK", "restored curated intro.md")

    # --- 6. Reconcile index.json ------------------------------------------
    idx_path = BRAINS / "index.json"
    idx = json.loads(idx_path.read_text())
    stage_entry = next((b for b in idx["brains"] if b["slug"] == stage), None)
    pack = json.loads((base_dir / "pack" / "brain-atoms.json").read_text())
    new_brains = []
    for b in idx["brains"]:
        if b["slug"] == stage:
            continue
        if b["slug"] == base:
            b["atom_count"] = len(pack.get("atoms", []))
            b["connection_count"] = len(pack.get("connections", []))
            if stage_entry and stage_entry.get("source"):
                b["source"] = stage_entry["source"]
            # Preserve the live brain's existing visibility — do NOT force "live"
            # (would wrongly publish a hidden/Rob-only brain on promotion).
            b["status"] = b.get("status", "live")
            b["pack_path"] = f"brains/{base}/pack/"
        new_brains.append(b)
    idx["brains"] = new_brains
    idx_path.write_text(json.dumps(idx, indent=2) + "\n")
    say("OK", f"index.json: {base} -> {len(pack.get('atoms', []))} atoms, {stage} entry removed")

    # --- 7. Re-sync website/public, remove staging public dir -------------
    subprocess.run(["node", "scripts/sync-brain-assets.mjs"], cwd=WEBSITE,
                   capture_output=True, text=True)
    shutil.rmtree(WEBSITE / "public" / "brains" / stage, ignore_errors=True)
    say("OK", "website/public re-synced; staging public dir removed")

    # --- 8. Drop orphaned staging Supabase tables -------------------------
    ok, msg = supabase_exec(
        f"DROP TABLE IF EXISTS {stage_us}_connections CASCADE; "
        f"DROP TABLE IF EXISTS {stage_us}_atoms CASCADE;")
    say("OK" if ok else "WARN", f"drop {stage_us}_* tables: {msg}")

    # --- 9. Finalize base Supabase: load pack + embed + parity ------------
    # Makes the promoted brain an exact, embedded DB mirror of its pack so it
    # isn't left with stale atoms (the deferred-finalize bug). finalize-supabase
    # is idempotent and robust (loop-until-count); for brains that cross_connections
    # FK-references (scott-belsky) it clears the stale links first.
    if not args.skip_finalize:
        say("i", "finalizing base Supabase (load pack + embed)...")
        r = subprocess.run(["python3", str(ROOT / "scripts" / "finalize-supabase.py"),
                            "--brain", base], cwd=ROOT)
        say("OK" if r.returncode == 0 else "WARN", f"finalize-supabase exited {r.returncode}")

    print()
    say("DONE", f"{stage} promoted to {base}. Review `git status`/diff, then commit.")


if __name__ == "__main__":
    main()
