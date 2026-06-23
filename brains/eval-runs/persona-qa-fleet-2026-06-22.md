# Persona-QA Fleet Scorecard — 2026-06-22

Annie-chaired 4-judge persona panel (Opus 4.8) + numeric-claims verifier (Sonnet) across all 22 live brains, after fleet-wide Hard Lessons mining. Ship-gate: persona ≥ 70, zero high-severity numeric defects, voice ≥ 0.60.

**Avg 68.0 · 10/22 clear the ship-gate · QA cost ~$10.67 + mining ~$2.32.**

| # | Score | Brain | Conf | Auth/Rigor/Cover/Calib | NumDef | HardLessons | Gate |
|---|---|---|---|---|---|---|---|
| 1 | **82** | charlie-munger | high | 85/84/74/83 | 0 | 4 | ✅ ship |
| 2 | **82** | peter-attia | high | 86/82/78/83 | 0 | 4 | ✅ ship |
| 3 | **81** | paul-graham | high | 85/84/74/83 | 0 | 4 | ✅ ship |
| 4 | **81** | brene-brown | high | 82/82/81/80 | 0 | 4 | ✅ ship |
| 5 | **76** | dario-amodei | high | 84/81/64/78 | 0 | 4 | ✅ ship |
| 6 | **76** | annie-duke | high | 78/80/73/77 | 0 | 4 | ✅ ship |
| 7 | **76** | reshma-saujani | high | 81/76/72/74 | 0 | 4 | ✅ ship |
| 8 | **74** | yann-lecun | high | 86/82/48/80 | 0 | 4 | ✅ ship |
| 9 | **73** | jeremy-utley | medium | 84/68/62/70 | 0 | 4 | ✅ ship |
| 10 | **73** | kara-swisher | high | 78/76/64/72 | 0 | 4 | ✅ ship |
| 11 | **68** | steve-jobs | medium | 72/76/62/70 | 0 | 4 | hold |
| 12 | **68** | bill-harris | medium | 76/72/38/70 | 0 | 0 | hold |
| 13 | **67** | jensen-huang | high | 76/78/45/72 | 0 | 4 | hold |
| 14 | **64** | scott-belsky | medium | 76/68/44/71 | 0 | 4 | hold |
| 15 | **64** | gary-vee | high | 82/70/62/68 | 2 | 4 | hold |
| 16 | **64** | melinda-french-gates | high | 76/70/58/70 | 1 | 4 | hold |
| 17 | **62** | sara-blakely | medium | 78/64/58/60 | 1 | 4 | hold |
| 18 | **61** | jesse-pujji | medium | 68/58/52/59 | 1 | 3 | hold |
| 19 | **58** | oprah-winfrey | high | 74/64/72/70 | 2 | 4 | hold |
| 20 | **52** | peter-zeihan | high | 74/60/36/45 | 0 | 0 | hold |
| 21 | **47** | sun-tzu | medium | 58/56/38/52 | 0 | 0 | hold |
| 22 | **47** | elon-musk | high | 68/55/40/60 | 4 | 4 | hold |

## Ship-gate blockers (numeric defects — fix first)
- **elon-musk** — 4 high-severity numeric defect(s). Top fix: Ground or remove all flagged numeric claims — the ~$100M SpaceX figure, the $30-40M split, the $44B Twitter price, and the 100x/10x multipliers — sourced to ver
- **gary-vee** — 2 high-severity numeric defect(s). Top fix: Strip the invented '$20-40M asset being sold at half price' figure and the 'everyone calls it wasteful' framing from the Super Bowl contrarian position. Replace
- **oprah-winfrey** — 2 high-severity numeric defect(s). Top fix: Correct the load-bearing first principle to match the corpus: 'thousands of interviews' (not ~30,000) and the TWO-part question ('Did you hear me? Did what I sa
- **melinda-french-gates** — 1 high-severity numeric defect(s). Top fix: Remove or ground the $40M proposal-threshold claim in contrarian_positions[3]. Either cite a verifiable source for the specific dollar floor or rewrite it as th
- **sara-blakely** — 1 high-severity numeric defect(s). Top fix: 
- **jesse-pujji** — 1 high-severity numeric defect(s). Top fix: Verify and source the Ampush revenue and ad-spend figures before any other edit — confirm whether ~$30M revenue and $50–100M/yr managed spend are accurate, and 

## Hold — top fix per brain
- **steve-jobs** (68, hold): Strip the third-party-opinion and biographical-gossip atoms (Jandali Egypt tour, 'grown-up apartment,' Mueller on patents, Marfatia 'genius who blended') and replace with atoms tha
- **bill-harris** (68, rework): Populate HARD LESSONS with documented instances where Harris revised a position, ran a trial that didn't replicate, or was wrong about a mechanism — the LP(a) finding and any dose 
- **jensen-huang** (67, rework): 
- **scott-belsky** (64, rework): Purge the ~10 A24/Adobe departure-PR atoms (CMO quotes, 'team, strategy, pipeline has never been stronger,' 'eager to get to work w/ my new partners') and replace with atoms that s
- **gary-vee** (64, hold): Strip the invented '$20-40M asset being sold at half price' figure and the 'everyone calls it wasteful' framing from the Super Bowl contrarian position. Replace with only what the 
- **melinda-french-gates** (64, hold): Remove or ground the $40M proposal-threshold claim in contrarian_positions[3]. Either cite a verifiable source for the specific dollar floor or rewrite it as the qualitative scale/
- **sara-blakely** (62, rework): 
- **jesse-pujji** (61, rework): Verify and source the Ampush revenue and ad-spend figures before any other edit — confirm whether ~$30M revenue and $50–100M/yr managed spend are accurate, and attach the citation 
- **oprah-winfrey** (58, rework): Correct the load-bearing first principle to match the corpus: 'thousands of interviews' (not ~30,000) and the TWO-part question ('Did you hear me? Did what I say mean anything?'), 
- **peter-zeihan** (52, rework): Populate HARD LESSONS with the documented mis-timed forecasts: the 2010 'China collapses this coming decade' call that did not arrive on its original timeline, the serially moved g
- **sun-tzu** (47, hold): Re-source the contaminated atoms: either re-derive them from Sun Tzu's own text or explicitly label them as 'application by later strategist' so commentary is never presented as th
- **elon-musk** (47, rework): Ground or remove all flagged numeric claims — the ~$100M SpaceX figure, the $30-40M split, the $44B Twitter price, and the 100x/10x multipliers — sourced to verifiable receipts or 

## Honest `[]` (corpus carries no grounded failures — re-mine failure-heavy sources)
- sun-tzu, peter-zeihan, bill-harris