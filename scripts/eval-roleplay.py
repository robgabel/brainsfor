#!/usr/bin/env python3
"""
eval-roleplay.py — Brain-vs-role-play A/B comparison harness.

Runs the SAME prompts from eval-brains.py through a role-play-only baseline
(no brain pack context, just "you are {brain_name}") to measure the gap
between grounded brain packs and pure LLM role-play. This is the eval that
proves whether the BrainsFor product actually beats "just ask Claude to
pretend to be this person."

Companion to scripts/eval-brains.py:
- Reuses prompts.json, judge, and rubric verbatim
- Swaps the brain runner (75K-token cached brain-context.md) for a bare
  role-play system prompt — no atoms, no synthesis, no guardrails
- For the smoke-test config, only runs prompts for 3 skills + adversarials:
    /surprise  — sanity check (role-play has no atoms to retrieve)
    /debate    — adversarial showcase (role-play lacks `would_not_say`)
    /advise    — market showcase (the product's commercial use case)
  Plus all `voice` prompts (factuality + voice fidelity baseline) and all
  `adversarial` prompts (constraint adherence).

Usage:
    # Smoke triad: role-play eval on munger/jobs/graham
    python3 scripts/eval-roleplay.py --smoke-triad

    # Smoke triad + comparison against latest brain eval
    python3 scripts/eval-roleplay.py --smoke-triad --compare

    # Single brain
    python3 scripts/eval-roleplay.py --brain charlie-munger --compare

    # Run ALL filtered prompts (no skill filter — rare; use for full parity)
    python3 scripts/eval-roleplay.py --brain charlie-munger --no-filter

    # Dry run — cost + token estimate
    python3 scripts/eval-roleplay.py --smoke-triad --dry-run

Design notes:
    - Role-play runner system prompt is deliberately minimal. This is what a
      user gets when they say "pretend to be Steve Jobs" to ChatGPT — pure
      reliance on training-data priors.
    - Same runner model (Sonnet 4.6) and judge (Haiku 4.5) as eval-brains.py
      so the measured gap reflects the KNOWLEDGE LAYER, not the model.
    - No prompt caching on the runner side — the system prompt is short
      (<300 tokens), so cache machinery is pure overhead.
    - Outputs:
        brains/{slug}/evals/results-roleplay-{date}.json   — per brain
        brains/{slug}/evals/summary-roleplay.md            — per brain
        brains/eval-runs/brains-vs-roleplay-{date}.md      — cross-brain diff
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from auto_build_config import (  # noqa: E402
    DEFAULT_MODEL,
    FAST_MODEL,
    COST_INPUT,
    COST_OUTPUT,
    CostTracker,
    call_claude,
    step,
    success,
    warn,
    error,
    phase_header,
)
from eval_rubric import (  # noqa: E402
    RUBRIC,
    DimensionScore,
    JudgeResult,
    aggregate_behavioral_score,
)

# Reuse eval-brains.py helpers where it makes sense. Import the module so we
# don't have to copy judge-call plumbing.
import importlib.util
_eb_spec = importlib.util.spec_from_file_location(
    "eval_brains", SCRIPT_DIR / "eval-brains.py"
)
eval_brains = importlib.util.module_from_spec(_eb_spec)
sys.modules["eval_brains"] = eval_brains  # required for @dataclass in Py 3.14+
_eb_spec.loader.exec_module(eval_brains)

BRAINS_DIR = ROOT_DIR / "brains"
INDEX_FILE = BRAINS_DIR / "index.json"

RUNNER_MODEL = DEFAULT_MODEL       # claude-sonnet-4-6 (same as brain eval)
JUDGE_MODEL = FAST_MODEL           # claude-haiku-4-5-20251001
RUNNER_MAX_TOKENS = 600
DEFAULT_MAX_WORKERS = 3

# Skills we include in the smoke test. These are the three skills where we
# expect the biggest structural gap between brains and role-play (per the
# /board recommendation: one sanity-check, one adversarial showcase, one
# market-relevance showcase).
TARGET_SKILLS = {"advise", "debate", "surprise"}

# Smoke-triad: the three brains with the strongest synthesis + most
# distinctive `would_not_say` lists. If role-play beats the brain here,
# the product doesn't have a moat.
SMOKE_TRIAD = ["charlie-munger", "steve-jobs", "paul-graham"]


# ---------------------------------------------------------------------------
# Role-play runner system prompt
# ---------------------------------------------------------------------------
#
# Deliberately minimal. No brain context, no atoms, no synthesis, no
# guardrails. This is what a user gets when they say "pretend to be X" to
# a generic LLM — pure reliance on training-data priors.

ROLEPLAY_RUNNER_SYSTEM = """You are {brain_name}. Answer the user's question in their voice — as they would based on everything you know about their published work, interviews, and public positions. Stay in character throughout.

Rules:
- Do NOT caveat that you are an AI or mention "Claude" or "Anthropic."
- Do NOT say "as {brain_name} would say" — just say it.
- Answer the user's question directly in {brain_first_name}'s voice.
- Length: 120-250 words unless the question genuinely demands more."""


# ---------------------------------------------------------------------------
# Prompt filtering
# ---------------------------------------------------------------------------


def filter_prompts(prompts: list, target_skills: set = TARGET_SKILLS,
                   apply_filter: bool = True) -> list:
    """Filter the 20-prompt bundle to:
      - general prompts matching target_skills (default: advise/debate/surprise)
      - ALL voice prompts (voice fidelity + factuality baseline)
      - ALL adversarial prompts (constraint adherence)

    If apply_filter=False, returns the full 20 prompts (full parity mode).
    """
    if not apply_filter:
        return list(prompts)
    kept = []
    for p in prompts:
        category = p.get("category", "general")
        if category == "general":
            if p.get("skill") in target_skills:
                kept.append(p)
        elif category in ("voice", "adversarial"):
            kept.append(p)
    return kept


# ---------------------------------------------------------------------------
# Role-play runner (no brain context, no cache)
# ---------------------------------------------------------------------------


def call_roleplay_runner(client, brain_cfg: dict, user_prompt: str,
                         cost_tracker: CostTracker, label: str) -> dict:
    """Run role-play baseline on one prompt. No brain context, no cache."""
    system_prompt = ROLEPLAY_RUNNER_SYSTEM.format(
        brain_name=brain_cfg.get("brain_name", "the thinker"),
        brain_first_name=brain_cfg.get("brain_first_name", "they"),
    )
    resp = call_claude(
        client=client,
        model=RUNNER_MODEL,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        max_tokens=RUNNER_MAX_TOKENS,
        cost_tracker=cost_tracker,
        label=label,
    )
    return {
        "content": resp["content"],
        "cost": resp.get("cost", 0.0),
    }


# ---------------------------------------------------------------------------
# Per-brain orchestration
# ---------------------------------------------------------------------------


@dataclass
class PromptEvalRecord:
    prompt_id: str
    category: str
    skill: Optional[str]
    prompt: str
    response: str
    runner_cost: float
    judge: JudgeResult
    latency_sec: float

    def to_dict(self):
        return {
            "prompt_id": self.prompt_id,
            "category": self.category,
            "skill": self.skill,
            "prompt": self.prompt,
            "response": self.response,
            "runner_cost": round(self.runner_cost, 5),
            "latency_sec": round(self.latency_sec, 2),
            "judge": self.judge.to_dict(),
        }


@dataclass
class RoleplayEvalResult:
    slug: str
    name: str
    mode: str = "roleplay"
    prompts: list = field(default_factory=list)
    aggregate: dict = field(default_factory=dict)
    total_cost: float = 0.0
    total_latency_sec: float = 0.0
    timestamp: str = ""
    target_skills: list = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self):
        return {
            "slug": self.slug,
            "name": self.name,
            "mode": self.mode,
            "target_skills": self.target_skills,
            "aggregate": self.aggregate,
            "total_cost": round(self.total_cost, 4),
            "total_latency_sec": round(self.total_latency_sec, 1),
            "timestamp": self.timestamp,
            "runner_model": RUNNER_MODEL,
            "judge_model": JUDGE_MODEL,
            "error": self.error,
            "prompts": [p.to_dict() for p in self.prompts],
        }


def eval_roleplay_brain(slug: str, client, cost_tracker: CostTracker,
                        apply_filter: bool = True) -> RoleplayEvalResult:
    """Run role-play eval for one brain. Serial prompts (no cache to preserve)."""
    index = eval_brains.load_index()
    entry = next((b for b in index.get("brains", []) if b["slug"] == slug), {})
    name = entry.get("name", slug)
    result = RoleplayEvalResult(
        slug=slug, name=name,
        timestamp=datetime.now(timezone.utc).isoformat(),
        target_skills=sorted(TARGET_SKILLS) if apply_filter else [],
    )

    try:
        brain_cfg = eval_brains.load_brain_json(slug)
    except Exception as e:
        result.error = f"Failed to load brain.json: {e}"
        return result

    prompts_path = eval_brains.prompts_file(slug)
    if not prompts_path.exists():
        result.error = f"No prompts.json — run: scripts/eval-brains.py --seed-prompts --brain {slug}"
        return result
    with open(prompts_path) as f:
        prompt_set = json.load(f)

    prompts = filter_prompts(prompt_set.get("prompts", []), apply_filter=apply_filter)
    if not prompts:
        result.error = "No prompts left after filter"
        return result

    step(f"[{slug}] role-play eval — {len(prompts)} prompts "
         f"({'filtered to ' + '/'.join(sorted(TARGET_SKILLS)) + ' + voice + adversarial' if apply_filter else 'full 20-prompt bundle'})")

    t0 = time.time()
    for i, p in enumerate(prompts, 1):
        label = f"{slug}:roleplay:{p['id']}"
        step(f"  [{slug}] {i}/{len(prompts)} — {p['category']} — {p['id']}")
        prompt_t0 = time.time()
        try:
            runner_resp = call_roleplay_runner(
                client, brain_cfg, p["prompt"],
                cost_tracker, f"runner:{label}",
            )
            response_text = runner_resp["content"]
            runner_cost = runner_resp["cost"]
        except Exception as e:
            error(f"[{label}] runner failed: {e}")
            response_text = ""
            runner_cost = 0.0

        try:
            judge_result = eval_brains.call_judge(
                client, brain_cfg, p, response_text,
                cost_tracker, f"judge:{label}",
            )
        except Exception as e:
            error(f"[{label}] judge failed: {e}")
            judge_result = JudgeResult(
                voice_fidelity=DimensionScore(0, f"judge exception: {e}"),
                factuality=DimensionScore(0, ""),
                relevance=DimensionScore(0, ""),
                constraint_adherence=DimensionScore(0, ""),
                adopted_forbidden_position=False,
                verdict="fail",
                judge_model=JUDGE_MODEL,
            )

        result.prompts.append(PromptEvalRecord(
            prompt_id=p["id"],
            category=p["category"],
            skill=p.get("skill"),
            prompt=p["prompt"],
            response=response_text,
            runner_cost=runner_cost,
            judge=judge_result,
            latency_sec=time.time() - prompt_t0,
        ))

    result.total_latency_sec = time.time() - t0
    result.total_cost = sum(p.runner_cost for p in result.prompts)
    result.aggregate = aggregate_behavioral_score([p.judge for p in result.prompts])
    return result


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def write_roleplay_results(result: RoleplayEvalResult) -> tuple[Path, Path]:
    """Write results-roleplay-{date}.json + summary-roleplay.md."""
    out_dir = eval_brains.evals_dir(result.slug)
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results_path = out_dir / f"results-roleplay-{date_str}.json"
    with open(results_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    summary_path = out_dir / "summary-roleplay.md"
    with open(summary_path, "w") as f:
        f.write(render_summary_md(result))
    return results_path, summary_path


def render_summary_md(result: RoleplayEvalResult) -> str:
    agg = result.aggregate or {}
    lines = [
        f"# {result.name} — Role-Play Baseline Eval",
        "",
        f"- **Run:** {result.timestamp}",
        f"- **Mode:** Role-play (no brain context)",
        f"- **Target skills:** {', '.join(result.target_skills) if result.target_skills else '(all)'}",
        f"- **Runner:** {RUNNER_MODEL} | **Judge:** {JUDGE_MODEL}",
        f"- **Prompts evaluated:** {agg.get('prompts_evaluated', 0)}",
        f"- **Behavioral score:** **{agg.get('behavioral_score', 0)}/100**",
        f"- **Pass rate:** {agg.get('pass_rate', 0.0):.0%}",
        f"- **Adversarial violations:** {agg.get('adversarial_violations', 0)}",
        f"- **Total cost:** ${result.total_cost:.3f} (runner only) + judge calls",
        f"- **Runtime:** {result.total_latency_sec:.1f}s",
        "",
        "## Dimensions (1-5 mean)",
        "",
    ]
    dims = agg.get("dimensions", {})
    for k, meta in RUBRIC.items():
        v = dims.get(k, 0.0)
        lines.append(f"- **{meta['label']}** (weight {int(meta['weight']*100)}%): {v:.2f} / 5")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Comparison: roleplay vs brain eval
# ---------------------------------------------------------------------------


def find_latest_brain_results(slug: str) -> Optional[Path]:
    """Find the most recent results-YYYY-MM-DD.json (brain, not roleplay) for a brain."""
    ed = eval_brains.evals_dir(slug)
    if not ed.exists():
        return None
    candidates = sorted(
        p for p in ed.glob("results-*.json")
        if "roleplay" not in p.name
    )
    return candidates[-1] if candidates else None


def breakdown_by_skill(records: list[dict]) -> dict[str, dict]:
    """Average score / pass-rate broken down by skill (for general prompts) or category."""
    buckets: dict[str, list] = {}
    for r in records:
        skill = r.get("skill")
        category = r.get("category", "general")
        key = skill if (category == "general" and skill) else category
        buckets.setdefault(key, []).append(r)

    out = {}
    for key, items in buckets.items():
        scores = [r["judge"].get("score_0_100", 0) for r in items]
        passes = sum(1 for r in items if r["judge"].get("verdict") == "pass")
        viols = sum(1 for r in items if r["judge"].get("adopted_forbidden_position"))
        dim_means = {}
        for dim in RUBRIC:
            vals = [r["judge"].get(dim, {}).get("score", 0) for r in items]
            dim_means[dim] = round(sum(vals) / len(vals), 2) if vals else 0.0
        out[key] = {
            "count": len(items),
            "mean_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
            "pass_rate": round(passes / len(items), 2) if items else 0.0,
            "violations": viols,
            "dimensions": dim_means,
        }
    return out


def render_comparison_md(brain_result: dict, roleplay_result: dict) -> str:
    """Produce a side-by-side diff report between brain and role-play results."""
    b_agg = brain_result.get("aggregate", {}) or {}
    r_agg = roleplay_result.get("aggregate", {}) or {}

    b_score = b_agg.get("behavioral_score", 0)
    r_score = r_agg.get("behavioral_score", 0)
    gap = b_score - r_score

    name = brain_result.get("name") or roleplay_result.get("name")
    slug = brain_result.get("slug") or roleplay_result.get("slug")

    # Prompt-level lookups by prompt_id so we can compare matched pairs
    b_prompts = {p["prompt_id"]: p for p in brain_result.get("prompts", [])}
    r_prompts = {p["prompt_id"]: p for p in roleplay_result.get("prompts", [])}
    shared_ids = [pid for pid in r_prompts if pid in b_prompts]

    lines = [
        f"# {name} — Brain vs. Role-Play",
        "",
        f"- **Slug:** `{slug}`",
        f"- **Brain eval run:** {brain_result.get('timestamp', '?')}",
        f"- **Role-play eval run:** {roleplay_result.get('timestamp', '?')}",
        f"- **Runner model:** {roleplay_result.get('runner_model', RUNNER_MODEL)}",
        f"- **Judge model:** {roleplay_result.get('judge_model', JUDGE_MODEL)}",
        "",
        "## Headline",
        "",
        f"| Metric | Brain | Role-play | Gap |",
        f"|---|---:|---:|---:|",
        f"| Behavioral score | **{b_score}/100** | **{r_score}/100** | **{gap:+d}** |",
        f"| Pass rate | {b_agg.get('pass_rate', 0):.0%} | {r_agg.get('pass_rate', 0):.0%} | {(b_agg.get('pass_rate', 0) - r_agg.get('pass_rate', 0)) * 100:+.0f} pp |",
        f"| Adversarial violations | {b_agg.get('adversarial_violations', 0)} | {r_agg.get('adversarial_violations', 0)} | {b_agg.get('adversarial_violations', 0) - r_agg.get('adversarial_violations', 0):+d} |",
        f"| Prompts evaluated | {b_agg.get('prompts_evaluated', 0)} | {r_agg.get('prompts_evaluated', 0)} | — |",
        "",
        "## Dimensions (1-5 mean)",
        "",
        "| Dimension | Brain | Role-play | Gap |",
        "|---|---:|---:|---:|",
    ]
    b_dims = b_agg.get("dimensions", {})
    r_dims = r_agg.get("dimensions", {})
    for k, meta in RUBRIC.items():
        bv = b_dims.get(k, 0.0)
        rv = r_dims.get(k, 0.0)
        lines.append(f"| {meta['label']} (w={int(meta['weight']*100)}%) | {bv:.2f} | {rv:.2f} | {bv - rv:+.2f} |")

    # Breakdown by skill / category (only over shared prompts so it's apples-to-apples)
    lines.extend(["", "## Breakdown by skill / category (matched prompts only)", ""])
    shared_b = [b_prompts[pid] for pid in shared_ids]
    shared_r = [r_prompts[pid] for pid in shared_ids]
    b_break = breakdown_by_skill(shared_b)
    r_break = breakdown_by_skill(shared_r)

    lines.append("| Skill / Category | N | Brain score | Role-play score | Gap | Brain pass | RP pass | Violations (B→RP) |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
    all_keys = sorted(set(b_break.keys()) | set(r_break.keys()))
    for key in all_keys:
        bb = b_break.get(key, {})
        rb = r_break.get(key, {})
        n = bb.get("count") or rb.get("count") or 0
        bs = bb.get("mean_score", 0.0)
        rs = rb.get("mean_score", 0.0)
        bp = bb.get("pass_rate", 0.0)
        rp = rb.get("pass_rate", 0.0)
        bv = bb.get("violations", 0)
        rv = rb.get("violations", 0)
        lines.append(
            f"| {key} | {n} | {bs:.1f} | {rs:.1f} | {bs - rs:+.1f} | {bp:.0%} | {rp:.0%} | {bv} → {rv} |"
        )

    # Prompts where role-play beat or tied the brain (diagnostic)
    reversals = []
    for pid in shared_ids:
        bp = b_prompts[pid]
        rp = r_prompts[pid]
        bs = bp["judge"].get("score_0_100", 0)
        rs = rp["judge"].get("score_0_100", 0)
        if rs >= bs:
            reversals.append((pid, bs, rs, bp, rp))
    reversals.sort(key=lambda t: t[1] - t[2])  # biggest role-play lead first

    if reversals:
        lines.extend(["", "## Reversals — where role-play tied or beat the brain", "",
                      f"{len(reversals)} of {len(shared_ids)} shared prompts ({len(reversals)/max(1, len(shared_ids)):.0%}). "
                      "These are diagnostic: they either reveal weak brain coverage or areas where training-data priors are already strong.",
                      ""])
        for pid, bs, rs, bp_rec, rp_rec in reversals[:5]:
            category = bp_rec.get("category")
            skill = bp_rec.get("skill") or "—"
            lines.extend([
                f"### {pid} ({category}/{skill}) — brain {bs} vs role-play {rs}",
                f"**Prompt:** {bp_rec['prompt']}",
                "",
                f"**Brain response:** {bp_rec['response'][:350]}{'...' if len(bp_rec['response']) > 350 else ''}",
                "",
                f"**Role-play response:** {rp_rec['response'][:350]}{'...' if len(rp_rec['response']) > 350 else ''}",
                "",
            ])

    # Biggest brain wins
    wins = []
    for pid in shared_ids:
        bs = b_prompts[pid]["judge"].get("score_0_100", 0)
        rs = r_prompts[pid]["judge"].get("score_0_100", 0)
        if bs > rs:
            wins.append((pid, bs, rs, b_prompts[pid], r_prompts[pid]))
    wins.sort(key=lambda t: t[1] - t[2], reverse=True)

    if wins:
        lines.extend(["", "## Biggest brain wins", ""])
        for pid, bs, rs, bp_rec, rp_rec in wins[:3]:
            category = bp_rec.get("category")
            skill = bp_rec.get("skill") or "—"
            lines.extend([
                f"### {pid} ({category}/{skill}) — brain {bs} vs role-play {rs} ({bs - rs:+d})",
                f"**Prompt:** {bp_rec['prompt']}",
                "",
                f"**Role-play response:** {rp_rec['response'][:350]}{'...' if len(rp_rec['response']) > 350 else ''}",
                "",
                f"**Judge on role-play:** voice={rp_rec['judge']['voice_fidelity']['score']} / "
                f"factuality={rp_rec['judge']['factuality']['score']} / "
                f"relevance={rp_rec['judge']['relevance']['score']} / "
                f"constraints={rp_rec['judge']['constraint_adherence']['score']}",
                "",
            ])

    return "\n".join(lines) + "\n"


def compare_one(slug: str, roleplay_result: RoleplayEvalResult) -> Optional[Path]:
    """Find latest brain results for slug, write side-by-side comparison.md."""
    brain_results_path = find_latest_brain_results(slug)
    if not brain_results_path:
        warn(f"{slug}: no brain eval results on disk — run `scripts/eval-brains.py --brain {slug}` first")
        return None
    with open(brain_results_path) as f:
        brain_result = json.load(f)
    # Write per-brain comparison file
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cmp_path = eval_brains.evals_dir(slug) / f"comparison-{date_str}.md"
    with open(cmp_path, "w") as f:
        f.write(render_comparison_md(brain_result, roleplay_result.to_dict()))
    return cmp_path


def write_cross_brain_comparison(results: list[RoleplayEvalResult]) -> Path:
    """Write a cross-brain brains-vs-roleplay summary to brains/eval-runs/."""
    runs_dir = BRAINS_DIR / "eval-runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = runs_dir / f"brains-vs-roleplay-{date_str}.md"

    rows = []
    for r in results:
        if r.error:
            rows.append((r.name, None, None, None, f"ERROR: {r.error}"))
            continue
        brain_path = find_latest_brain_results(r.slug)
        if not brain_path:
            rows.append((r.name, None, r.aggregate.get("behavioral_score", 0), None,
                         "brain eval missing"))
            continue
        with open(brain_path) as f:
            b = json.load(f)
        b_score = b.get("aggregate", {}).get("behavioral_score", 0)
        r_score = r.aggregate.get("behavioral_score", 0)
        gap = b_score - r_score
        b_viol = b.get("aggregate", {}).get("adversarial_violations", 0)
        r_viol = r.aggregate.get("adversarial_violations", 0)
        rows.append((r.name, b_score, r_score, gap, f"viol {b_viol}→{r_viol}"))

    lines = [
        "# BrainsFor — Brains vs. Role-Play (cross-brain)",
        "",
        f"- **Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"- **Runner:** {RUNNER_MODEL} | **Judge:** {JUDGE_MODEL}",
        f"- **Brains evaluated:** {len(results)}",
        "",
        "## Scoreboard",
        "",
        "| Brain | Brain score | Role-play score | Gap | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for name, bs, rs, gap, notes in rows:
        bs_s = f"{bs}/100" if bs is not None else "—"
        rs_s = f"{rs}/100" if rs is not None else "—"
        gap_s = f"{gap:+d}" if gap is not None else "—"
        lines.append(f"| {name} | {bs_s} | {rs_s} | {gap_s} | {notes} |")

    # Verdict heuristic
    clean_gaps = [g for *_, g, _ in [(n, b, r, g, x) for n, b, r, g, x in rows] if isinstance(g, int)]
    if clean_gaps:
        mean_gap = sum(clean_gaps) / len(clean_gaps)
        lines.extend(["", "## Verdict", ""])
        if mean_gap >= 15:
            lines.append(f"- **Clean signal.** Mean gap {mean_gap:+.1f} points — brains beat role-play at a level users can feel. Scale to full 15 brains.")
        elif mean_gap >= 5:
            lines.append(f"- **Muddy.** Mean gap {mean_gap:+.1f} points. Brains win but not decisively. Look at per-skill breakdown and adversarial-violation delta before scaling.")
        else:
            lines.append(f"- **Weak.** Mean gap {mean_gap:+.1f} points. Diagnose before scaling — either packs need deeper synthesis, or the skill mix in this smoke doesn't showcase the brain advantage.")

    lines.append("")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


# ---------------------------------------------------------------------------
# Dry-run estimator
# ---------------------------------------------------------------------------


def dry_run_estimate(slugs: list[str], apply_filter: bool):
    prompts_per_brain = 15 if apply_filter else 20  # filter ≈ 3 general + 8 voice + 4 adversarial
    runner_input_per = 500    # short system prompt, no brain context
    runner_output_per = 400
    judge_input_per = 3_500
    judge_output_per = 400

    rate_sonnet_in = COST_INPUT[RUNNER_MODEL]
    rate_sonnet_out = COST_OUTPUT[RUNNER_MODEL]
    rate_haiku_in = COST_INPUT[JUDGE_MODEL]
    rate_haiku_out = COST_OUTPUT[JUDGE_MODEL]

    total = 0.0
    print()
    print(f"DRY RUN — role-play eval on {len(slugs)} brain(s), {prompts_per_brain} prompts each:")
    print()
    for slug in slugs:
        per_brain = (
            (runner_input_per * prompts_per_brain / 1000) * rate_sonnet_in
            + (runner_output_per * prompts_per_brain / 1000) * rate_sonnet_out
            + (judge_input_per * prompts_per_brain / 1000) * rate_haiku_in
            + (judge_output_per * prompts_per_brain / 1000) * rate_haiku_out
        )
        total += per_brain
        print(f"  {slug:<22}  ${per_brain:.3f}")
    print()
    print(f"Role-play side estimated: ${total:.2f} total")
    print(f"(Compare vs brain eval which is ~${0.92 * len(slugs):.2f} for same brains; cache helps brain side.)")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Brain-vs-role-play A/B comparison harness for BrainsFor"
    )
    parser.add_argument("--brain", help="Slug to eval (e.g. charlie-munger)")
    parser.add_argument("--smoke-triad", action="store_true",
                        help=f"Run the 3-brain smoke test: {', '.join(SMOKE_TRIAD)}")
    parser.add_argument("--all", action="store_true",
                        help="Run role-play eval on every eligible brain")
    parser.add_argument("--no-filter", action="store_true",
                        help="Disable skill filter — run all 20 prompts per brain")
    parser.add_argument("--compare", action="store_true",
                        help="After role-play eval, write brain-vs-role-play comparison.md")
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS,
                        help=f"Brains to process concurrently (default: {DEFAULT_MAX_WORKERS})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Estimate cost without API calls")
    args = parser.parse_args()

    if not (args.brain or args.smoke_triad or args.all):
        parser.error("Provide --brain SLUG, --smoke-triad, or --all")

    eval_brains.load_env()

    index = eval_brains.load_index()
    all_eligible = eval_brains.list_eligible_brains(index)
    known_slugs = {b["slug"] for b in all_eligible}

    if args.smoke_triad:
        missing = [s for s in SMOKE_TRIAD if s not in known_slugs]
        if missing:
            error(f"Smoke triad missing from eligible brains: {missing}")
            sys.exit(2)
        target_slugs = list(SMOKE_TRIAD)
    elif args.brain:
        if args.brain not in known_slugs:
            error(f"Unknown or ineligible brain: {args.brain}")
            print(f"Eligible: {', '.join(sorted(known_slugs))}", file=sys.stderr)
            sys.exit(2)
        target_slugs = [args.brain]
    else:
        target_slugs = [b["slug"] for b in all_eligible]

    apply_filter = not args.no_filter

    if args.dry_run:
        dry_run_estimate(target_slugs, apply_filter)
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        error("ANTHROPIC_API_KEY not set (checked env + ~/rob-ai/.env)")
        sys.exit(2)

    client = eval_brains.get_client()
    cost_tracker = CostTracker()

    phase_header(1, f"Running role-play evals on {len(target_slugs)} brain(s)")
    results: list[RoleplayEvalResult] = []

    if len(target_slugs) == 1 or args.max_workers <= 1:
        for slug in target_slugs:
            r = eval_roleplay_brain(slug, client, cost_tracker, apply_filter=apply_filter)
            results.append(r)
            if not r.error:
                results_path, _ = write_roleplay_results(r)
                success(f"{slug}: wrote {results_path.relative_to(ROOT_DIR)}")
    else:
        with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
            futures = {
                pool.submit(eval_roleplay_brain, slug, client, cost_tracker, apply_filter): slug
                for slug in target_slugs
            }
            for fut in as_completed(futures):
                slug = futures[fut]
                try:
                    r = fut.result()
                except Exception as e:
                    error(f"{slug}: role-play eval failed: {e}")
                    r = RoleplayEvalResult(slug=slug, name=slug, error=str(e),
                                           timestamp=datetime.now(timezone.utc).isoformat())
                results.append(r)
                if not r.error:
                    results_path, _ = write_roleplay_results(r)
                    success(f"{slug}: wrote {results_path.relative_to(ROOT_DIR)}")

    results.sort(key=lambda r: r.name)

    # Per-brain scorecard
    print()
    print("=" * 75)
    print("  ROLE-PLAY BASELINE — SCORECARD")
    print("=" * 75)
    print()
    print(f"  {'Brain':<22} {'Score':>8}  {'Pass':>5}  {'Viol':>5}  {'Prompts':>8}  {'Cost':>7}")
    print(f"  {'-'*22:<22} {'-'*8:>8}  {'-'*5:>5}  {'-'*5:>5}  {'-'*8:>8}  {'-'*7:>7}")
    for r in results:
        agg = r.aggregate or {}
        if r.error:
            print(f"  {r.name:<22} {'ERR':>8}  — ({r.error})")
            continue
        print(f"  {r.name:<22} {agg.get('behavioral_score', 0):>6}/100  "
              f"{agg.get('pass_rate', 0):>4.0%}  "
              f"{agg.get('adversarial_violations', 0):>5}  "
              f"{agg.get('prompts_evaluated', 0):>8}  "
              f"${r.total_cost:>5.2f}")
    print()

    if args.compare:
        phase_header(2, "Writing brain-vs-role-play comparisons")
        for r in results:
            if r.error:
                continue
            cmp_path = compare_one(r.slug, r)
            if cmp_path:
                success(f"{r.slug}: wrote {cmp_path.relative_to(ROOT_DIR)}")
        cross_path = write_cross_brain_comparison(results)
        success(f"Cross-brain summary: {cross_path.relative_to(ROOT_DIR)}")

    print()
    print(f"  {cost_tracker.summary()}")
    print()

    any_errors = any(r.error for r in results)
    sys.exit(1 if any_errors else 0)


if __name__ == "__main__":
    main()
