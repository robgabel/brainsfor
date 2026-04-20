#!/usr/bin/env python3
"""
auto_build_config.py — Shared constants, cost tables, prompts, and utilities
for the auto-build-brain pipeline.
"""

import json
import time
import logging
from pathlib import Path

# --- Paths ---
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
BRAINS_DIR = ROOT_DIR / "brains"
TEMPLATES_DIR = ROOT_DIR / "templates"

# --- Models (canonical — all BrainsFor scripts import from here) ---
DEFAULT_MODEL = "claude-sonnet-4-6"
SYNTHESIS_MODEL = "claude-opus-4-7"
FAST_MODEL = "claude-haiku-4-5-20251001"

# --- Cost per 1K tokens (USD) ---
COST_INPUT = {
    "claude-opus-4-7": 0.015,
    "claude-sonnet-4-6": 0.003,
    "claude-haiku-4-5-20251001": 0.0008,
}
COST_OUTPUT = {
    "claude-opus-4-7": 0.075,
    "claude-sonnet-4-6": 0.015,
    "claude-haiku-4-5-20251001": 0.004,
}

# --- Quality targets ---
TARGET_ATOMS = 250
TARGET_CONNECTIONS = 400
MIN_ATOMS_PER_CLUSTER = 5
MIN_AUDIT_SCORE = 70
MAX_REMEDIATION_CYCLES = 2

# --- Phase names ---
PHASE_NAMES = {
    0: "Source Discovery",
    1: "Scaffolding",
    2: "Content Ingestion",
    3: "Synthesis",
    4: "Enrichment",
    5: "Export & QA",
}

# --- Logging helpers ---
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
    "dim": "\033[2m",
}


def phase_header(phase_num: int, label: str = None):
    """Print a colorful phase header."""
    label = label or PHASE_NAMES.get(phase_num, f"Phase {phase_num}")
    c = COLORS
    print(f"\n{c['bold']}{c['blue']}{'=' * 60}")
    print(f"  PHASE {phase_num}: {label}")
    print(f"{'=' * 60}{c['reset']}\n")


def step(msg: str):
    """Print a step within a phase."""
    print(f"  {COLORS['cyan']}>{COLORS['reset']} {msg}")


def success(msg: str):
    """Print a success message."""
    print(f"  {COLORS['green']}OK{COLORS['reset']} {msg}")


def warn(msg: str):
    """Print a warning."""
    print(f"  {COLORS['yellow']}WARN{COLORS['reset']} {msg}")


def error(msg: str):
    """Print an error."""
    print(f"  {COLORS['red']}ERROR{COLORS['reset']} {msg}")


# --- Cost tracker ---
class CostTracker:
    """Track API call costs across the pipeline."""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.calls = []

    def record(self, model: str, input_tokens: int, output_tokens: int, label: str = ""):
        in_cost = (input_tokens / 1000) * COST_INPUT.get(model, 0.003)
        out_cost = (output_tokens / 1000) * COST_OUTPUT.get(model, 0.015)
        cost = in_cost + out_cost
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost
        self.calls.append({
            "model": model, "input": input_tokens, "output": output_tokens,
            "cost": cost, "label": label,
        })
        return cost

    def summary(self) -> str:
        return (
            f"API calls: {len(self.calls)} | "
            f"Tokens: {self.total_input_tokens:,} in / {self.total_output_tokens:,} out | "
            f"Cost: ${self.total_cost:.2f}"
        )


# --- Claude API wrapper with retries ---
def call_claude(
    client,
    model: str,
    messages: list,
    system: str = None,
    max_tokens: int = 4096,
    max_retries: int = 3,
    parse_json: bool = False,
    cost_tracker: CostTracker = None,
    label: str = "",
) -> dict:
    """
    Call Claude API with retry logic and optional JSON parsing.

    Returns dict with keys: content, input_tokens, output_tokens, model.
    If parse_json=True, also includes 'parsed' key with parsed JSON.
    """
    kwargs = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if system:
        kwargs["system"] = system

    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.messages.create(**kwargs)
            content = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            if cost_tracker:
                cost_tracker.record(model, input_tokens, output_tokens, label)

            result = {
                "content": content,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model,
            }

            if parse_json:
                # Extract JSON from markdown code blocks if present
                text = content.strip()
                if text.startswith("```"):
                    lines = text.split("\n")
                    # Remove first and last lines (``` markers)
                    json_lines = []
                    started = False
                    for line in lines:
                        if line.strip().startswith("```") and not started:
                            started = True
                            continue
                        if line.strip() == "```" and started:
                            break
                        if started:
                            json_lines.append(line)
                    text = "\n".join(json_lines)
                result["parsed"] = json.loads(text)

            return result

        except json.JSONDecodeError as e:
            last_error = e
            if attempt < max_retries - 1:
                warn(f"JSON parse failed (attempt {attempt + 1}), retrying with stricter prompt...")
                # Add instruction to return valid JSON
                if messages and messages[-1]["role"] == "user":
                    messages = messages.copy()
                    messages[-1] = {
                        "role": "user",
                        "content": messages[-1]["content"] + "\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no explanation, no code blocks.",
                    }
                time.sleep(1)
            continue

        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            if "rate_limit" in err_str or "429" in err_str:
                wait = (2 ** attempt) * 5
                warn(f"Rate limited, waiting {wait}s...")
                time.sleep(wait)
            elif "overloaded" in err_str or "529" in err_str:
                wait = (2 ** attempt) * 10
                warn(f"API overloaded, waiting {wait}s...")
                time.sleep(wait)
            else:
                if attempt < max_retries - 1:
                    warn(f"API error (attempt {attempt + 1}): {e}")
                    time.sleep(2)
                else:
                    raise

    raise last_error


# --- Search queries for source discovery ---
def get_search_queries(person_name: str) -> list:
    """Return the 5 search queries for discovering sources about a person."""
    return [
        f"{person_name} best way to understand",
        f"{person_name} best interviews",
        f"{person_name} best essays OR best writing OR best articles",
        f"{person_name} books",
        f"{person_name} podcast appearances OR keynotes OR talks",
    ]


# --- Prompt templates ---

SOURCE_CLASSIFY_PROMPT = """You are classifying search results about {person_name} for a knowledge extraction project.

For each URL, determine:
1. type: "video" | "essay" | "book" | "podcast" | "interview" | "profile" | "other"
2. priority: "essential" (must-have primary sources) | "high" (valuable) | "medium" (supplementary)
3. youtube_id: Extract the YouTube video ID if it's a YouTube URL, otherwise null
4. title: A short descriptive title

Prefer PRIMARY sources (the person speaking/writing directly) over secondary sources (articles about them).
YouTube long-form interviews and the person's own writing are highest priority.

Return a JSON array of objects. Example:
[{{"url": "...", "type": "interview", "priority": "essential", "youtube_id": "abc123", "title": "Lex Fridman Interview"}}]

URLs to classify:
{urls_json}

Return ONLY the JSON array."""

BRAIN_JSON_PROMPT = """You are creating a brain.json configuration file for a BrainsFor brain pack about {person_name}.

BrainsFor packages notable thinkers' knowledge into structured "brain packs" that AI assistants can use. Each brain has atoms (atomic insights), connections between atoms, topic clusters, and 8 thinking skills.

Here is a complete exemplar brain.json to use as your template — follow this structure EXACTLY:

{exemplar_json}

Here is what we know about {person_name}'s sources:
{sources_summary}

Create a complete brain.json for {person_name}. Requirements:
- Fill ALL fields from the exemplar (brain_name, brain_first_name, brain_last_name, brain_slug, brain_possessive, etc.)
- brain_slug should be: {slug}
- Create 12-16 topic clusters that represent the major themes of {person_name}'s thinking
- Each cluster needs a "name" and "description" (2-3 sentences)
- cluster_order should list all cluster keys in logical order
- skill_examples: write realistic example prompts a user might ask this thinker for each of the 8 skills
- workflow_examples: create 2 realistic skill-chaining workflows
- supabase.project_id: "uzediwokyshjbsymevtp"
- supabase.atoms_table: "{atoms_table}"
- supabase.connections_table: "{connections_table}"
- synthesis section: create a DRAFT with first_principles (8-11), thinking_patterns (6-9), contrarian_positions (8-12), does_not_believe (5-7), would_not_say (4-6), biography (4-6 entries), skills (copy from exemplar, just update examples)
- website section: tagline, bio (2-3 sentences), topics (6 items), price (29)

The synthesis section is a draft — it will be refined later after atom extraction. But make it as good as you can based on what you know about {person_name}.

Return ONLY valid JSON. No markdown, no explanation."""

SYNTHESIS_PROMPT = """You are writing a deep intellectual synthesis of how {person_name} thinks, based on {atom_count} extracted knowledge atoms from their work.

This synthesis will be the foundation of a "brain pack" — a product that lets AI assistants think like {person_name}. It must capture their AUTHENTIC intellectual identity: not a Wikipedia summary, but how someone who deeply studied them would describe their worldview.

Here is the format to follow (from a completed synthesis of Scott Belsky):

{exemplar_synthesis}

Here is the draft synthesis from brain.json (use as a starting point but improve significantly):

{draft_synthesis}

Here are ALL {atom_count} atoms extracted from {person_name}'s work, grouped by cluster:

{atoms_by_cluster}

Write a complete synthesis.md for {person_name}. Requirements:

1. **First Principles** (8-11): The foundational beliefs that drive everything. Each should have a bold title and 2-3 sentence explanation. These should feel like genuine insights, not platitudes.

2. **Thinking Patterns** (6-9): How they reason — their signature moves. Name each pattern and explain how they use it.

3. **Contrarian Positions** (8-12): Where they disagree with conventional wisdom. These should be genuinely provocative, not just restatements of their views.

4. **What They Do NOT Believe** (5-7): Common beliefs in their field that they explicitly reject.

5. **What They Would NOT Say** (4-6): Phrases or positions that would be out of character for them.

6. **Biographical Pattern** (4-6 timeline entries): Key career transitions and what each one taught them.

Write in the voice of an expert analyst, not a fan. Be specific — cite actual concepts, frameworks, and vocabulary that {person_name} uses. Every entry should reveal genuine intellectual insight.

Start with "## How {person_name} Thinks" and include an italicized update line."""

SYNTHESIS_JSON_PROMPT = """Based on the synthesis.md you just created for {person_name}, extract the structured data for brain.json.

Return a JSON object with these keys:
- hero_tagline: string (short, evocative — like "Originals, agents, and organizational design")
- hero_updated: string (describes what sources were used)
- first_principles: array of {{title, desc}}
- thinking_patterns: array of {{name, desc}}
- contrarian_positions: array of {{title, desc}}
- does_not_believe: array of {{title, desc}}
- would_not_say: array of {{title, desc}}
- biography: array of {{date, role, lesson}}
- skills: (copy from existing brain.json — don't modify)

Here is the synthesis.md to extract from:

{synthesis_md}

Return ONLY valid JSON."""
