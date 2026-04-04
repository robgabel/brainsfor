---
name: brain-setup
description: "Load the Scott Belsky brain and configure all 10 thinking skills. One-time setup that detects your AI tool, loads brain context, and verifies everything works."
---

# Scott Belsky Brain Pack — Setup & Configuration

Welcome to the **Belsky Brain Pack** from [brainsforsale.com](https://brainsforsale.com). This is a premium knowledge asset extracted from Scott Belsky's "Implications" newsletter — a curated collection of his most strategic thinking on originality, organizational design, agentic commerce, and the future of work.

## What You're Getting

- **284 knowledge atoms** — Core insights, frameworks, and strategic principles from 77 editions of the Implications newsletter
- **161 typed connections** — Relationships between ideas (supports, contradicts, extends, related, inspired_by)
- **10 specialized thinking skills** — Each designed to activate different modes of reasoning
- **Cross-referenced topics** — Superhumanity, originality, AI agents, organizational design, longevity, emergence, decision-making, scaling, and more

This brain is designed to augment YOUR thinking — not replace it. Use it for strategic decisions, creative problem-solving, research, and to challenge your assumptions.

---

## Setup Instructions

### Step 1: Verify Installation

Your Belsky Brain Pack folder should contain:

```
brainsforsale-belsky/
  ├── SKILL.md                 ← you are here
  ├── brain-context.md         ← full knowledge base + usage guide
  ├── brain-atoms.json         ← structured atoms (284 insights)
  └── README.md                ← quick reference
```

If any files are missing, reinstall from [brainsforsale.com](https://brainsforsale.com).

### Step 2: Detect Your AI Environment

This brain works across multiple AI tools. Identify which one you're using:

- **Claude Code** — Run this skill directly; brain context loads automatically
- **Cowork (Claude in Slack)** — Use `/brain-setup` command; Cowork syncs context
- **Cursor** — Paste brain-context.md into `.cursor/rules` or project instructions
- **ChatGPT / Claude.ai** — Copy brain-context.md into system prompt or conversation starter
- **Other tools** — Load brain-context.md as your first message or context injection

### Step 3: Load Brain Context

The brain operates in three layers:

1. **Layer 1 — Quick Reference** (brain-atoms.json)
   - JSON structure of 284 atoms with titles, summaries, connections
   - Ideal for: Rapid lookups, programmatic access, integrations
   - Use when: You need structured data for routing or filtering

2. **Layer 2 — Full Knowledge Base** (brain-context.md)
   - Complete narrative knowledge graph with topic tags, people, themes
   - Ideal for: Deep reasoning, strategy sessions, comprehensive understanding
   - Load this file when: Starting a session that requires brain-informed thinking

3. **Layer 3 — Thinking Skills** (the 10 skills below)
   - Each skill is a reasoning mode that activates specific parts of the brain
   - Ideal for: Targeted analysis, creative workflows, decision-making
   - Use when: You have a specific type of problem to solve

**Recommended:** Load `brain-context.md` at the start of each session where you want to use the brain. Claude will index it automatically.

### Step 4: Verify Everything Works

Test your setup with the Quick Start prompt below. You should get a thoughtful response grounded in Scott's thinking.

---

## The 10 Thinking Skills

Each skill is a specialized reasoning mode. Use them in combination for more powerful thinking.

### 🧠 **1. /advise** — Strategic Counsel
Ask for advice on decisions grounded in Scott's frameworks. Best for: career moves, company decisions, strategy choices.
*Example: "Should I raise my Series A or stay bootstrapped?"*

### 🔥 **2. /debate** — Steel-Man Both Sides
Present a position; brain argues both for and against it. Best for: understanding tradeoffs, challenging assumptions.
*Example: "Is remote work better for innovation?"*

### 🎯 **3. /apply** — Actionable Frameworks
Get concrete steps to apply an idea to your situation. Best for: implementation, execution, tactical work.
*Example: "How do I apply the originality framework to my product?"*

### 📚 **4. /teach** — Explain Like I'm Learning
Get a clear explanation of a concept as Scott sees it. Best for: understanding unfamiliar ideas, building mental models.
*Example: "Explain agentic commerce to me."*

### 🔍 **5. /deep-dive** — Exhaustive Analysis
Explore a topic across all connected atoms and frameworks. Best for: research, comprehensive understanding, thesis writing.
*Example: "Deep dive into Scott's thinking on organizational design."*

### 🎨 **6. /surprise** — Unexpected Connections
Get a random connection or counterintuitive insight you wouldn't think to ask for. Best for: creative breakthroughs, morning inspiration.
*Example: No input needed — just run it.*

### 🔗 **7. /connect** — Bridge Ideas
Find unexpected connections between two concepts. Best for: synthesis, innovation, cross-domain thinking.
*Example: "Connect originality to organizational structure."*

### ⚔️ **8. /brainfight** — Ideas in Conflict
Pit two ideas against each other. Best for: understanding nuance, avoiding false consensus, strategic clarity.
*Example: "Longevity vs. urgency — which should win?"*

### 🔄 **9. /mashup** — Synthesize Atoms
Combine multiple ideas into a new framework or thesis. Best for: original thinking, writing, strategy synthesis.
*Example: "Mashup: originality + AI agents + organizational design."*

### 📈 **10. /evolve** — How Ideas Build On Each Other
Trace how a concept develops and changes across the brain. Best for: historical perspective, maturity models, trajectory thinking.
*Example: "How does Scott's thinking on AI agents evolve?"*

---

## Recommended Workflows

Use these skill combinations for better results:

### 🎯 Decision Workflow
→ `/advise` (get perspective) → `/debate` (stress-test) → `/apply` (make it real)

*Example: Deciding on a hire? Ask for advice, debate the tradeoffs, then map out decision criteria.*

### 📚 Learning Workflow
→ `/teach` (understand) → `/deep-dive` (go deeper) → `/evolve` (see how it develops)

*Example: New to originality? Teach → deep-dive → evolve to get the full picture.*

### 💡 Creative Workflow
→ `/surprise` (get inspired) → `/connect` (build bridges) → `/apply` (make it work)

*Example: Stuck on a problem? Surprise + connect often surface unexpected angles.*

### 🔬 Research Workflow
→ `/deep-dive` (understand the landscape) → `/mashup` (synthesize) → `/brainfight` (sharpen)

*Example: Writing about AI agents? Deep-dive the atoms → mashup a thesis → brainfight it.*

### 🌅 Daily Ritual
→ Run `/surprise` each morning for 10 seconds of strategic inspiration.

---

## Quick Start

**Try this right now to verify setup:**

```
/advise

"I'm thinking about whether to focus my company on serving large enterprises or build a platform for creators. What would Scott think?"
```

You should get a thoughtful response that:
- References specific frameworks from the brain
- Weighs tradeoffs from Scott's perspective
- Suggests which of his mental models apply here
- Feels strategic and grounded (not generic)

If you get that, you're all set.

---

## Troubleshooting

**Q: The brain doesn't seem to know what I'm asking about.**
→ Make sure `brain-context.md` is loaded in your session. If using Claude Code, check that the file is in your working directory.

**Q: I want to search the brain for a specific topic.**
→ Use `/deep-dive` with a keyword: `"Deep dive: Scott's thinking on emergence"` → The brain will pull all relevant atoms.

**Q: Can I combine skills?**
→ Absolutely. Chain them: `"First /advise on whether to pivot, then /debate the tradeoffs, then /apply the decision framework."`

**Q: What if a skill doesn't feel relevant to my question?**
→ Try a different one. `/brainfight` often works when you're stuck; `/mashup` when you need something original; `/surprise` when you need inspiration.

**Q: How often should I reload the brain?**
→ Once per session is sufficient. Brain context doesn't expire, and atoms don't change. But if you're switching between different projects, fresh context load = sharper thinking.

---

## About Scott Belsky

Scott Belsky is a legendary entrepreneur and strategic thinker who has shaped product and organizational thinking across the tech industry. His "Implications" newsletter is where he shares his latest thinking on originality, organizational design, AI, and the future of work.

This brain pack extracts and structures his core ideas so you can activate his mental models in your own thinking.

**More:** Visit [brainsforsale.com](https://brainsforsale.com) for other brain packs, documentation, and community.

---

## Support & Feedback

If you encounter issues or have feedback:

1. Check `README.md` for quick answers
2. Verify all files are present and readable
3. Try a fresh load of `brain-context.md`
4. Contact support via [brainsforsale.com](https://brainsforsale.com)

---

**You're ready to think like Scott. Let's go.** 🚀
