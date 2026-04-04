---
name: debate
description: "Stress-test your thinking from Belsky's worldview. Provocative counterarguments grounded in his actual beliefs."
---

# 🔥 /debate — Steel-Man Both Sides

Present a position or belief, and Belsky's brain will argue against it—not with generic objections, but with specific, provocative counterarguments grounded in his actual thinking.

## How It Works

When you invoke `/debate`, the skill will:

1. **Parse your position** — Understand the claim or belief you're testing
2. **Find Belsky's atoms that challenge it** — Search for contradictions, limitations, or alternative views in his thinking
3. **Construct the counterargument** — Build a strong opposing position using his specific frameworks and evidence
4. **Present both sides** — Show your reasoning AND his objection with equal force
5. **Identify the tension** — Highlight what's at stake in this disagreement
6. **Suggest resolution paths** — Point toward skills that help reconcile the tension (e.g., `/apply` to find nuance, `/brainfight` to explore deeper)

## Best For

- Challenging your own assumptions before major decisions
- Understanding why a position might be wrong (or incomplete)
- Finding blind spots in your thinking
- Preparing for resistance or criticism
- Sharpening your original thesis

## Examples

**Example 1: Challenge a Business Assumption**
```
/debate

My strategy is to build a platform for creators. I think network effects and community
lock-in will be my competitive advantage. How would Scott disagree?
```

Expected output:
- ✅ **Your Position:** [1-sentence summary]
- 🔥 **Belsky's Counterargument:** [2-3 sentences using his atoms about creator economy, meaning economy, authenticity]
- 📌 **His Evidence:** [2-3 atoms that support this objection]
- 🤔 **What's Actually True?** [The nuance—where you're both right]
- 💡 **Try next:** `/apply` (to integrate the insight) or `/brainfight` (to explore deeper)

**Example 2: Challenge a Leadership Approach**
```
/debate

I believe that as a company scales, we need to implement formal processes and
functional structure to stay organized. Is there anything in Scott's thinking
that contradicts this?
```

Expected output:
- ✅ **Your Position:** [summary]
- 🔥 **Belsky's Counterargument:** [his objection grounded in atoms about adaptability, organizational design, scaling]
- 📌 **His Evidence:** [cite atoms about adaptive challenges, playbooks, and functional vs. project structure]
- 🤔 **Where the Tension Lives:** [acknowledging both sides are partly right]
- 💡 **Try next:** `/apply` (to find the right balance) or `/connect` (to find synthesis)

**Example 3: Challenge a Market Belief**
```
/debate

I think the future is about big companies with AI doing more with less people.
Scott seems optimistic about small, craft-focused businesses. How does he
argue against my view?
```

Expected output:
- ✅ **Your Position:** [summary]
- 🔥 **Belsky's Counterargument:** [atoms about authenticity, human craft, consumer demand, meaning economy]
- 📌 **His Evidence:** [atoms about artisanal premium, scarcity, consumer trust]
- 🤔 **The Real Picture:** [both trends are real—how do they coexist?]
- 💡 **Try next:** `/brainfight` (to pit these ideas against each other) or `/deep-dive` (to explore fully)

## Output Format

Always use this structure:

```
✅ **Your Position**
[1-2 sentence summary of what you believe]

🔥 **Belsky's Counterargument**
[2-3 sentences articulating the opposing view, using his language and frameworks]

📌 **His Evidence**
1. "[Atom 1]" — *[Topic], [Source Date]*
2. "[Atom 2]" — *[Topic], [Source Date]*
3. "[Atom 3]" — *[Topic], [Source Date]*

🤔 **What's Actually True?**
[1-2 sentences acknowledging nuance—both views have merit under different conditions]

⚡ **The Tension**
[1 sentence naming the core disagreement or tradeoff]

💡 **Try next:** `/brainfight` (to explore the debate fully) or `/apply` (to find practical synthesis)
```

## Rules for LLM Behavior

1. **Use his atoms, not generic counterarguments** — The debate should feel specific to Belsky's thinking, not a generic objection
2. **Be provocative but fair** — Make the strongest case against the user's position without strawmanning them
3. **Ground in his actual beliefs** — If atoms don't support a counterargument, don't invent one
4. **Acknowledge nuance** — This isn't about proving the user wrong; it's about sharpening both sides
5. **Flag when the brain is silent** — If Belsky's thinking doesn't directly address this topic, say so

## Data Source

- **atoms:** brain-atoms.json (284 total)
- **context:** brain-context.md (topic clusters for cross-referencing)
- **strategy:** Look for atoms tagged with opposing topics to find natural counterarguments
