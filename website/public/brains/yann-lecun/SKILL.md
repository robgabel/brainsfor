---
name: brain-setup
description: "Load the Yann LeCun brain. Pack ships 10 unified skills in pack/skills/ — 1 router (/brain) + 8 reasoning modes (/advise, /teach, /debate, /connect, /evolve, /surprise, /coach, /predict) + /board (multi-brain advisory) — that work with this brain and any other installed BrainsFor brain."
---

# Yann LeCun Brain Pack — Setup & Configuration

Welcome to the **LeCun Brain Pack** from [brainsforagents.com](https://brainsforagents.com). This is a premium knowledge asset extracted from Yann LeCun's published research papers, academic lectures, public interviews, and video presentations — a curated collection of his most rigorous thinking on deep learning, convolutional networks, world models, and the path to human-level AI.

## What You're Getting

- **609 knowledge atoms** — Core insights, frameworks, and strategic principles from Foundational research papers including the 1989 NeurIPS paper and 1998 IEEE proceedings, Turing Award materials, JEPA path paper, Lex Fridman podcast episodes, and major video lectures from Facebook AI Research and academic institutions
- **616 typed connections** — Relationships between ideas (supports, contradicts, extends, related, inspired_by)
- **8 specialized thinking skills** — Each a distinct reasoning mode with a unique output type
- **A `/board` of advisors** — Convene this brain alongside your other installed brains for one question (needs 2+ brains)
- **Cross-referenced topics** — Convolutional neural networks, world models, self-supervised learning, AI safety, autonomous machines, energy-based models, cognitive architecture, open-source AI, and more

This brain is designed to augment YOUR thinking — not replace it. Use it for strategic decisions, creative problem-solving, research, and to challenge your assumptions.

---

## Setup Instructions

### Step 1: Verify Installation

Your LeCun Brain Pack folder should contain:

```
pack/
  ├── SKILL.md                 ← you are here (brain-setup)
  ├── brain-context.md         ← full knowledge base + usage guide
  ├── brain-atoms.json         ← structured atoms (609 insights)
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
   - JSON structure of 609 atoms with titles, summaries, connections
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

**Recommended:** Run `/brain yann-lecun` at the start of each session. The router writes the active brain to `${BRAINSFOR_HOME:-~/.brainsfor}/state/active-brain.txt` and loads `brain-context.md` as session context. After that, the 8 thinking skills (`/advise`, `/teach`, etc.) will use this brain automatically — no need to retype the slug on every call.

### Step 4: Verify Everything Works

Test your setup with the Quick Start prompt below. You should get a thoughtful response grounded in Yann's thinking.

---

## The 9 Unified Skills

These skills live in `pack/skills/` and are brain-agnostic — they work with Yann LeCun and with any other BrainsFor brain installed under `${BRAINSFOR_HOME:-~/.brainsfor}/brains/`. Set the active brain with `/brain yann-lecun`, or override per call with an inline slug like `/advise yann-lecun <question>`.

### 🎛️ **0. /brain** — Router
Set, show, list, or clear the active brain for the session.
*Usage: `/brain yann-lecun` activates, `/brain` shows current, `/brain list` shows all installed, `/brain clear` unsets.*

### 🧠 **1. /advise** — Strategic Counsel
Ask for advice on decisions grounded in Yann's frameworks. Best for: career moves, company decisions, strategy choices.
*Example: "Should I focus my AI research on scaling transformers or explore alternative architectures like JEPA?"*

### 📚 **2. /teach** — Explain Like I'm Learning
Get a clear explanation of a concept as Yann sees it. Best for: understanding unfamiliar ideas, building mental models.
*Example: "Explain convolutional neural networks to me from first principles, the way LeCun would."*

### 🔥 **3. /debate** — Steel-Man Both Sides
Present a position or pit two ideas against each other; brain argues the counterpoint. Best for: understanding tradeoffs, challenging assumptions, resolving strategic tensions.
*Example: "Is the current path of scaling LLMs sufficient to achieve AGI?"*

### 🔗 **4. /connect** — Bridge Ideas
Find unexpected connections between two concepts or synthesize multiple ideas into something new. Best for: synthesis, innovation, cross-domain thinking.
*Example: "Connect self-supervised learning to the idea of world models in LeCun's framework."*

### 📈 **5. /evolve** — How Ideas Build On Each Other
Trace how a concept develops and changes across the brain. Best for: historical perspective, maturity models, trajectory thinking.
*Example: "How does Yann's thinking on unsupervised learning evolve from his early Bell Labs work to JEPA?"*

### 🎨 **6. /surprise** — Unexpected Insights
Get a random high-quality atom you wouldn't think to ask for. Best for: creative breakthroughs, morning inspiration, breaking tunnel vision.
*Example: No input needed — just run it.*

### 🪞 **7. /coach** — Socratic Questions
No answers — just the questions Yann would ask you. Best for: uncovering blind spots, pressure-testing decisions, team discussions.
*Example: "I'm deciding whether to pursue a PhD in deep learning or join an AI startup. What should I be asking myself?"*

### 🔮 **8. /predict** — Implication Chains
Trace the second and third-order effects of a trend or decision. Best for: forecasting, strategic planning, seeing around corners.
*Example: "What happens to AI safety and autonomy if we successfully build agents with world models?"*

### 🪑 **/board** — Board of Advisors (Multi-Brain)
Ask one question and hear from several thinkers at once. Each installed brain answers **independently** (no brain sees another's answer), then a synthesis names where they agree and where they clash. Best for: high-stakes decisions where you want genuine disagreement, not one voice.
*Requires 2+ brains installed, plus a host that can run parallel sub-agents (Claude Code's Agent tool or Cowork). No MCP server needed — each board member reads its brain's local pack. With only Yann LeCun installed, `/board` will ask you to add another brain from [brainsforagents.com](https://brainsforagents.com).*
*Usage: `/board <question>`, `/board set <slug-a> <slug-b> ...`, `/board list`, `/board clear`.*

---

## Recommended Workflows

Use these skill combinations for better results:

### 🎯 Decision Workflow
→ `/advise` (get perspective) → `/debate` (stress-test) → `/coach` (check your blind spots)

*Example: Deciding on a hire? Get advice, challenge the reasoning, then surface what you're not asking.*

### 📚 Learning Workflow
→ `/teach` (understand) → `/evolve` (see how it develops) → `/coach` (test your understanding)

*Example: New to deep learning? Teach convolutional neural networks → evolve LeCun's thinking on unsupervised learning → coach on choosing a research direction to build foundational understanding.*

### 💡 Creative Workflow
→ `/surprise` (get inspired) → `/connect` (build bridges) → `/predict` (where does this lead?)

*Example: Stuck on a problem? Surprise + connect often surface unexpected angles.*

### 🔮 Forecast Workflow
→ `/predict` (trace implications) → `/debate` (challenge the prediction) → `/advise` (act on it)

*Example: Writing about the limits of LLMs? Debate the scaling hypothesis → connect self-supervised learning to world models → predict implications of JEPA-style architectures → advise on research direction.*

### 🌅 Daily Ritual
→ Run `/surprise` each morning for 10 seconds of strategic inspiration.

---

## Quick Start

**Try this right now to verify setup:**

```
/brain yann-lecun

/advise "I'm trying to understand why LeCun thinks large language models won't be enough to reach human-level AI. What's his core argument?"
```

Or skip the activation step and use an inline slug for a one-off:

```
/advise yann-lecun "I'm trying to understand why LeCun thinks large language models won't be enough to reach human-level AI. What's his core argument?"
```

You should get a thoughtful response that:
- References specific frameworks from the brain
- Weighs tradeoffs from Yann's perspective
- Suggests which of his mental models apply here
- Feels strategic and grounded (not generic)

If you get that, you're all set.

---

## Troubleshooting

**Q: The brain doesn't seem to know what I'm asking about.**
→ Make sure `brain-context.md` is loaded in your session. If using Claude Code, check that the file is in your working directory.

**Q: I want to search the brain for a specific topic.**
→ Use `/advise` with a keyword: `"What does Yann think about world models?"` → The brain will pull all relevant atoms.

**Q: Can I combine skills?**
→ Absolutely. Chain them: `"First /advise on whether to pivot, then /debate the tradeoffs, then /coach me on what I'm missing."`

**Q: What if a skill doesn't feel relevant to my question?**
→ Try a different one. `/coach` often works when you're stuck; `/connect` when you need something original; `/surprise` when you need inspiration.

**Q: How often should I reload the brain?**
→ Once per session is sufficient. Brain context doesn't expire, and atoms don't change. But if you're switching between different projects, fresh context load = sharper thinking.

---

## About Yann LeCun

Yann LeCun is one of the founding fathers of modern deep learning and a Turing Award laureate who pioneered convolutional neural networks and backpropagation. As Chief AI Scientist at Meta and Silver Professor at NYU, he is one of the most influential and contrarian voices on the future of artificial intelligence.

This brain pack extracts and structures his core ideas so you can activate his mental models in your own thinking.

**More:** Visit [brainsforagents.com](https://brainsforagents.com) for other brain packs, documentation, and community.

---

## Sources & Ethics

This brain was built exclusively from **freely available, public sources** — LeCun's peer-reviewed research papers, public academic lectures, IEEE and NeurIPS proceedings, ACM Turing Award materials, Lex Fridman podcast interviews, YouTube lectures, and widely distributed interviews and social media posts.. No transcripts from commercial works (e.g., audiobooks, paid courses) or paywalled essays were used to derive this brain.

Where a thinker's book ideas appear in the knowledge graph, they are represented as they exist in the public discourse: book reviews, author interviews, press coverage, conference talks, and widely discussed concepts. Authors typically share their core ideas through extensive public appearances — those public representations are what this brain captures.

## Support & Feedback

If you encounter issues or have feedback:

1. Check `README.md` for quick answers
2. Verify all files are present and readable
3. Try a fresh load of `brain-context.md`
4. Contact support via [brainsforagents.com](https://brainsforagents.com)

---

**You're ready to think with Yann. Let's go.** 🚀
