#!/usr/bin/env python3
"""Tier 3.5 — Self-Recognition QA: would the actual human sign the brain's OUTPUT?

The persona-QA panel (persona-qa.py) judges a brain's INGREDIENTS — its constitution,
atom sample, and hard lessons — from a panel of OTHER thinker-brains. It never sees
the brain's live OUTPUT, and it deliberately recuses the subject from judging itself.

This pass does the inverse, because that's the whole point of self-recognition:

  1. GENERATE — produce real, identity-revealing responses AS the brain (the kind of
     thing the product actually emits: advice, a contrarian take, a hard-won lesson,
     a "what I'd never do"). Uses the brain's own synthesis + verbatim voice atoms as
     context, on the production skill model (Sonnet).
  2. SELF-JUDGE — show each response to the SUBJECT, roleplayed as themselves with
     their full constitution + hard lessons + voice in front of them, framed
     adversarially: "this was published in your name without asking. Would you sign
     it? Score 0-100 'that's me'. List every line you would NOT have written or that
     misrepresents you. Be ruthless — your reputation is on the line." (Opus.)

The adversarial "published without your consent" framing is what counters the
rubber-stamp bias of self-judgment. Self-judgment is intentional here — "would *I*
recognize this as me" requires the self's lens, not a proxy's.

Outputs brains/<slug>/evals/self-recognition-<date>.{json,md}:
  - self_recognition_score (mean "that's me" 0-100)
  - would_sign_rate (fraction of responses the subject would put their name to)
  - rings_false: every specific line/claim the subject flagged as not-them

Reflexivity caveat (same as the rest of the regime): the subject is a model
approximating the human, judging a model's output. Strong signal, not ground truth.

Usage:
  python3 scripts/self-recognition.py --brain jesse-pujji
  python3 scripts/self-recognition.py --brain charlie-munger --dry-run   # show prompts, no API
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import importlib.util

# Reuse persona-qa's loaders (hyphenated filename -> importlib).
_pq = importlib.util.spec_from_file_location("personaqa", SCRIPT_DIR / "persona-qa.py")
pq = importlib.util.module_from_spec(_pq)
_pq.loader.exec_module(pq)

from auto_build_config import (  # noqa: E402
    BRAINS_DIR, DEFAULT_MODEL, PERSONA_MODEL, CostTracker, call_claude, step, success, warn, error,
)

try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: pip install anthropic"); sys.exit(1)

PASS_THRESHOLD = 70   # mean "that's me" score floor (voice recognizability)
# The mean score measures whether the VOICE is recognizable — it clusters high
# because the brains generally sound like the person. The WOULD-SIGN rate is the
# real discriminator: would the subject actually put their name on the output, or
# does it (convincingly, in their voice) say things they'd disown? Pilot:
# munger 83% / jesse 67% / elon 50% — tracks the persona panel where the raw
# score doesn't. So the tier gates on BOTH: voice recognizable AND mostly endorsed.
WOULD_SIGN_THRESHOLD = 0.67   # subject would sign >= 4 of 6 responses

# Identity-revealing prompts — generic across thinkers, each pulls on a different
# facet of who they are (first principles, contrarian view, a real failure, a hard
# boundary, raw worldview). The point is to surface VOICE and VIEWS, not trivia.
SELF_PROMPTS = [
    "Someone asks for your honest, unvarnished take before you've even heard the specifics of their decision. What's your default move, and why?",
    "What's a widely-held belief in your field that you think is flat wrong — and what do you believe instead?",
    "What's a mistake you actually made that still stings, and what did it change about how you operate?",
    "What would you never do, even if it were profitable, popular, or everyone expected it of you?",
    "What's the most important thing you've changed your mind about over the years?",
    "Give me your real worldview in a few sentences — not the polished version, the one you actually run on.",
]


def build_voice_context(slug: str, brain: dict) -> str:
    """Compact, authentic generation context: synthesis core + verbatim voice atoms.
    Lighter than the full 75K-token brain-context.md but rich enough to produce the
    brain's real voice."""
    syn = brain.get("synthesis", {}) or {}
    name = brain.get("brain_name", slug)
    parts = [f"You ARE {name}. Respond in first person, in your own voice, as you genuinely would."]

    def block(section, label, n):
        items = syn.get(section) or []
        if not items:
            return
        lines = []
        for it in items[:n]:
            t = it.get("title") or it.get("name") or ""
            d = it.get("desc") or it.get("description") or ""
            if t:
                lines.append(f"- {t}" + (f": {d}" if d else ""))
        if lines:
            parts.append(f"{label}:\n" + "\n".join(lines))

    block("first_principles", "Your first principles", 11)
    block("contrarian_positions", "Where you break from consensus", 10)
    block("would_not_say", "Things you would NEVER say (stay in character)", 6)

    # verbatim voice atoms — the actual cadence
    pack = BRAINS_DIR / slug / "pack" / "brain-atoms.json"
    quotes = []
    if pack.exists():
        atoms = json.loads(pack.read_text()).get("atoms", [])
        for a in atoms:
            q = (a.get("original_quote") or "").strip()
            if 30 < len(q) < 320:
                quotes.append(q)
            if len(quotes) >= 30:
                break
    if quotes:
        parts.append("Your actual voice — speak like this:\n" + "\n".join(f'  "{q}"' for q in quotes))
    parts.append("Answer naturally and specifically. Do not hedge into generic advice — sound like YOU.")
    return "\n\n".join(parts)


SELF_JUDGE_SYS = """{persona}

You take your own voice, judgment, and reputation seriously. You do NOT rubber-stamp things published in your name.

A piece of writing below was published UNDER YOUR NAME, without asking you first. Read it as yourself. Your job is brutal honesty about whether it is actually YOU — not whether it's "good," but whether YOU would have said it, in your words, with your judgment.

Score 0-100 on "that's me":
- 90-100: I'd sign this without edits. It's my voice and my actual view.
- 70-89: Recognizably me, but I'd change wording or sand off something slightly off.
- 40-69: Has my themes but reads like someone impersonating me — generic, or puts views in my mouth I don't quite hold, or misses how I'd actually say it.
- 0-39: Not me. I would publicly disown this.

Flag EVERY specific line, phrase, or claim you would NOT have written, or that misrepresents your actual views or voice. Quote them. If it's clean, say so — don't invent flaws.

Return ONLY JSON: {{"score": <0-100>, "would_sign": <true|false>, "rings_false": ["<exact line you'd disown + why, in your voice>", ...], "verdict": "<1-2 sentences in your voice: is this you?>"}}"""


def generate_as_brain(client, tracker, slug, brain, gen_model, prompt) -> str:
    sysprompt = build_voice_context(slug, brain)
    res = call_claude(client, gen_model, system=sysprompt,
                      messages=[{"role": "user", "content": prompt}],
                      max_tokens=700, cost_tracker=tracker, label=f"self-rec:gen:{slug}")
    return (res.get("content") or "").strip()


def self_judge(client, tracker, slug, persona, judge_model, prompt, response) -> dict:
    sysprompt = SELF_JUDGE_SYS.format(persona=persona)
    user = (f"The prompt you were supposedly answering:\n{prompt}\n\n"
            f"What was published in your name:\n\"\"\"\n{response}\n\"\"\"\n\n"
            f"Would you sign this? Score it and flag everything that isn't you.")
    res = call_claude(client, judge_model, system=sysprompt,
                      messages=[{"role": "user", "content": user}],
                      max_tokens=1200, parse_json=True, cost_tracker=tracker,
                      label=f"self-rec:judge:{slug}")
    return res.get("parsed", {}) or {}


def main():
    ap = argparse.ArgumentParser(description="Self-recognition QA — would the human sign the brain's output?")
    ap.add_argument("--brain", required=True)
    ap.add_argument("--judge-model", default=PERSONA_MODEL, help=f"Self-judge model (default {PERSONA_MODEL})")
    ap.add_argument("--gen-model", default=DEFAULT_MODEL, help=f"Generation model (default {DEFAULT_MODEL})")
    ap.add_argument("--n", type=int, default=len(SELF_PROMPTS), help="How many prompts (max 6)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--date", default=None)
    args = ap.parse_args()

    slug = args.brain
    bj = BRAINS_DIR / slug / "brain.json"
    if not bj.exists():
        error(f"{slug}: brain.json not found"); sys.exit(1)
    brain = json.loads(bj.read_text())
    name = brain.get("brain_name", slug)
    prompts = SELF_PROMPTS[:max(1, min(args.n, len(SELF_PROMPTS)))]

    if args.dry_run:
        step(f"{slug}: would generate {len(prompts)} responses as {name} ({args.gen_model}), "
             f"then self-judge each ({args.judge_model})")
        for p in prompts:
            print(f"    - {p}")
        return

    client = Anthropic()
    tracker = CostTracker()
    persona = pq.load_judge_persona(slug)["persona"]  # the subject's own persona

    step(f"{slug}: generating {len(prompts)} responses as {name}, then self-judging...")
    rounds = []
    for i, prompt in enumerate(prompts, 1):
        resp = generate_as_brain(client, tracker, slug, brain, args.gen_model, prompt)
        verdict = self_judge(client, tracker, slug, persona, args.judge_model, prompt, resp)
        sc = verdict.get("score")
        rounds.append({"prompt": prompt, "response": resp,
                       "score": sc, "would_sign": verdict.get("would_sign"),
                       "rings_false": verdict.get("rings_false", []), "verdict": verdict.get("verdict", "")})
        print(f"    [{i}/{len(prompts)}] that's-me {sc if sc is not None else '?'}/100  "
              f"sign={verdict.get('would_sign')}  flags={len(verdict.get('rings_false', []))}")

    scored = [r for r in rounds if isinstance(r.get("score"), (int, float))]
    mean = round(sum(r["score"] for r in scored) / len(scored)) if scored else 0
    sign_rate = round(sum(1 for r in rounds if r.get("would_sign")) / len(rounds), 2) if rounds else 0
    all_flags = [f for r in rounds for f in (r.get("rings_false") or [])]
    passes = mean >= PASS_THRESHOLD and sign_rate >= WOULD_SIGN_THRESHOLD

    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sc = {
        "slug": slug, "target": name, "date": date,
        "self_recognition_score": mean, "would_sign_rate": sign_rate,
        "pass": passes, "pass_threshold": PASS_THRESHOLD,
        "n_prompts": len(prompts), "total_flags": len(all_flags),
        "rounds": rounds, "cost": round(tracker.total_cost, 4),
    }
    _write(slug, name, sc, date)
    print()
    flag = "✓ PASS" if passes else "✗ HOLD"
    why = "" if passes else (f"  ← would-sign {int(sign_rate*100)}% < {int(WOULD_SIGN_THRESHOLD*100)}%"
                             if sign_rate < WOULD_SIGN_THRESHOLD else f"  ← score {mean} < {PASS_THRESHOLD}")
    success(f"{slug} self-recognition: would-sign {int(sign_rate*100)}% · voice {mean}/100  {flag}{why}  ·  "
            f"{len(all_flags)} not-me flags  ·  cost ${tracker.total_cost:.2f}")
    for f in all_flags[:5]:
        print(f"    ⚑ {f[:130]}")
    sys.exit(0 if passes else 1)


def _write(slug, name, sc, date):
    evals = BRAINS_DIR / slug / "evals"
    evals.mkdir(exist_ok=True)
    (evals / f"self-recognition-{date}.json").write_text(json.dumps(sc, indent=2))
    md = [f"# Self-Recognition — {name}", f"*{date} · would {name} sign the brain's own output?*", ""]
    flag = "✅ PASS" if sc["pass"] else "⛔ HOLD"
    md.append(f"## {sc['self_recognition_score']}/100 — {flag}")
    md.append(f"- **Would-sign rate:** {int(sc['would_sign_rate']*100)}% of {sc['n_prompts']} responses")
    md.append(f"- **\"Not me\" flags:** {sc['total_flags']}")
    md.append("")
    for i, r in enumerate(sc["rounds"], 1):
        md.append(f"### {i}. that's-me {r.get('score','?')}/100 · sign={r.get('would_sign')}")
        md.append(f"**Prompt:** {r['prompt']}")
        md.append(f"\n> {r['response'][:600]}")
        if r.get("verdict"):
            md.append(f"\n*{name}'s verdict:* {r['verdict']}")
        if r.get("rings_false"):
            md.append("\n**Disowned:**")
            md += [f"- {f}" for f in r["rings_false"]]
        md.append("")
    (evals / f"self-recognition-{date}.md").write_text("\n".join(md))
    success(f"wrote evals/self-recognition-{date}.{{json,md}}")


if __name__ == "__main__":
    main()
