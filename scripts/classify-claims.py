#!/usr/bin/env python3
"""Epistemic classifier — tag every atom fact | opinion | prediction.

Phase 1 of the universal epistemic-atoms upgrade. BrainsFor used to store a
verifiable fact ("the casino filed Chapter 11 in 1991") and an asserted falsehood
("the election was stolen") identically — both as "a distilled thing the person
believes". The persona contract then voices either in first person as truth.

This is the CHEAP, SAFE half: classify each atom's `claim_type`. It does NOT
verify anything — every fact stays `verification='unverified'` (Phase 3 /
verify-facts.py attaches verdicts + proof, lazily, only where it pays). Defaults
mean an unclassified or unsure atom reads as `opinion` — never asserted as fact.

The classification rule (kept deliberately narrow so thinker-brains don't over-hedge):
  fact       = a DISCRETE, CHECKABLE assertion about what is/was true in the world:
               events, dates, quantities, named entities and their relationships,
               historical occurrences. Could be confirmed/refuted by an external record.
  opinion    = a stance, value, preference, strategic judgment, framing, or general
               THESIS the person argues for. Not settled by a record. (Most atoms.)
  prediction = a claim about the FUTURE.

So "compute is the primary driver of AI progress" (a thesis) → opinion; "Anthropic
was founded in 2021" → fact; "AGI arrives by 2027" → prediction; "the election was
stolen" → fact (a discrete checkable claim; Phase 3 then marks verification=false).

Reads/writes the build project's <slug>_atoms table (uzediwokyshjbsymevtp via
~/rob-ai/.env), so a subsequent `export-brain.py --brain <slug>` carries the field
into the shipped pack JSON (which both the MCP and the website read).

Usage:
  python3 scripts/classify-claims.py --brain dario-amodei            # classify all atoms
  python3 scripts/classify-claims.py --brain dario-amodei --dry-run  # sample, no API/writes
  python3 scripts/classify-claims.py --brain dario-amodei --limit 80 # cap (smoke test)
  python3 scripts/classify-claims.py --brain dario-amodei --only-unset  # skip already-classified
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from auto_build_config import (  # noqa: E402
    BRAINS_DIR, FAST_MODEL, CostTracker, call_claude, step, success, warn, error,
)

try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: pip install anthropic"); sys.exit(1)

VALID = ("fact", "opinion", "prediction")
BATCH = 40  # atoms per LLM call

CLASSIFY_SYS = """You label atoms from a knowledge "brain pack" by their EPISTEMIC TYPE — what KIND of claim each is, NOT whether it's true. Three labels:

- "fact": a DISCRETE, CHECKABLE assertion about what is or was true in the world — a dated event, a quantity, a named entity and its relationships, a historical occurrence, who-did-what-when. The test: could an external record (court filing, news archive, company page, biography) in principle CONFIRM OR REFUTE it? If yes → fact. (This includes claims that may be FALSE or contested — "the election was stolen" is a fact-type claim, because it's checkable. You are not judging truth here, only checkability.)

- "opinion": a stance, value, preference, strategic judgment, framing, mental model, or general THESIS the person argues for. Not settled by any record. Most atoms in a thinker's brain are opinions — "taste is the ultimate moat", "compute is the primary driver of AI progress", "you should fire fast". When unsure, default to opinion.

- "prediction": a claim about the FUTURE — what WILL or WON'T happen, a forecast, a timeline ("AGI by 2027", "this category will consolidate").

Bias: reserve "fact" for genuinely discrete, record-checkable assertions. A broad empirical thesis the person reasons toward is an OPINION, not a fact. When genuinely torn between fact and opinion, choose opinion (the safe default — opinions are voiced freely; facts get verification-gated downstream).

Return ONLY JSON, no markdown:
{"labels": [{"i": <int index>, "type": "fact|opinion|prediction"}]}"""


def get_client():
    try:
        from supabase import create_client
    except ImportError:
        error("supabase package not installed. Run: pip install supabase python-dotenv"); sys.exit(1)
    # Load ~/rob-ai/.env if present (mirrors export-brain.py expectations)
    try:
        from dotenv import load_dotenv
        load_dotenv(Path.home() / "rob-ai" / ".env")
    except ImportError:
        pass
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    svc = os.environ.get("SUPABASE_SERVICE_KEY", "")
    anon = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
    key = svc if svc.count(".") == 2 else anon
    if not url or not key:
        error("SUPABASE_URL + SUPABASE_SERVICE_KEY must be set (~/rob-ai/.env)"); sys.exit(1)
    return create_client(url, key)


def atom_text(a: dict) -> str:
    parts = [a.get("content") or ""]
    if a.get("original_quote"):
        parts.append(f"(quote: {a['original_quote']})")
    if a.get("implication"):
        parts.append(f"(implication: {a['implication']})")
    return " ".join(parts).strip()


def main():
    ap = argparse.ArgumentParser(description="Classify atom claim_type (fact/opinion/prediction)")
    ap.add_argument("--brain", required=True)
    ap.add_argument("--model", default=FAST_MODEL)
    ap.add_argument("--limit", type=int, default=None, help="Cap atoms classified (smoke test)")
    ap.add_argument("--only-unset", action="store_true", help="Skip atoms already non-default-classified")
    ap.add_argument("--dry-run", action="store_true", help="Sample + show, no API call, no writes")
    args = ap.parse_args()

    slug = args.brain
    bj = BRAINS_DIR / slug / "brain.json"
    if not bj.exists():
        error(f"{slug}: brain.json not found"); sys.exit(1)
    table = json.loads(bj.read_text()).get("supabase", {}).get("atoms_table")
    if not table:
        error(f"{slug}: brain.json missing supabase.atoms_table"); sys.exit(1)

    sb = get_client()
    rows, offset = [], 0
    while True:
        resp = sb.table(table).select(
            "id, content, original_quote, implication, claim_type"
        ).range(offset, offset + 999).execute()
        chunk = resp.data or []
        rows.extend(chunk)
        if len(chunk) < 1000:
            break
        offset += 1000

    if args.only_unset:
        rows = [r for r in rows if (r.get("claim_type") or "opinion") == "opinion"]
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        success(f"{slug}: nothing to classify"); return

    step(f"{slug}: classifying {len(rows)} atoms (model={args.model}, batch={BATCH}) table={table}")

    if args.dry_run:
        for r in rows[:12]:
            print(f"  - {atom_text(r)[:120]}")
        warn("dry-run: no API call, no writes"); return

    client = Anthropic()
    tracker = CostTracker()
    labels: dict[str, str] = {}
    for start in range(0, len(rows), BATCH):
        batch = rows[start:start + BATCH]
        numbered = "\n".join(f"{i}: {atom_text(a)[:600]}" for i, a in enumerate(batch))
        res = call_claude(
            client, args.model,
            messages=[{"role": "user", "content": f"Classify each atom by index:\n\n{numbered}"}],
            system=CLASSIFY_SYS, max_tokens=2000, parse_json=True,
            cost_tracker=tracker, label=f"classify:{slug}:{start}",
        )
        for item in (res.get("parsed", {}) or {}).get("labels", []):
            try:
                idx = int(item.get("i"))
                t = item.get("type")
            except (TypeError, ValueError):
                continue
            if 0 <= idx < len(batch) and t in VALID:
                labels[batch[idx]["id"]] = t
        done = min(start + BATCH, len(rows))
        print(f"    {done}/{len(rows)} classified · ${tracker.total_cost:.2f}", end="\r")
    print()

    # Default any atom the model skipped to opinion (safe).
    for r in rows:
        labels.setdefault(r["id"], "opinion")

    counts = {t: 0 for t in VALID}
    by_type: dict[str, list[str]] = {t: [] for t in VALID}
    for aid, t in labels.items():
        counts[t] += 1
        by_type[t].append(aid)

    # Bulk write: one UPDATE per type via .in_(id, [...]).
    for t, ids in by_type.items():
        for s in range(0, len(ids), 200):
            sb.table(table).update({"claim_type": t}).in_("id", ids[s:s + 200]).execute()

    success(f"{slug}: fact={counts['fact']} opinion={counts['opinion']} "
            f"prediction={counts['prediction']} · ${tracker.total_cost:.2f} written to {table}")
    print("    → re-export to carry into the pack: "
          f"python3 scripts/export-brain.py --brain {slug} --no-sync-website")


if __name__ == "__main__":
    main()
