#!/usr/bin/env python3
"""
audit-brains.py — Deterministic QA for BrainsFor brain packs.

Checks every brain registered in brains/index.json for structural completeness,
schema validity, data quality, and unresolved template variables. Produces a
0-100 completeness score per brain across 6 weighted criteria.

With --with-behavioral, also reads the latest behavioral eval results (from
brains/{slug}/evals/results-*.json, produced by scripts/eval-brains.py) and
shows both scores side-by-side. Behavioral evals are not run during audit —
run scripts/eval-brains.py --all separately.

Usage:
    python3 scripts/audit-brains.py                       # Audit all brains
    python3 scripts/audit-brains.py --brain scott-belsky   # Audit one brain
    python3 scripts/audit-brains.py --json                 # Machine-readable output
    python3 scripts/audit-brains.py --fix-hints            # Include remediation hints
    python3 scripts/audit-brains.py --remediate            # Generate fix script
    python3 scripts/audit-brains.py --with-behavioral      # Add behavioral eval scores
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BRAINS_DIR = Path(__file__).resolve().parent.parent / "brains"
SCRIPTS_DIR = Path(__file__).resolve().parent
INDEX_FILE = BRAINS_DIR / "index.json"

REQUIRED_BRAIN_JSON_KEYS = {
    "identity": ["brain_name", "brain_first_name", "brain_last_name", "brain_slug", "brain_possessive"],
    "source": ["brain_source_description", "brain_source_url", "brain_source_detail", "brain_tagline", "brain_bio"],
    "taxonomy": ["clusters", "cluster_order"],
    "examples": ["topic_examples", "example_topic", "quick_start_prompt", "skill_examples"],
    "synthesis": ["synthesis"],
}

REQUIRED_SKILL_EXAMPLES = [
    "advise", "teach", "debate", "connect",
    "evolve", "surprise", "coach", "predict",
]

REQUIRED_SYNTHESIS_KEYS = [
    "hero_tagline", "first_principles", "thinking_patterns",
    "contrarian_positions", "does_not_believe", "would_not_say",
    "biography", "skills",
]

REQUIRED_PACK_FILES = [
    "brain-atoms.json",
    "brain-atoms.js",
    "brain-context.md",
    "explore.html",
    "README.md",
    "SKILL.md",
]

REQUIRED_SKILLS = [
    "advise", "coach", "connect", "debate",
    "evolve", "predict", "surprise", "teach",
]

TEMPLATE_VAR_PATTERN = re.compile(r"\{\{[a-z_]+\}\}")

# Quality thresholds
MIN_ATOMS_LIVE = 100
MIN_CONNECTIONS_LIVE = 50
VOICE_ENRICHMENT_TARGET = 0.5   # 50% of atoms should have original_quote
ORPHAN_ATOM_THRESHOLD = 0.15    # <15% orphan atoms for live brains
PROVENANCE_TARGET = 0.5         # 50% of quoted atoms should trace to source corpus
GROUNDING_TARGET = 0.7          # 70% of synthesis principles should appear in source corpus
QUOTE_SIGNATURE_LEN = 35        # chars used as substring lookup signature
GROUNDING_NGRAM_LEN = 4         # tokens in n-gram extracted from principles

# ---------------------------------------------------------------------------
# Scoring: 8 criteria, weighted to 100
# ---------------------------------------------------------------------------
#
#   1. Structure (15)     — all files, dirs, skills present; no duplicates
#   2. Schema (13)        — brain.json has all required keys, synthesis complete
#   3. Atom Volume (12)   — enough atoms to be useful (scaled 0→200+)
#   4. Connections (12)   — atoms linked, low orphan rate
#   5. Voice (15)         — original_quote + implication coverage (field populated)
#   6. Provenance (10)    — % of quoted atoms whose quote traces to YouTube transcript corpus
#   7. Synthesis (13)     — synthesis.md depth + brain-atoms.json synthesis section
#   8. Grounding (10)     — % of synthesis principles whose key phrases appear in source corpus
#   6. Synthesis (15)    — synthesis.md depth + brain-atoms.json synthesis section
#
# Each criterion scores 0.0–1.0, then is multiplied by its weight.
# Total = sum of weighted scores, capped at 100.

SCORING_CRITERIA = {
    "structure":  {"weight": 14, "label": "Structure & Files"},
    "schema":     {"weight": 12, "label": "Schema Completeness"},
    "atoms":      {"weight": 11, "label": "Atom Volume"},
    "connections": {"weight": 11, "label": "Connection Density"},
    "voice":      {"weight": 14, "label": "Voice Enrichment"},
    "provenance": {"weight": 9,  "label": "Quote Verifiability"},
    "synthesis":  {"weight": 12, "label": "Synthesis Depth"},
    "grounding":  {"weight": 9,  "label": "Synthesis Grounding"},
    "temporal":   {"weight": 8,  "label": "Temporal Density"},
}

# Temporal density thresholds (match scripts/compute-evolve-flags.py)
TEMPORAL_COVERAGE_TARGET = 0.50   # ≥50% of atoms must have source_date
TEMPORAL_YEAR_SPAN_TARGET = 3     # dated atoms must span ≥3 distinct years
_TEMPORAL_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    severity: str       # "error", "warning", "info"
    category: str       # "structure", "schema", "data", "template", "quality"
    message: str
    fix_hint: str = ""
    fix_command: str = ""   # shell command for --remediate

@dataclass
class BrainAudit:
    slug: str
    name: str
    status: str
    issues: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    scores: dict = field(default_factory=dict)  # criterion -> 0.0-1.0
    behavioral: Optional[dict] = None  # populated when --with-behavioral and cached results exist

    @property
    def errors(self):
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self):
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def passed(self):
        return len(self.errors) == 0

    @property
    def completeness_score(self) -> int:
        total = 0.0
        for key, meta in SCORING_CRITERIA.items():
            raw = self.scores.get(key, 0.0)
            total += raw * meta["weight"]
        return min(100, round(total))


# ---------------------------------------------------------------------------
# Audit checks  (each populates issues + stats used for scoring)
# ---------------------------------------------------------------------------

def check_directory_structure(brain_dir: Path, audit: BrainAudit):
    """Check that all expected directories and files exist."""
    pack_dir = brain_dir / "pack"

    if not brain_dir.exists():
        audit.issues.append(Issue("error", "structure", f"Brain directory missing: {brain_dir}",
                                  f"mkdir -p {brain_dir}",
                                  f"mkdir -p {brain_dir}"))
        return

    if not (brain_dir / "brain.json").exists():
        audit.issues.append(Issue("error", "structure", "brain.json missing",
                                  "Create brain.json from template"))

    if not (brain_dir / "synthesis.md").exists():
        audit.issues.append(Issue("warning", "structure", "synthesis.md missing",
                                  "Write synthesis.md with first principles and thinking patterns"))

    if not pack_dir.exists():
        audit.issues.append(Issue("error", "structure", "pack/ directory missing",
                                  f"Run: python3 scripts/export-brain.py --brain {audit.slug}",
                                  f"python3 scripts/export-brain.py --brain {audit.slug}"))
        return

    # Check required pack files
    pack_present = 0
    for f in REQUIRED_PACK_FILES:
        if (pack_dir / f).exists():
            pack_present += 1
        else:
            audit.issues.append(Issue("error", "structure", f"pack/{f} missing",
                                      f"Run export-brain.py to generate pack/{f}",
                                      f"python3 scripts/export-brain.py --brain {audit.slug}"))

    # Check skill directories
    skills_present = 0
    skills_clean = 0
    for skill in REQUIRED_SKILLS:
        skill_file = pack_dir / "skills" / skill / "SKILL.md"
        skill_file_alt = pack_dir / "skills" / f"{skill}.md" / "SKILL.md"

        has_canonical = skill_file.exists()
        has_alt = skill_file_alt.exists()

        if has_canonical or has_alt:
            skills_present += 1

        if not has_canonical and not has_alt:
            audit.issues.append(Issue("error", "structure",
                                      f"pack/skills/{skill}/SKILL.md missing",
                                      f"Run export-brain.py to generate skill files",
                                      f"python3 scripts/export-brain.py --brain {audit.slug}"))
        elif has_canonical and has_alt:
            audit.issues.append(Issue("warning", "structure",
                                      f"Duplicate skill dirs: skills/{skill}/ AND skills/{skill}.md/",
                                      f"rm -rf pack/skills/{skill}.md",
                                      f"rm -rf {pack_dir}/skills/{skill}.md"))
        elif has_alt and not has_canonical:
            audit.issues.append(Issue("warning", "structure",
                                      f"Skill uses non-canonical path: skills/{skill}.md/ (should be skills/{skill}/)",
                                      f"mv pack/skills/{skill}.md pack/skills/{skill}",
                                      f"mv {pack_dir}/skills/{skill}.md {pack_dir}/skills/{skill}"))
        else:
            skills_clean += 1

    # Store for scoring
    has_brain_json = (brain_dir / "brain.json").exists()
    has_synthesis = (brain_dir / "synthesis.md").exists()
    total_items = len(REQUIRED_PACK_FILES) + len(REQUIRED_SKILLS) + 2  # +brain.json +synthesis.md
    present_items = pack_present + skills_present + (1 if has_brain_json else 0) + (1 if has_synthesis else 0)
    # Penalty for non-canonical paths: -0.02 per warning
    structural_warnings = len([i for i in audit.issues if i.category == "structure" and i.severity == "warning"])
    raw = (present_items / total_items) - (structural_warnings * 0.02)
    audit.scores["structure"] = max(0.0, min(1.0, raw))


def check_brain_json_schema(brain_dir: Path, audit: BrainAudit):
    """Validate brain.json has all required fields."""
    brain_json_path = brain_dir / "brain.json"
    if not brain_json_path.exists():
        audit.scores["schema"] = 0.0
        return

    try:
        with open(brain_json_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        audit.issues.append(Issue("error", "schema", f"brain.json is invalid JSON: {e}"))
        audit.scores["schema"] = 0.0
        return

    total_checks = 0
    passed_checks = 0

    # Check required key groups
    for group, keys in REQUIRED_BRAIN_JSON_KEYS.items():
        for key in keys:
            total_checks += 1
            if key not in config:
                audit.issues.append(Issue("error", "schema",
                                          f"brain.json missing required key: {key} ({group})",
                                          f"Add '{key}' to brain.json"))
            elif isinstance(config[key], str) and not config[key].strip():
                audit.issues.append(Issue("warning", "schema",
                                          f"brain.json key '{key}' is empty string"))
            else:
                passed_checks += 1

    # Check skill_examples
    skill_examples = config.get("skill_examples", {})
    for skill in REQUIRED_SKILL_EXAMPLES:
        total_checks += 1
        if skill in skill_examples:
            passed_checks += 1
        else:
            sev = "info" if skill == "surprise" else "warning"
            audit.issues.append(Issue(sev, "schema",
                                      f"brain.json skill_examples missing '{skill}'"))

    # Check synthesis sub-keys
    synthesis = config.get("synthesis", {})
    for key in REQUIRED_SYNTHESIS_KEYS:
        total_checks += 1
        if key not in synthesis:
            audit.issues.append(Issue("error", "schema",
                                      f"brain.json synthesis.{key} missing",
                                      f"Add synthesis.{key} to brain.json"))
        elif isinstance(synthesis[key], list) and len(synthesis[key]) == 0:
            audit.issues.append(Issue("warning", "schema",
                                      f"brain.json synthesis.{key} is empty array"))
            passed_checks += 0.5  # Half credit for present-but-empty
        else:
            passed_checks += 1

    # Check clusters have descriptions
    clusters = config.get("clusters", {})
    cluster_order = config.get("cluster_order", [])

    for cid in cluster_order:
        if cid not in clusters:
            audit.issues.append(Issue("error", "schema",
                                      f"cluster_order references '{cid}' but it's not in clusters"))

    for cid, cluster in clusters.items():
        if "name" not in cluster or "description" not in cluster:
            audit.issues.append(Issue("warning", "schema",
                                      f"Cluster '{cid}' missing name or description"))

    audit.stats["cluster_count"] = len(clusters)
    audit.scores["schema"] = (passed_checks / total_checks) if total_checks > 0 else 0.0


def check_pack_data(brain_dir: Path, audit: BrainAudit):
    """Validate brain-atoms.json structure and data quality."""
    atoms_path = brain_dir / "pack" / "brain-atoms.json"
    if not atoms_path.exists():
        audit.scores["atoms"] = 0.0
        audit.scores["connections"] = 0.0
        audit.scores["voice"] = 0.0
        return

    try:
        with open(atoms_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        audit.issues.append(Issue("error", "data", f"brain-atoms.json is invalid JSON: {e}"))
        audit.scores["atoms"] = 0.0
        audit.scores["connections"] = 0.0
        audit.scores["voice"] = 0.0
        return

    atoms = data.get("atoms", [])
    brain_meta = data.get("brain", {})
    synthesis_data = data.get("synthesis", {})

    atom_count = len(atoms)
    audit.stats["atom_count"] = atom_count
    audit.stats["declared_atom_count"] = brain_meta.get("atom_count", "?")
    audit.stats["declared_connection_count"] = brain_meta.get("connection_count", "?")

    # --- Atom Volume Score ---
    # 0 atoms = 0, 100 atoms = 0.5, 200+ atoms = 1.0 (linear scale)
    audit.scores["atoms"] = min(1.0, atom_count / 200.0)

    # Check atom count matches declaration
    declared = brain_meta.get("atom_count", 0)
    if isinstance(declared, int) and declared != atom_count:
        audit.issues.append(Issue("warning", "data",
                                  f"Declared {declared} atoms but found {atom_count} in brain-atoms.json",
                                  f"Update brain metadata or re-export"))

    # --- Connection Score ---
    total_connections = sum(len(a.get("connections", [])) for a in atoms)
    audit.stats["actual_connections_refs"] = total_connections

    orphans = sum(1 for a in atoms if len(a.get("connections", [])) == 0)
    orphan_pct = orphans / atom_count if atom_count else 1.0
    audit.stats["orphan_atoms"] = orphans
    audit.stats["orphan_pct"] = round(orphan_pct * 100, 1)

    # Connection score: inverse orphan rate, with floor for having any connections
    if total_connections == 0:
        conn_score = 0.0
    else:
        connected_pct = 1.0 - orphan_pct
        # Scale: 50% connected = 0.3, 85% connected = 0.85, 100% = 1.0
        conn_score = min(1.0, connected_pct * 1.1)
    audit.scores["connections"] = conn_score

    if audit.status == "live" and total_connections < MIN_CONNECTIONS_LIVE:
        audit.issues.append(Issue("warning", "quality",
                                  f"Live brain has only {total_connections} connection refs (target: {MIN_CONNECTIONS_LIVE}+)",
                                  f"Run: python3 scripts/enrich-connections.py --brain {audit.slug} --discover --llm",
                                  f"python3 scripts/enrich-connections.py --brain {audit.slug} --discover --llm --auto-apply"))
    if audit.status == "live" and orphan_pct > ORPHAN_ATOM_THRESHOLD:
        audit.issues.append(Issue("warning", "quality",
                                  f"Orphan atoms at {orphan_pct:.0%} (target: <{ORPHAN_ATOM_THRESHOLD:.0%})",
                                  f"Run: python3 scripts/enrich-connections.py --brain {audit.slug} --discover --llm",
                                  f"python3 scripts/enrich-connections.py --brain {audit.slug} --discover --llm --auto-apply"))

    # --- Voice Score ---
    with_quote = sum(1 for a in atoms if a.get("original_quote"))
    with_implication = sum(1 for a in atoms if a.get("implication"))
    quote_pct = with_quote / atom_count if atom_count else 0
    impl_pct = with_implication / atom_count if atom_count else 0
    audit.stats["voice_enrichment_pct"] = round(quote_pct * 100, 1)
    audit.stats["implication_pct"] = round(impl_pct * 100, 1)

    # Voice score: weighted average of quote coverage (70%) and implication coverage (30%)
    audit.scores["voice"] = (quote_pct * 0.7) + (impl_pct * 0.3)

    if audit.status == "live" and quote_pct < VOICE_ENRICHMENT_TARGET:
        audit.issues.append(Issue("warning", "quality",
                                  f"Voice enrichment at {quote_pct:.0%} (target: {VOICE_ENRICHMENT_TARGET:.0%}+)",
                                  f"Run: python3 scripts/enrich-voice.py --brain {audit.slug}",
                                  f"python3 scripts/enrich-voice.py --brain {audit.slug}"))

    # Cluster coverage
    clusters_seen = set()
    for a in atoms:
        c = a.get("cluster")
        if c:
            clusters_seen.add(c)
    audit.stats["clusters_with_atoms"] = len(clusters_seen)

    # Atoms missing required fields
    missing_content = sum(1 for a in atoms if not a.get("content"))
    missing_cluster = sum(1 for a in atoms if not a.get("cluster"))
    if missing_content:
        audit.issues.append(Issue("error", "data", f"{missing_content} atoms missing 'content' field"))
    if missing_cluster:
        audit.issues.append(Issue("warning", "data", f"{missing_cluster} atoms missing 'cluster' field"))

    if audit.status == "live" and atom_count < MIN_ATOMS_LIVE:
        audit.issues.append(Issue("warning", "quality",
                                  f"Live brain has only {atom_count} atoms (target: {MIN_ATOMS_LIVE}+)"))

    # Synthesis in atoms JSON
    if not synthesis_data:
        audit.issues.append(Issue("warning", "data",
                                  "brain-atoms.json missing 'synthesis' section (explore.html needs it)",
                                  "Re-export with synthesis included",
                                  f"python3 scripts/export-brain.py --brain {audit.slug}"))
    else:
        for key in REQUIRED_SYNTHESIS_KEYS:
            if key not in synthesis_data or not synthesis_data[key]:
                audit.issues.append(Issue("warning", "data",
                                          f"brain-atoms.json synthesis.{key} missing or empty",
                                          f"Re-export after filling brain.json synthesis.{key}",
                                          f"python3 scripts/export-brain.py --brain {audit.slug}"))


def check_temporal_density(brain_dir: Path, audit: BrainAudit):
    """Score whether the pack has enough dated atoms across enough years for /evolve.

    Score (0.0–1.0) = 0.6 × coverage_normalized + 0.4 × year_span_normalized
    Coverage hits 1.0 at 50%+ dated atoms; year span hits 1.0 at 5+ distinct years.
    """
    atoms_path = brain_dir / "pack" / "brain-atoms.json"
    if not atoms_path.exists():
        audit.scores["temporal"] = 0.0
        return
    try:
        atoms = json.loads(atoms_path.read_text(encoding="utf-8")).get("atoms", [])
    except Exception:
        audit.scores["temporal"] = 0.0
        return

    total = len(atoms)
    if total == 0:
        audit.scores["temporal"] = 0.0
        return

    years: set[int] = set()
    dated = 0
    for a in atoms:
        raw = a.get("source_date")
        if not raw:
            continue
        s = str(raw).strip()
        if not s or s.lower() in {"unknown", "none", "null", "n/a"}:
            continue
        m = _TEMPORAL_YEAR_RE.search(s)
        if not m:
            continue
        dated += 1
        years.add(int(m.group(1)))

    coverage = dated / total
    year_span = len(years)
    audit.stats["temporal_coverage_pct"] = round(coverage * 100, 1)
    audit.stats["temporal_year_span"] = year_span
    audit.stats["temporal_year_min"] = min(years) if years else None
    audit.stats["temporal_year_max"] = max(years) if years else None

    coverage_norm = min(1.0, coverage / TEMPORAL_COVERAGE_TARGET)
    span_norm = min(1.0, year_span / 5.0)
    audit.scores["temporal"] = (coverage_norm * 0.6) + (span_norm * 0.4)

    supports_evolve = (
        coverage >= TEMPORAL_COVERAGE_TARGET
        and year_span >= TEMPORAL_YEAR_SPAN_TARGET
    )
    audit.stats["supports_evolve"] = supports_evolve

    if audit.status == "live" and not supports_evolve:
        # Only warn for live brains — hidden brains are local-only
        if coverage < TEMPORAL_COVERAGE_TARGET:
            audit.issues.append(Issue("warning", "quality",
                                      f"Only {coverage*100:.0f}% of atoms have source_date "
                                      f"(/evolve target: {int(TEMPORAL_COVERAGE_TARGET*100)}%+)",
                                      "Run backfill or rebuild text-source atoms with dates",
                                      f"python3 scripts/backfill-source-dates.py --brain {audit.slug} --pack-only"))
        if year_span < TEMPORAL_YEAR_SPAN_TARGET:
            audit.issues.append(Issue("info", "quality",
                                      f"Dated atoms span only {year_span} distinct year(s) — "
                                      f"/evolve needs {TEMPORAL_YEAR_SPAN_TARGET}+ for a real timeline"))


# ---------------------------------------------------------------------------
# Source corpus utilities (used by provenance + grounding checks)
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "is", "are", "was", "were",
    "be", "been", "being", "to", "of", "in", "on", "at", "by", "for", "with",
    "as", "from", "into", "that", "this", "these", "those", "it", "its", "i",
    "you", "your", "we", "our", "they", "their", "he", "she", "his", "her",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "not", "no", "so", "than",
    "then", "there", "here", "what", "which", "who", "when", "where", "how",
    "why", "all", "any", "some", "more", "most", "such", "about", "also",
    "just", "only", "very", "really", "too", "much", "even", "still",
}


def normalize_text(s: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation noise."""
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def load_source_corpus(brain_dir: Path) -> dict:
    """Load raw source text available for provenance/grounding checks.

    Returns a dict with:
      - "youtube_text":      normalized concat of all transcripts/*.json full_text
      - "blog_podcast_text": normalized concat of all source/raw/*.md (Firecrawl-scraped
                             blog essays, podcast pages, interviews, Substack posts)
      - "atom_pool_text":    normalized concat of original_quote across video/text atoms
                             (lower signal — round-trip from atom extraction)
      - "any_text":          all three concatenated, fast .find() lookup target
      - "video_count":       number of transcripts loaded
      - "text_source_count": number of raw markdown files loaded
    """
    corpus = {
        "youtube_text": "",
        "blog_podcast_text": "",
        "atom_pool_text": "",
        "any_text": "",
        "video_count": 0,
        "text_source_count": 0,
    }

    transcripts_dir = brain_dir / "source" / "transcripts"
    yt_parts = []
    if transcripts_dir.exists():
        for tp in sorted(transcripts_dir.glob("*.json")):
            try:
                d = json.loads(tp.read_text(encoding="utf-8"))
            except Exception:
                continue
            ft = d.get("full_text") or ""
            if ft:
                yt_parts.append(ft)
                corpus["video_count"] += 1
    corpus["youtube_text"] = normalize_text(" ".join(yt_parts))

    # Blog / podcast / interview raw text persisted by auto-build-brain.py's
    # scrape_text_sources() (or by scripts/backfill-raw-sources.py for older brains).
    raw_dir = brain_dir / "source" / "raw"
    raw_parts = []
    if raw_dir.exists():
        for rp in sorted(raw_dir.glob("*.md")):
            try:
                txt = rp.read_text(encoding="utf-8")
            except Exception:
                continue
            if txt:
                raw_parts.append(txt)
                corpus["text_source_count"] += 1
    corpus["blog_podcast_text"] = normalize_text(" ".join(raw_parts))

    # Atom-pool fallback: original_quote strings extracted from video/text atoms
    atom_quotes = []
    for fname in ("video-atoms.json", "text-atoms.json"):
        fp = brain_dir / "research" / fname
        if not fp.exists():
            continue
        try:
            atoms = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(atoms, list):
            for a in atoms:
                q = a.get("original_quote") or ""
                if q:
                    atom_quotes.append(q)
    corpus["atom_pool_text"] = normalize_text(" ".join(atom_quotes))

    corpus["any_text"] = (
        corpus["youtube_text"]
        + " ||| "
        + corpus["blog_podcast_text"]
        + " ||| "
        + corpus["atom_pool_text"]
    )
    return corpus


def quote_signature(quote: str) -> str:
    """Take a distinctive substring of the middle of a quote for lookup."""
    n = normalize_text(quote)
    if len(n) <= QUOTE_SIGNATURE_LEN:
        return n
    # Skip first ~10 chars (often generic openers) and take a chunk
    return n[10 : 10 + QUOTE_SIGNATURE_LEN]


def extract_principle_phrases(item: dict) -> list:
    """Pull 2-3 distinctive n-grams from a synthesis principle's title + desc."""
    title = item.get("title") or item.get("name") or ""
    desc = item.get("desc") or item.get("description") or ""
    text = normalize_text(f"{title}. {desc}")
    tokens = [t for t in re.findall(r"[a-z][a-z\-']+", text) if t not in _STOPWORDS and len(t) > 2]
    if len(tokens) < GROUNDING_NGRAM_LEN:
        return [" ".join(tokens)] if tokens else []
    # Build sliding n-grams; pick 3 distinct ones spaced across the text
    ngrams = [" ".join(tokens[i : i + GROUNDING_NGRAM_LEN])
              for i in range(0, len(tokens) - GROUNDING_NGRAM_LEN + 1)]
    if not ngrams:
        return []
    if len(ngrams) <= 3:
        return ngrams
    # Sample beginning, middle, end
    return [ngrams[0], ngrams[len(ngrams) // 2], ngrams[-1]]


# ---------------------------------------------------------------------------
# New check: quote provenance — do atom quotes actually appear in source text?
# ---------------------------------------------------------------------------

def check_quote_provenance(brain_dir: Path, audit: BrainAudit):
    """For each atom with an original_quote, verify the quote exists in source text.

    Strong verification: quote signature appears in raw YouTube transcript full_text.
    Weak verification: quote signature appears in atom-pool (round-trip from extraction).
    No verification: quote not found anywhere → likely LLM-fabricated.
    """
    atoms_path = brain_dir / "pack" / "brain-atoms.json"
    if not atoms_path.exists():
        audit.scores["provenance"] = 0.0
        return

    try:
        data = json.loads(atoms_path.read_text(encoding="utf-8"))
    except Exception:
        audit.scores["provenance"] = 0.0
        return

    atoms = data.get("atoms", [])
    quoted = [a for a in atoms if a.get("original_quote")]
    if not quoted:
        # No quotes to verify — leave provenance score neutral (1.0 means no-quotes-no-problem)
        # but only credit it if Voice score is high; otherwise call it 0
        audit.scores["provenance"] = 0.0
        audit.stats["quoted_atoms"] = 0
        audit.stats["verified_youtube"] = 0
        audit.stats["verified_blog_podcast"] = 0
        audit.stats["verified_atom_pool"] = 0
        audit.stats["unverified_quotes"] = 0
        return

    corpus = load_source_corpus(brain_dir)
    yt = corpus["youtube_text"]
    raw = corpus["blog_podcast_text"]
    pool = corpus["atom_pool_text"]
    audit.stats["youtube_transcript_count"] = corpus["video_count"]
    audit.stats["raw_source_count"] = corpus["text_source_count"]

    strong_yt = 0           # found in YouTube transcripts
    strong_blog = 0         # found in blog/podcast scrape (source/raw/)
    weak = 0                # only round-trip via atom-pool
    unverified = 0
    unverified_examples = []
    for a in quoted:
        sig = quote_signature(a.get("original_quote", ""))
        if not sig:
            unverified += 1
            continue
        if yt and sig in yt:
            strong_yt += 1
        elif raw and sig in raw:
            strong_blog += 1
        elif pool and sig in pool:
            weak += 1
        else:
            unverified += 1
            if len(unverified_examples) < 3:
                unverified_examples.append(a.get("original_quote", "")[:80])

    strong = strong_yt + strong_blog
    total_q = len(quoted)
    audit.stats["quoted_atoms"] = total_q
    audit.stats["verified_youtube"] = strong_yt
    audit.stats["verified_blog_podcast"] = strong_blog
    audit.stats["verified_atom_pool"] = weak
    audit.stats["unverified_quotes"] = unverified
    audit.stats["provenance_pct"] = round(100 * (strong + weak) / total_q, 1)
    audit.stats["strong_verified_pct"] = round(100 * strong / total_q, 1)

    # Score: full credit for strong (YouTube OR blog/podcast scrape), half for atom-pool weak match
    score = ((strong * 1.0) + (weak * 0.5)) / total_q
    audit.scores["provenance"] = max(0.0, min(1.0, score))

    if audit.status == "live" and audit.scores["provenance"] < PROVENANCE_TARGET:
        unv_pct = round(100 * unverified / total_q, 1)
        example_str = (" — examples: " + " / ".join(f'"{e}…"' for e in unverified_examples)) if unverified_examples else ""
        audit.issues.append(Issue("warning", "quality",
                                  f"Quote provenance at {audit.scores['provenance']:.0%} — "
                                  f"{unverified}/{total_q} atom quotes ({unv_pct}%) don't appear "
                                  f"in source corpus (YouTube + blog/podcast + atom-pool). "
                                  f"Likely LLM-fabricated.{example_str}",
                                  f"Re-ingest with raw text persistence; or re-run synthesis only on verifiable atoms",
                                  ""))

    if corpus["video_count"] == 0 and corpus["text_source_count"] == 0:
        audit.issues.append(Issue("info", "quality",
                                  "No raw source text in source/transcripts/ or source/raw/ — "
                                  "provenance check falling back to atom-pool only (weak). "
                                  "Run scripts/backfill-raw-sources.py to populate."))
    elif corpus["text_source_count"] == 0:
        audit.issues.append(Issue("info", "quality",
                                  "No blog/podcast text in source/raw/ — non-YouTube quotes "
                                  "can only weak-verify via atom-pool. "
                                  "Run scripts/backfill-raw-sources.py to expand corpus."))


# ---------------------------------------------------------------------------
# New check: synthesis grounding — do principle key phrases appear in source?
# ---------------------------------------------------------------------------

def _load_latest_fact_check(brain_dir: Path) -> Optional[dict]:
    """Return the most recent fact-check JSON if present."""
    evals = brain_dir / "evals"
    if not evals.exists():
        return None
    candidates = sorted(evals.glob("fact-check-*.json"))
    if not candidates:
        return None
    try:
        return json.loads(candidates[-1].read_text(encoding="utf-8"))
    except Exception:
        return None


def check_synthesis_grounding(brain_dir: Path, audit: BrainAudit):
    """For each synthesis principle, check whether its key phrases appear in source corpus.

    Prefers a recent fact-check JSON (semantic, Sonnet-verified) over lexical n-gram match.
    Lexical match suffers high false-negatives (4-gram exact-order is too strict for
    paraphrased principles). When a fact-check result is available, use its grounding
    score as the source of truth and only run the lexical check as a fallback.

    Targets the 4 most factually-loaded synthesis sections:
      - first_principles
      - contrarian_positions
      - does_not_believe
      - would_not_say
    """
    # Prefer semantic fact-check result when available
    fc = _load_latest_fact_check(brain_dir)
    if fc and "scorecard" in fc:
        sc = fc["scorecard"]
        pct = sc.get("grounding_pct", 0)
        audit.scores["grounding"] = max(0.0, min(1.0, pct / 100.0))
        audit.stats["grounding_pct"] = round(pct, 1)
        audit.stats["grounding_source"] = "semantic (fact-check-brain.py)"
        audit.stats["grounded_principles"] = sc["totals"].get("grounded", 0)
        audit.stats["total_principles"] = sc["totals"].get("total", 0)
        audit.stats["grounding_by_section"] = {
            s: f"{stats.get('grounded', 0)}/{stats.get('total', 0)}"
            for s, stats in sc.get("by_section", {}).items()
        }

        if audit.status == "live" and audit.scores["grounding"] < GROUNDING_TARGET:
            ung = [r for r in fc.get("results", []) if r.get("status") == "ungrounded"][:3]
            examples = (
                " — examples: " + "; ".join(
                    f"[{r['section']}] {r.get('title', '')[:50]}" for r in ung
                )
            ) if ung else ""
            audit.issues.append(Issue("warning", "quality",
                                      f"Synthesis grounding at {pct:.0f}% (semantic fact-check, "
                                      f"{sc['totals']['grounded']}/{sc['totals']['total']} principles).{examples}",
                                      f"Run: python3 scripts/synthesize-from-source.py --brain {audit.slug}",
                                      f"python3 scripts/synthesize-from-source.py --brain {audit.slug}"))
        return

    # Fallback: lexical n-gram match (high false-negative rate; advisory only)
    brain_json_path = brain_dir / "brain.json"
    if not brain_json_path.exists():
        audit.scores["grounding"] = 0.0
        return

    try:
        config = json.loads(brain_json_path.read_text(encoding="utf-8"))
    except Exception:
        audit.scores["grounding"] = 0.0
        return

    syn = config.get("synthesis", {})
    sections = ("first_principles", "contrarian_positions", "does_not_believe", "would_not_say")

    items_by_section = {s: syn.get(s) or [] for s in sections}
    total_items = sum(len(v) for v in items_by_section.values())
    if total_items == 0:
        audit.scores["grounding"] = 0.0
        return

    corpus = load_source_corpus(brain_dir)
    # Allow either YouTube text or atom-pool to ground a principle
    haystack = corpus["any_text"]
    if not haystack.strip():
        audit.scores["grounding"] = 0.0
        audit.issues.append(Issue("info", "quality",
                                  "Synthesis grounding skipped — no source corpus available"))
        return

    grounded = 0
    ungrounded_examples = []
    per_section_stats = {}
    for section, items in items_by_section.items():
        sec_grounded = 0
        for item in items:
            phrases = extract_principle_phrases(item)
            hit = any(p in haystack for p in phrases if len(p) >= 12)
            if hit:
                grounded += 1
                sec_grounded += 1
            else:
                if len(ungrounded_examples) < 3:
                    title = item.get("title") or item.get("name") or ""
                    ungrounded_examples.append(f"[{section}] {title[:60]}")
        per_section_stats[section] = (sec_grounded, len(items))

    pct = grounded / total_items if total_items else 0.0
    audit.scores["grounding"] = max(0.0, min(1.0, pct))
    audit.stats["grounded_principles"] = grounded
    audit.stats["total_principles"] = total_items
    audit.stats["grounding_pct"] = round(pct * 100, 1)
    audit.stats["grounding_by_section"] = {
        s: f"{g}/{n}" for s, (g, n) in per_section_stats.items()
    }

    if audit.status == "live" and pct < GROUNDING_TARGET:
        examples = (" — examples: " + "; ".join(ungrounded_examples)) if ungrounded_examples else ""
        audit.issues.append(Issue("warning", "quality",
                                  f"Synthesis grounding at {pct:.0%} ({grounded}/{total_items} principles) — "
                                  f"the remaining principles' key phrases don't appear in source corpus.{examples}",
                                  f"Run: python3 scripts/fact-check-brain.py --brain {audit.slug}",
                                  f"python3 scripts/fact-check-brain.py --brain {audit.slug}"))


def check_template_variables(brain_dir: Path, audit: BrainAudit):
    """Scan pack files for unresolved {{template_variables}}."""
    pack_dir = brain_dir / "pack"
    if not pack_dir.exists():
        return

    for path in pack_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in (".json", ".html") and path.stat().st_size > 500_000:
            continue  # Skip large data files for speed

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        matches = TEMPLATE_VAR_PATTERN.findall(text)
        if matches:
            rel = path.relative_to(pack_dir)
            unique = sorted(set(matches))
            audit.issues.append(Issue("error", "template",
                                      f"pack/{rel}: unresolved template vars: {', '.join(unique)}",
                                      "Re-run export-brain.py to resolve template variables",
                                      f"python3 scripts/export-brain.py --brain {audit.slug}"))


def check_index_consistency(index_data: dict, brain_dir: Path, audit: BrainAudit):
    """Check that index.json entry is consistent with actual data."""
    entry = None
    for b in index_data.get("brains", []):
        if b["slug"] == audit.slug:
            entry = b
            break

    if not entry:
        audit.issues.append(Issue("error", "structure",
                                  f"Brain '{audit.slug}' not registered in brains/index.json",
                                  "Add entry to brains/index.json"))
        return

    # Check atom count consistency
    atoms_path = brain_dir / "pack" / "brain-atoms.json"
    if atoms_path.exists():
        try:
            with open(atoms_path) as f:
                data = json.load(f)
            actual = len(data.get("atoms", []))
            declared = entry.get("atom_count", 0)
            if actual != declared:
                audit.issues.append(Issue("warning", "data",
                                          f"index.json says {declared} atoms but pack has {actual}",
                                          f"Update atom_count in index.json to {actual}"))
        except Exception:
            pass


def check_explore_html(brain_dir: Path, audit: BrainAudit):
    """Check that explore.html is data-driven."""
    html_path = brain_dir / "pack" / "explore.html"
    if not html_path.exists():
        return

    text = html_path.read_text(encoding="utf-8", errors="ignore")

    if "brain-atoms.json" not in text:
        audit.issues.append(Issue("warning", "structure",
                                  "explore.html does not reference brain-atoms.json",
                                  "Use the template-based explore.html that reads brain-atoms.json"))

    size_kb = html_path.stat().st_size / 1024
    audit.stats["explore_html_size_kb"] = round(size_kb, 1)
    if size_kb > 200:
        audit.issues.append(Issue("warning", "structure",
                                  f"explore.html is {size_kb:.0f}KB — may have inlined data"))


def check_synthesis_md(brain_dir: Path, audit: BrainAudit):
    """Check synthesis.md exists and has substance."""
    syn_path = brain_dir / "synthesis.md"
    if not syn_path.exists():
        audit.scores["synthesis"] = 0.0
        return

    text = syn_path.read_text(encoding="utf-8", errors="ignore")
    size_kb = len(text.encode("utf-8")) / 1024
    word_count = len(text.split())
    audit.stats["synthesis_md_size_kb"] = round(size_kb, 1)
    audit.stats["synthesis_md_words"] = word_count

    if word_count < 200:
        audit.issues.append(Issue("warning", "quality",
                                  f"synthesis.md is only {word_count} words — likely needs more depth",
                                  "Expand synthesis.md with first principles, thinking patterns, contrarian positions"))

    # Check for key sections. "not believe" matches both "does not believe" and
    # "do not believe" (brains vary on singular vs. plural subject).
    text_lower = text.lower()
    expected_sections = ["first principle", "thinking pattern", "contrarian", "not believe", "would not say"]
    found = sum(1 for s in expected_sections if s in text_lower)
    missing = [s for s in expected_sections if s not in text_lower]
    audit.stats["synthesis_sections_found"] = found

    if missing and audit.status == "live":
        audit.issues.append(Issue("warning", "quality",
                                  f"synthesis.md missing sections: {', '.join(missing)}"))

    # Synthesis score: word depth (50%) + section coverage (30%) + brain-atoms.json synthesis (20%)
    # Word depth: 0 = 0, 500 = 0.5, 1500+ = 1.0
    word_score = min(1.0, word_count / 1500.0)
    section_score = found / len(expected_sections)

    # Check brain-atoms.json synthesis section presence
    atoms_path = brain_dir / "pack" / "brain-atoms.json"
    atoms_syn_score = 0.0
    if atoms_path.exists():
        try:
            with open(atoms_path) as f:
                data = json.load(f)
            syn = data.get("synthesis", {})
            if syn:
                syn_keys = ["first_principles", "thinking_patterns", "contrarian_positions",
                            "does_not_believe", "would_not_say", "biography", "skills"]
                present = sum(1 for k in syn_keys if syn.get(k))
                atoms_syn_score = present / len(syn_keys)
        except Exception:
            pass

    audit.scores["synthesis"] = (word_score * 0.5) + (section_score * 0.3) + (atoms_syn_score * 0.2)


def check_brain_context_md(brain_dir: Path, audit: BrainAudit):
    """Basic checks on the LLM context file."""
    ctx_path = brain_dir / "pack" / "brain-context.md"
    if not ctx_path.exists():
        return

    text = ctx_path.read_text(encoding="utf-8", errors="ignore")
    size_kb = len(text.encode("utf-8")) / 1024
    audit.stats["brain_context_size_kb"] = round(size_kb, 1)

    if size_kb < 5:
        audit.issues.append(Issue("warning", "quality",
                                  f"brain-context.md is only {size_kb:.0f}KB — seems too small"))

    if "## How" not in text and "first principles" not in text.lower():
        audit.issues.append(Issue("info", "quality",
                                  "brain-context.md may be missing synthesis section"))

    # Synthesis section coverage. synthesis.md is injected verbatim into
    # brain-context.md, but header level (##/###) and wording ("NOT"/"Not",
    # "Biographical Pattern"/"Biography") vary by brain — so we use
    # case-insensitive substring matches that tolerate both.
    text_lower = text.lower()
    required_ctx_sections = [
        ("first_principles", "first principles"),
        ("thinking_patterns", "thinking patterns"),
        ("contrarian_positions", "contrarian"),
        ("does_not_believe", "not believe"),
        ("would_not_say", "would not say"),
        ("biography", "biograph"),
    ]
    ctx_sections_found = 0
    for label, needle in required_ctx_sections:
        if needle in text_lower:
            ctx_sections_found += 1
        else:
            audit.issues.append(Issue("warning", "quality",
                                      f"brain-context.md missing synthesis section: {label}",
                                      f"Ensure synthesis.md has the section, then re-export",
                                      f"python3 scripts/export-brain.py --brain {audit.slug}"))
    audit.stats["brain_context_sections_found"] = ctx_sections_found

    atom_markers = text.count("**Atom")
    if atom_markers == 0:
        atom_markers = text.count("### ") + text.count("## Atom")
    audit.stats["brain_context_atom_markers"] = atom_markers


# ---------------------------------------------------------------------------
# Behavioral eval: read latest cached results from brains/{slug}/evals/
# ---------------------------------------------------------------------------


def load_latest_behavioral(slug: str) -> Optional[dict]:
    """Return the most recent results-YYYY-MM-DD.json payload, or None."""
    evals_dir = BRAINS_DIR / slug / "evals"
    if not evals_dir.exists():
        return None
    candidates = sorted(evals_dir.glob("results-*.json"))
    if not candidates:
        return None
    try:
        with open(candidates[-1]) as f:
            data = json.load(f)
    except Exception:
        return None
    agg = data.get("aggregate") or {}
    return {
        "source": str(candidates[-1].relative_to(BRAINS_DIR.parent)),
        "timestamp": data.get("timestamp"),
        "runner_model": data.get("runner_model"),
        "judge_model": data.get("judge_model"),
        "behavioral_score": agg.get("behavioral_score", 0),
        "pass_rate": agg.get("pass_rate", 0.0),
        "adversarial_violations": agg.get("adversarial_violations", 0),
        "prompts_evaluated": agg.get("prompts_evaluated", 0),
        "dimensions": agg.get("dimensions", {}),
    }


# ---------------------------------------------------------------------------
# Main audit runner
# ---------------------------------------------------------------------------

def audit_brain(slug: str, index_data: dict, with_behavioral: bool = False) -> BrainAudit:
    """Run all checks on a single brain."""
    entry = next((b for b in index_data.get("brains", []) if b["slug"] == slug), None)
    name = entry["name"] if entry else slug
    status = entry["status"] if entry else "unknown"

    audit = BrainAudit(slug=slug, name=name, status=status)
    brain_dir = BRAINS_DIR / slug

    check_directory_structure(brain_dir, audit)
    check_brain_json_schema(brain_dir, audit)
    check_pack_data(brain_dir, audit)
    check_temporal_density(brain_dir, audit)
    check_quote_provenance(brain_dir, audit)
    check_synthesis_grounding(brain_dir, audit)
    check_template_variables(brain_dir, audit)
    check_index_consistency(index_data, brain_dir, audit)
    check_explore_html(brain_dir, audit)
    check_synthesis_md(brain_dir, audit)
    check_brain_context_md(brain_dir, audit)

    if with_behavioral:
        audit.behavioral = load_latest_behavioral(slug)

    return audit


# ---------------------------------------------------------------------------
# Output: human-readable report
# ---------------------------------------------------------------------------

def print_report(audits: list[BrainAudit], show_hints: bool = False, with_behavioral: bool = False):
    """Print a human-readable report with completeness scores."""
    total_errors = sum(len(a.errors) for a in audits)
    total_warnings = sum(len(a.warnings) for a in audits)
    all_passed = all(a.passed for a in audits)

    print()
    print("=" * 65)
    print("  BRAINSFOR — BRAIN PACK AUDIT")
    print("=" * 65)
    print()

    for audit in audits:
        score = audit.completeness_score
        status_badge = f"[{audit.status}]"
        grade = score_to_grade(score)
        print(f"  {grade}  {audit.name} {status_badge}  —  {score}/100")
        print(f"       {audit.slug}/")

        # Score breakdown
        print(f"       Scores: ", end="")
        parts = []
        for key, meta in SCORING_CRITERIA.items():
            raw = audit.scores.get(key, 0.0)
            weighted = round(raw * meta["weight"])
            parts.append(f"{meta['label']} {weighted}/{meta['weight']}")
        print(" | ".join(parts))

        # Key stats
        if audit.stats:
            stats_line = []
            if "atom_count" in audit.stats:
                stats_line.append(f"{audit.stats['atom_count']} atoms")
            if "actual_connections_refs" in audit.stats:
                stats_line.append(f"{audit.stats['actual_connections_refs']} conn refs")
            if "voice_enrichment_pct" in audit.stats:
                stats_line.append(f"{audit.stats['voice_enrichment_pct']}% voice")
            if "provenance_pct" in audit.stats:
                stats_line.append(f"{audit.stats['provenance_pct']}% verified")
            if "grounding_pct" in audit.stats:
                stats_line.append(f"{audit.stats['grounding_pct']}% grounded")
            if "orphan_pct" in audit.stats:
                stats_line.append(f"{audit.stats['orphan_pct']}% orphans")
            if "temporal_coverage_pct" in audit.stats:
                span = audit.stats.get("temporal_year_span", 0)
                ymin = audit.stats.get("temporal_year_min")
                ymax = audit.stats.get("temporal_year_max")
                year_range = f"{ymin}–{ymax}" if ymin and ymax else "n/a"
                supports = audit.stats.get("supports_evolve", False)
                evolve_tag = "✓ evolve" if supports else "✗ evolve"
                stats_line.append(
                    f"{audit.stats['temporal_coverage_pct']}% dated ({span}yr, {year_range}) {evolve_tag}"
                )
            if stats_line:
                print(f"       Stats:  {' | '.join(stats_line)}")

        # Behavioral (if --with-behavioral was requested)
        if with_behavioral:
            b = audit.behavioral
            if not b:
                print(f"       Behavioral: (no eval results — run: python3 scripts/eval-brains.py --brain {audit.slug})")
            else:
                bscore = b.get("behavioral_score", 0)
                prompts = b.get("prompts_evaluated", 0)
                pr = b.get("pass_rate", 0.0)
                vi = b.get("adversarial_violations", 0)
                ts = (b.get("timestamp") or "")[:10]
                print(f"       Behavioral: {bscore}/100  |  pass {pr:.0%}  |  adv violations {vi}  |  {prompts} prompts  |  {ts}")

        # Issues
        if not audit.issues:
            print(f"       No issues found.")
        else:
            for issue in sorted(audit.issues, key=lambda i: {"error": 0, "warning": 1, "info": 2}[i.severity]):
                severity_tag = {"error": "ERR ", "warning": "WARN", "info": "INFO"}[issue.severity]
                print(f"       [{severity_tag}] [{issue.category}] {issue.message}")
                if show_hints and issue.fix_hint:
                    print(f"              -> {issue.fix_hint}")
        print()

    # Summary
    print("-" * 65)
    brains_passed = sum(1 for a in audits if a.passed)
    avg_score = round(sum(a.completeness_score for a in audits) / len(audits)) if audits else 0
    print(f"  {brains_passed}/{len(audits)} brains passed | {total_errors} errors | {total_warnings} warnings | avg struct score: {avg_score}/100")

    # Behavioral summary if we were asked for it
    if with_behavioral:
        with_b = [a for a in audits if a.behavioral]
        missing_b = [a.slug for a in audits if not a.behavioral]
        if with_b:
            b_scores = [a.behavioral.get("behavioral_score", 0) for a in with_b]
            avg_b = round(sum(b_scores) / len(b_scores))
            total_viol = sum(a.behavioral.get("adversarial_violations", 0) for a in with_b)
            print(f"  Behavioral: {len(with_b)}/{len(audits)} brains evaluated | avg behavioral score: {avg_b}/100 | {total_viol} adversarial violations")
        if missing_b:
            print(f"  Brains without cached behavioral results: {', '.join(missing_b)}")
            print(f"  Run: python3 scripts/eval-brains.py --all")
    print()

    # Highest-impact improvement suggestion
    worst = min(audits, key=lambda a: a.completeness_score) if audits else None
    if worst and worst.completeness_score < 90:
        # Find the lowest-scoring criterion
        lowest_key = min(SCORING_CRITERIA.keys(), key=lambda k: worst.scores.get(k, 0.0))
        lowest_meta = SCORING_CRITERIA[lowest_key]
        lowest_raw = worst.scores.get(lowest_key, 0.0)
        print(f"  Biggest opportunity: {worst.name} → {lowest_meta['label']} ({round(lowest_raw * lowest_meta['weight'])}/{lowest_meta['weight']})")
        # Find the first fix command for that category
        for issue in worst.issues:
            if issue.fix_hint:
                print(f"  Next step: {issue.fix_hint}")
                break
        print()

    return 0 if all_passed else 1


def score_to_grade(score: int) -> str:
    """Convert score to a letter grade."""
    if score >= 90: return " A "
    if score >= 75: return " B "
    if score >= 60: return " C "
    if score >= 40: return " D "
    return " F "


# ---------------------------------------------------------------------------
# Output: JSON
# ---------------------------------------------------------------------------

def print_json(audits: list[BrainAudit]):
    """Print machine-readable JSON output."""
    output = {
        "brains": [],
        "summary": {
            "total": len(audits),
            "passed": sum(1 for a in audits if a.passed),
            "failed": sum(1 for a in audits if not a.passed),
            "total_errors": sum(len(a.errors) for a in audits),
            "total_warnings": sum(len(a.warnings) for a in audits),
            "avg_score": round(sum(a.completeness_score for a in audits) / len(audits)) if audits else 0,
        }
    }
    for audit in audits:
        brain_data = {
            "slug": audit.slug,
            "name": audit.name,
            "status": audit.status,
            "passed": audit.passed,
            "completeness_score": audit.completeness_score,
            "scores": {k: {"raw": round(audit.scores.get(k, 0.0), 3),
                           "weighted": round(audit.scores.get(k, 0.0) * SCORING_CRITERIA[k]["weight"]),
                           "max": SCORING_CRITERIA[k]["weight"],
                           "label": SCORING_CRITERIA[k]["label"]}
                       for k in SCORING_CRITERIA},
            "stats": audit.stats,
            "issues": [asdict(i) for i in audit.issues],
            "behavioral": audit.behavioral,
        }
        output["brains"].append(brain_data)
    print(json.dumps(output, indent=2))
    return 0 if output["summary"]["failed"] == 0 else 1


# ---------------------------------------------------------------------------
# Output: remediation script
# ---------------------------------------------------------------------------

def print_remediation(audits: list[BrainAudit]):
    """Generate a runnable shell script to fix issues."""
    print("#!/usr/bin/env bash")
    print("# Auto-generated remediation script from audit-brains.py --remediate")
    print(f"# Generated: $(date)")
    print(f"# Run from: brainsfor/ directory")
    print()
    print("set -e")
    print(f"cd {BRAINS_DIR.parent}")
    print()

    any_commands = False
    for audit in audits:
        commands = []
        seen = set()

        for issue in audit.issues:
            if issue.fix_command and issue.fix_command not in seen:
                commands.append((issue.severity, issue.message, issue.fix_command))
                seen.add(issue.fix_command)

        if commands:
            any_commands = True
            print(f"# === {audit.name} ({audit.slug}) — Score: {audit.completeness_score}/100 ===")
            print()

            # Deduplicate and order: structural fixes first, then enrichment
            structural = [(s, m, c) for s, m, c in commands if "rm -rf" in c or "mv " in c or "mkdir" in c]
            export = [(s, m, c) for s, m, c in commands if "export-brain" in c]
            enrich = [(s, m, c) for s, m, c in commands if "enrich-" in c]

            if structural:
                print(f"# -- Structural cleanup --")
                for sev, msg, cmd in structural:
                    print(f"# Fix: {msg}")
                    print(cmd)
                print()

            if export:
                print(f"# -- Re-export pack --")
                # Deduplicate to one export command
                export_cmd = export[0][2]
                print(f"# Fixes: {len(export)} issues")
                print(export_cmd)
                print()

            if enrich:
                print(f"# -- Enrichment (may take a while, requires API keys) --")
                for sev, msg, cmd in enrich:
                    print(f"# Fix: {msg}")
                    print(cmd)
                print()

    if not any_commands:
        print("# No automated fixes needed. All brains look good!")
        print()

    print("echo 'Remediation complete. Re-run: python3 scripts/audit-brains.py'")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Audit BrainsFor brain packs")
    parser.add_argument("--brain", help="Audit a specific brain by slug")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--fix-hints", action="store_true", help="Include remediation hints")
    parser.add_argument("--remediate", action="store_true", help="Generate fix script to stdout")
    parser.add_argument("--with-behavioral", action="store_true",
                        help="Include cached behavioral eval results (from scripts/eval-brains.py)")
    args = parser.parse_args()

    if not INDEX_FILE.exists():
        print(f"ERROR: {INDEX_FILE} not found. Run from the brainsfor/ directory.", file=sys.stderr)
        sys.exit(1)

    with open(INDEX_FILE) as f:
        index_data = json.load(f)

    if args.brain:
        slugs = [args.brain]
        known = [b["slug"] for b in index_data.get("brains", [])]
        if args.brain not in known:
            print(f"WARNING: '{args.brain}' not in index.json (known: {', '.join(known)})", file=sys.stderr)
    else:
        slugs = [b["slug"] for b in index_data.get("brains", [])]

    audits = [audit_brain(slug, index_data, with_behavioral=args.with_behavioral) for slug in slugs]

    if args.remediate:
        print_remediation(audits)
        sys.exit(0)
    elif args.json:
        exit_code = print_json(audits)
    else:
        exit_code = print_report(audits, show_hints=args.fix_hints, with_behavioral=args.with_behavioral)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
