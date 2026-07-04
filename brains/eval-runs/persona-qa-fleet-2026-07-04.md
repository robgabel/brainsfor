# Persona-QA Fleet Scorecard — 2026-07-04

Refresh after: #44 verifier root-cause fix + corpus-aligned data fixes, #47/#50 elon attribution audit, hard-lessons export into packs, re-panel of the 5 content-fixed brains (Opus 4.8 panel, Sonnet-5-era pipeline). Supersedes persona-qa-fleet-2026-06-22.md.

**Avg 71.6 · 6/22 clear the full ship-gate · 14/22 pass persona ≥70 · numeric defects: ZERO fleet-wide.**

**The remaining lever is voice enrichment**: gary-vee (80), sara-blakely (79), oprah (76), jesse (74) all pass persona and are blocked ONLY by voice < 0.60.

| # | Score | (date) | Brain | Auth/Rigor/Cover/Calib | Voice | NumDef | Gate |
|---|---|---|---|---|---|---|---|
| 1 | **82** | 2026-06-22 | charlie-munger | 85/84/74/83 | 0.62 | 0 | ✅ ship |
| 2 | **82** | 2026-06-22 | peter-attia | 86/82/78/83 | 0.55 | 0 | hold |
| 3 | **81** | 2026-06-22 | paul-graham | 85/84/74/83 | 0.70 | 0 | ✅ ship |
| 4 | **81** | 2026-06-22 | brene-brown | 82/82/81/80 | 0.62 | 0 | ✅ ship |
| 5 | **80** | 2026-07-04 | gary-vee | 86/76/78/79 | 0.56 | 0 | hold |
| 6 | **79** | 2026-07-04 | sara-blakely | 88/76/72/80 | 0.57 | 0 | hold |
| 7 | **76** | 2026-06-22 | dario-amodei | 84/81/64/78 | 0.64 | 0 | ✅ ship |
| 8 | **76** | 2026-07-04 | oprah-winfrey | 78/74/78/77 | 0.53 | 0 | hold |
| 9 | **76** | 2026-06-22 | annie-duke | 78/80/73/77 | 0.68 | 0 | ✅ ship |
| 10 | **76** | 2026-06-22 | reshma-saujani | 81/76/72/74 | 0.53 | 0 | hold |
| 11 | **74** | 2026-06-22 | yann-lecun | 86/82/48/80 | 0.51 | 0 | hold |
| 12 | **74** | 2026-07-04 | jesse-pujji | 82/72/62/76 | 0.56 | 0 | hold |
| 13 | **73** | 2026-06-22 | jeremy-utley | 84/68/62/70 | 0.62 | 0 | ✅ ship |
| 14 | **73** | 2026-06-22 | kara-swisher | 78/76/64/72 | 0.57 | 0 | hold |
| 15 | **68** | 2026-06-22 | steve-jobs | 72/76/62/70 | 0.57 | 0 | hold |
| 16 | **68** | 2026-06-22 | bill-harris | 76/72/38/70 | 0.42 | 0 | hold |
| 17 | **67** | 2026-06-22 | jensen-huang | 76/78/45/72 | 0.58 | 0 | hold |
| 18 | **64** | 2026-06-22 | scott-belsky | 76/68/44/71 | 0.61 | 0 | hold |
| 19 | **64** | 2026-06-22 | melinda-french-gates | 76/70/58/70 | 0.63 | 0 | hold |
| 20 | **63** | 2026-07-04 | elon-musk | 76/72/40/68 | 0.47 | 0 | hold |
| 21 | **52** | 2026-06-22 | peter-zeihan | 74/60/36/45 | 0.52 | 0 | hold |
| 22 | **47** | 2026-06-22 | sun-tzu | 58/56/38/52 | 0.65 | 0 | hold |

## Notes
- **annie-duke**: a 'de-resolve the hard lessons' experiment (from a parallel session's finding) was tried and REVERTED — the Opus panel scored the de-resolved version 68 (auth 78→64) vs canonical 76. Negative result recorded; canonical lessons stand.
- **elon-musk**: 63 (flat). Numeric clean + attribution audited (#47/#50); real blockers are coverage 40 (the mess-free highlight reel) and voice 0.47 — both Phase-C/source work.
- Evolve flags recomputed against current packs (20 changes; oprah/kara/brene et al. now honestly False below the 50%-dated bar).