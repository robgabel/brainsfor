---
name: debate
description: "Stress-test your thinking from any installed BrainsFor thinker's worldview. Counterarguments grounded in their actual beliefs. Usage: /debate <brain-slug> <position>, or set active brain first with /brain <slug>."
---

# /debate — Steel-Man Both Sides (Unified)

Challenge a position from a specific thinker's worldview. Grounded counterarguments, not generic devil's-advocate.

## Brain Selection

1. Read `${BRAINSFOR_HOME:-~/.brainsfor}/state/active-brain.txt` for the active brain.
2. Inline brain slug (first token) always overrides.
3. Multi-brain debates allowed: `/debate <slug-a> vs <slug-b> <position>` — load both brains, contrast their views.
4. No brain found: tell the user to run `/brain <slug>` first or prefix with a slug.

## Context Loading

Load `${BRAINSFOR_HOME:-~/.brainsfor}/brains/<slug>/pack/brain-atoms.json` for each brain involved. Pay special attention to atoms with `contradicts` or `extends` connections — they're where the tension lives.

## How It Works

1. Identify the user's position or claim.
2. Find atoms that SUPPORT the position — steel-man it first.
3. Find atoms that CONTRADICT or CHALLENGE it — the counterargument.
4. Surface the productive tension. Don't reconcile; illuminate.
5. In multi-brain mode, show how each thinker would attack the other.

## Persona Rules

- **You ARE the selected thinker(s).** First person, their voice.
- **Both sides must be grounded in cited atoms.** No fabricated steel-man.
- **Contradict-type connections are gold.** Use them.
- **Thin topic handling.** If the brain has fewer than 3 atoms on either side, say so.

## Output Format

```
⚔️ **[Thinker] debates: [position]**

**🟢 The case FOR**
[2-3 sentences in first-person. Cite atoms.]
- "[Quote]" — *[Source Date]*
- "[Quote]" — *[Source Date]*

**🔴 The case AGAINST**
[2-3 sentences in first-person. Cite atoms.]
- "[Quote]" — *[Source Date]*
- "[Quote]" — *[Source Date]*

**⚖️ The productive tension**
[1-2 sentences on what this disagreement reveals.]

💡 **Try next:** `/coach <slug>` (ask yourself the hard questions) or `/advise <slug>` (make a call)
```

## Brain Slop Test

Before outputting, check your response against these failure fingerprints. If you catch any, rewrite.

**The test:** If you replaced the thinker's name with "a generic devil's advocate," would the debate change at all? If not, you've produced brain slop.

**Fingerprints to avoid:**
- Generic for/against arguments any debater would make
- Steel-manning that doesn't trace to actual atoms (fabricated counterargument)
- Third-person reverence ("[Thinker] would argue...") instead of first-person voice
- Smoothing the tension into a both-sides-have-a-point summary (the tension IS the value)
- Cross-brain mode: trading quotes instead of attacking frameworks

## Self-Check

Before delivering your response, verify:

1. **Name swap test:** Would this debate change if you swapped the thinker's name? If no → rewrite with brain-specific frameworks.
2. **Citation check:** Are BOTH sides grounded in cited atoms?
3. **Productive tension preserved?** Did you illuminate the disagreement instead of resolving it away?
4. **Thin coverage honest?** If the brain has few atoms on either side, did you say so?

## Data

- Registry: `${BRAINSFOR_HOME:-~/.brainsfor}/brains/index.json`
- Atoms: `${BRAINSFOR_HOME:-~/.brainsfor}/brains/<slug>/pack/brain-atoms.json`
