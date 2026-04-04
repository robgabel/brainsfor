---
name: brainfight
description: "Head-to-head comparison of ideas. Pit two concepts against each other and discover where they agree, contradict, and diverge."
---

# ⚔️ /brainfight — Ideas in Conflict

Pit two ideas, frameworks, or positions head-to-head. Discover where they agree, where they conflict, and what's at stake in the disagreement.

## How It Works

When you invoke `/brainfight`, the skill will:

1. **Parse both ideas** — Understand the two concepts you want to compare
2. **Find atoms for both** — Locate all atoms that support, explain, or relate to each idea
3. **Identify overlaps** — Show where they agree or complement each other
4. **Surface contradictions** — Highlight where they genuinely conflict
5. **Name the tension** — Articulate what's actually at stake in the disagreement
6. **Declare a winner (conditionally)** — Based on the context YOU provide, which idea wins under what conditions?
7. **Suggest resolution** — Offer paths to reconcile or choose between them

## Best For

- Understanding nuance in strategic tradeoffs (e.g., innovation vs. efficiency)
- Testing your own position against an alternative
- Preparing arguments for presentations or debates
- Finding where two ideas might actually be complementary
- Settling a team disagreement by grounding both sides in research
- Discovering conditions under which one approach beats the other

## Examples

**Example 1: Strategic Tradeoff**
```
/brainfight

Scott seems to believe in both "scaling through AI automation" and "building meaning
through craft and human connection." Aren't these in conflict? How does he reconcile them?
```

Expected output:
- ⚔️ **Brainfight: "AI Automation" vs. "Human Craft"**
- 📌 **Team A: Automation & Scaling**
  - Atoms supporting this position
  - Core thesis
- 📌 **Team B: Craft & Meaning**
  - Atoms supporting this position
  - Core thesis
- 🤝 **Where They Agree:**
  - [Shared principles both embrace]
- 💥 **Where They Conflict:**
  - [Genuine tradeoff #1]
  - [Genuine tradeoff #2]
- 🧠 **The Real Insight:**
  - [How Belsky reconciles them, or under what conditions each wins]
- 🏆 **Winner Conditions:**
  - [When automation wins]
  - [When craft wins]
- 💡 **Try next:** `/connect` (find synthesis) or `/apply` (use this in your strategy)

**Example 2: Platform Strategy Decision**
```
/brainfight

Enterprise software (big contracts, predictable revenue) vs. creator tools
(network effects, meaning, but unpredictable). Which path would Scott recommend?
```

Expected output:
- ⚔️ **Brainfight: "Enterprise" vs. "Creator"**
- 📌 **Team A: Enterprise Strategy**
  - [Atoms from intent-driven AI, scale, organizational design]
  - Core rationale
- 📌 **Team B: Creator Strategy**
  - [Atoms from meaning economy, authenticity, small craft businesses]
  - Core rationale
- 🤝 **Where They Agree:**
  - [Both value clarity, both work with current trends]
- 💥 **Where They Conflict:**
  - [Enterprise demands scale; creators demand meaning]
  - [Different hiring, culture, metrics]
- 🏆 **Belsky's Likely Take:**
  - [Which way his thinking leans, and why]
  - [Conditions under which the other approach could win]
- 💡 **Try next:** `/apply` (use his logic to make your choice) or `/deep-dive` (explore both paths fully)

**Example 3: Organizational Design**
```
/brainfight

Should my organization be highly structured and process-driven to scale reliably,
or adaptive and loosely coupled to stay innovative? Scott's thinking seems to favor
the second, but is that always right?
```

Expected output:
- ⚔️ **Brainfight: "Process" vs. "Adaptability"**
- 📌 **Team A: Structured & Scalable**
  - [Atoms on what happens when orgs grow]
  - Thesis: clear processes enable faster hiring and coordination
- 📌 **Team B: Adaptive & Loose**
  - [Atoms on adaptive challenges, organizational agility]
  - Thesis: flexibility enables innovation and responsive culture
- 🤝 **Where They Agree:**
  - [Both care about sustainable growth]
  - [Both acknowledge tradeoffs]
- 💥 **Where They Conflict:**
  - [Processes slow innovation]
  - [Adaptability creates coordination costs]
- 🏆 **Context Matters:**
  - [When structure wins: regulated industries, global scale, coordination at 500+]
  - [When adaptability wins: fast-moving markets, small teams, survival mode]
- 💡 **Try next:** `/apply` (design your hybrid model) or `/teach` (understand organizational design fully)

## Output Format

Always use this structure:

```
⚔️ **Brainfight: "[Idea A]" vs. "[Idea B]"**

📌 **Team A: [Idea A]**
[2-3 sentences on core thesis + atoms supporting it]
*Key Atoms: [1-2 atom summaries]*

📌 **Team B: [Idea B]**
[2-3 sentences on core thesis + atoms supporting it]
*Key Atoms: [1-2 atom summaries]*

🤝 **Where They Agree**
- [Common ground 1]
- [Common ground 2]

💥 **Where They Conflict**
- **Conflict 1:** [Tradeoff 1]
- **Conflict 2:** [Tradeoff 2]

🏆 **Who Wins?**
- [Belsky's likely lean, or which context favors which approach]
- **Team A wins when:** [conditions]
- **Team B wins when:** [conditions]

🧠 **The Actual Truth**
[1-2 sentences on the nuance—how both are right in different contexts]

💡 **Try next:** `/mashup` (synthesize a hybrid) or `/apply` (resolve the choice in your context)
```

## Rules for LLM Behavior

1. **Give both sides equal strength** — Steel-man both positions; don't strawman
2. **Ground in atoms** — Every argument should reference supporting atoms
3. **Find real tensions** — Not just different angles, but genuine tradeoffs where one hurts the other
4. **Acknowledge nuance** — Almost always, both are right under different conditions
5. **Use Belsky's language** — If he uses specific terms ("adaptive challenges," "meaning economy"), use them
6. **Suggest resolution** — Either `/mashup` (find synthesis) or `/apply` (make the choice in your context)

## Data Source

- **atoms:** brain-atoms.json (284 total)
- **context:** brain-context.md (topic clusters and thematic groupings)
- **method:** Find atoms supporting both positions; identify where they contradict; use Belsky's broader thinking to hint at his likely reconciliation
