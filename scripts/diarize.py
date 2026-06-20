"""
diarize.py — speaker diarization + subject attribution for transcript/interview sources.

SYSTEMIC across the BrainsFor pipeline (local desktop builds AND the remote
GitHub Action run the same scripts/). Used by both extraction points so that
`original_quote` atoms are attributed ONLY to the brain subject, never the
interviewer/host:
  - build-brain.decompose_transcript       (YouTube / audio transcripts)
  - auto-build-brain.extract_atoms_from_text (Firecrawl-scraped text sources)

Waterfall — cheapest first, graceful fallback at every step:
  1. NAMED — transcript already carries "Name:" speaker labels (e.g. Mixergy,
            many podcast transcript pages). Parse, keep only the subject's turns.
            Free, deterministic, no API.
  2. LLM  — unlabeled transcript from an interview-type source. A fast model
            (Haiku) splits speakers and returns only the subject's words. Cheap.
  3. STT  — audio URL + ASSEMBLYAI_API_KEY. Diarizing speech-to-text on the
            (non-IP-blocked) podcast audio. Optional vendor; no key => skipped.
  4. NONE — no signal (single-author essay, no client, etc.). Return text
            unchanged. Back-compatible: behaves exactly as the pipeline did
            before diarization existed.

Nothing here raises on failure — every tier degrades to the next, and the final
fallback is "return the text as-is", so adding this module can never break a build.
"""

import os
import re
import time

# Source types that are multi-speaker by nature and worth LLM diarization when
# they arrive unlabeled. Single-author essays/profiles are NOT in this set, so
# they never pay for an LLM diarization pass.
INTERVIEW_TYPES = {"interview", "podcast", "video", "transcript", "conversation", "fireside"}

# Minimum structure required before we trust "Name:" labels as real diarization.
_MIN_TURNS = 4
_MIN_SPEAKERS = 2

# Speaker label at the start of a line: 1-4 capitalized words then a colon.
# e.g. "Jesse Pujji:", "Andrew Warner:", "Patrick:", "Dr. Bill Harris:"
_SPEAKER_RE = re.compile(
    r"(?:^|\n)\s*([A-Z][A-Za-z.''\-]+(?:\s+[A-Z][A-Za-z.''\-]+){0,3})\s*:\s",
)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


def _tokens(s: str):
    return [t for t in re.split(r"\s+", (s or "").strip()) if t]


# --------------------------------------------------------------------------- #
# Tier 1: named-speaker parsing (free, deterministic)
# --------------------------------------------------------------------------- #
def parse_named_turns(text: str):
    """Parse a transcript with "Name:" speaker labels into [(speaker, text), ...].

    Returns [] when the text doesn't look diarized (fewer than _MIN_TURNS labeled
    turns or fewer than _MIN_SPEAKERS distinct speakers)."""
    if not text:
        return []
    matches = list(_SPEAKER_RE.finditer(text))
    if len(matches) < _MIN_TURNS:
        return []
    turns = []
    for i, m in enumerate(matches):
        speaker = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            turns.append((speaker, body))
    speakers = {_norm(s) for s, _ in turns}
    # Guard against false positives like "Note:" / "Summary:" by requiring at
    # least two distinct speaker labels actually carrying content.
    if len([s for s in speakers if s]) < _MIN_SPEAKERS:
        return []
    return turns


def match_subject(speakers, subject_name: str):
    """Pick which speaker label is the brain subject. Matches on full-name
    containment or shared surname. Returns the label string, or None."""
    subj_norm = _norm(subject_name)
    subj_tokens = [_norm(t) for t in _tokens(subject_name) if len(t) > 1]
    surname = subj_tokens[-1] if subj_tokens else ""
    best = None
    for sp in speakers:
        n = _norm(sp)
        if not n:
            continue
        # full name either way
        if n == subj_norm or n in subj_norm or subj_norm in n:
            return sp
        sp_tokens = [_norm(t) for t in _tokens(sp)]
        # shared surname (and not a one-letter coincidence)
        if surname and len(surname) > 2 and surname in sp_tokens:
            best = best or sp
    return best


def subject_text_from_named(text: str, subject_name: str):
    """If `text` is named-diarized and we can identify the subject, return the
    concatenation of ONLY the subject's turns. Otherwise None."""
    turns = parse_named_turns(text)
    if not turns:
        return None
    speakers = {s for s, _ in turns}
    subj = match_subject(speakers, subject_name)
    if not subj:
        return None
    subj_norm = _norm(subj)
    kept = [body for sp, body in turns if _norm(sp) == subj_norm]
    n_kept, n_other = len(kept), len(turns) - len(kept)
    if not kept:
        return None
    return "\n\n".join(kept), n_kept, n_other


# --------------------------------------------------------------------------- #
# Tier 2: LLM diarization (cheap, for unlabeled interview transcripts)
# --------------------------------------------------------------------------- #
_LLM_PROMPT = """The text below is part of an interview/conversation transcript. \
It contains {subject}'s words mixed with one or more OTHER speakers (interviewer/host). \
The transcript is NOT labeled by speaker.

Your job: output ONLY the sentences spoken by {subject}, verbatim, in order, \
concatenated into prose. Remove every sentence spoken by anyone else (questions, \
prompts, host commentary). Remove timestamps and filler markers. If you are not \
confident a sentence is {subject} speaking, leave it OUT.

Return ONLY {subject}'s words as plain text — no labels, no commentary, no JSON. \
If none of the text is clearly {subject} speaking, return an empty response.

TRANSCRIPT:
{chunk}"""


def _chunks(text: str, size: int):
    for i in range(0, len(text), size):
        yield text[i:i + size]


def llm_diarize(text: str, subject_name: str, client, model: str,
                max_chars: int = 60000, chunk_size: int = 14000):
    """Use a fast model to keep only the subject's spoken turns from an unlabeled
    transcript. Returns subject-only text, or None on total failure."""
    if not text or client is None:
        return None
    text = text[:max_chars]
    out = []
    try:
        for chunk in _chunks(text, chunk_size):
            prompt = _LLM_PROMPT.format(subject=subject_name, chunk=chunk)
            resp = client.messages.create(
                model=model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            piece = (resp.content[0].text or "").strip()
            if piece:
                out.append(piece)
    except Exception:
        return None
    joined = "\n\n".join(out).strip()
    return joined or None


# --------------------------------------------------------------------------- #
# Tier 3: diarizing speech-to-text (AssemblyAI) — optional, key-gated
# --------------------------------------------------------------------------- #
def transcribe_audio_diarized(audio_url: str, subject_name: str = "",
                              api_key: str = None, timeout: int = 900):
    """Diarizing STT via AssemblyAI on a (non-IP-blocked) audio URL — e.g. a
    podcast MP3. Returns subject-only text, or None if no key / failure.

    Identifies the subject as the speaker with the most spoken words (the guest
    in a typical host+guest interview). Best-effort; never raises."""
    api_key = api_key or os.environ.get("ASSEMBLYAI_API_KEY")
    if not api_key or not audio_url:
        return None
    try:
        import httpx
    except Exception:
        return None
    base = "https://api.assemblyai.com/v2"
    headers = {"authorization": api_key}
    try:
        with httpx.Client(timeout=60) as http:
            r = http.post(f"{base}/transcript", headers=headers,
                          json={"audio_url": audio_url, "speaker_labels": True})
            r.raise_for_status()
            tid = r.json()["id"]
            deadline = time.time() + timeout
            data = None
            while time.time() < deadline:
                pr = http.get(f"{base}/transcript/{tid}", headers=headers)
                pr.raise_for_status()
                data = pr.json()
                status = data.get("status")
                if status == "completed":
                    break
                if status == "error":
                    return None
                time.sleep(5)
            if not data or data.get("status") != "completed":
                return None
        utterances = data.get("utterances") or []
        if not utterances:
            return None
        # Speaker with the most words = the guest (subject) in a host+guest interview.
        words_by_speaker = {}
        for u in utterances:
            spk = u.get("speaker")
            words_by_speaker[spk] = words_by_speaker.get(spk, 0) + len((u.get("text") or "").split())
        if not words_by_speaker:
            return None
        subject_speaker = max(words_by_speaker, key=words_by_speaker.get)
        kept = [u.get("text", "") for u in utterances if u.get("speaker") == subject_speaker]
        joined = "\n\n".join(t for t in kept if t).strip()
        return joined or None
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------------- #
def to_subject_text(*, raw_text: str = None, audio_url: str = None,
                    subject_name: str, subject_first: str = None,
                    src_type: str = None, client=None, model: str = None,
                    assemblyai_key: str = None) -> dict:
    """Return only the brain subject's spoken words from an interview source,
    using the cheapest tier that works.

    Returns a dict:
      {"method": "named"|"llm"|"stt"|"none", "text": str, "diarized": bool,
       "subject_turns": int|None, "other_turns": int|None}

    `text` is always safe to use downstream — on the "none" path it is the
    original `raw_text` unchanged (or "" if only audio was given and STT failed)."""
    src_type = (src_type or "").lower()

    # Tier 1 — named labels (free). Always attempt on text.
    if raw_text:
        named = subject_text_from_named(raw_text, subject_name)
        if named:
            text, n_subj, n_other = named
            return {"method": "named", "text": text, "diarized": True,
                    "subject_turns": n_subj, "other_turns": n_other}

    # Tier 2 — LLM diarization, only for unlabeled interview-type sources.
    if raw_text and client and (src_type in INTERVIEW_TYPES):
        llm = llm_diarize(raw_text, subject_name, client, model or "")
        if llm:
            return {"method": "llm", "text": llm, "diarized": True,
                    "subject_turns": None, "other_turns": None}

    # Tier 3 — diarizing STT on audio (optional, key-gated).
    if audio_url:
        stt = transcribe_audio_diarized(audio_url, subject_name, assemblyai_key)
        if stt:
            return {"method": "stt", "text": stt, "diarized": True,
                    "subject_turns": None, "other_turns": None}

    # Tier 4 — passthrough (back-compatible).
    return {"method": "none", "text": raw_text or "", "diarized": False,
            "subject_turns": None, "other_turns": None}
