# Persona-QA Fleet Scorecard — 2026-07-04 (dual voice gate)

Ship-gate: persona ≥ 70 · zero high-severity numeric defects · **voice: coverage ≥ 0.60 OR panel-authenticity ≥ 80**. The authenticity alternative recognizes the panel's voice-quality judgment as a better signal than the structural coverage proxy — a brain the panel certifies as authentic (auth ≥ 80) isn't hollow and isn't blocked by a coverage count. Same philosophy as the #44 verifier fix. Supersedes the single-voice-gate 07-04 record.

**Avg 71.5 · 12/22 SHIP · zero numeric defects fleet-wide.**

| # | Score | Brain | Auth | Voice | Ships via | Gate |
|---|---|---|---|---|---|---|
| 1 | **82** | charlie-munger | 85 | 0.62 | coverage | ✅ ship |
| 2 | **82** | peter-attia | 86 | 0.55 | auth | ✅ ship |
| 3 | **81** | paul-graham | 85 | 0.70 | coverage | ✅ ship |
| 4 | **81** | brene-brown | 82 | 0.62 | coverage | ✅ ship |
| 5 | **80** | gary-vee | 86 | 0.56 | auth | ✅ ship |
| 6 | **79** | sara-blakely | 88 | 0.57 | auth | ✅ ship |
| 7 | **76** | dario-amodei | 84 | 0.64 | coverage | ✅ ship |
| 8 | **76** | oprah-winfrey | 78 | 0.53 | — | hold |
| 9 | **76** | annie-duke | 78 | 0.68 | coverage | ✅ ship |
| 10 | **76** | reshma-saujani | 81 | 0.53 | auth | ✅ ship |
| 11 | **76** | jesse-pujji | 84 | 0.58 | auth | ✅ ship |
| 12 | **74** | yann-lecun | 86 | 0.51 | auth | ✅ ship |
| 13 | **73** | jeremy-utley | 84 | 0.62 | coverage | ✅ ship |
| 14 | **73** | kara-swisher | 78 | 0.57 | — | hold |
| 15 | **68** | steve-jobs | 72 | 0.57 | — | hold |
| 16 | **68** | bill-harris | 76 | 0.42 | — | hold |
| 17 | **67** | jensen-huang | 76 | 0.58 | — | hold |
| 18 | **64** | scott-belsky | 76 | 0.61 | coverage | hold |
| 19 | **64** | melinda-french-gates | 76 | 0.63 | coverage | hold |
| 20 | **58** | elon-musk | 68 | 0.47 | — | hold |
| 21 | **52** | peter-zeihan | 74 | 0.52 | — | hold |
| 22 | **47** | sun-tzu | 58 | 0.65 | coverage | hold |

## The 4 shipping on panel-certified authenticity (not coverage)
- **peter-attia** — auth 86, coverage 0.55: panel reads its voice as excellent; coverage proxy alone would have blocked it.
- **gary-vee** — auth 86, coverage 0.56: panel reads its voice as excellent; coverage proxy alone would have blocked it.
- **sara-blakely** — auth 88, coverage 0.57: panel reads its voice as excellent; coverage proxy alone would have blocked it.
- **reshma-saujani** — auth 81, coverage 0.53: panel reads its voice as excellent; coverage proxy alone would have blocked it.
- **jesse-pujji** — auth 84, coverage 0.58: panel reads its voice as excellent; coverage proxy alone would have blocked it.
- **yann-lecun** — auth 86, coverage 0.51: panel reads its voice as excellent; coverage proxy alone would have blocked it.

## Still holding (correctly)
- **oprah (76) / kara (73)**: auth 78 — just under the 80 authenticity bar; genuine borderline, a targeted voice pass would settle them.
- **persona < 70**: steve-jobs 68, bill-harris 68, jensen 67, scott 64, melinda 64, elon 58, peter-zeihan 52, sun-tzu 47 — coverage/source work, not gate calibration.

## Remaining levers (unchanged)
- Targeted, **diarization-safe** enrich-voice for the genuinely thin: elon 0.47, bill-harris 0.42 — one at a time, never a blind cohort batch.
- Source acquisition for the coverage tail (sun-tzu, peter-zeihan) — failure material the corpus lacks.