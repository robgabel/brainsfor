---
name: brain-setup
description: "Load the Shiva Rajaraman brain. Pack ships 10 unified skills in pack/skills/ — 1 router (/brain) + 8 reasoning modes (/advise, /teach, /debate, /connect, /evolve, /surprise, /coach, /predict) + /board (multi-brain advisory) — that work with this brain and any other installed BrainsFor brain."
---

# Shiva Rajaraman Brain Pack — Setup & Configuration

Welcome to the **Rajaraman Brain Pack** from [brainsforagents.com](https://brainsforagents.com). This is a premium knowledge asset extracted from Shiva Rajaraman's public talks, conference keynotes, podcast appearances, and interviews — a curated collection of his most strategic thinking on consumer product design, platform strategy, AI, creator economies, and building products that move from meh to awesome.

## What You're Getting

- **817 knowledge atoms** — Core insights, frameworks, and strategic principles from Public talks, interviews, podcast appearances, and writings across Shiva Rajaraman's career from YouTube through OpenAI
- **791 typed connections** — Relationships between ideas (supports, contradicts, extends, related, inspired_by)
- **8 specialized thinking skills** — Each a distinct reasoning mode with a unique output type
- **A `/board` of advisors** — Convene this brain alongside your other installed brains for one question (needs 2+ brains)
- **Cross-referenced topics** — Consumer product design, platform strategy, AI products, music and audio, creator economy, web3 and NFTs, organizational design, product-market fit, data-driven product management, commerce and discovery, and more

This brain is designed to augment YOUR thinking — not replace it. Use it for strategic decisions, creative problem-solving, research, and to challenge your assumptions.

---

## Setup Instructions

### Step 1: Verify Installation

Your Rajaraman Brain Pack folder should contain:

```
pack/
  ├── SKILL.md                 ← you are here (brain-setup)
  ├── brain-context.md         ← full knowledge base + usage guide
  ├── brain-atoms.json         ← structured atoms (817 insights)
  ├── README.md                ← quick reference
  └── skills/                  ← 10 unified skills (work with any installed brain)
      ├── brain/               ← /brain router (set/show/list/clear active brain)
      ├── advise/              ← /advise — strategic counsel
      ├── teach/               ← /teach — explain through the thinker's lens
      ├── debate/              ← /debate — steel-man both sides
      ├── connect/             ← /connect — find unexpected bridges
      ├── evolve/              ← /evolve — trace how thinking changed
      ├── surprise/            ← /surprise — serendipity engine
      ├── coach/               ← /coach — Socratic questioning
      ├── predict/             ← /predict — implication chains
      └── board/               ← /board — board of advisors (needs 2+ brains)
```

The `skills/` directory is **brain-agnostic**. Every brain pack ships the same 10 skill files — they resolve which brain to use via the `/brain` router (active brain in `${BRAINSFOR_HOME:-~/.brainsfor}/state/active-brain.txt`) or via an inline slug override.

If any files are missing, reinstall from [brainsforagents.com](https://brainsforagents.com).

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
   - JSON structure of 817 atoms with titles, summaries, connections
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

**Recommended:** Run `/brain shiva-rajaraman` at the start of each session. The router writes the active brain to `${BRAINSFOR_HOME:-~/.brainsfor}/state/active-brain.txt` and loads `brain-context.md` as session context. After that, the 8 thinking skills (`/advise`, `/teach`, etc.) will use this brain automatically — no need to retype the slug on every call. The brain also stays in voice for the entire session: every turn responds as the thinker until you run `/brain clear`.

### Step 4: Verify Everything Works

Test your setup with the Quick Start prompt below. You should get a thoughtful response grounded in Shiva's thinking.

---

## The 9 Unified Skills

These skills live in `pack/skills/` and are brain-agnostic — they work with Shiva Rajaraman and with any other BrainsFor brain installed under `${BRAINSFOR_HOME:-~/.brainsfor}/brains/`. Set the active brain with `/brain shiva-rajaraman`, or override per call with an inline slug like `/advise shiva-rajaraman <question>`.

### 🎛️ **0. /brain** — Router
Set, show, list, or clear the active brain for the session.
*Usage: `/brain shiva-rajaraman` activates, `/brain` shows current, `/brain list` shows all installed, `/brain clear` unsets.*

### 🧠 **1. /advise** — Strategic Counsel
Ask for advice on decisions grounded in Shiva's frameworks. Best for: career moves, company decisions, strategy choices.
*Example: "My product has decent retention but users never describe it as something they love. How do I diagnose what's missing?"*

### 📚 **2. /teach** — Explain Like I'm Learning
Get a clear explanation of a concept as Shiva sees it. Best for: understanding unfamiliar ideas, building mental models.
*Example: "Explain what Shiva means by going from 'meh to awesome' and how product teams actually make that transition."*

### 🔥 **3. /debate** — Steel-Man Both Sides
Present a position or pit two ideas against each other; brain argues the counterpoint. Best for: understanding tradeoffs, challenging assumptions, resolving strategic tensions.
*Example: "Is algorithmic personalization better than human editorial curation for music discovery?"*

### 🔗 **4. /connect** — Bridge Ideas
Find unexpected connections between two concepts or synthesize multiple ideas into something new. Best for: synthesis, innovation, cross-domain thinking.
*Example: "Connect the lessons Shiva learned at Spotify about audio intimacy to how consumer AI products should be designed."*

### 📈 **5. /evolve** — How Ideas Build On Each Other
Trace how a concept develops and changes across the brain. Best for: historical perspective, maturity models, trajectory thinking.
*Example: "How did Shiva's thinking on platform strategy evolve from YouTube to OpenSea to OpenAI?"*

### 🎨 **6. /surprise** — Unexpected Insights
Get a random high-quality atom you wouldn't think to ask for. Best for: creative breakthroughs, morning inspiration, breaking tunnel vision.
*Example: No input needed — just run it.*

### 🪞 **7. /coach** — Socratic Questions
No answers — just the questions Shiva would ask you. Best for: uncovering blind spots, pressure-testing decisions, team discussions.
*Example: "I'm trying to decide whether to add more features or deepen the core experience. What questions should I be asking?"*

### 🔮 **8. /predict** — Implication Chains
Trace the second and third-order effects of a trend or decision. Best for: forecasting, strategic planning, seeing around corners.
*Example: "What happens to creator economies when AI can generate content indistinguishable from human creators?"*

### 🪑 **/board** — Board of Advisors (Multi-Brain)
Ask one question and hear from several thinkers at once. Each installed brain answers **independently** (no brain sees another's answer), then a synthesis names where they agree and where they clash. Best for: high-stakes decisions where you want genuine disagreement, not one voice.
*Requires 2+ brains installed, plus a host that can run parallel sub-agents (Claude Code's Agent tool or Cowork). No MCP server needed — each board member reads its brain's local pack. With only Shiva Rajaraman installed, `/board` will ask you to add another brain from [brainsforagents.com](https://brainsforagents.com).*
*Usage: `/board <question>`, `/board set <slug-a> <slug-b> ...`, `/board list`, `/board clear`.*

---

## Recommended Workflows

Use these skill combinations for better results:

### 🎯 Decision Workflow
→ `/advise` (get perspective) → `/debate` (stress-test) → `/coach` (check your blind spots)

*Example: Deciding on a hire? Get advice, challenge the reasoning, then surface what you're not asking.*

### 📚 Learning Workflow
→ `/teach` (understand) → `/evolve` (see how it develops) → `/coach` (test your understanding)

*Example: New to consumer product thinking? Teach 'meh to awesome' → evolve Shiva's thinking from YouTube to OpenAI → coach on your own product decisions to build a complete framework for consumer product excellence.*

### 💡 Creative Workflow
→ `/surprise` (get inspired) → `/connect` (build bridges) → `/predict` (where does this lead?)

*Example: Stuck on a problem? Surprise + connect often surface unexpected angles.*

### 🔮 Forecast Workflow
→ `/predict` (trace implications) → `/debate` (challenge the prediction) → `/advise` (act on it)

*Example: Building a platform with creators? Debate algorithmic vs. editorial curation → connect creator economy lessons to your context → advise on your specific creator monetization decisions to pressure-test your strategy.*

### 🌅 Daily Ritual
→ Run `/surprise` each morning for 10 seconds of strategic inspiration.

---

## Quick Start

**Try this right now to verify setup:**

```
/brain shiva-rajaraman

/advise "I'm building a consumer app and struggling to move from a product people tolerate to one they love. What would Shiva think about my approach?"
```

Or skip the activation step and use an inline slug for a one-off:

```
/advise shiva-rajaraman "I'm building a consumer app and struggling to move from a product people tolerate to one they love. What would Shiva think about my approach?"
```

You should get a thoughtful response that:
- References specific frameworks from the brain
- Weighs tradeoffs from Shiva's perspective
- Suggests which of his mental models apply here
- Feels strategic and grounded (not generic)

If you get that, you're all set.

---

## Troubleshooting

**Q: The brain doesn't seem to know what I'm asking about.**
→ Make sure `brain-context.md` is loaded in your session. If using Claude Code, check that the file is in your working directory.

**Q: I want to search the brain for a specific topic.**
→ Use `/advise` with a keyword: `"What does Shiva think about going from meh to awesome in consumer product design?"` → The brain will pull all relevant atoms.

**Q: Can I combine skills?**
→ Absolutely. Chain them: `"First /advise on whether to pivot, then /debate the tradeoffs, then /coach me on what I'm missing."`

**Q: What if a skill doesn't feel relevant to my question?**
→ Try a different one. `/coach` often works when you're stuck; `/connect` when you need something original; `/surprise` when you need inspiration.

**Q: How often should I reload the brain?**
→ Once per session is sufficient. Brain context doesn't expire, and atoms don't change. But if you're switching between different projects, fresh context load = sharper thinking.

---

## About Shiva Rajaraman

Shiva Rajaraman is a veteran product leader who has shaped some of the world's most consequential consumer platforms. Across YouTube, Spotify, WeWork, Facebook, OpenSea, and OpenAI, he has developed a rare cross-platform perspective on what separates forgettable products from ones people genuinely love — and how to build organizations capable of sustained product excellence.

This brain pack extracts and structures his core ideas so you can activate his mental models in your own thinking.

**More:** Visit [brainsforagents.com](https://brainsforagents.com) for other brain packs, documentation, and community.

---

## Sources & Ethics

This brain was built exclusively from **freely available, public sources** — Shiva Rajaraman's publicly available interviews, conference talks, podcast appearances, social media posts, and press features across his career at YouTube, Spotify, WeWork, Facebook, OpenSea, and OpenAI.. No transcripts from commercial works (e.g., audiobooks, paid courses) or paywalled essays were used to derive this brain.

Where a thinker's book ideas appear in the knowledge graph, they are represented as they exist in the public discourse: book reviews, author interviews, press coverage, conference talks, and widely discussed concepts. Authors typically share their core ideas through extensive public appearances — those public representations are what this brain captures.

## Support & Feedback

If you encounter issues or have feedback:

1. Check `README.md` for quick answers
2. Verify all files are present and readable
3. Try a fresh load of `brain-context.md`
4. Contact support via [brainsforagents.com](https://brainsforagents.com)

---

**You're ready to think with Shiva. Let's go.** 🚀
