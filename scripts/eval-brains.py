#!/usr/bin/env python3
"""
eval-brains.py — Behavioral eval harness for BrainsFor brain packs.

Runs 20 prompts through each brain pack, scores each response with a Haiku
judge on 4 dimensions (voice / factuality / relevance / constraint adherence),
and produces a 0-100 behavioral score per brain plus a human-readable summary.

Usage:
    # Seed prompts.json for every brain that doesn't have one yet
    python3 scripts/eval-brains.py --seed-prompts

    # Seed a specific brain (force overwrite)
    python3 scripts/eval-brains.py --seed-prompts --brain dario-amodei --force

    # Smoke test: 2 prompts on one brain end-to-end (plumbing check)
    python3 scripts/eval-brains.py --brain dario-amodei --smoke

    # Run behavioral eval on one brain
    python3 scripts/eval-brains.py --brain dario-amodei

    # Run behavioral eval on all brains
    python3 scripts/eval-brains.py --all

    # Dry-run (no API calls, prints planned work + cost estimate)
    python3 scripts/eval-brains.py --all --dry-run

    # JSON output for machine consumption
    python3 scripts/eval-brains.py --all --json

Design notes:
    - Runner model: claude-sonnet-4-6 (matches production skill quality).
    - Judge model: claude-haiku-4-5-20251001 with optional sonnet escalation
      when any dimension scores <= 2 (rules out judge noise).
    - Prompt caching (cache_control: ephemeral) is applied to the brain-context
      system prompt so the ~75K-token context is only charged full-rate once
      per brain per 5-minute window.
    - Prompts per brain: 8 general (from brain.json.skill_examples) + 8 voice
      + 4 adversarial = 20. The voice + adversarial sets are LLM-generated
      from each brain's synthesis (would_not_say, does_not_believe, etc.).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent

# Share constants + Claude API helpers with the auto-build pipeline so we
# don't drift on model strings or cost tables.
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
    COLORS,
)
from eval_rubric import (  # noqa: E402
    RUBRIC,
    JUDGE_ESCALATION_THRESHOLD,
    BRAIN_RUNNER_SYSTEM_TEMPLATE,
    JUDGE_SYSTEM_PROMPT,
    JUDGE_USER_TEMPLATE,
    PROMPT_SEED_SYSTEM_PROMPT,
    PROMPT_SEED_USER_TEMPLATE,
    DimensionScore,
    JudgeResult,
    parse_judge_response,
    aggregate_behavioral_score,
    synthesis_to_numbered_list,
)

BRAINS_DIR = ROOT_DIR / "brains"
INDEX_FILE = BRAINS_DIR / "index.json"

# Model overrides live here so they're easy to tune without touching the
# shared auto_build_config defaults.
RUNNER_MODEL = DEFAULT_MODEL          # claude-sonnet-4-6
JUDGE_MODEL = FAST_MODEL              # claude-haiku-4-5-20251001
JUDGE_ESCALATION_MODEL = DEFAULT_MODEL  # claude-sonnet-4-6

DEFAULT_MAX_WORKERS = 3  # brains processed concurrently
RUNNER_MAX_TOKENS = 600
JUDGE_MAX_TOKENS = 900
SMOKE_PROMPT_LIMIT = 2

# ---------------------------------------------------------------------------
# Env + client bootstrap
# ---------------------------------------------------------------------------


def load_env():
    """Load .env into os.environ, overwriting unset OR empty values."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    env_path = Path.home() / "rob-ai" / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and not os.environ.get(k):
            os.environ[k] = v


def get_client():
    """Lazy-import anthropic so --dry-run works without the SDK."""
    import anthropic  # type: ignore
    return anthropic.Anthropic()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_index() -> dict:
    with open(INDEX_FILE) as f:
        return json.load(f)


def list_eligible_brains(index: dict) -> list[dict]:
    """Brains that have real content (skip `scaffolded` / `planned`)."""
    return [
        b for b in index.get("brains", [])
        if b.get("status") in ("live", "hidden") and int(b.get("atom_count", 0)) > 0
    ]


def brain_dir(slug: str) -> Path:
    return BRAINS_DIR / slug


def load_brain_json(slug: str) -> dict:
    with open(brain_dir(slug) / "brain.json") as f:
        return json.load(f)


def load_brain_context(slug: str) -> str:
    return (brain_dir(slug) / "pack" / "brain-context.md").read_text()


def evals_dir(slug: str) -> Path:
    return brain_dir(slug) / "evals"


def prompts_file(slug: str) -> Path:
    return evals_dir(slug) / "prompts.json"


# ---------------------------------------------------------------------------
# Prompt seeding: generate prompts.json from brain.json synthesis
# ---------------------------------------------------------------------------


def build_general_prompts(brain_cfg: dict) -> list[dict]:
    """8 prompts, one per skill, pulled from brain.json.skill_examples."""
    examples = brain_cfg.get("skill_examples", {}) or {}
    # Ordered the same way as the spec
    skills = ["advise", "teach", "debate", "connect", "evolve", "surprise", "coach", "predict"]
    prompts = []
    for i, skill in enumerate(skills, 1):
        text = examples.get(skill, "").strip()
        # `surprise` often has placeholder text like "No input needed — just run it."
        # Substitute a generic surprise trigger so the brain has something to answer.
        if skill == "surprise" and (not text or "no input" in text.lower()):
            text = f"Surprise me with a high-confidence idea I probably haven't seen."
        if not text:
            text = f"Use your {skill} skill — give me something useful."
        prompts.append({
            "id": f"general-{skill}-{i:02d}",
            "category": "general",
            "skill": skill,
            "prompt": text,
            "expected_themes": [],
        })
    return prompts


def seed_one_brain(slug: str, brain_cfg: dict, client, cost_tracker: CostTracker,
                   force: bool = False) -> Optional[Path]:
    """Generate or refresh prompts.json for a single brain. Returns the path, or None if skipped."""
    dest = prompts_file(slug)
    if dest.exists() and not force:
        step(f"{slug}: prompts.json already exists (use --force to regenerate) — skipping")
        return None

    evals_dir(slug).mkdir(parents=True, exist_ok=True)

    synthesis = brain_cfg.get("synthesis", {}) or {}
    required = ["first_principles", "contrarian_positions", "does_not_believe", "would_not_say"]
    missing = [k for k in required if not synthesis.get(k)]
    if missing:
        warn(f"{slug}: synthesis is missing {missing} — prompts will be generated from what's available")

    brain_name = brain_cfg.get("brain_name", slug)
    user_msg = PROMPT_SEED_USER_TEMPLATE.format(
        brain_name=brain_name,
        first_principles=synthesis_to_numbered_list(synthesis.get("first_principles", [])),
        contrarian_positions=synthesis_to_numbered_list(synthesis.get("contrarian_positions", [])),
        does_not_believe=synthesis_to_numbered_list(synthesis.get("does_not_believe", [])),
        would_not_say=synthesis_to_numbered_list(synthesis.get("would_not_say", [])),
    )
    system_prompt = PROMPT_SEED_SYSTEM_PROMPT.format(brain_name=brain_name)

    step(f"{slug}: generating voice + adversarial prompts via {RUNNER_MODEL}")
    resp = call_claude(
        client=client,
        model=RUNNER_MODEL,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
        max_tokens=2500,
        parse_json=True,
        cost_tracker=cost_tracker,
        label=f"seed-prompts:{slug}",
    )
    parsed = resp["parsed"]

    voice_prompts = [
        {
            "id": p.get("id", f"voice-{i:02d}"),
            "category": "voice",
            "prompt": p["prompt"],
            "expected_themes": p.get("expected_themes", []),
            "source_reference": p.get("source_reference", ""),
        }
        for i, p in enumerate(parsed.get("voice", []), 1)
    ]
    adversarial_prompts = [
        {
            "id": p.get("id", f"adversarial-{i:02d}"),
            "category": "adversarial",
            "prompt": p["prompt"],
            "forbidden_position": p.get("forbidden_position", ""),
            "source_reference": p.get("source_reference", ""),
            "pass_condition": p.get("pass_condition", "rebuts the framing; does not agree"),
        }
        for i, p in enumerate(parsed.get("adversarial", []), 1)
    ]

    general_prompts = build_general_prompts(brain_cfg)

    if len(voice_prompts) < 8 or len(adversarial_prompts) < 4:
        warn(f"{slug}: model returned {len(voice_prompts)} voice + {len(adversarial_prompts)} adversarial (expected 8 + 4)")

    output = {
        "brain_slug": slug,
        "brain_name": brain_name,
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prompt_counts": {
            "general": len(general_prompts),
            "voice": len(voice_prompts),
            "adversarial": len(adversarial_prompts),
            "total": len(general_prompts) + len(voice_prompts) + len(adversarial_prompts),
        },
        "prompts": general_prompts + voice_prompts + adversarial_prompts,
    }
    with open(dest, "w") as f:
        json.dump(output, f, indent=2)
    success(f"{slug}: wrote {dest.relative_to(ROOT_DIR)} with {output['prompt_counts']['total']} prompts")
    return dest


# ---------------------------------------------------------------------------
# Brain runner: plays the thinker
# ---------------------------------------------------------------------------


def build_runner_system(brain_cfg: dict, brain_context: str) -> list[dict]:
    """Return the cached system block for the brain runner."""
    filled = BRAIN_RUNNER_SYSTEM_TEMPLATE.format(
        brain_name=brain_cfg.get("brain_name", "the thinker"),
        brain_first_name=brain_cfg.get("brain_first_name", "they"),
        brain_context=brain_context,
    )
    # Use prompt caching: ~75K tokens of system prompt is read once per 5-min
    # window. Subsequent reads within TTL cost ~10% of input rate.
    return [{"type": "text", "text": filled, "cache_control": {"type": "ephemeral"}}]


def call_brain_runner(client, brain_cfg: dict, brain_context: str, user_prompt: str,
                      cost_tracker: CostTracker, label: str) -> dict:
    """Run the brain against a single prompt. Returns the API response dict."""
    system_block = build_runner_system(brain_cfg, brain_context)
    # We can't use the shared call_claude() helper because it doesn't accept a
    # list-of-blocks system. Inline the retry loop for this path.
    last_err = None
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=RUNNER_MODEL,
                max_tokens=RUNNER_MAX_TOKENS,
                system=system_block,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = response.content[0].text
            usage = response.usage
            input_tokens = (
                getattr(usage, "input_tokens", 0)
                + getattr(usage, "cache_read_input_tokens", 0)
                + getattr(usage, "cache_creation_input_tokens", 0)
            )
            output_tokens = getattr(usage, "output_tokens", 0)
            # Cost: cache reads are 10% of input, cache writes are 125% of input.
            # The call_claude tracker assumes flat rate, so we compute here.
            flat_in = getattr(usage, "input_tokens", 0)
            cache_read = getattr(usage, "cache_read_input_tokens", 0)
            cache_write = getattr(usage, "cache_creation_input_tokens", 0)
            rate_in = COST_INPUT.get(RUNNER_MODEL, 0.003)
            rate_out = COST_OUTPUT.get(RUNNER_MODEL, 0.015)
            cost = (
                (flat_in / 1000) * rate_in
                + (cache_read / 1000) * rate_in * 0.1
                + (cache_write / 1000) * rate_in * 1.25
                + (output_tokens / 1000) * rate_out
            )
            cost_tracker.total_input_tokens += input_tokens
            cost_tracker.total_output_tokens += output_tokens
            cost_tracker.total_cost += cost
            cost_tracker.calls.append({
                "model": RUNNER_MODEL,
                "input": input_tokens,
                "output": output_tokens,
                "cache_read": cache_read,
                "cache_write": cache_write,
                "cost": cost,
                "label": label,
            })
            return {
                "content": text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_tokens": cache_read,
                "cache_write_tokens": cache_write,
                "cost": cost,
            }
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            if "rate_limit" in err_str or "429" in err_str:
                wait = (2 ** attempt) * 5
                warn(f"[{label}] rate limited, waiting {wait}s")
                time.sleep(wait)
            elif "overloaded" in err_str or "529" in err_str:
                wait = (2 ** attempt) * 10
                warn(f"[{label}] overloaded, waiting {wait}s")
                time.sleep(wait)
            else:
                if attempt < 2:
                    warn(f"[{label}] error attempt {attempt + 1}: {e}")
                    time.sleep(2)
                else:
                    raise
    raise last_err


# ---------------------------------------------------------------------------
# Judge
# ---------------------------------------------------------------------------


def format_judge_user(brain_cfg: dict, prompt_record: dict, response: str) -> str:
    """Build the judge's user message from a prompt record + response."""
    synthesis = brain_cfg.get("synthesis", {}) or {}
    category = prompt_record.get("category", "general")
    if category == "adversarial":
        ctx = f"forbidden: {prompt_record.get('forbidden_position', '')} — pass_condition: {prompt_record.get('pass_condition', '')}"
    elif category == "voice":
        themes = prompt_record.get("expected_themes") or []
        ctx = f"expected themes: {', '.join(themes) if themes else '(none)'}"
    else:
        ctx = f"skill: {prompt_record.get('skill', 'n/a')}"

    return JUDGE_USER_TEMPLATE.format(
        brain_name=brain_cfg.get("brain_name", "the thinker"),
        first_principles=synthesis_to_numbered_list(synthesis.get("first_principles", [])),
        contrarian_positions=synthesis_to_numbered_list(synthesis.get("contrarian_positions", [])),
        does_not_believe=synthesis_to_numbered_list(synthesis.get("does_not_believe", [])),
        would_not_say=synthesis_to_numbered_list(synthesis.get("would_not_say", [])),
        category=category,
        prompt_context=ctx,
        prompt=prompt_record["prompt"],
        response=response,
        voice_fidelity_q=RUBRIC["voice_fidelity"]["question"].format(brain_name=brain_cfg.get("brain_name", "the thinker")),
        factuality_q=RUBRIC["factuality"]["question"].format(brain_name=brain_cfg.get("brain_name", "the thinker")),
        relevance_q=RUBRIC["relevance"]["question"],
        constraint_adherence_q=RUBRIC["constraint_adherence"]["question"].format(brain_name=brain_cfg.get("brain_name", "the thinker")),
    )


def call_judge(client, brain_cfg: dict, prompt_record: dict, response: str,
               cost_tracker: CostTracker, label: str,
               model: str = JUDGE_MODEL) -> JudgeResult:
    """Score one (prompt, response) pair. Escalates to Sonnet if a dimension <= threshold."""
    system_prompt = JUDGE_SYSTEM_PROMPT.format(brain_name=brain_cfg.get("brain_name", "the thinker"))
    user_msg = format_judge_user(brain_cfg, prompt_record, response)

    resp = call_claude(
        client=client,
        model=model,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
        max_tokens=JUDGE_MAX_TOKENS,
        cost_tracker=cost_tracker,
        label=label,
    )
    try:
        result = parse_judge_response(resp["content"])
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        warn(f"[{label}] judge returned unparseable JSON ({e}); returning neutral scores")
        result = JudgeResult(
            voice_fidelity=DimensionScore(3, "judge parse error"),
            factuality=DimensionScore(3, "judge parse error"),
            relevance=DimensionScore(3, "judge parse error"),
            constraint_adherence=DimensionScore(3, "judge parse error"),
            adopted_forbidden_position=False,
            verdict="fail",
        )
    result.judge_model = model

    # Escalate very-low scores to a stronger judge to rule out noise.
    if (
        model == JUDGE_MODEL
        and result.min_dimension_score <= JUDGE_ESCALATION_THRESHOLD
    ):
        escalated = call_judge(
            client, brain_cfg, prompt_record, response,
            cost_tracker, label + ":escalate", model=JUDGE_ESCALATION_MODEL,
        )
        escalated.escalated = True
        return escalated
    return result


# ---------------------------------------------------------------------------
# Per-brain orchestration
# ---------------------------------------------------------------------------


@dataclass
class PromptEvalRecord:
    prompt_id: str
    category: str
    prompt: str
    response: str
    runner_cost: float
    judge: JudgeResult
    latency_sec: float

    def to_dict(self):
        return {
            "prompt_id": self.prompt_id,
            "category": self.category,
            "prompt": self.prompt,
            "response": self.response,
            "runner_cost": round(self.runner_cost, 5),
            "latency_sec": round(self.latency_sec, 2),
            "judge": self.judge.to_dict(),
        }


@dataclass
class BrainEvalResult:
    slug: str
    name: str
    prompts: list = field(default_factory=list)
    aggregate: dict = field(default_factory=dict)
    total_cost: float = 0.0
    total_latency_sec: float = 0.0
    timestamp: str = ""
    error: Optional[str] = None

    def to_dict(self):
        return {
            "slug": self.slug,
            "name": self.name,
            "aggregate": self.aggregate,
            "total_cost": round(self.total_cost, 4),
            "total_latency_sec": round(self.total_latency_sec, 1),
            "timestamp": self.timestamp,
            "runner_model": RUNNER_MODEL,
            "judge_model": JUDGE_MODEL,
            "error": self.error,
            "prompts": [p.to_dict() for p in self.prompts],
        }


def eval_brain(slug: str, client, cost_tracker: CostTracker,
               smoke: bool = False, max_prompts: Optional[int] = None) -> BrainEvalResult:
    """Run all prompts for one brain. Serial within the brain for cache hits."""
    index = load_index()
    entry = next((b for b in index.get("brains", []) if b["slug"] == slug), {})
    name = entry.get("name", slug)
    result = BrainEvalResult(slug=slug, name=name, timestamp=datetime.now(timezone.utc).isoformat())

    brain_cfg = load_brain_json(slug)
    brain_context = load_brain_context(slug)

    prompts_path = prompts_file(slug)
    if not prompts_path.exists():
        result.error = f"No prompts.json — run: scripts/eval-brains.py --seed-prompts --brain {slug}"
        return result

    with open(prompts_path) as f:
        prompt_set = json.load(f)
    prompts = prompt_set.get("prompts", [])
    if smoke:
        prompts = prompts[:SMOKE_PROMPT_LIMIT]
    elif max_prompts:
        prompts = prompts[:max_prompts]

    if not prompts:
        result.error = "prompts.json has no prompts"
        return result

    t0 = time.time()
    for i, p in enumerate(prompts, 1):
        label = f"{slug}:{p['id']}"
        step(f"[{slug}] prompt {i}/{len(prompts)} — {p['category']} — {p['id']}")
        prompt_t0 = time.time()
        try:
            runner_resp = call_brain_runner(
                client, brain_cfg, brain_context, p["prompt"],
                cost_tracker, f"runner:{label}",
            )
            response_text = runner_resp["content"]
            runner_cost = runner_resp["cost"]
        except Exception as e:
            error(f"[{label}] runner failed: {e}")
            response_text = ""
            runner_cost = 0.0

        try:
            judge_result = call_judge(
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

        record = PromptEvalRecord(
            prompt_id=p["id"],
            category=p["category"],
            prompt=p["prompt"],
            response=response_text,
            runner_cost=runner_cost,
            judge=judge_result,
            latency_sec=time.time() - prompt_t0,
        )
        result.prompts.append(record)

    result.total_latency_sec = time.time() - t0
    result.total_cost = sum(p.runner_cost for p in result.prompts)
    # Judge cost is tracked in cost_tracker.calls; not split per-prompt here.
    result.aggregate = aggregate_behavioral_score([p.judge for p in result.prompts])
    return result


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def write_brain_results(result: BrainEvalResult) -> tuple[Path, Path]:
    """Write results-{date}.json + summary.md. Returns both paths."""
    out_dir = evals_dir(result.slug)
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results_path = out_dir / f"results-{date_str}.json"
    with open(results_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    summary_path = out_dir / "summary.md"
    with open(summary_path, "w") as f:
        f.write(render_summary_md(result))
    return results_path, summary_path


def render_summary_md(result: BrainEvalResult) -> str:
    """Human-readable single-brain scorecard."""
    agg = result.aggregate or {}
    lines = [
        f"# {result.name} — Behavioral Eval",
        "",
        f"- **Run:** {result.timestamp}",
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

    # Worst 3 prompts
    sorted_prompts = sorted(result.prompts, key=lambda p: p.judge.score_0_100)[:3]
    if sorted_prompts:
        lines.extend(["", "## Lowest-scoring prompts", ""])
        for p in sorted_prompts:
            lines.append(f"### {p.prompt_id} ({p.category}) — {p.judge.score_0_100}/100 — verdict: {p.judge.verdict}")
            lines.append(f"**Prompt:** {p.prompt}")
            lines.append("")
            lines.append(f"**Response:** {p.response[:500]}{'...' if len(p.response) > 500 else ''}")
            lines.append("")
            lines.append(f"- voice: {p.judge.voice_fidelity.score} — {p.judge.voice_fidelity.rationale}")
            lines.append(f"- factuality: {p.judge.factuality.score} — {p.judge.factuality.rationale}")
            lines.append(f"- relevance: {p.judge.relevance.score} — {p.judge.relevance.rationale}")
            lines.append(f"- constraints: {p.judge.constraint_adherence.score} — {p.judge.constraint_adherence.rationale}")
            if p.category == "adversarial" and p.judge.adopted_forbidden_position:
                lines.append(f"- **ADVERSARIAL VIOLATION** — response adopted forbidden position")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cross-brain report
# ---------------------------------------------------------------------------


def print_scorecard(results: list[BrainEvalResult]):
    """Print a short cross-brain scoreboard to stdout."""
    print()
    print("=" * 75)
    print("  BRAINSFOR — BEHAVIORAL EVAL SCORECARD")
    print("=" * 75)
    print()
    print(f"  {'Brain':<22} {'Score':>8}  {'Pass':>5}  {'Viol':>5}  {'Prompts':>8}  {'Cost':>7}")
    print(f"  {'-'*22:<22} {'-'*8:>8}  {'-'*5:>5}  {'-'*5:>5}  {'-'*8:>8}  {'-'*7:>7}")
    for r in results:
        agg = r.aggregate or {}
        if r.error:
            print(f"  {r.name:<22} {'ERR':>8}  {'-':>5}  {'-':>5}  {'-':>8}  {'-':>7}  ({r.error})")
            continue
        score = agg.get("behavioral_score", 0)
        pr = agg.get("pass_rate", 0.0)
        vi = agg.get("adversarial_violations", 0)
        np_ = agg.get("prompts_evaluated", 0)
        print(f"  {r.name:<22} {score:>6}/100  {pr:>4.0%}  {vi:>5}  {np_:>8}  ${r.total_cost:>5.2f}")
    print()
    if results:
        valid = [r for r in results if not r.error]
        if valid:
            mean = sum((r.aggregate or {}).get("behavioral_score", 0) for r in valid) / len(valid)
            worst = min(valid, key=lambda r: (r.aggregate or {}).get("behavioral_score", 0))
            worst_score = (worst.aggregate or {}).get("behavioral_score", 0)
            print(f"  Average behavioral score: {round(mean)}/100 across {len(valid)} brains")
            print(f"  Worst: {worst.name} ({worst_score}/100) — biggest opportunity")
            print()


def write_cross_brain_summary(results: list[BrainEvalResult]) -> Path:
    """Write a timestamped cross-brain run log to brains/eval-runs/."""
    runs_dir = BRAINS_DIR / "eval-runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    path = runs_dir / f"run-{ts}.json"
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runner_model": RUNNER_MODEL,
        "judge_model": JUDGE_MODEL,
        "brains": [r.to_dict() for r in results],
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path


# ---------------------------------------------------------------------------
# Dry-run estimation
# ---------------------------------------------------------------------------


def dry_run_estimate(slugs: list[str]):
    """Rough cost + time estimate without any API calls."""
    # rough per-brain numbers from context size (~75K tokens cached)
    runner_cache_write = 75_000
    runner_cache_read_per = 75_000
    runner_output_per = 400
    judge_input_per = 3_500
    judge_output_per = 400
    prompts_per = 20

    rate_sonnet_in = COST_INPUT[RUNNER_MODEL]
    rate_sonnet_out = COST_OUTPUT[RUNNER_MODEL]
    rate_haiku_in = COST_INPUT[JUDGE_MODEL]
    rate_haiku_out = COST_OUTPUT[JUDGE_MODEL]

    total = 0.0
    print()
    print("DRY RUN — estimated costs per brain (assuming cache hits after first prompt):")
    print()
    for slug in slugs:
        per_brain = (
            (runner_cache_write / 1000) * rate_sonnet_in * 1.25
            + (runner_cache_read_per / 1000) * rate_sonnet_in * 0.1 * (prompts_per - 1)
            + (runner_output_per * prompts_per / 1000) * rate_sonnet_out
            + (judge_input_per * prompts_per / 1000) * rate_haiku_in
            + (judge_output_per * prompts_per / 1000) * rate_haiku_out
        )
        total += per_brain
        print(f"  {slug:<22}  ${per_brain:.3f}  ({prompts_per} prompts)")
    print()
    print(f"Total estimated: ${total:.2f} across {len(slugs)} brains ({len(slugs) * prompts_per} prompts)")
    print("Estimated time: 2-5 min serial per brain. With max-workers=3: ~{} min.".format(
        max(3, len(slugs) // 3 * 2)
    ))
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Behavioral eval harness for BrainsFor brain packs")
    parser.add_argument("--brain", help="Slug to eval (e.g. dario-amodei)")
    parser.add_argument("--all", action="store_true", help="Eval every eligible brain")
    parser.add_argument("--seed-prompts", action="store_true", help="Generate prompts.json for target brain(s)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing prompts.json during seeding")
    parser.add_argument("--smoke", action="store_true", help="Run only 2 prompts for quick plumbing check")
    parser.add_argument("--max-prompts", type=int, help="Cap prompts per brain (debugging)")
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS,
                        help=f"Brains to process concurrently (default: {DEFAULT_MAX_WORKERS})")
    parser.add_argument("--dry-run", action="store_true", help="Estimate cost + time without API calls")
    parser.add_argument("--json", action="store_true", help="JSON output for --all")
    args = parser.parse_args()

    if not (args.brain or args.all or args.seed_prompts):
        parser.error("Provide --brain SLUG or --all (optionally with --seed-prompts / --smoke)")

    load_env()

    index = load_index()
    all_eligible = list_eligible_brains(index)
    known_slugs = {b["slug"] for b in all_eligible}

    if args.brain:
        if args.brain not in known_slugs:
            error(f"Unknown or ineligible brain: {args.brain}")
            print(f"Eligible: {', '.join(sorted(known_slugs))}", file=sys.stderr)
            sys.exit(2)
        target_slugs = [args.brain]
    else:
        target_slugs = [b["slug"] for b in all_eligible]

    if args.dry_run:
        dry_run_estimate(target_slugs)
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        error("ANTHROPIC_API_KEY not set (checked env + ~/rob-ai/.env)")
        sys.exit(2)

    client = get_client()
    cost_tracker = CostTracker()

    # --- Seed mode ---
    if args.seed_prompts:
        phase_header(1, "Seeding eval prompts")
        for slug in target_slugs:
            try:
                brain_cfg = load_brain_json(slug)
                seed_one_brain(slug, brain_cfg, client, cost_tracker, force=args.force)
            except Exception as e:
                error(f"{slug}: seed failed: {e}")
        print()
        print(cost_tracker.summary())
        return

    # --- Eval mode ---
    phase_header(2, "Running behavioral evals")
    results: list[BrainEvalResult] = []

    if len(target_slugs) == 1 or args.max_workers <= 1:
        for slug in target_slugs:
            r = eval_brain(slug, client, cost_tracker,
                           smoke=args.smoke, max_prompts=args.max_prompts)
            results.append(r)
            if not r.error:
                results_path, summary_path = write_brain_results(r)
                success(f"{slug}: wrote {results_path.relative_to(ROOT_DIR)}")
    else:
        # ThreadPoolExecutor: brains run concurrently; prompts within a brain
        # are serial (so prompt caching works). Each thread has its own
        # local-ish view; CostTracker uses GIL-protected list/int appends so
        # it's safe enough for this use case.
        with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
            futures = {
                pool.submit(eval_brain, slug, client, cost_tracker,
                            args.smoke, args.max_prompts): slug
                for slug in target_slugs
            }
            for fut in as_completed(futures):
                slug = futures[fut]
                try:
                    r = fut.result()
                except Exception as e:
                    error(f"{slug}: eval failed: {e}")
                    r = BrainEvalResult(slug=slug, name=slug, error=str(e),
                                        timestamp=datetime.now(timezone.utc).isoformat())
                results.append(r)
                if not r.error:
                    results_path, _ = write_brain_results(r)
                    success(f"{slug}: wrote {results_path.relative_to(ROOT_DIR)}")

    # Sort by name for stable output
    results.sort(key=lambda r: r.name)
    run_path = write_cross_brain_summary(results)

    print_scorecard(results)
    print(f"  Cross-brain run log: {run_path.relative_to(ROOT_DIR)}")
    print(f"  {cost_tracker.summary()}")
    print()

    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))

    # Exit code: 1 if any brain had errors or scored < 50 (the floor from the
    # spec's success criteria — "proving the harness catches real issues")
    any_errors = any(r.error for r in results)
    any_failures = any(
        not r.error and (r.aggregate or {}).get("behavioral_score", 0) < 50
        for r in results
    )
    sys.exit(1 if (any_errors or any_failures) else 0)


if __name__ == "__main__":
    main()
