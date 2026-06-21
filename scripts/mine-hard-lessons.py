#!/usr/bin/env python3
"""Phase 3.6 — Hard Lessons + Receipts mining.

Auto-generates `synthesis.hard_lessons` for a brain from its OWN diarized atom
corpus (subject-only quotes), instead of hand-mining. Each lesson is:

    { "title": "the mistake, first person",
      "cost":  "what it actually cost (must name a REAL, grounded cost)",
      "change":"what changed as a result",
      "receipts": [ { "quote": "<verbatim backing quote>",
                      "source": "<human label>", "atom_id": "<traceability>" } ] }

The honesty rubric is the entire point: a lesson that can't name a real,
corpus-grounded cost is DROPPED, and an empty list is the CORRECT output for a
sanitized/thin corpus — it's a QA signal, not a hole to fill with filler.

Anti-fabrication: the LLM may only cite quotes from a numbered RECEIPT POOL built
from the brain's research/*-atoms.json. Every returned receipt is validated to
substring-match a real pool quote; receipts that don't match are dropped, and a
lesson left with zero valid receipts is dropped (the cost was ungrounded).

The structured `synthesis.hard_lessons` key is the source of truth — explore.html
renders it, and export-brain.py renders a "## Hard Lessons" section in
brain-context.md from it, so the LLM (/advise, /coach, ...) sees them too.

Usage:
  python3 scripts/mine-hard-lessons.py --brain jesse-pujji            # mine + write
  python3 scripts/mine-hard-lessons.py --brain jesse-pujji --dry-run  # no write, show plan + result
  python3 scripts/mine-hard-lessons.py --brain jesse-pujji --target 4 # aim for N lessons
  python3 scripts/mine-hard-lessons.py --brain jesse-pujji --force    # overwrite existing hard_lessons
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from auto_build_config import (  # noqa: E402
    BRAINS_DIR,
    DEFAULT_MODEL,
    HARD_LESSONS_PROMPT,
    CostTracker,
    call_claude,
    step,
    success,
    warn,
    error,
)

try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: pip install anthropic")
    sys.exit(1)

# Pool sizing: ~140K chars (~35K tokens) leaves room for synthesis context + a
# generous response under any model's window.
POOL_MAX_CHARS = 140_000
SYNTH_CONTEXT_MAX_CHARS = 6_000
DEFAULT_TARGET = 4
MIN_QUOTE_LEN = 25

# Words that flag failure / cost / reversal material. Used ONLY to prioritize which
# atoms fill a capacity-limited pool — never to exclude. Lessons can hide in
# neutrally-phrased atoms, so non-failure atoms still get included until the budget
# is exhausted; this just front-loads the richest material.
FAILURE_HINTS = (
    "fail", "mistake", "wrong", "regret", "lost", "lose", "losing", "cost me",
    "should have", "shouldn't", "wish i", "the hard way", "struggle", "almost",
    "nearly", "died", "die", "broke", "debt", "fired", "quit", "gave up",
    "too long", "too late", "naive", "hubris", "ego", "blind", "painful",
    "worst", "screwed", "blew it", "messed up", "bad call", "burned", "burnout",
    "overconfident", "underestimat", "i was wrong", "in hindsight", "looking back",
    "if i could go back", "biggest lesson", "learned", "humbl", "fell apart",
)


def _norm(s: str) -> str:
    """Whitespace-collapsed, lowercased — for tolerant quote matching."""
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def humanize_source(source_ref: str) -> str:
    """Best-effort human label from a source_ref (often a title already, sometimes a URL)."""
    s = (source_ref or "").strip()
    if not s or s.lower() == "unknown":
        return "source"
    if s.startswith("http"):
        # Pull a readable slug from the path; fall back to the domain.
        m = re.match(r"https?://([^/]+)(/.*)?", s)
        host = (m.group(1) if m else s).replace("www.", "")
        path = (m.group(2) or "") if m else ""
        slug = path.rstrip("/").split("/")[-1] if path.strip("/") else ""
        slug = re.sub(r"[-_]+", " ", re.sub(r"\.\w+$", "", slug)).strip()
        if slug and len(slug) > 3:
            return slug[:70].title()
        return host
    return s[:80]


def load_receipt_pool(slug: str) -> list[dict]:
    """Build the citation pool: every atom with a verbatim original_quote, deduped,
    carrying id + source_ref so receipts are traceable. Mirrors
    fact-check-brain.load_source_corpus's globbing but keeps the atom id."""
    brain_dir = BRAINS_DIR / slug
    research_dir = brain_dir / "research"
    pool = []
    seen = set()
    if not research_dir.exists():
        return pool
    for fp in sorted(research_dir.glob("*-atoms.json")):
        try:
            atoms = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(atoms, list):
            continue
        for a in atoms:
            q = (a.get("original_quote") or "").strip()
            if len(q) < MIN_QUOTE_LEN:
                continue
            key = _norm(q)
            if key in seen:
                continue
            seen.add(key)
            pool.append({
                "id": a.get("id") or "",
                "quote": q,
                "source_ref": a.get("source_ref") or "",
                "content": (a.get("content") or "").strip(),
            })
    return pool


def failure_score(entry: dict) -> int:
    hay = (entry["content"] + " " + entry["quote"]).lower()
    return sum(1 for h in FAILURE_HINTS if h in hay)


def build_pool_block(pool: list[dict]) -> tuple[str, list[dict]]:
    """Render the numbered pool under a char budget, failure-relevant atoms first.
    Returns (rendered_block, included_entries) where included_entries[i] is pool
    index i in the prompt (so we can validate by pool_index)."""
    ranked = sorted(pool, key=failure_score, reverse=True)
    lines = []
    included = []
    used = 0
    for entry in ranked:
        src = humanize_source(entry["source_ref"])
        line = f'[{len(included)}] ({src}) "{entry["quote"]}"'
        if used + len(line) > POOL_MAX_CHARS and included:
            break
        lines.append(line)
        included.append(entry)
        used += len(line) + 1
    return "\n".join(lines), included


def build_synthesis_context(brain: dict) -> str:
    """Compact who-they-are context. Titles only — we never mine lessons from here."""
    syn = brain.get("synthesis", {}) or {}
    parts = []
    tag = syn.get("hero_tagline")
    if tag:
        parts.append(f"Tagline: {tag}")
    for section, label in (
        ("first_principles", "First principles"),
        ("contrarian_positions", "Contrarian positions"),
        ("biography", "Career arc"),
    ):
        items = syn.get(section) or []
        if not items:
            continue
        bullets = []
        for it in items[:8]:
            t = it.get("title") or it.get("name") or it.get("role") or ""
            if section == "biography":
                t = f'{it.get("date","")} {it.get("role","")}: {it.get("lesson","")}'
            if t.strip():
                bullets.append(f"- {t.strip()}")
        if bullets:
            parts.append(f"{label}:\n" + "\n".join(bullets))
    return ("\n\n".join(parts))[:SYNTH_CONTEXT_MAX_CHARS]


def validate_receipt(rec: dict, included: list[dict]) -> dict | None:
    """Validate a single returned receipt against the pool. Returns a cleaned
    receipt (quote/source/atom_id) or None if it can't be grounded."""
    idx = rec.get("pool_index")
    cited = (rec.get("quote") or "").strip()
    if not isinstance(idx, int) or idx < 0 or idx >= len(included) or len(cited) < MIN_QUOTE_LEN:
        return None
    pool_quote = included[idx]["quote"]
    nc, np_ = _norm(cited), _norm(pool_quote)
    # Tolerant containment either direction (LLM may copy a sub-span or the whole
    # entry). Require a real overlap, not an incidental short fragment.
    grounded = (nc in np_ or np_ in nc) and min(len(nc), len(np_)) >= 25
    if not grounded:
        # Last-chance: 60-char prefix containment (handles minor trailing edits).
        grounded = len(nc) >= 60 and nc[:60] in np_
    if not grounded:
        return None
    src = (rec.get("source") or "").strip() or humanize_source(included[idx]["source_ref"])
    out = {"quote": pool_quote, "source": src, "atom_id": included[idx]["id"]}
    return out


def mine(slug: str, target: int, model: str, dry_run: bool, force: bool) -> dict:
    bdir = BRAINS_DIR / slug
    bj_path = bdir / "brain.json"
    if not bj_path.exists():
        error(f"{slug}: brain.json not found")
        return {"ok": False}
    brain = json.loads(bj_path.read_text())
    person = brain.get("brain_name", slug)
    first = brain.get("brain_first_name") or person.split()[0]

    existing = (brain.get("synthesis", {}) or {}).get("hard_lessons")
    if existing and not force and not dry_run:
        warn(f"{slug}: synthesis.hard_lessons already has {len(existing)} entries — use --force to overwrite")
        return {"ok": True, "skipped": True, "count": len(existing)}

    pool = load_receipt_pool(slug)
    if not pool:
        warn(f"{slug}: no atoms with original_quote — corpus carries no verbatim voice to ground lessons in. Writing []. (QA signal: add failure-heavy primary sources.)")
        if not dry_run:
            _write(brain, bj_path, [])
        return {"ok": True, "count": 0, "pool": 0, "reason": "no_voice"}

    pool_block, included = build_pool_block(pool)
    synth_ctx = build_synthesis_context(brain)
    step(f"{slug}: receipt pool {len(included)}/{len(pool)} atoms ({len(pool_block):,} chars) · person={person}")

    prompt = HARD_LESSONS_PROMPT.format(
        person_name=person,
        person_first=first,
        target=target,
        pool_size=len(included),
        receipt_pool=pool_block,
        synthesis_context=synth_ctx or "(no synthesis context available)",
    )

    if dry_run:
        step(f"[DRY RUN] would call {model} with {len(included)}-entry pool, target {target} lessons")
        print(f"    top failure-relevant atoms:")
        for e in sorted(included, key=failure_score, reverse=True)[:5]:
            print(f"      ({failure_score(e)}) {e['quote'][:90]}")
        return {"ok": True, "dry_run": True, "pool": len(included)}

    client = Anthropic()
    tracker = CostTracker()
    res = call_claude(
        client, model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000, parse_json=True,
        cost_tracker=tracker, label=f"hard-lessons:{slug}",
    )
    parsed = res.get("parsed", {}) or {}
    raw = parsed.get("hard_lessons", []) if isinstance(parsed, dict) else []
    notes = parsed.get("notes", "") if isinstance(parsed, dict) else ""

    # --- Validate receipts; drop ungrounded lessons ---
    clean = []
    dropped = 0
    for L in raw:
        if not isinstance(L, dict):
            continue
        title = (L.get("title") or "").strip()
        cost = (L.get("cost") or "").strip()
        change = (L.get("change") or "").strip()
        receipts = []
        for rec in (L.get("receipts") or []):
            v = validate_receipt(rec, included)
            if v:
                receipts.append(v)
        # A hard lesson must have a title, a named cost, and at least one grounded
        # receipt — the receipt is the proof the cost was real. No receipt -> drop.
        if title and cost and receipts:
            clean.append({"title": title, "cost": cost, "change": change, "receipts": receipts})
        else:
            dropped += 1

    print()
    success(f"{slug}: {len(clean)} grounded hard lessons "
            f"({dropped} dropped for ungrounded/missing cost) · cost ${tracker.total_cost:.2f}")
    if notes:
        step(f"miner notes: {notes[:200]}")
    for L in clean:
        print(f"    • {L['title'][:80]}  [{len(L['receipts'])} receipt(s)]")
    if not clean:
        warn(f"{slug}: returning [] — corpus did not honestly support a single grounded hard lesson. "
             f"This is a QA signal (sanitized/thin failure material), not a script failure.")

    _write(brain, bj_path, clean)
    return {"ok": True, "count": len(clean), "dropped": dropped, "pool": len(included),
            "cost": tracker.total_cost, "notes": notes}


def _write(brain: dict, bj_path: Path, lessons: list):
    brain.setdefault("synthesis", {})
    brain["synthesis"]["hard_lessons"] = lessons
    bj_path.write_text(json.dumps(brain, indent=2))
    success(f"wrote synthesis.hard_lessons ({len(lessons)} entries) -> {bj_path.name}")


def main():
    ap = argparse.ArgumentParser(description="Mine grounded hard lessons + receipts from a brain's corpus")
    ap.add_argument("--brain", required=True)
    ap.add_argument("--target", type=int, default=DEFAULT_TARGET, help="Aim for N lessons (fewer/zero is OK)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true", help="No write; show pool + plan")
    ap.add_argument("--force", action="store_true", help="Overwrite existing synthesis.hard_lessons")
    args = ap.parse_args()
    r = mine(args.brain, args.target, args.model, args.dry_run, args.force)
    sys.exit(0 if r.get("ok") else 1)


if __name__ == "__main__":
    main()
