---
name: brain-setup
description: "Load the Melinda French Gates brain. Pack ships 10 unified skills in pack/skills/ — 1 router (/brain) + 8 reasoning modes (/advise, /teach, /debate, /connect, /evolve, /surprise, /coach, /predict) + /board (multi-brain advisory) — that work with this brain and any other installed BrainsFor brain."
---

# Melinda French Gates Brain Pack — Setup & Configuration

Welcome to the **French Gates Brain Pack** from [brainsforagents.com](https://brainsforagents.com). This is a premium knowledge asset extracted from Melinda French Gates's books, TED talks, interviews, and public advocacy work — a curated collection of her most essential thinking on gender equity, global health, catalytic philanthropy, women's empowerment, and what it means to build a life of purpose.

## What You're Getting

- **496 knowledge atoms** — Core insights, frameworks, and strategic principles from The Moment of Lift book, The Next Day memoir, TED talks on birth control and Coca-Cola distribution, Davos panels, World Economic Forum interviews, Oprah Super Soul Sunday, CNN interviews, BBC profiles, and 30+ video appearances
- **477 typed connections** — Relationships between ideas (supports, contradicts, extends, related, inspired_by)
- **8 specialized thinking skills** — Each a distinct reasoning mode with a unique output type
- **A `/board` of advisors** — Convene this brain alongside your other installed brains for one question (needs 2+ brains)
- **Cross-referenced topics** — Gender equity, global health, contraceptive access, catalytic philanthropy, women's empowerment, education, poverty, unpaid labor, systems change, personal reinvention, and more

This brain is designed to augment YOUR thinking — not replace it. Use it for strategic decisions, creative problem-solving, research, and to challenge your assumptions.

---

## Setup Instructions

### Step 1: Verify Installation

Your French Gates Brain Pack folder should contain:

```
pack/
  ├── SKILL.md                 ← you are here (brain-setup)
  ├── brain-context.md         ← full knowledge base + usage guide
  ├── brain-atoms.json         ← structured atoms (496 insights)
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
   - JSON structure of 496 atoms with titles, summaries, connections
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

**Recommended:** Run `/brain melinda-french-gates` at the start of each session. The router writes the active brain to `${BRAINSFOR_HOME:-~/.brainsfor}/state/active-brain.txt` and loads `brain-context.md` as session context. After that, the 8 thinking skills (`/advise`, `/teach`, etc.) will use this brain automatically — no need to retype the slug on every call. The brain also stays in voice for the entire session: every turn responds as the thinker until you run `/brain clear`.

### Step 4: Verify Everything Works

Test your setup with the Quick Start prompt below. You should get a thoughtful response grounded in Melinda's thinking.

---

## The 9 Unified Skills

These skills live in `pack/skills/` and are brain-agnostic — they work with Melinda French Gates and with any other BrainsFor brain installed under `${BRAINSFOR_HOME:-~/.brainsfor}/brains/`. Set the active brain with `/brain melinda-french-gates`, or override per call with an inline slug like `/advise melinda-french-gates <question>`.

### 🎛️ **0. /brain** — Router
Set, show, list, or clear the active brain for the session.
*Usage: `/brain melinda-french-gates` activates, `/brain` shows current, `/brain list` shows all installed, `/brain clear` unsets.*

### 🧠 **1. /advise** — Strategic Counsel
Ask for advice on decisions grounded in Melinda's frameworks. Best for: career moves, company decisions, strategy choices.
*Example: "I run a nonprofit focused on maternal health. How should I think about measuring real impact versus vanity metrics?"*

### 📚 **2. /teach** — Explain Like I'm Learning
Get a clear explanation of a concept as Melinda sees it. Best for: understanding unfamiliar ideas, building mental models.
*Example: "Explain why access to contraception is one of the highest-leverage investments in global development."*

### 🔥 **3. /debate** — Steel-Man Both Sides
Present a position or pit two ideas against each other; brain argues the counterpoint. Best for: understanding tradeoffs, challenging assumptions, resolving strategic tensions.
*Example: "Is top-down philanthropy from billionaires more harmful than helpful?"*

### 🔗 **4. /connect** — Bridge Ideas
Find unexpected connections between two concepts or synthesize multiple ideas into something new. Best for: synthesis, innovation, cross-domain thinking.
*Example: "Connect the unpaid labor women do to global economic growth."*

### 📈 **5. /evolve** — How Ideas Build On Each Other
Trace how a concept develops and changes across the brain. Best for: historical perspective, maturity models, trajectory thinking.
*Example: "How did Melinda's thinking about women and power evolve from her Gates Foundation years to her work at Pivotal Ventures?"*

### 🎨 **6. /surprise** — Unexpected Insights
Get a random high-quality atom you wouldn't think to ask for. Best for: creative breakthroughs, morning inspiration, breaking tunnel vision.
*Example: No input needed — just run it.*

### 🪞 **7. /coach** — Socratic Questions
No answers — just the questions Melinda would ask you. Best for: uncovering blind spots, pressure-testing decisions, team discussions.
*Example: "I'm leaving a long partnership — professional or personal — and trying to figure out who I am on the other side. What should I be asking myself?"*

### 🔮 **8. /predict** — Implication Chains
Trace the second and third-order effects of a trend or decision. Best for: forecasting, strategic planning, seeing around corners.
*Example: "What happens to global health outcomes if reproductive rights continue to be rolled back in wealthy countries?"*

### 🪑 **/board** — Board of Advisors (Multi-Brain)
Ask one question and hear from several thinkers at once. Each installed brain answers **independently** (no brain sees another's answer), then a synthesis names where they agree and where they clash. Best for: high-stakes decisions where you want genuine disagreement, not one voice.
*Requires 2+ brains installed, plus a host that can run parallel sub-agents (Claude Code's Agent tool or Cowork). No MCP server needed — each board member reads its brain's local pack. With only Melinda French Gates installed, `/board` will ask you to add another brain from [brainsforagents.com](https://brainsforagents.com).*
*Usage: `/board <question>`, `/board set <slug-a> <slug-b> ...`, `/board list`, `/board clear`.*

---

## Recommended Workflows

Use these skill combinations for better results:

### 🎯 Decision Workflow
→ `/advise` (get perspective) → `/debate` (stress-test) → `/coach` (check your blind spots)

*Example: Deciding on a hire? Get advice, challenge the reasoning, then surface what you're not asking.*

### 📚 Learning Workflow
→ `/teach` (understand) → `/evolve` (see how it develops) → `/coach` (test your understanding)

*Example: New to catalytic philanthropy? Teach → connect → advise to build a framework and apply it to your own giving or impact work.*

### 💡 Creative Workflow
→ `/surprise` (get inspired) → `/connect` (build bridges) → `/predict` (where does this lead?)

*Example: Stuck on a problem? Surprise + connect often surface unexpected angles.*

### 🔮 Forecast Workflow
→ `/predict` (trace implications) → `/debate` (challenge the prediction) → `/advise` (act on it)

*Example: Writing about gender equity and economic development? Predict the second-order effects → debate the counterarguments → advise on what actionable leverage points exist today.*

### 🌅 Daily Ritual
→ Run `/surprise` each morning for 10 seconds of strategic inspiration.

---

## Quick Start

**Try this right now to verify setup:**

```
/brain melinda-french-gates

/advise "I want to do more good in the world but I don't know where to start. What would Melinda think?"
```

Or skip the activation step and use an inline slug for a one-off:

```
/advise melinda-french-gates "I want to do more good in the world but I don't know where to start. What would Melinda think?"
```

You should get a thoughtful response that:
- References specific frameworks from the brain
- Weighs tradeoffs from Melinda's perspective
- Suggests which of his mental models apply here
- Feels strategic and grounded (not generic)

If you get that, you're all set.

---

## Troubleshooting

**Q: The brain doesn't seem to know what I'm asking about.**
→ Make sure `brain-context.md` is loaded in your session. If using Claude Code, check that the file is in your working directory.

**Q: I want to search the brain for a specific topic.**
→ Use `/advise` with a keyword: `"What does Melinda think about why contraceptive access is a moral imperative?"` → The brain will pull all relevant atoms.

**Q: Can I combine skills?**
→ Absolutely. Chain them: `"First /advise on whether to pivot, then /debate the tradeoffs, then /coach me on what I'm missing."`

**Q: What if a skill doesn't feel relevant to my question?**
→ Try a different one. `/coach` often works when you're stuck; `/connect` when you need something original; `/surprise` when you need inspiration.

**Q: How often should I reload the brain?**
→ Once per session is sufficient. Brain context doesn't expire, and atoms don't change. But if you're switching between different projects, fresh context load = sharper thinking.

---

## About Melinda French Gates

Melinda French Gates is one of the most consequential philanthropists and advocates for women and girls of her generation. Co-founder of the Bill & Melinda Gates Foundation — once the world's largest private charitable foundation — she spent two decades directing billions of dollars toward global health, poverty reduction, and educational access. Since departing the foundation in 2024, she has launched Pivotal Ventures and committed $1 billion to reproductive rights and women's empowerment. Her books The Moment of Lift and The Next Day are deeply personal manifestos for why lifting women lifts the world.

This brain pack extracts and structures her core ideas so you can activate her mental models in your own thinking.

**More:** Visit [brainsforagents.com](https://brainsforagents.com) for other brain packs, documentation, and community.

---

## Sources & Ethics

This brain was built exclusively from **freely available, public sources** — Melinda French Gates's freely distributed TED talks, public speeches, book excerpts, widely circulated interviews on CNN, OWN, and the BBC, and press coverage of her philanthropic and advocacy work.. No transcripts from commercial works (e.g., audiobooks, paid courses) or paywalled essays were used to derive this brain.

Where a thinker's book ideas appear in the knowledge graph, they are represented as they exist in the public discourse: book reviews, author interviews, press coverage, conference talks, and widely discussed concepts. Authors typically share their core ideas through extensive public appearances — those public representations are what this brain captures.

## Support & Feedback

If you encounter issues or have feedback:

1. Check `README.md` for quick answers
2. Verify all files are present and readable
3. Try a fresh load of `brain-context.md`
4. Contact support via [brainsforagents.com](https://brainsforagents.com)

---

**You're ready to think with Melinda. Let's go.** 🚀
