---
name: brain-setup
description: "Load the Gokul Rajaram brain. Pack ships 9 unified skills in pack/skills/ — 1 router (/brain) + 8 reasoning modes (/advise, /teach, /debate, /connect, /evolve, /surprise, /coach, /predict) — that work with this brain and any other installed BrainsFor brain."
---

# Gokul Rajaram Brain Pack — Setup & Configuration

Welcome to the **Rajaram Brain Pack** from [brainsforfree.com](https://brainsforfree.com). This is a premium knowledge asset extracted from Gokul Rajaram's public talks, interviews, and writing on product, social media, and the creator economy — a curated collection of his sharpest thinking on product leadership, ads/monetization, decision-making, angel investing, and how AI is reshaping how products get built.

## What You're Getting

- **554 knowledge atoms** — Core insights, frameworks, and strategic principles from Podcast interviews (Invest Like the Best, 20VC, Lenny's Podcast, World of DaaS, Aarthi & Sriram Show), conference talks, Medium essays, and decision-making frameworks like SPADE — spanning product leadership at Google AdSense, Facebook Ads, Square/Caviar, and DoorDash, plus angel investing across 700+ companies.
- **906 typed connections** — Relationships between ideas (supports, contradicts, extends, related, inspired_by)
- **8 specialized thinking skills** — Each a distinct reasoning mode with a unique output type
- **Cross-referenced topics** — Creator economy, social commerce, platform strategy, product-market fit, consumer behavior, monetization, social graphs, growth loops, and more

This brain is designed to augment YOUR thinking — not replace it. Use it for strategic decisions, creative problem-solving, research, and to challenge your assumptions.

---

## Setup Instructions

### Step 1: Verify Installation

Your Rajaram Brain Pack folder should contain:

```
pack/
  ├── SKILL.md                 ← you are here (brain-setup)
  ├── brain-context.md         ← full knowledge base + usage guide
  ├── brain-atoms.json         ← structured atoms (554 insights)
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
   - JSON structure of 554 atoms with titles, summaries, connections
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

**Recommended:** Run `/brain gokul-rajaram` at the start of each session. The router writes the active brain to `${BRAINSFOR_HOME:-~/.brainsfor}/state/active-brain.txt` and loads `brain-context.md` as session context. After that, the 8 thinking skills (`/advise`, `/teach`, etc.) will use this brain automatically — no need to retype the slug on every call.

### Step 4: Verify Everything Works

Test your setup with the Quick Start prompt below. You should get a thoughtful response grounded in Gokul's thinking.

---

## The 9 Unified Skills

These skills live in `pack/skills/` and are brain-agnostic — they work with Gokul Rajaram and with any other BrainsFor brain installed under `${BRAINSFOR_HOME:-~/.brainsfor}/brains/`. Set the active brain with `/brain gokul-rajaram`, or override per call with an inline slug like `/advise gokul-rajaram <question>`.

### 🎛️ **0. /brain** — Router
Set, show, list, or clear the active brain for the session.
*Usage: `/brain gokul-rajaram` activates, `/brain` shows current, `/brain list` shows all installed, `/brain clear` unsets.*

### 🧠 **1. /advise** — Strategic Counsel
Ask for advice on decisions grounded in Gokul's frameworks. Best for: career moves, company decisions, strategy choices.
*Example: "Should I build a standalone creator monetization tool or embed it inside an existing social platform?"*

### 📚 **2. /teach** — Explain Like I'm Learning
Get a clear explanation of a concept as Gokul sees it. Best for: understanding unfamiliar ideas, building mental models.
*Example: "Explain how platform flywheels work in social commerce."*

### 🔥 **3. /debate** — Steel-Man Both Sides
Present a position or pit two ideas against each other; brain argues the counterpoint. Best for: understanding tradeoffs, challenging assumptions, resolving strategic tensions.
*Example: "Is the creator economy a sustainable economic model or a bubble?"*

### 🔗 **4. /connect** — Bridge Ideas
Find unexpected connections between two concepts or synthesize multiple ideas into something new. Best for: synthesis, innovation, cross-domain thinking.
*Example: "Connect trust graphs to creator monetization."*

### 📈 **5. /evolve** — How Ideas Build On Each Other
Trace how a concept develops and changes across the brain. Best for: historical perspective, maturity models, trajectory thinking.
*Example: "How does Gokul's thinking on social commerce evolve over time?"*

### 🎨 **6. /surprise** — Unexpected Insights
Get a random high-quality atom you wouldn't think to ask for. Best for: creative breakthroughs, morning inspiration, breaking tunnel vision.
*Example: No input needed — just run it.*

### 🪞 **7. /coach** — Socratic Questions
No answers — just the questions Gokul would ask you. Best for: uncovering blind spots, pressure-testing decisions, team discussions.
*Example: "I'm trying to figure out the right monetization model for my creator platform. What should I be asking myself?"*

### 🔮 **8. /predict** — Implication Chains
Trace the second and third-order effects of a trend or decision. Best for: forecasting, strategic planning, seeing around corners.
*Example: "What happens to Instagram if TikTok is banned in the US?"*

---

## Recommended Workflows

Use these skill combinations for better results:

### 🎯 Decision Workflow
→ `/advise` (get perspective) → `/debate` (stress-test) → `/coach` (check your blind spots)

*Example: Deciding on a hire? Get advice, challenge the reasoning, then surface what you're not asking.*

### 📚 Learning Workflow
→ `/teach` (understand) → `/evolve` (see how it develops) → `/coach` (test your understanding)

*Example: New to platform strategy? Teach → evolve → coach to build a working mental model.*

### 💡 Creative Workflow
→ `/surprise` (get inspired) → `/connect` (build bridges) → `/predict` (where does this lead?)

*Example: Stuck on a problem? Surprise + connect often surface unexpected angles.*

### 🔮 Forecast Workflow
→ `/predict` (trace implications) → `/debate` (challenge the prediction) → `/advise` (act on it)

*Example: Writing about creator monetization? Predict the implications → debate the forecast → advise on action.*

### 🌅 Daily Ritual
→ Run `/surprise` each morning for 10 seconds of strategic inspiration.

---

## Quick Start

**Try this right now to verify setup:**

```
/brain gokul-rajaram

/advise "I'm building a social product and trying to decide whether to focus on creators or consumers first. What would Gokul think?"
```

Or skip the activation step and use an inline slug for a one-off:

```
/advise gokul-rajaram "I'm building a social product and trying to decide whether to focus on creators or consumers first. What would Gokul think?"
```

You should get a thoughtful response that:
- References specific frameworks from the brain
- Weighs tradeoffs from Gokul's perspective
- Suggests which of his mental models apply here
- Feels strategic and grounded (not generic)

If you get that, you're all set.

---

## Troubleshooting

**Q: The brain doesn't seem to know what I'm asking about.**
→ Make sure `brain-context.md` is loaded in your session. If using Claude Code, check that the file is in your working directory.

**Q: I want to search the brain for a specific topic.**
→ Use `/advise` with a keyword: `"What does Gokul think about creator monetization?"` → The brain will pull all relevant atoms.

**Q: Can I combine skills?**
→ Absolutely. Chain them: `"First /advise on whether to pivot, then /debate the tradeoffs, then /coach me on what I'm missing."`

**Q: What if a skill doesn't feel relevant to my question?**
→ Try a different one. `/coach` often works when you're stuck; `/connect` when you need something original; `/surprise` when you need inspiration.

**Q: How often should I reload the brain?**
→ Once per session is sufficient. Brain context doesn't expire, and atoms don't change. But if you're switching between different projects, fresh context load = sharper thinking.

---

## About Gokul Rajaram

Gokul Rajaram is one of the most prolific operator-investors in tech — known as the 'Godfather of AdSense' for growing Google's AdSense from zero to $1B+, then leading Ads Product at Facebook, holding product leadership roles at Square and DoorDash, and angel investing in 700+ companies (Airtable, Figma, Groq, Runway, Supabase, Vercel, and more). He now runs Marathon Management Partners. His writing on SPADE decision-making, hiring PMs, and AI's impact on product building has become required reading for tech operators.

This brain pack extracts and structures his core ideas so you can activate his mental models in your own thinking.

**More:** Visit [brainsforfree.com](https://brainsforfree.com) for other brain packs, documentation, and community.

---

## Sources & Ethics

This brain was built exclusively from **freely available, public sources** — Gokul Rajaram's publicly available podcast appearances, conference talks, written essays, Twitter/X threads, and media interviews on product strategy, social platforms, and the creator economy.. No transcripts from commercial works (e.g., audiobooks, paid courses) or paywalled essays were used to derive this brain.

Where a thinker's book ideas appear in the knowledge graph, they are represented as they exist in the public discourse: book reviews, author interviews, press coverage, conference talks, and widely discussed concepts. Authors typically share their core ideas through extensive public appearances — those public representations are what this brain captures.

## Support & Feedback

If you encounter issues or have feedback:

1. Check `README.md` for quick answers
2. Verify all files are present and readable
3. Try a fresh load of `brain-context.md`
4. Contact support via [brainsforfree.com](https://brainsforfree.com)

---

**You're ready to think with Gokul. Let's go.** 🚀
