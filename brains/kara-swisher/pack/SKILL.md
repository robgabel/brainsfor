---
name: brain-setup
description: "Load the Kara Swisher brain. Pack ships 9 unified skills in pack/skills/ — 1 router (/brain) + 8 reasoning modes (/advise, /teach, /debate, /connect, /evolve, /surprise, /coach, /predict) — that work with this brain and any other installed BrainsFor brain."
---

# Kara Swisher Brain Pack — Setup & Configuration

Welcome to the **Swisher Brain Pack** from [brainsforfree.com](https://brainsforfree.com). This is a premium knowledge asset extracted from Kara Swisher's Pivot and Sway podcasts, NYT Opinion columns, Burn Book memoir, Code Conference interviews, and three decades of tech journalism — a curated collection of her most incisive thinking on tech power, accountability, AI risk, media disruption, Silicon Valley culture, and the defense of democracy.

## What You're Getting

- **885 knowledge atoms** — Core insights, frameworks, and strategic principles from Pivot and On with Kara Swisher podcast episodes, NYT Opinion columns, Code Conference and DLD keynote interviews, Burn Book memoir, and landmark interviews with Gates, Jobs, Zuckerberg, Bezos, Musk, Cook, Sandberg, and Musk spanning 30+ years
- **772 typed connections** — Relationships between ideas (supports, contradicts, extends, related, inspired_by)
- **8 specialized thinking skills** — Each a distinct reasoning mode with a unique output type
- **Cross-referenced topics** — AI accountability, tech regulation, Big Tech power, media disruption, democracy and technology, Silicon Valley culture, journalism ethics, CEO accountability, and more

This brain is designed to augment YOUR thinking — not replace it. Use it for strategic decisions, creative problem-solving, research, and to challenge your assumptions.

---

## Setup Instructions

### Step 1: Verify Installation

Your Swisher Brain Pack folder should contain:

```
pack/
  ├── SKILL.md                 ← you are here (brain-setup)
  ├── brain-context.md         ← full knowledge base + usage guide
  ├── brain-atoms.json         ← structured atoms (885 insights)
  ├── README.md                ← quick reference
  └── skills/                  ← 9 unified skills (work with any installed brain)
      ├── brain/               ← /brain router (set/show/list/clear active brain)
      ├── advise/              ← /advise — strategic counsel
      ├── teach/               ← /teach — explain through the thinker's lens
      ├── debate/              ← /debate — steel-man both sides
      ├── connect/             ← /connect — find unexpected bridges
      ├── evolve/              ← /evolve — trace how thinking changed
      ├── surprise/            ← /surprise — serendipity engine
      ├── coach/               ← /coach — Socratic questioning
      └── predict/             ← /predict — implication chains
```

The `skills/` directory is **brain-agnostic**. Every brain pack ships the same 9 skill files — they resolve which brain to use via the `/brain` router (active brain in `${BRAINSFOR_HOME:-~/.brainsfor}/state/active-brain.txt`) or via an inline slug override.

If any files are missing, reinstall from [brainsforfree.com](https://brainsforfree.com).

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
   - JSON structure of 885 atoms with titles, summaries, connections
   - Ideal for: Rapid lookups, programmatic access, integrations
   - Use when: You need structured data for routing or filtering

2. **Layer 2 — Full Knowledge Base** (brain-context.md)
   - Complete narrative knowledge graph with topic tags, people, themes
   - Ideal for: Deep reasoning, strategy sessions, comprehensive understanding
   - Load this file when: Starting a session that requires brain-informed thinking

3. **Layer 3 — Thinking Skills** (the 8 skills below)
   - Each skill is a reasoning mode that produces a distinct type of output
   - Ideal for: Targeted analysis, creative workflows, decision-making
   - Use when: You have a specific type of problem to solve

**Recommended:** Run `/brain kara-swisher` at the start of each session. The router writes the active brain to `${BRAINSFOR_HOME:-~/.brainsfor}/state/active-brain.txt` and loads `brain-context.md` as session context. After that, the 8 thinking skills (`/advise`, `/teach`, etc.) will use this brain automatically — no need to retype the slug on every call.

### Step 4: Verify Everything Works

Test your setup with the Quick Start prompt below. You should get a thoughtful response grounded in Kara's thinking.

---

## The 9 Unified Skills

These skills live in `pack/skills/` and are brain-agnostic — they work with Kara Swisher and with any other BrainsFor brain installed under `${BRAINSFOR_HOME:-~/.brainsfor}/brains/`. Set the active brain with `/brain kara-swisher`, or override per call with an inline slug like `/advise kara-swisher <question>`.

### 🎛️ **0. /brain** — Router
Set, show, list, or clear the active brain for the session.
*Usage: `/brain kara-swisher` activates, `/brain` shows current, `/brain list` shows all installed, `/brain clear` unsets.*

### 🧠 **1. /advise** — Strategic Counsel
Ask for advice on decisions grounded in Kara's frameworks. Best for: career moves, company decisions, strategy choices.
*Example: "Should my startup engage proactively with government regulators, or wait until they come to us?"*

### 📚 **2. /teach** — Explain Like I'm Learning
Get a clear explanation of a concept as Kara sees it. Best for: understanding unfamiliar ideas, building mental models.
*Example: "Explain why Kara thinks the attention economy is a machine optimized for outrage, not truth."*

### 🔥 **3. /debate** — Steel-Man Both Sides
Present a position or pit two ideas against each other; brain argues the counterpoint. Best for: understanding tradeoffs, challenging assumptions, resolving strategic tensions.
*Example: "Is Elon Musk's ownership of X good or bad for free speech?"*

### 🔗 **4. /connect** — Bridge Ideas
Find unexpected connections between two concepts or synthesize multiple ideas into something new. Best for: synthesis, innovation, cross-domain thinking.
*Example: "Connect the collapse of local journalism to the rise of political disinformation."*

### 📈 **5. /evolve** — How Ideas Build On Each Other
Trace how a concept develops and changes across the brain. Best for: historical perspective, maturity models, trajectory thinking.
*Example: "How has Kara's thinking on Mark Zuckerberg and Facebook evolved over 20 years?"*

### 🎨 **6. /surprise** — Unexpected Insights
Get a random high-quality atom you wouldn't think to ask for. Best for: creative breakthroughs, morning inspiration, breaking tunnel vision.
*Example: No input needed — just run it.*

### 🪞 **7. /coach** — Socratic Questions
No answers — just the questions Kara would ask you. Best for: uncovering blind spots, pressure-testing decisions, team discussions.
*Example: "I'm a journalist deciding whether to go public with a story about a powerful tech CEO. What should I be asking myself?"*

### 🔮 **8. /predict** — Implication Chains
Trace the second and third-order effects of a trend or decision. Best for: forecasting, strategic planning, seeing around corners.
*Example: "What happens to democracy if three companies control the world's AI infrastructure?"*

---

## Recommended Workflows

Use these skill combinations for better results:

### 🎯 Decision Workflow
→ `/advise` (get perspective) → `/debate` (stress-test) → `/coach` (check your blind spots)

*Example: Deciding on a hire? Get advice, challenge the reasoning, then surface what you're not asking.*

### 📚 Learning Workflow
→ `/teach` (understand) → `/evolve` (see how it develops) → `/coach` (test your understanding)

*Example: New to tech accountability? Teach → evolve → coach to understand how Swisher's framework developed and how to apply it yourself.*

### 💡 Creative Workflow
→ `/surprise` (get inspired) → `/connect` (build bridges) → `/predict` (where does this lead?)

*Example: Stuck on a problem? Surprise + connect often surface unexpected angles.*

### 🔮 Forecast Workflow
→ `/predict` (trace implications) → `/debate` (challenge the prediction) → `/advise` (act on it)

*Example: Writing about AI regulation? Predict the second-order implications → debate the tradeoffs with stakeholders → advise on what policymakers should actually do.*

### 🌅 Daily Ritual
→ Run `/surprise` each morning for 10 seconds of strategic inspiration.

---

## Quick Start

**Try this right now to verify setup:**

```
/brain kara-swisher

/advise "I'm trying to understand why Kara thinks Big Tech companies have failed democracy. Where would she start?"
```

Or skip the activation step and use an inline slug for a one-off:

```
/advise kara-swisher "I'm trying to understand why Kara thinks Big Tech companies have failed democracy. Where would she start?"
```

You should get a thoughtful response that:
- References specific frameworks from the brain
- Weighs tradeoffs from Kara's perspective
- Suggests which of his mental models apply here
- Feels strategic and grounded (not generic)

If you get that, you're all set.

---

## Troubleshooting

**Q: The brain doesn't seem to know what I'm asking about.**
→ Make sure `brain-context.md` is loaded in your session. If using Claude Code, check that the file is in your working directory.

**Q: I want to search the brain for a specific topic.**
→ Use `/advise` with a keyword: `"What does Kara think about AI accountability?"` → The brain will pull all relevant atoms.

**Q: Can I combine skills?**
→ Absolutely. Chain them: `"First /advise on whether to pivot, then /debate the tradeoffs, then /coach me on what I'm missing."`

**Q: What if a skill doesn't feel relevant to my question?**
→ Try a different one. `/coach` often works when you're stuck; `/connect` when you need something original; `/surprise` when you need inspiration.

**Q: How often should I reload the brain?**
→ Once per session is sufficient. Brain context doesn't expire, and atoms don't change. But if you're switching between different projects, fresh context load = sharper thinking.

---

## About Kara Swisher

Kara Swisher is the most influential tech journalist of her generation — a relentless interrogator of Silicon Valley power, co-host of the Pivot podcast, host of On with Kara Swisher, and author of the memoir Burn Book. For three decades she has covered, challenged, and occasionally embarrassed the most powerful figures in technology, earning a reputation for fearless questioning, sharp political instincts, and an unwillingness to trade access for favorable coverage.

This brain pack extracts and structures her core ideas so you can activate her mental models in your own thinking.

**More:** Visit [brainsforfree.com](https://brainsforfree.com) for other brain packs, documentation, and community.

---

## Sources & Ethics

This brain was built exclusively from **freely available, public sources** — Swisher's publicly available podcast episodes, New York Times Opinion columns, Vox Media interviews, public keynote appearances, widely circulated journalism across AllThingsD, Re/code, and Recode, and her memoir Burn Book published in 2024.. No transcripts from commercial works (e.g., audiobooks, paid courses) or paywalled essays were used to derive this brain.

Where a thinker's book ideas appear in the knowledge graph, they are represented as they exist in the public discourse: book reviews, author interviews, press coverage, conference talks, and widely discussed concepts. Authors typically share their core ideas through extensive public appearances — those public representations are what this brain captures.

## Support & Feedback

If you encounter issues or have feedback:

1. Check `README.md` for quick answers
2. Verify all files are present and readable
3. Try a fresh load of `brain-context.md`
4. Contact support via [brainsforfree.com](https://brainsforfree.com)

---

**You're ready to think with Kara. Let's go.** 🚀
