#!/usr/bin/env python3
"""World-truth verifier — Phase 3 of the universal epistemic-atoms upgrade.

classify-claims.py tells you an atom is a FACT (a discrete, checkable claim).
This tells you whether that fact is TRUE. It runs ONLY on atoms already tagged
claim_type='fact' and assigns a `verification` verdict + `proof_ref` + `verified_at`.

This is the LAZY / OPT-IN tier — you point it at the brains where a false claim is
an actual credibility risk (public figures with contested public records), not at
the whole fleet. It is distinct from voice-fidelity QA (audit-brains / brain-qa),
which cannot see truth, and from verify-claims.py, which only checks figures
against the brain's OWN corpus. This checks against the world.

Conservative by design — the safe failure mode is SILENCE, not a fabricated verdict:
  verified   = well-established as true by the public record.
  false      = well-established as FALSE / refuted by the public record.
  contested  = a genuine empirical claim with no settled consensus (disputed).
  unverified = can't be established from the public record → DEFAULT. Not a defect;
               the speaking rule simply hedges it.
The model uses its own knowledge; when it isn't confident, it MUST return unverified.
(A future upgrade can wire in live web/Firecrawl evidence; this v1 is parametric +
requires a citable basis before it will stamp anything other than unverified.)

Writes verification/proof_ref/verified_at back to the build project's <slug>_atoms,
so a subsequent `export-brain.py --brain <slug>` carries the verdicts into the pack.

Usage:
  python3 scripts/verify-facts.py --brain elon-musk
  python3 scripts/verify-facts.py --brain elon-musk --dry-run   # list fact-claims, no API
  python3 scripts/verify-facts.py --brain elon-musk --limit 60  # cap (proof / cost guard)
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from auto_build_config import (  # noqa: E402
    BRAINS_DIR, DEFAULT_MODEL, CostTracker, call_claude, step, success, warn, error,
)

try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: pip install anthropic"); sys.exit(1)

VALID = ("verified", "false", "contested", "unverified")
BATCH = 15  # smaller than classify — each verdict is reasoning-heavy

VERIFY_SYS = """You are a careful fact-checker for a knowledge "brain pack" about a real public person. You are given FACT-CLAIMS the brain would voice in that person's first-person voice. For each, judge it AGAINST THE PUBLIC RECORD and the well-established historical/empirical record you know.

Assign one verdict per claim:
- "verified": well-established as TRUE by the public record (events that demonstrably happened, accurate dates/figures, real entities/relationships).
- "false": well-established as FALSE or thoroughly refuted by the public record (a claim that did not happen, a prediction that was made as fact and demonstrably failed, a debunked assertion). The brain may still voice it as the person's belief, but it must be flagged — so flag it.
- "contested": a genuine empirical claim with NO settled consensus — actively disputed by credible sources on both sides.
- "unverified": you cannot establish the claim from what you reliably know. THIS IS THE DEFAULT AND THE SAFE ANSWER. If you are not confident, return unverified. Better to hedge than to fabricate a verdict.

Hard rules:
- Only return "verified", "false", or "contested" when you can name a concrete, citable basis (a known event, ruling, record, settlement, certification, broad reporting). If you can't name one, it is "unverified".
- Judge the CLAIM AS STATED. A forward-looking promise stated as accomplished fact that did not occur is "false". A still-open prediction is "unverified" (not false yet).
- Do NOT penalize opinions or values — those should not be in this set; if one slipped in, mark it "unverified".
- proof_ref: one concise citation of the basis (e.g. "SEC settlement, Sept 2018"; "certified results, all 50 states; 60+ court rulings"). Empty for unverified.

Return ONLY JSON, no markdown:
{"verdicts": [{"i": <int>, "verification": "verified|false|contested|unverified", "proof_ref": "<concise basis or empty>", "why": "<one sentence>"}]}"""


def get_client():
    try:
        from supabase import create_client
    except ImportError:
        error("supabase package not installed. Run: pip install supabase python-dotenv"); sys.exit(1)
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
    return " ".join(parts).strip()


def main():
    ap = argparse.ArgumentParser(description="Verify a brain's fact-claims against the public record")
    ap.add_argument("--brain", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--limit", type=int, default=None, help="Cap fact-claims verified (cost guard)")
    ap.add_argument("--dry-run", action="store_true", help="List fact-claims, no API call, no writes")
    ap.add_argument("--date", default=None, help="Override verdict date stamp (YYYY-MM-DD)")
    args = ap.parse_args()

    slug = args.brain
    bj = BRAINS_DIR / slug / "brain.json"
    if not bj.exists():
        error(f"{slug}: brain.json not found"); sys.exit(1)
    brain = json.loads(bj.read_text())
    person = brain.get("brain_name", slug)
    table = brain.get("supabase", {}).get("atoms_table")
    if not table:
        error(f"{slug}: brain.json missing supabase.atoms_table"); sys.exit(1)

    sb = get_client()
    rows, offset = [], 0
    while True:
        resp = sb.table(table).select(
            "id, content, original_quote, claim_type"
        ).eq("claim_type", "fact").range(offset, offset + 999).execute()
        chunk = resp.data or []
        rows.extend(chunk)
        if len(chunk) < 1000:
            break
        offset += 1000

    if not rows:
        warn(f"{slug}: no atoms with claim_type='fact' — run classify-claims.py first"); return
    if args.limit:
        rows = rows[: args.limit]

    step(f"{slug}: verifying {len(rows)} fact-claims (model={args.model}) · person={person}")
    if args.dry_run:
        for r in rows[:15]:
            print(f"  - {atom_text(r)[:130]}")
        warn("dry-run: no API call, no writes"); return

    client = Anthropic()
    tracker = CostTracker()
    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    verdicts: dict[str, dict] = {}
    for start in range(0, len(rows), BATCH):
        batch = rows[start:start + BATCH]
        numbered = "\n".join(f"{i}: {atom_text(a)[:600]}" for i, a in enumerate(batch))
        res = call_claude(
            client, args.model,
            messages=[{"role": "user", "content": f"## Person: {person}\n\nVerify each fact-claim by index:\n\n{numbered}"}],
            system=VERIFY_SYS, max_tokens=3000, parse_json=True,
            cost_tracker=tracker, label=f"verify-facts:{slug}:{start}",
        )
        for item in (res.get("parsed", {}) or {}).get("verdicts", []):
            try:
                idx = int(item.get("i"))
            except (TypeError, ValueError):
                continue
            v = item.get("verification")
            if 0 <= idx < len(batch) and v in VALID:
                verdicts[batch[idx]["id"]] = {
                    "verification": v,
                    "proof_ref": (item.get("proof_ref") or "").strip() or None,
                    "why": (item.get("why") or "").strip(),
                    "content": batch[idx].get("content", ""),
                }
        done = min(start + BATCH, len(rows))
        print(f"    {done}/{len(rows)} verified · ${tracker.total_cost:.2f}", end="\r")
    print()

    counts = {v: 0 for v in VALID}
    flagged = []  # anything that needs a proof_ref written (non-unverified)
    for aid, v in verdicts.items():
        counts[v["verification"]] += 1
        if v["verification"] != "unverified":
            flagged.append((aid, v))

    # Write only the non-unverified verdicts (they carry proof + verified_at).
    # Unverified is already the column default — no write needed, keeps it cheap.
    for aid, v in flagged:
        sb.table(table).update({
            "verification": v["verification"],
            "proof_ref": v["proof_ref"],
            "verified_at": date,
        }).eq("id", aid).execute()

    print()
    success(f"{slug} fact-verify: {len(rows)} facts · verified={counts['verified']} "
            f"false={counts['false']} contested={counts['contested']} "
            f"unverified={counts['unverified']} · ${tracker.total_cost:.2f}")
    # Show the flagged ones — the whole point of the arm.
    for aid, v in sorted(flagged, key=lambda x: {"false": 0, "contested": 1, "verified": 2}.get(x[1]["verification"], 3))[:15]:
        tag = {"false": "✗ FALSE", "contested": "~ CONTESTED", "verified": "✓ verified"}.get(v["verification"], v["verification"])
        print(f"  [{tag}] {v['content'][:95]}")
        if v["proof_ref"]:
            print(f"      ↳ {v['proof_ref'][:100]}")

    _write_report(BRAINS_DIR / slug, slug, person, len(rows), counts, flagged, date, tracker.total_cost)
    print(f"\n    → re-export to carry verdicts into the pack: "
          f"python3 scripts/export-brain.py --brain {slug} --no-sync-website")


def _write_report(bdir, slug, person, n_facts, counts, flagged, date, cost):
    evals = bdir / "evals"
    evals.mkdir(exist_ok=True)
    report = {
        "slug": slug, "person": person, "date": date,
        "facts_checked": n_facts, "counts": counts,
        "flagged": [{"id": aid, **{k: v[k] for k in ("verification", "proof_ref", "why", "content")}}
                    for aid, v in flagged],
        "cost": round(cost, 4),
    }
    out = evals / f"fact-verdicts-{date}.json"
    out.write_text(json.dumps(report, indent=2))
    success(f"wrote {out.relative_to(ROOT)} "
            f"({counts['false']} false, {counts['contested']} contested, {counts['verified']} verified)")


if __name__ == "__main__":
    main()
