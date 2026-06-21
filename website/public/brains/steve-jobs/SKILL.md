---
name: brain-setup
description: "Load the Steve Jobs brain. Pack ships 10 unified skills in pack/skills/ — 1 router (/brain) + 8 reasoning modes (/advise, /teach, /debate, /connect, /evolve, /surprise, /coach, /predict) + /board (multi-brain advisory) — that work with this brain and any other installed BrainsFor brain."
---

# Steve Jobs Brain Pack — Setup & Configuration

Welcome to the **Jobs Brain Pack** from [brainsforagents.com](https://brainsforagents.com). This is a premium knowledge asset extracted from Steve Jobs's speeches, interviews, keynotes, and public appearances — a curated collection of his most provocative thinking on product design, simplicity, taste, team-building, and the intersection of technology and liberal arts.

## What You're Getting

- **1029 knowledge atoms** — Core insights, frameworks, and strategic principles from 50+ years of speeches, interviews, keynotes, and documented conversations (1976–2011)
- **1019 typed connections** — Relationships between ideas (supports, contradicts, extends, related, inspired_by)
- **8 specialized thinking skills** — Each a distinct reasoning mode with a unique output type
- **A `/board` of advisors** — Convene this brain alongside your other installed brains for one question (needs 2+ brains)
- **Cross-referenced topics** — Simplicity, taste, product design, marketing, innovation, team building, focus, craftsmanship, the intersection of technology and liberal arts, and more

This brain is designed to augment YOUR thinking — not replace it. Use it for strategic decisions, creative problem-solving, research, and to challenge your assumptions.

---

## Setup Instructions

### Step 1: Verify Installation

Your Jobs Brain Pack folder should contain:

```
pack/
  ├── SKILL.md                 ← you are here (brain-setup)
  ├── brain-context.md         ← full knowledge base + usage guide
  ├── brain-atoms.json         ← structured atoms (1029 insights)
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
   - JSON structure of 1029 atoms with titles, summaries, connections
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

**Recommended:** Run `/brain steve-jobs` at the start of each session. The router writes the active brain to `${BRAINSFOR_HOME:-~/.brainsfor}/state/active-brain.txt` and loads `brain-context.md` as session context. After that, the 8 thinking skills (`/advise`, `/teach`, etc.) will use this brain automatically — no need to retype the slug on every call.

### Step 4: Verify Everything Works

Test your setup with the Quick Start prompt below. You should get a thoughtful response grounded in Steve's thinking.

---

## The 9 Unified Skills

These skills live in `pack/skills/` and are brain-agnostic — they work with Steve Jobs and with any other BrainsFor brain installed under `${BRAINSFOR_HOME:-~/.brainsfor}/brains/`. Set the active brain with `/brain steve-jobs`, or override per call with an inline slug like `/advise steve-jobs <question>`.

### 🎛️ **0. /brain** — Router
Set, show, list, or clear the active brain for the session.
*Usage: `/brain steve-jobs` activates, `/brain` shows current, `/brain list` shows all installed, `/brain clear` unsets.*

### 🧠 **1. /advise** — Strategic Counsel
Ask for advice on decisions grounded in Steve's frameworks. Best for: career moves, company decisions, strategy choices.
*Example: "Should I add more features or strip my product down to its essence?"*

### 📚 **2. /teach** — Explain Like I'm Learning
Get a clear explanation of a concept as Steve sees it. Best for: understanding unfamiliar ideas, building mental models.
*Example: "Explain what Steve meant by the intersection of technology and liberal arts."*

### 🔥 **3. /debate** — Steel-Man Both Sides
Present a position or pit two ideas against each other; brain argues the counterpoint. Best for: understanding tradeoffs, challenging assumptions, resolving strategic tensions.
*Example: "Is owning the full hardware-software stack worth the market share you sacrifice?"*

### 🔗 **4. /connect** — Bridge Ideas
Find unexpected connections between two concepts or synthesize multiple ideas into something new. Best for: synthesis, innovation, cross-domain thinking.
*Example: "Connect Steve's Zen practice to his approach to product simplicity."*

### 📈 **5. /evolve** — How Ideas Build On Each Other
Trace how a concept develops and changes across the brain. Best for: historical perspective, maturity models, trajectory thinking.
*Example: "How did Steve's thinking on leadership evolve from his first stint at Apple through the NeXT years and his return?"*

### 🎨 **6. /surprise** — Unexpected Insights
Get a random high-quality atom you wouldn't think to ask for. Best for: creative breakthroughs, morning inspiration, breaking tunnel vision.
*Example: No input needed — just run it.*

### 🪞 **7. /coach** — Socratic Questions
No answers — just the questions Steve would ask you. Best for: uncovering blind spots, pressure-testing decisions, team discussions.
*Example: "I'm about to launch a product I know isn't ready. What questions should I be asking myself?"*

### 🔮 **8. /predict** — Implication Chains
Trace the second and third-order effects of a trend or decision. Best for: forecasting, strategic planning, seeing around corners.
*Example: "What would Steve think about the future of AI-generated interfaces replacing human-designed ones?"*

### 🪑 **/board** — Board of Advisors (Multi-Brain)
Ask one question and hear from several thinkers at once. Each installed brain answers **independently** (no brain sees another's answer), then a synthesis names where they agree and where they clash. Best for: high-stakes decisions where you want genuine disagreement, not one voice.
*Requires 2+ brains installed, plus a host that can run parallel sub-agents (Claude Code's Agent tool or Cowork). No MCP server needed — each board member reads its brain's local pack. With only Steve Jobs installed, `/board` will ask you to add another brain from [brainsforagents.com](https://brainsforagents.com).*
*Usage: `/board <question>`, `/board set <slug-a> <slug-b> ...`, `/board list`, `/board clear`.*

---

## Recommended Workflows

Use these skill combinations for better results:

### 🎯 Decision Workflow
→ `/advise` (get perspective) → `/debate` (stress-test) → `/coach` (check your blind spots)

*Example: Deciding on a hire? Get advice, challenge the reasoning, then surface what you're not asking.*

### 📚 Learning Workflow
→ `/teach` (understand) → `/evolve` (see how it develops) → `/coach` (test your understanding)

*Example: New to Jobs' philosophy? Start with teach → evolve → coach to absorb the ideas, trace their development, and apply them to your own situation.*

### 💡 Creative Workflow
→ `/surprise` (get inspired) → `/connect` (build bridges) → `/predict` (where does this lead?)

*Example: Stuck on a problem? Surprise + connect often surface unexpected angles.*

### 🔮 Forecast Workflow
→ `/predict` (trace implications) → `/debate` (challenge the prediction) → `/advise` (act on it)

*Example: Building a product? Use predict to see where the market is heading → debate to stress-test your assumptions → advise to get a strategic recommendation grounded in Steve's frameworks.*

### 🌅 Daily Ritual
→ Run `/surprise` each morning for 10 seconds of strategic inspiration.

---

## Quick Start

**Try this right now to verify setup:**

```
/brain steve-jobs

/advise "I'm launching a new product and struggling to decide which features to cut. What would Steve think?"
```

Or skip the activation step and use an inline slug for a one-off:

```
/advise steve-jobs "I'm launching a new product and struggling to decide which features to cut. What would Steve think?"
```

You should get a thoughtful response that:
- References specific frameworks from the brain
- Weighs tradeoffs from Steve's perspective
- Suggests which of his mental models apply here
- Feels strategic and grounded (not generic)

If you get that, you're all set.

---

## Troubleshooting

**Q: The brain doesn't seem to know what I'm asking about.**
→ Make sure `brain-context.md` is loaded in your session. If using Claude Code, check that the file is in your working directory.

**Q: I want to search the brain for a specific topic.**
→ Use `/advise` with a keyword: `"What does Steve think about simplicity?"` → The brain will pull all relevant atoms.

**Q: Can I combine skills?**
→ Absolutely. Chain them: `"First /advise on whether to pivot, then /debate the tradeoffs, then /coach me on what I'm missing."`

**Q: What if a skill doesn't feel relevant to my question?**
→ Try a different one. `/coach` often works when you're stuck; `/connect` when you need something original; `/surprise` when you need inspiration.

**Q: How often should I reload the brain?**
→ Once per session is sufficient. Brain context doesn't expire, and atoms don't change. But if you're switching between different projects, fresh context load = sharper thinking.

---

## About Steve Jobs

Steve Jobs co-founded Apple, led Pixar, built NeXT, and returned to transform Apple into the most valuable company in history. His thinking on product design, marketing, simplicity, and the intersection of technology and humanities remains the most referenced playbook in tech. He died in 2011 but his ideas only grow more relevant.

This brain pack extracts and structures his core ideas so you can activate his mental models in your own thinking.

**More:** Visit [brainsforagents.com](https://brainsforagents.com) for other brain packs, documentation, and community.

---

## Sources & Ethics

This brain was built exclusively from **freely available, public sources** — Jobs's publicly broadcast speeches (including the Stanford commencement address), Apple keynote presentations circulating in public archives, press interviews with outlets including 60 Minutes and Charlie Rose, the 1996 Lost Interview, D5 Conference appearances, WWDC 1997, and widely quoted historical appearances. No proprietary Apple internal documents are reproduced.. No transcripts from commercial works (e.g., audiobooks, paid courses) or paywalled essays were used to derive this brain.

Where a thinker's book ideas appear in the knowledge graph, they are represented as they exist in the public discourse: book reviews, author interviews, press coverage, conference talks, and widely discussed concepts. Authors typically share their core ideas through extensive public appearances — those public representations are what this brain captures.

## Support & Feedback

If you encounter issues or have feedback:

1. Check `README.md` for quick answers
2. Verify all files are present and readable
3. Try a fresh load of `brain-context.md`
4. Contact support via [brainsforagents.com](https://brainsforagents.com)

---

**You're ready to think with Steve. Let's go.** 🚀
