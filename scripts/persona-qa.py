#!/usr/bin/env python3
"""Tier-3 Persona QA — judge a brain from its human's perspective.

The structural audit (Tier 1) and behavioral eval (Tier 2) can't see the thing
that matters most: would the actual person recognize themselves, is every hard
claim true, is the mess included, does it ever break the person's constitution.
This is that tier.

A panel of four brains judges the target, each in an INDEPENDENT model call (the
/board pattern — no judge ever reads another judge's verdict, so we don't get
consensus mush). Each carries a different lens:

  Kara Swisher   — Authenticity / recognizability  ("real person or performing? where does it dodge?")
  Charlie Munger — Rigor / anti-slop               ("real insight or platitudes with a name on them?")
  Brené Brown    — Coverage of the human/mess       ("is the WHOLE person here — the failures, not just wins?")
  Annie Duke     — Calibration / judge-of-judges    CHAIR ("good judgment or just good-sounding? how confident should we be?")

Constitution graded against = first_principles + does_not_believe + would_not_say
(+ hard_lessons). Constitutional-AI applied to personas.

Recusal: no brain judges its own pack or a close peer — that seat swaps to an
alternate. The chair (Annie) reads the three field verdicts + the numeric-claims
report and produces the final calibrated scorecard + ranked fixes.

Ship-gate coupling: a brain with ANY high-severity numeric defect (verify-claims.py)
is hard-capped below the pass threshold here — "zero unverified hard numbers" is a
gate, not a vibe.

Outputs:
  brains/<slug>/evals/persona-review-<date>.md   (human-readable panel review)
  brains/<slug>/evals/persona-qa-<date>.json     (machine-readable scorecard; /brain-qa input)

Usage:
  python3 scripts/persona-qa.py --brain jesse-pujji
  python3 scripts/persona-qa.py --brain jesse-pujji --dry-run     # resolve panel + sample, no API
  python3 scripts/persona-qa.py --brain jesse-pujji --model claude-opus-4-7
"""
from __future__ import annotations
import argparse
import glob
import json
import sys
from concurrent.futures import ThreadPoolExecutor
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

PASS_THRESHOLD = 70          # persona-QA score needed to clear the ship-gate
NUMERIC_DEFECT_CAP = 69      # any high-severity numeric defect hard-caps the score here
ATOM_SAMPLE = 36             # atoms shown to each judge (diverse across clusters, voice-first)

# --- Panel definition. Each seat has a default judge + ordered alternates used on
# recusal. Judges must be distinct; resolution skips already-assigned slugs. ---
PANEL = [
    {"seat": "authenticity", "lens": "Authenticity / recognizability",
     "judge": "kara-swisher", "alts": ["oprah-winfrey", "gary-vee", "scott-belsky"]},
    {"seat": "rigor", "lens": "Rigor / anti-slop",
     "judge": "charlie-munger", "alts": ["paul-graham", "yann-lecun", "peter-attia"]},
    {"seat": "coverage", "lens": "Coverage of the human / the mess",
     "judge": "brene-brown", "alts": ["melinda-french-gates", "oprah-winfrey", "reshma-saujani"]},
    {"seat": "chair", "lens": "Calibration / judge-of-judges", "is_chair": True,
     "judge": "annie-duke", "alts": ["charlie-munger", "paul-graham", "peter-zeihan"]},
]

# Symmetric close-peer recusals (judge recuses from these targets). Self is always recused.
CLOSE_PEERS = {
    "hank-green": {"john-green"}, "john-green": {"hank-green"},
    "gokul-rajaram": {"shiva-rajaraman"}, "shiva-rajaraman": {"gokul-rajaram"},
    "charlie-munger": {"warren-buffett"},
}


def recuses(judge: str, target: str) -> bool:
    if judge == target:
        return True
    return target in CLOSE_PEERS.get(judge, set())


def resolve_panel(target: str) -> list[dict]:
    """Assign a distinct judge to each seat, honoring recusal."""
    assigned = set()
    out = []
    for seat in PANEL:
        pick = None
        for cand in [seat["judge"]] + seat["alts"]:
            if cand in assigned or recuses(cand, target):
                continue
            if not (BRAINS_DIR / cand / "brain.json").exists():
                continue
            pick = cand
            break
        if pick is None:
            warn(f"seat '{seat['seat']}': no eligible judge found (all recused/missing) — seat left empty")
            continue
        assigned.add(pick)
        out.append({**seat, "judge": pick, "recused": pick != seat["judge"]})
    return out


# ---------------------------------------------------------------------------
# Loading: judge persona (compact) + target brain rendering
# ---------------------------------------------------------------------------
def load_judge_persona(slug: str) -> dict:
    brain = json.loads((BRAINS_DIR / slug / "brain.json").read_text())
    syn = brain.get("synthesis", {}) or {}
    name = brain.get("brain_name", slug)

    def bullets(section, fields, n):
        out = []
        for it in (syn.get(section) or [])[:n]:
            t = next((it.get(f) for f in fields if it.get(f)), "")
            d = it.get("desc") or it.get("description") or ""
            if t:
                out.append(f"- {t}" + (f": {d}" if d else ""))
        return "\n".join(out)

    persona = (
        f"You ARE {name}. Judge in the FIRST PERSON, in your own voice and standards.\n\n"
        f"Tagline: {syn.get('hero_tagline','')}\n\n"
        f"Your first principles:\n{bullets('first_principles', ('title','name'), 8)}\n\n"
        f"How you think:\n{bullets('thinking_patterns', ('name','title'), 6)}\n\n"
        f"Where you break from consensus:\n{bullets('contrarian_positions', ('title','name'), 6)}"
    )
    return {"name": name, "persona": persona}


def render_constitution(syn: dict) -> str:
    parts = []
    for section, label in (
        ("first_principles", "FIRST PRINCIPLES (what they believe at the root)"),
        ("contrarian_positions", "CONTRARIAN POSITIONS (where they break from consensus)"),
        ("does_not_believe", "DOES NOT BELIEVE (rejections — violating these is a constitution break)"),
        ("would_not_say", "WOULD NOT SAY (out-of-character — saying these is a constitution break)"),
    ):
        items = syn.get(section) or []
        if not items:
            parts.append(f"### {label}\n(EMPTY — itself a QA signal)")
            continue
        lines = []
        for it in items:
            t = it.get("title") or it.get("name") or ""
            d = it.get("desc") or it.get("description") or ""
            lines.append(f"- {t}" + (f" — {d}" if d else ""))
        parts.append(f"### {label}\n" + "\n".join(lines))
    return "\n\n".join(parts)


def render_hard_lessons(syn: dict) -> str:
    hl = syn.get("hard_lessons") or []
    if not hl:
        return ("### HARD LESSONS\n(EMPTY — the corpus surfaced no grounded failures. "
                "If this person has well-documented failures, an empty section is a coverage defect.)")
    out = ["### HARD LESSONS (mistake → cost → change, with receipts)"]
    for h in hl:
        out.append(f"\n**{h.get('title','')}**")
        if h.get("cost"):
            out.append(f"- Cost: {h['cost']}")
        if h.get("change"):
            out.append(f"- Changed: {h['change']}")
        for r in (h.get("receipts") or []):
            out.append(f"  > \"{(r.get('quote') or '')[:200]}\" — {r.get('source','')}")
    return "\n".join(out)


def sample_atoms(slug: str, n: int = ATOM_SAMPLE) -> str:
    """A diverse, voice-first sample spread across clusters."""
    pack = BRAINS_DIR / slug / "pack" / "brain-atoms.json"
    if not pack.exists():
        return "(no atom pack found)"
    atoms = json.loads(pack.read_text()).get("atoms", [])
    if not atoms:
        return "(no atoms)"
    by_cluster: dict[str, list] = {}
    for a in atoms:
        by_cluster.setdefault(a.get("cluster", "?"), []).append(a)
    # Round-robin across clusters, preferring atoms that carry a verbatim quote.
    for c in by_cluster:
        by_cluster[c].sort(key=lambda a: 0 if a.get("original_quote") else 1)
    picked = []
    clusters = list(by_cluster)
    idx = {c: 0 for c in clusters}
    while len(picked) < n and any(idx[c] < len(by_cluster[c]) for c in clusters):
        for c in clusters:
            if idx[c] < len(by_cluster[c]):
                picked.append(by_cluster[c][idx[c]])
                idx[c] += 1
                if len(picked) >= n:
                    break
    lines = []
    for a in picked:
        line = f"- [{a.get('cluster','?')}] {a.get('content','')[:220]}"
        if a.get("original_quote"):
            line += f'\n    voice: "{a["original_quote"][:200]}"'
        lines.append(line)
    return "\n".join(lines)


def load_numeric_report(slug: str) -> dict | None:
    files = sorted(glob.glob(str(BRAINS_DIR / slug / "evals" / "numeric-claims-*.json")))
    if not files:
        return None
    try:
        return json.loads(Path(files[-1]).read_text())
    except Exception:
        return None


def render_numeric_summary(rep: dict | None) -> str:
    if not rep:
        return ("NUMERIC VERIFICATION: not run for this brain. Treat all hard figures as UNVERIFIED "
                "and weight authenticity/calibration cautiously.")
    lines = [f"NUMERIC VERIFICATION (verify-claims.py, {rep.get('date','?')}): "
             f"{rep.get('total_claims',0)} figure claims, {rep.get('high_severity_count',0)} HIGH-severity defect(s), "
             f"fidelity penalty {rep.get('fidelity_penalty',0)}."]
    for d in rep.get("defects", [])[:6]:
        lines.append(f"  - [{d.get('severity')}/{d.get('status')}] ({d.get('where')}) {d.get('claim','')[:100]}")
        if d.get("corpus_value"):
            lines.append(f"      corpus says: {d['corpus_value'][:90]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Judge + chair prompts
# ---------------------------------------------------------------------------
FIELD_JUDGE_SYS = """{persona}

You have been asked to judge a "brain pack" — a structured attempt to capture how a DIFFERENT person ({target_name}) thinks, so an AI can reason as them. You are judging it through ONE lens: **{lens}**.

Your job is NOT to be nice. A brain that scores high is one that {target_name} themselves would recognize as real, rigorous, and complete on your dimension. Apply YOUR standards — the ones that make you you.

Lens-specific question to answer: {lens_question}

You will see: the target's CONSTITUTION (first principles, contrarian positions, what they do/don't believe, what they'd never say), their HARD LESSONS (failures with receipts), a SAMPLE of atoms (with the person's own voice), and a NUMERIC-VERIFICATION summary.

Score 0-100 on your lens ONLY. Be specific — cite the exact atom/claim text when you flag something. Empty constitution or hard-lessons sections are signals, not neutral.

Return ONLY JSON, no markdown:
{{"score": <0-100>, "recognizable": <true|false>, "verdict": "<2-4 sentence judgment in your voice>", "strengths": ["<specific>", ...], "weaknesses": ["<specific>", ...], "flags": [{{"issue": "<what's wrong>", "evidence": "<quote the offending atom/claim>", "fix": "<concrete fix>"}}]}}"""

LENS_QUESTIONS = {
    "authenticity": "Is this the real person, or a performance of them? Where is it generic, sanitized, or dodging? Would they recognize themselves — or wince?",
    "rigor": "Is this real, hard-won insight, or platitudes with a famous name stapled on? Invert: what would make this brain STUPID or fooled? Where is it standard-issue wisdom anyone could say?",
    "coverage": "Is the WHOLE human here — the failures, the doubt, the cost — or only the highlight reel? What's missing that would make this person real instead of a LinkedIn version of themselves?",
}

CHAIR_SYS = """{persona}

You are the CHAIR of a four-judge panel reviewing a "brain pack" for {target_name} — a structured capture of how {target_name} thinks. Three field judges have each scored ONE dimension independently (they did not see each other's verdicts). You judge the FOURTH dimension — **Calibration** — and you synthesize.

Your dimension (Calibration / judge-of-judges): Is this brain the product of good JUDGMENT, or is it just good-sounding? How much should we TRUST these three verdicts on THIS brain — where might a judge be over- or under-reacting? Resulting is the enemy of learning: don't reward a confident-sounding brain that's actually thin, and don't punish an honest brain for surfacing its own mess.

You also see the NUMERIC-VERIFICATION report. Hard rule: if there is ANY high-severity numeric defect, this brain CANNOT be recommended to ship — "zero unverified hard numbers" is a gate.

Produce the final scorecard. dimension_scores should reflect (and may recalibrate, with a one-line reason) the field judges' scores plus your own calibration score. persona_qa_score is your holistic 0-100 for whether {target_name} is faithfully, rigorously, completely captured. ranked_fixes are the highest-leverage changes, most important first.

Return ONLY JSON, no markdown:
{{"persona_qa_score": <0-100>, "dimension_scores": {{"authenticity": <0-100>, "rigor": <0-100>, "coverage": <0-100>, "calibration": <0-100>}}, "confidence": "high|medium|low", "ship_recommendation": "ship|hold|rework", "summary": "<3-5 sentences in your voice: would {target_name} recognize themselves, and how sure are we>", "calibration_note": "<how much to trust these judges on this brain, and any recalibration you made>", "ranked_fixes": [{{"priority": <int>, "fix": "<concrete>", "why": "<leverage>"}}]}}"""


def build_target_block(target_name, syn, slug, numeric_rep) -> str:
    return (
        f"# BRAIN UNDER REVIEW: {target_name}\n\n"
        f"## CONSTITUTION\n{render_constitution(syn)}\n\n"
        f"## {render_hard_lessons(syn)}\n\n"
        f"## ATOM SAMPLE (the person's distilled ideas + verbatim voice)\n{sample_atoms(slug)}\n\n"
        f"## {render_numeric_summary(numeric_rep)}"
    )


def run_field_judge(seat, target_name, target_block, model, tracker, client) -> dict:
    persona = load_judge_persona(seat["judge"])
    sys_prompt = FIELD_JUDGE_SYS.format(
        persona=persona["persona"], target_name=target_name, lens=seat["lens"],
        lens_question=LENS_QUESTIONS.get(seat["seat"], "Judge faithfully on your lens."),
    )
    res = call_claude(client, model, system=sys_prompt,
                      messages=[{"role": "user", "content": target_block}],
                      max_tokens=1800, parse_json=True, cost_tracker=tracker,
                      label=f"persona-qa:{seat['seat']}:{seat['judge']}")
    v = res.get("parsed", {}) or {}
    return {"seat": seat["seat"], "lens": seat["lens"], "judge": seat["judge"],
            "judge_name": persona["name"], "recused": seat["recused"], **v}


def run_chair(chair_seat, target_name, target_block, field_verdicts, numeric_rep, model, tracker, client) -> dict:
    persona = load_judge_persona(chair_seat["judge"])
    sys_prompt = CHAIR_SYS.format(persona=persona["persona"], target_name=target_name)
    panel_block = "\n\n".join(
        f"### Field judge — {v['lens']} (played by {v['judge_name']}{' [ALT]' if v['recused'] else ''})\n"
        f"score={v.get('score','?')} recognizable={v.get('recognizable','?')}\n"
        f"verdict: {v.get('verdict','')}\n"
        f"weaknesses: {'; '.join(v.get('weaknesses', []))[:500]}\n"
        f"flags: {'; '.join(f'{f.get('issue','')}' for f in v.get('flags', []))[:500]}"
        for v in field_verdicts
    )
    user = (f"{target_block}\n\n# FIELD-JUDGE VERDICTS (independent — they did not see each other)\n\n{panel_block}\n\n"
            f"Now deliver your calibration judgment and the final synthesized scorecard.")
    res = call_claude(client, model, system=sys_prompt,
                      messages=[{"role": "user", "content": user}],
                      max_tokens=2000, parse_json=True, cost_tracker=tracker,
                      label=f"persona-qa:chair:{chair_seat['judge']}")
    v = res.get("parsed", {}) or {}
    v["chair"] = chair_seat["judge"]
    v["chair_name"] = persona["name"]
    v["chair_recused"] = chair_seat["recused"]
    return v


def main():
    ap = argparse.ArgumentParser(description="Annie-chaired persona-QA panel for a brain")
    ap.add_argument("--brain", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true", help="Resolve panel + show target block size, no API")
    ap.add_argument("--date", default=None, help="Override output date stamp (YYYY-MM-DD)")
    args = ap.parse_args()

    slug = args.brain
    bj = BRAINS_DIR / slug / "brain.json"
    if not bj.exists():
        error(f"{slug}: brain.json not found"); sys.exit(1)
    brain = json.loads(bj.read_text())
    target_name = brain.get("brain_name", slug)
    syn = brain.get("synthesis", {}) or {}

    panel = resolve_panel(slug)
    field_seats = [s for s in panel if not s.get("is_chair")]
    chair_seat = next((s for s in panel if s.get("is_chair")), None)
    if not chair_seat or not field_seats:
        error(f"{slug}: could not assemble a panel (chair or field seats missing)"); sys.exit(1)

    print(f"\n  Panel for {target_name}:")
    for s in panel:
        role = "CHAIR" if s.get("is_chair") else s["seat"]
        print(f"    {role:13s} → {s['judge']}{'  [recused→alt]' if s['recused'] else ''}")

    numeric_rep = load_numeric_report(slug)
    target_block = build_target_block(target_name, syn, slug, numeric_rep)

    if args.dry_run:
        step(f"[DRY RUN] target block {len(target_block):,} chars · "
             f"numeric report: {'present' if numeric_rep else 'MISSING (run verify-claims.py first)'}")
        print(target_block[:1500] + "\n    ...")
        return

    client = Anthropic()
    tracker = CostTracker()

    # --- 3 field judges, independent + concurrent (CostTracker is thread-safe) ---
    step(f"running {len(field_seats)} field judges (independent) + chair...")
    with ThreadPoolExecutor(max_workers=len(field_seats)) as ex:
        field_verdicts = list(ex.map(
            lambda s: run_field_judge(s, target_name, target_block, args.model, tracker, client),
            field_seats,
        ))
    for v in field_verdicts:
        print(f"    {v['lens'][:34]:34s} {v['judge']:16s} score={v.get('score','?')}")

    # --- chair synthesizes ---
    chair = run_chair(chair_seat, target_name, target_block, field_verdicts, numeric_rep,
                      args.model, tracker, client)

    # --- final score with numeric hard-cap ---
    raw_score = chair.get("persona_qa_score", 0) or 0
    high_defects = (numeric_rep or {}).get("high_severity_count", 0)
    capped = high_defects > 0 and raw_score > NUMERIC_DEFECT_CAP
    final_score = min(raw_score, NUMERIC_DEFECT_CAP) if capped else raw_score
    passes = final_score >= PASS_THRESHOLD and high_defects == 0

    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    scorecard = {
        "slug": slug, "target": target_name, "date": date,
        "persona_qa_score": final_score, "raw_chair_score": raw_score,
        "numeric_capped": capped, "high_severity_numeric_defects": high_defects,
        "pass": passes, "pass_threshold": PASS_THRESHOLD,
        "dimension_scores": chair.get("dimension_scores", {}),
        "confidence": chair.get("confidence", ""),
        "ship_recommendation": "hold" if high_defects and chair.get("ship_recommendation") == "ship"
                               else chair.get("ship_recommendation", ""),
        "summary": chair.get("summary", ""),
        "calibration_note": chair.get("calibration_note", ""),
        "ranked_fixes": chair.get("ranked_fixes", []),
        "panel": [{"seat": s["seat"], "judge": s["judge"], "recused": s["recused"]} for s in panel],
        "field_verdicts": field_verdicts,
        "cost": round(tracker.total_cost, 4),
    }
    _write_outputs(slug, target_name, scorecard, date)

    print()
    flag = "✓ PASS" if passes else "✗ HOLD"
    capnote = f"  (capped from {raw_score} — {high_defects} high-severity numeric defect)" if capped else ""
    success(f"{slug} persona-QA: {final_score}/100  {flag}{capnote}  ·  "
            f"rec={scorecard['ship_recommendation']}  conf={scorecard['confidence']}  ·  cost ${tracker.total_cost:.2f}")
    for f in scorecard["ranked_fixes"][:5]:
        print(f"    {f.get('priority','?')}. {f.get('fix','')[:100]}")
    sys.exit(0 if passes else 1)


def _write_outputs(slug, target_name, sc, date):
    evals = BRAINS_DIR / slug / "evals"
    evals.mkdir(exist_ok=True)
    (evals / f"persona-qa-{date}.json").write_text(json.dumps(sc, indent=2))

    md = [f"# Persona QA — {target_name}", f"*{date} · Annie-chaired judge panel*", ""]
    flag = "✅ PASS" if sc["pass"] else "⛔ HOLD"
    md.append(f"## {sc['persona_qa_score']}/100 — {flag}")
    md.append(f"- **Ship recommendation:** {sc['ship_recommendation']}  ·  **Confidence:** {sc['confidence']}")
    if sc["numeric_capped"]:
        md.append(f"- ⚠️ **Score hard-capped** at {sc['pass_threshold']-1}: {sc['high_severity_numeric_defects']} "
                  f"high-severity numeric defect(s) (zero unverified hard numbers is a gate).")
    ds = sc.get("dimension_scores", {})
    md.append(f"- **Dimensions:** authenticity {ds.get('authenticity','?')} · rigor {ds.get('rigor','?')} · "
              f"coverage {ds.get('coverage','?')} · calibration {ds.get('calibration','?')}")
    md += ["", f"> {sc['summary']}", "", f"**Calibration (chair):** {sc['calibration_note']}", ""]

    md.append("## Ranked fixes")
    for f in sc.get("ranked_fixes", []):
        md.append(f"{f.get('priority','?')}. **{f.get('fix','')}** — {f.get('why','')}")
    md.append("")

    md.append("## Field-judge verdicts (independent)")
    for v in sc["field_verdicts"]:
        alt = " *(alternate — primary recused)*" if v["recused"] else ""
        md.append(f"\n### {v['lens']} — {v['judge_name']}{alt}  ·  {v.get('score','?')}/100")
        md.append(f"*Recognizable as {target_name}: {v.get('recognizable','?')}*")
        md.append(f"\n{v.get('verdict','')}")
        if v.get("weaknesses"):
            md.append("\n**Weaknesses:**")
            md += [f"- {w}" for w in v["weaknesses"]]
        if v.get("flags"):
            md.append("\n**Flags:**")
            for fl in v["flags"]:
                md.append(f"- **{fl.get('issue','')}** — _{fl.get('evidence','')[:160]}_ → {fl.get('fix','')}")
    md.append(f"\n---\n*Panel: " + ", ".join(f"{p['seat']}={p['judge']}" for p in sc["panel"]) +
              f" · cost ${sc['cost']}*")

    (evals / f"persona-review-{date}.md").write_text("\n".join(md))
    success(f"wrote evals/persona-review-{date}.md + persona-qa-{date}.json")


if __name__ == "__main__":
    main()
