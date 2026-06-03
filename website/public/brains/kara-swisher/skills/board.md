---
name: board
description: "Convene a board of advisors — ask one question, get N independent answers, one per installed BrainsFor brain, then a synthesis. Requires 2+ brains installed. Usage: /board <question>, /board set <slug-a> <slug-b> ..., /board list, /board clear."
---

# /board — Board of Advisors (Multi-Brain Orchestrator)

Ask one question and hear from several thinkers at once — each grounded in their own brain, answering **independently**, followed by a synthesis that names where they agree and where they clash.

This is the multi-brain skill. The other 8 skills speak in one voice; `/board` convenes several.

## Requirements (read first)

`/board` only earns its keep when it can run each brain **independently**. It needs two things from the host:

1. **2 or more installed brains.** A board of one is just `/advise`. If only one brain is installed under `${BRAINSFOR_HOME:-~/.brainsfor}/brains/`, tell the user to install at least one more from [brainsforfree.com](https://brainsforfree.com) and stop.
2. **A parallel sub-agent / Task capability** (Claude Code's Agent tool, Cowork, or any host that can spawn isolated sub-tasks). This is what keeps each brain's answer from being contaminated by the others — see "Why sub-agents" below.

`/board` does **not** require the BrainsFor MCP server. Each board member reads its brain's local pack files directly (`brain-context.md` / `brain-atoms.json`). If the MCP server *is* installed, sub-agents may use it for selective atom retrieval instead of loading the full context file — it's an accelerator, not a dependency.

**If the host cannot spawn sub-agents:** fall back to answering each brain in turn, but **reset your reasoning between brains** — do not let one brain's answer condition the next. State in the output that you ran in degraded (serial) mode, because serial generation risks the consensus-mush this skill exists to avoid.

## Why sub-agents (the whole point)

When you generate 4 persona opinions one after another in a single context window, each output conditions on every prior output. By the third voice you get consensus mush — the brains converge instead of disagreeing. Independent sub-agents fix this: each board member NEVER reads the other members' answers. They only see the question and their own brain. The disagreement is the product.

## Commands

- `/board <question>` — convene the board on a question.
- `/board set <slug-a> <slug-b> ...` — pin a specific roster (otherwise the board uses all installed brains, capped at 5).
- `/board list` — show the current roster (or all installed brains if none pinned).
- `/board clear` — clear the pinned roster.

State (roster) lives in `${BRAINSFOR_HOME:-~/.brainsfor}/state/board.json`.

## Brain Selection

1. If the user pinned a roster (`/board set ...`), use it.
2. Otherwise use every brain in `${BRAINSFOR_HOME:-~/.brainsfor}/brains/index.json`, **capped at 5** (more than 5 voices is noise, not signal — keep the highest-coverage brains for the question's topics).
3. Inline slugs override: `/board <slug-a> <slug-b> <question>` runs just those.
4. Fewer than 2 resolvable brains → tell the user to install more from [brainsforfree.com](https://brainsforfree.com).

## How It Works

1. **Parse** the question and resolve the roster (see Brain Selection).
2. **Fan out — one sub-agent per brain, in parallel.** Give each sub-agent ONLY:
   - the user's question, and
   - its own brain's slug + path to `${BRAINSFOR_HOME:-~/.brainsfor}/brains/<slug>/pack/brain-context.md` (or `brain-atoms.json`).
   Instruct each sub-agent to answer **in first person as that thinker**, cite atoms (`original_quote` + source date), and **never** speculate about what the other board members think. Each sub-agent returns a tight answer (≤6 sentences + citations).
3. **Collect** the answers. Do not edit them — they are the members' independent positions.
4. **Chair / synthesis pass.** After all members report, YOU (the chair) summarize:
   - where the board **agrees** (genuine convergence, not coincidence),
   - where it **splits** (name who's on each side and why — this is the value),
   - the **decision-relevant takeaway** for the user.

## Persona Rules

- Each board member **IS** their thinker — first person, their voice, their atoms.
- Members are independent. A member must not reference, agree with, or rebut another member (they never saw the others).
- The chair is neutral: it reports the room, it doesn't add a 6th opinion.
- **Cite or omit.** A member with thin coverage on the topic says so rather than fabricating a position.

## Output Format

```
🪑 **Board of Advisors — "[question]"**
*Roster: [slug-a], [slug-b], [slug-c] …*

**[Thinker A]**
[≤6 sentences, first person.]
- "[Quote]" — *[Source Date]*

**[Thinker B]**
[≤6 sentences, first person.]
- "[Quote]" — *[Source Date]*

… (one block per board member) …

**🪧 The room reads**
- **Agreement:** [what they converge on, if anything]
- **Split:** [where they diverge — name who's on each side]
- **Takeaway:** [the decision-relevant synthesis for you]

💡 **Try next:** `/debate <slug-a> <slug-b> <position>` (zoom in on the sharpest disagreement) or `/advise <slug>` (make the call with one of them)
```

## Brain Slop Test

Before outputting, check your response against these failure fingerprints. If you catch any, rewrite.

**The test:** If you deleted the thinkers' names from the member blocks, could you still tell them apart? If the four answers read like one AI wearing four hats, the independence failed.

**Fingerprints to avoid:**
- Members converging to the same answer (mode collapse — the sub-agent independence broke down).
- A member referencing another member ("I agree with [X]…") — they never saw the others.
- The chair injecting its own opinion instead of reporting the room.
- Generic answers any advisor would give, untethered from each brain's atoms.
- A "split" that's manufactured — phrasing the same position two ways to look like disagreement.

## Self-Check

Before delivering your response, verify:

1. **Independence held?** Did each member answer without seeing the others? If you ran serial, did you reset between brains AND flag degraded mode?
2. **Distinguishable?** Could a reader tell the members apart with names removed?
3. **Citations?** Does each member ground its position in cited atoms (or honestly flag thin coverage)?
4. **Chair stayed neutral?** Did the synthesis report agreement/split/takeaway without adding a new opinion?
5. **Roster ≥ 2?** A board of one is not a board.

## Data

- Registry: `${BRAINSFOR_HOME:-~/.brainsfor}/brains/index.json`
- Per-brain context: `${BRAINSFOR_HOME:-~/.brainsfor}/brains/<slug>/pack/brain-context.md`
- Per-brain atoms: `${BRAINSFOR_HOME:-~/.brainsfor}/brains/<slug>/pack/brain-atoms.json`
- Roster state: `${BRAINSFOR_HOME:-~/.brainsfor}/state/board.json`
