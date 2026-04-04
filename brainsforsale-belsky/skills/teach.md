---
name: teach
description: "Explain concepts using Scott Belsky's frameworks, language, and mental models. Learn through his lens."
---

# 🧠 /teach — Explain Like I'm Learning

Get a clear, accessible explanation of a concept as Scott Belsky would teach it, using his actual vocabulary, frameworks, and mental models.

## How It Works

When you invoke `/teach`, the skill will:

1. **Parse the concept** — Understand what you want to learn about
2. **Find Belsky's frameworks** — Locate atoms that break down this concept using his thinking
3. **Build explanation** — Structure a narrative that teaches the concept in his voice and language
4. **Use his vocabulary** — Reference his actual terms (e.g., "meaning economy," "adaptive challenges," "scaling without growing")
5. **Provide examples** — Show how he applies the concept to real situations
6. **Signal next learning** — Suggest which skill deepens understanding (e.g., `/deep-dive` for exhaustive coverage, `/evolve` for how his thinking developed)

## Best For

- Learning Belsky's core frameworks (originality, organizational design, AI agents, scaling)
- Understanding new concepts through his mental models
- Building intuition for how he thinks about a topic
- Getting unstuck on an idea that confuses you
- Teaching someone else using his language

## Examples

**Example 1: Explain a Framework**
```
/teach

Explain "scaling without growing" the way Scott talks about it.
```

Expected output:
- 🧠 **What Scott Means By "Scaling Without Growing"**
  - Definition grounded in his atoms
  - Why this distinction matters to him
  - How it differs from traditional scaling
- 📚 **His Key Insight**
  - Core principle in 1-2 sentences
- 🔍 **How He Applies It**
  - 2-3 concrete examples from atoms showing application
- 💡 **Try next:** `/deep-dive` (to explore all dimensions) or `/apply` (to use it in your situation)

**Example 2: Explain a Concept in Context**
```
/teach

Explain the "meaning economy" and why it matters in the age of AI.
```

Expected output:
- 🧠 **What the Meaning Economy Is**
  - Definition from Belsky's perspective
  - Why it's becoming more relevant (with AI context)
- 📚 **Core Principle**
  - His thesis in 1-2 sentences
- 🔍 **Implications**
  - 2-3 consequences or applications he identifies
- 💡 **Try next:** `/apply` (to apply to your creator/business) or `/brainfight` (to debate meaning vs. content)

**Example 3: Explain a Skill or Mindset**
```
/teach

Explain what Scott means by "adaptive leadership" and how it differs from strategic thinking.
```

Expected output:
- 🧠 **Adaptive Leadership (In Belsky's Words)**
  - Definition and core distinction
  - Why it matters during platform shifts
- 📚 **The Key Difference**
  - Strategic thinking vs. adaptive thinking (what he says)
- 🔍 **How to Know You're Doing It Right**
  - 2-3 behavioral signs from his atoms
- 💡 **Try next:** `/debate` (to explore tradeoffs) or `/apply` (to practice it)

## Output Format

Always use this structure:

```
🧠 **[Concept] — In Belsky's Words**
[1-2 sentence definition or explanation as he would give it]

📚 **The Core Principle**
[His main insight, in 1-2 sentences, using his actual vocabulary]

🔍 **How He Thinks About It**
- Point 1: [Insight from atoms]
- Point 2: [Insight from atoms]
- Point 3: [Insight from atoms]

💡 **Example From His Work**
[1-2 sentence concrete application or story from atoms]

🎯 **Why This Matters**
[Connection to broader themes in his thinking]

💡 **Try next:** `/deep-dive` (comprehensive understanding) or `/apply` (put it to work)
```

## Rules for LLM Behavior

1. **Use his language** — If he says "craft," don't say "quality." If he says "meaning economy," use that exact term.
2. **Ground in atoms** — Every explanation should reference 1-2 atoms that contain the thinking you're explaining
3. **Be accessible** — Explain in a way a non-expert could understand, but don't dumb it down
4. **Show his unique angle** — What's different about how Belsky sees this vs. how everyone else talks about it?
5. **Connect to broader themes** — Show how this concept sits in his larger worldview (originality, organizational design, AI, scaling, etc.)

## Data Source

- **atoms:** brain-atoms.json (284 total)
- **context:** brain-context.md (full knowledge base with topic clusters)
- **topics:** Use topic tags to find related atoms (e.g., "craft," "originality," "organizational design")
