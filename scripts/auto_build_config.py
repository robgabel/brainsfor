#!/usr/bin/env python3
"""
auto_build_config.py — Shared constants, cost tables, prompts, and utilities
for the auto-build-brain pipeline.
"""

import json
import re
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

# Quote provenance floor: % of atom quotes that must substring-match the source
# corpus (YouTube transcripts + scraped MD) at audit time. Below this, Phase 5
# re-runs the verifier (stripping fabrications) and re-audits. If the brain
# still fails after remediation, the build aborts — better to fix sources than
# ship LLM-invented words attributed to a real person.
MIN_QUOTE_PROVENANCE = 50

# Hard floor: pipeline halts after Phase 2 if total atoms < this value.
# Override per-build via --min-atoms or bypass with --allow-thin-pack.
MIN_BRAIN_ATOMS = 250

# Voice floor: pipeline halts after Phase 2 if too few atoms carry a verbatim
# original_quote. This catches the "transcript fetch silently failed" failure mode
# (e.g. YouTube blocks cloud/CI IPs) where text-scraping still clears the atom
# floor but the brain ships at ~7% voice with ungrounded synthesis. The atom
# count looks fine; the brain is hollow. Bypass with --allow-thin-pack.
# Audit recommended ~0.35; set to 0.30 because the healthy brains cluster at
# 36-47% voice (reshma the lowest at 36%), so a 0.35 floor leaves only a 1pt
# margin and would risk tripping its own "blocks >1 in 4 legit brains" kill
# criterion. 0.30 still catches hollow (7%) and clearly-thin builds. Tunable;
# --allow-thin-pack is the explicit override for rare-source thinkers.
MIN_VOICE_PCT = 0.30
# If at least this many YouTube videos were discovered but ZERO transcripts were
# fetched, that's the transcript-fetch-failure signature (not a real "no videos"
# case) — halt rather than ship a quote-less brain.
MIN_VIDEOS_EXPECT_TRANSCRIPTS = 5

# Firecrawl scrape settings
SCRAPE_MAX_CHARS = 12000
SCRAPE_MIN_CHARS = 500
SCRAPE_TIMEOUT_SEC = 60
SCRAPE_SKIP_DOMAINS = ("facebook.com", "twitter.com", "x.com", "instagram.com", "tiktok.com")

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
    """Track API call costs across the pipeline. Thread-safe — Phase 2.2 / 2.3
    fire `record()` concurrently from ThreadPoolExecutor workers, and `+=` on
    primitives is not atomic in CPython (read-modify-write loses updates)."""

    def __init__(self):
        import threading
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.calls = []
        self._lock = threading.Lock()

    def record(self, model: str, input_tokens: int, output_tokens: int, label: str = ""):
        in_cost = (input_tokens / 1000) * COST_INPUT.get(model, 0.003)
        out_cost = (output_tokens / 1000) * COST_OUTPUT.get(model, 0.015)
        cost = in_cost + out_cost
        with self._lock:
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
def extract_json_block(text: str) -> str:
    """Best-effort extraction of a JSON value from an LLM response.

    Handles markdown fences, leading/trailing prose, and trailing garbage by
    scanning from the first {/[ through its balanced close (string- and
    escape-aware). If the value is truncated (no balanced close — the max_tokens
    ceiling case), returns what's present so json.loads raises and the caller
    escalates the token budget on retry. Never raises itself.
    """
    t = (text or "").strip()
    if "```" in t:
        m = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL)
        t = (m.group(1) if m else t.replace("```json", "").replace("```", "")).strip()
    start = next((i for i, ch in enumerate(t) if ch in "{["), None)
    if start is None:
        return t
    open_ch = t[start]
    close_ch = "}" if open_ch == "{" else "]"
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(t)):
        ch = t[i]
        if in_str:
            esc = (ch == "\\" and not esc)
            if ch == '"' and not esc:
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return t[start:i + 1]
    return t[start:]  # truncated — caller will escalate max_tokens


def call_claude(
    client,
    model: str,
    messages: list,
    system: str = None,
    max_tokens: int = 4096,
    max_retries: int = 4,
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
                result["parsed"] = json.loads(extract_json_block(content))

            return result

        except json.JSONDecodeError as e:
            last_error = e
            if attempt < max_retries - 1:
                # The dominant cause is truncation at the max_tokens ceiling (valid
                # JSON cut mid-string). Retrying at the SAME budget just truncates
                # again — escalate it, and re-prompt for complete JSON. This turns
                # the charlie-munger/jensen-huang abort class into a self-heal.
                kwargs["max_tokens"] = min(32000, int(kwargs.get("max_tokens", max_tokens) * 1.6))
                warn(f"JSON parse failed (attempt {attempt + 1}) — "
                     f"retrying at max_tokens={kwargs['max_tokens']}...")
                if messages and messages[-1]["role"] == "user":
                    messages = messages.copy()
                    messages[-1] = {
                        "role": "user",
                        "content": messages[-1]["content"]
                        + "\n\nReturn ONLY valid, COMPLETE JSON — no markdown, no prose, "
                          "and do not truncate. If large, be concise but keep it well-formed.",
                    }
                    kwargs["messages"] = messages  # original code forgot this — kwargs kept stale messages
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
    """Return web-search queries for TEXT source discovery via Firecrawl.

    YouTube videos are handled separately by discover_youtube_videos() using
    yt-dlp — do NOT add video/podcast-oriented queries here or they'll return
    YouTube URLs that Firecrawl can't usefully scrape.
    """
    return [
        f"{person_name} best way to understand",
        f"{person_name} best interviews transcript",
        f"{person_name} best essays OR best writing OR best articles",
        f"{person_name} books",
    ]


# --- YouTube partner discovery prompt ---
YOUTUBE_PARTNER_PROMPT = """\
You are helping build a knowledge database about {person_name}.

List podcast hosts, interviewers, and events that are HIGHLY LIKELY to have
a recorded interview with {person_name} available on YouTube.

STRICT RULES:
- Only include entries where you are HIGHLY CONFIDENT the interview exists on YouTube
- If you are unsure whether someone has ever hosted {person_name}, DO NOT include them
- Each name will be used as an exact quoted string in a YouTube search alongside
  "{person_name}" — so use the person's or event's full recognizable name
- Prefer long-form interviews (podcasts, talks, conference keynotes) over clips

Return a JSON object — no markdown, no explanation:
{{"partners": ["Tim Ferriss", "Shane Parrish", ...]}}

Include at most 12 partners. Fewer high-confidence entries beat many uncertain ones.

Who are the most well-known people or events that have hosted or interviewed {person_name} on YouTube?\
"""


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

CRITICAL — DISAMBIGUATION: The sources above are the GROUND TRUTH for which {person_name} this brain is about. Common names (e.g. "Bill Harris", "John Smith", "Sarah Lee") refer to multiple notable people. Read the URLs, descriptions, and titles carefully BEFORE generating clusters — the domains (e.g. paypal.com vs holosync.com) and titles tell you exactly which person. Do NOT rely on your prior knowledge of who is most famous with this name; rely on what the sources are about. Clusters, synthesis, and skill examples MUST reflect THIS specific person, not a different person who shares the name.

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

(Note: do NOT include a "skills" key — the synthesis.skills array is generated programmatically from a stable template, not extracted from synthesis.md.)

Here is the synthesis.md to extract from:

{synthesis_md}

Return ONLY valid JSON."""
