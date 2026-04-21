#!/usr/bin/env python3
"""
eval_rubric.py — Rubric definitions, judge prompts, and scoring utilities for
the BrainsFor behavioral eval harness.

Used by scripts/eval-brains.py. Kept separate so the rubric can be tuned
without touching the eval runner.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# 4-dimension rubric (matches projects/brain-evals-phase1.md)
# ---------------------------------------------------------------------------

RUBRIC = {
    "voice_fidelity": {
        "weight": 0.30,
        "label": "Voice Fidelity",
        "question": "Does this response sound like {brain_name} — vocabulary, cadence, framing, characteristic turns of phrase?",
    },
    "factuality": {
        "weight": 0.25,
        "label": "Factuality",
        "question": "Does this response align with {brain_name}'s actual public positions as described in the synthesis? Any fabricated claims or positions the thinker would reject?",
    },
    "relevance": {
        "weight": 0.20,
        "label": "Relevance / Utility",
        "question": "Does the response genuinely answer the user's question, or does it dodge / ramble / restate the prompt?",
    },
    "constraint_adherence": {
        "weight": 0.25,
        "label": "Constraint Adherence",
        "question": "Does the response violate any item in {brain_name}'s `would_not_say` or `does_not_believe`? (5 = fully respects constraints, 1 = flagrantly violates them.)",
    },
}

# Judge model escalation: any dimension at or below this triggers a re-judge
# with a stronger model to rule out judge noise.
JUDGE_ESCALATION_THRESHOLD = 2


# ---------------------------------------------------------------------------
# Brain-runner system prompt
# ---------------------------------------------------------------------------
#
# The brain runner is the model playing the thinker. We give it the full
# brain-context.md and tell it to answer the prompt in character. This is
# deliberately close to what the production /api/skill endpoint does so
# that behavioral scores reflect what users actually get.

BRAIN_RUNNER_SYSTEM_TEMPLATE = """You are answering questions as {brain_name}, drawing on the brain pack context below. Stay in character — vocabulary, framing, and positions should reflect {brain_first_name}'s actual thinking as captured in the atoms and synthesis.

Important rules:
- Do NOT caveat that you are an AI or mention "Claude" or "Anthropic."
- Do NOT say "as {brain_name} would say" — just say it.
- Answer the user's question directly. Draw on specific frameworks, vocabulary, and positions from the brain pack.
- If the question presses on something {brain_first_name} would reject or find uninteresting, push back as {brain_first_name} would — don't just comply.
- Length: 120-250 words unless the question genuinely demands more.

BRAIN PACK CONTEXT:
------------------------------------------------------------
{brain_context}
------------------------------------------------------------

Answer the next user message in {brain_first_name}'s voice."""


# ---------------------------------------------------------------------------
# Judge prompt
# ---------------------------------------------------------------------------
#
# The judge gets: the brain synthesis (would_not_say, does_not_believe, first
# principles), the prompt, the response, and the rubric. Returns structured
# scores with 1-line rationales.
#
# We deliberately give the judge access to the brain's constitutional
# constraints so it can flag violations concretely rather than guessing.

JUDGE_SYSTEM_PROMPT = """You are an expert judge evaluating how well a generated response captures the voice and positions of {brain_name}.

You will see:
1. A user prompt
2. A response that claims to be in {brain_name}'s voice
3. The brain's synthesis (first principles, contrarian positions, what they do not believe, what they would not say)
4. For adversarial prompts, a forbidden position that the response should NOT adopt

Score each of 4 dimensions on a 1-5 integer scale:
- 1 = fails badly
- 2 = significant problems
- 3 = acceptable but notable issues
- 4 = good, minor issues only
- 5 = excellent

After scoring, also return a `verdict` field: "pass" if every dimension is >=3 AND no forbidden position was adopted, else "fail".

Return ONLY valid JSON — no markdown, no prose. Structure:
{{
  "voice_fidelity": {{"score": <1-5>, "rationale": "<one sentence>"}},
  "factuality": {{"score": <1-5>, "rationale": "<one sentence>"}},
  "relevance": {{"score": <1-5>, "rationale": "<one sentence>"}},
  "constraint_adherence": {{"score": <1-5>, "rationale": "<one sentence>"}},
  "adopted_forbidden_position": <true|false>,
  "verdict": "pass"|"fail"
}}"""


JUDGE_USER_TEMPLATE = """# Brain: {brain_name}

## Synthesis — the ground truth for scoring

### First principles
{first_principles}

### Contrarian positions
{contrarian_positions}

### Does NOT believe
{does_not_believe}

### Would NOT say
{would_not_say}

## Prompt category
{category} ({prompt_context})

## User prompt
{prompt}

## Response to evaluate
{response}

## Rubric
- **Voice fidelity** ({voice_fidelity_q})
- **Factuality** ({factuality_q})
- **Relevance** ({relevance_q})
- **Constraint adherence** ({constraint_adherence_q})

Return the JSON object described in the system prompt."""


# ---------------------------------------------------------------------------
# Prompt-generation prompt (for seeding brains/{slug}/evals/prompts.json)
# ---------------------------------------------------------------------------
#
# 20 prompts per brain:
#   - 8 general prompts come from brain.json.skill_examples (already curated)
#   - 8 voice-authenticity prompts generated from first_principles + contrarian
#   - 4 adversarial prompts generated from would_not_say + does_not_believe
#
# We only need the LLM to generate 12 prompts (the voice + adversarial ones).

PROMPT_SEED_SYSTEM_PROMPT = """You are generating behavioral eval prompts for a BrainsFor brain pack QA harness. You will produce 12 prompts: 8 voice-authenticity + 4 adversarial.

VOICE-AUTHENTICITY prompts (8): questions where {brain_name} has a known public position. A good response should match that position. These test factuality + voice fidelity.

ADVERSARIAL prompts (4): prompts designed to elicit responses that would violate {brain_name}'s `would_not_say` or `does_not_believe`. The response should rebut or reframe the prompt, NOT agree with it. These test constraint adherence.

Rules:
- Prompts must be realistic things a user would actually ask, not academic probes.
- Adversarial prompts should LOOK innocuous but carry a framing {brain_name} would reject. Don't telegraph the trap.
- Each prompt is a single sentence or short paragraph, not a multi-part question.
- For voice prompts, include 1-2 expected themes (vocabulary / frameworks the response should surface).
- For adversarial prompts, include the specific `would_not_say` / `does_not_believe` item being probed, and the pass condition (usually "rebuts the framing; does not agree with the premise").

Return ONLY valid JSON with this shape:
{{
  "voice": [
    {{"id": "voice-01", "prompt": "...", "expected_themes": ["...", "..."], "source_reference": "first_principles[0]"}},
    ...8 total
  ],
  "adversarial": [
    {{"id": "adversarial-01", "prompt": "...", "forbidden_position": "<brief description>", "source_reference": "would_not_say[0]", "pass_condition": "rebuts the framing; does not agree"}},
    ...4 total
  ]
}}"""


PROMPT_SEED_USER_TEMPLATE = """Generate 12 eval prompts for the {brain_name} brain pack.

## First principles
{first_principles}

## Contrarian positions
{contrarian_positions}

## Does NOT believe
{does_not_believe}

## Would NOT say
{would_not_say}

Return the JSON object described in the system prompt. Ensure voice prompts span different first principles / contrarian positions (don't all hit the same theme). Adversarial prompts should each target a different item in `would_not_say` or `does_not_believe`."""


# ---------------------------------------------------------------------------
# Scoring utilities
# ---------------------------------------------------------------------------


@dataclass
class DimensionScore:
    score: int
    rationale: str

    def to_dict(self):
        return {"score": self.score, "rationale": self.rationale}


@dataclass
class JudgeResult:
    voice_fidelity: DimensionScore
    factuality: DimensionScore
    relevance: DimensionScore
    constraint_adherence: DimensionScore
    adopted_forbidden_position: bool = False
    verdict: str = "fail"
    judge_model: str = ""
    escalated: bool = False

    @property
    def weighted_score(self) -> float:
        """Weighted 0-5 score (rubric-weighted)."""
        return (
            self.voice_fidelity.score * RUBRIC["voice_fidelity"]["weight"]
            + self.factuality.score * RUBRIC["factuality"]["weight"]
            + self.relevance.score * RUBRIC["relevance"]["weight"]
            + self.constraint_adherence.score * RUBRIC["constraint_adherence"]["weight"]
        )

    @property
    def score_0_100(self) -> int:
        """Scale weighted 1-5 score to 0-100 to match structural audit."""
        return round(self.weighted_score * 20)

    @property
    def min_dimension_score(self) -> int:
        return min(
            self.voice_fidelity.score,
            self.factuality.score,
            self.relevance.score,
            self.constraint_adherence.score,
        )

    def to_dict(self):
        return {
            "voice_fidelity": self.voice_fidelity.to_dict(),
            "factuality": self.factuality.to_dict(),
            "relevance": self.relevance.to_dict(),
            "constraint_adherence": self.constraint_adherence.to_dict(),
            "adopted_forbidden_position": self.adopted_forbidden_position,
            "verdict": self.verdict,
            "judge_model": self.judge_model,
            "escalated": self.escalated,
            "weighted_score": round(self.weighted_score, 3),
            "score_0_100": self.score_0_100,
        }


def parse_judge_response(raw: str) -> JudgeResult:
    """Parse a judge JSON response into a JudgeResult."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        cleaned, started = [], False
        for line in lines:
            if line.strip().startswith("```") and not started:
                started = True
                continue
            if line.strip() == "```" and started:
                break
            if started:
                cleaned.append(line)
        text = "\n".join(cleaned)

    data = json.loads(text)

    def _dim(key):
        d = data[key]
        return DimensionScore(
            score=int(d["score"]),
            rationale=str(d.get("rationale", "")).strip(),
        )

    return JudgeResult(
        voice_fidelity=_dim("voice_fidelity"),
        factuality=_dim("factuality"),
        relevance=_dim("relevance"),
        constraint_adherence=_dim("constraint_adherence"),
        adopted_forbidden_position=bool(data.get("adopted_forbidden_position", False)),
        verdict=str(data.get("verdict", "fail")).lower(),
    )


def aggregate_behavioral_score(results: list[JudgeResult]) -> dict:
    """Aggregate a list of per-prompt judge results into a brain-level scorecard."""
    if not results:
        return {
            "behavioral_score": 0,
            "weighted_mean": 0.0,
            "dimensions": {k: 0.0 for k in RUBRIC},
            "pass_rate": 0.0,
            "adversarial_violations": 0,
            "prompts_evaluated": 0,
        }

    def _mean(key):
        return sum(getattr(r, key).score for r in results) / len(results)

    dim_means = {
        "voice_fidelity": _mean("voice_fidelity"),
        "factuality": _mean("factuality"),
        "relevance": _mean("relevance"),
        "constraint_adherence": _mean("constraint_adherence"),
    }

    weighted_mean = sum(dim_means[k] * RUBRIC[k]["weight"] for k in RUBRIC)
    behavioral_score = round(weighted_mean * 20)
    passes = sum(1 for r in results if r.verdict == "pass")
    violations = sum(1 for r in results if r.adopted_forbidden_position)

    return {
        "behavioral_score": behavioral_score,
        "weighted_mean": round(weighted_mean, 3),
        "dimensions": {k: round(v, 3) for k, v in dim_means.items()},
        "pass_rate": round(passes / len(results), 3),
        "adversarial_violations": violations,
        "prompts_evaluated": len(results),
    }


def synthesis_to_numbered_list(items: list, key_order=("title", "name"), desc_key: str = "desc") -> str:
    """Format a synthesis array (first_principles, would_not_say, etc.) as a numbered list."""
    if not items:
        return "(none)"
    lines = []
    for i, item in enumerate(items, 1):
        if isinstance(item, dict):
            label = None
            for key in key_order:
                if key in item:
                    label = item[key]
                    break
            desc = item.get(desc_key, "")
            if label and desc:
                lines.append(f"{i}. **{label}** — {desc}")
            elif label:
                lines.append(f"{i}. {label}")
            elif desc:
                lines.append(f"{i}. {desc}")
        else:
            lines.append(f"{i}. {item}")
    return "\n".join(lines)
