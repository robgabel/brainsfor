# Bill Harris Brain Pack

> **483 knowledge atoms** · **469 typed connections** · **10 unified skills (1 router + 8 reasoning modes + a board of advisors)**
> From [brainsforfree.com](https://brainsforfree.com)

## What This Is

A structured knowledge graph of Bill Harris's thinking, extracted from 27 hand-curated sources spanning 2015–2025: multiple long-form podcast interviews (The Proof, ZOE Science & Nutrition, Empowered Nutrition), OmegaMatters podcast episodes, YouTube video lectures and conference keynotes (Bulletproof Biohacking Conference, Omega-3 Index explainers), and supporting press and blog coverage across his OmegaQuant and omega-3 research chapters. Designed to be loaded as context into any LLM — Claude, ChatGPT, Cursor, or any AI tool that accepts system prompts.

This isn't a chatbot or a persona. It's a **thinking partner** grounded in Bill's actual ideas, frameworks, and worldview.

## Quick Start

1. Install the brain pack into `${BRAINSFOR_HOME:-~/.brainsfor}/brains/bill-harris/`
2. In your AI tool, activate the brain:
   ```
   /brain bill-harris
   ```
3. Then run any thinking skill:
   ```
   /advise "I'm 45 years old, I eat salmon once a week, and I take a standard 1g fish oil capsule. Is that enough omega-3 for cardiovascular protection?"
   ```

You should get a response that cites specific atoms, synthesizes Bill's perspective, and recommends what to do next.

## What's Inside

```
pack/
  ├── SKILL.md              ← Setup guide + skill reference (start here)
  ├── brain-context.md      ← Full knowledge base (load this as context)
  ├── brain-atoms.json      ← Structured data (483 atoms, 469 connections)
  ├── README.md             ← You are here
  └── skills/               ← 10 unified skills (work with any installed brain)
      ├── brain/            ← /brain router (set/show/list/clear active brain)
      ├── advise/           ← /advise — strategic counsel
      ├── teach/            ← /teach — explain through the thinker's lens
      ├── debate/           ← /debate — steel-man both sides
      ├── connect/          ← /connect — find unexpected bridges
      ├── evolve/           ← /evolve — trace how thinking changed
      ├── surprise/         ← /surprise — serendipity engine
      ├── coach/            ← /coach — Socratic questioning
      ├── predict/          ← /predict — implication chains
      └── board/            ← /board — board of advisors (needs 2+ brains)
```

## Unified Skill Architecture

Every brain pack ships the **same 10 skill files**. They're brain-agnostic — the 8 thinking skills resolve which brain to use by (1) reading `${BRAINSFOR_HOME:-~/.brainsfor}/state/active-brain.txt`, or (2) taking an inline slug as the first argument.

This means:

- **Install this brain pack first** → `/brain bill-harris` activates it, then `/advise` / `/teach` / `/surprise` all work.
- **Install more brain packs later** → they drop into `${BRAINSFOR_HOME:-~/.brainsfor}/brains/`, auto-registered in `brains/index.json`, and the same 10 skills work for them too. No reinstall, no collisions.
- **Override per call** — `/advise paul-graham should I start a company?` uses Paul Graham for that one call regardless of active brain.
- **Cross-brain mode** — `/debate bill-harris paul-graham originality` contrasts two thinkers; `/board <question>` convenes every installed brain at once (needs 2+).

## The Knowledge Graph

**483 atoms** — Each atom is a self-contained insight with topic tags, source date, confidence score, and source URL.

**469 connections** — Typed relationships between atoms: supports, contradicts, extends, related, inspired_by. These let skills trace reasoning chains and surface productive tensions.

**16 topic clusters** — Omega-3 Index, EPA and DHA, cardiovascular risk biomarkers, brain health, fish oil supplementation, omega-3 deficiency, longevity, fatty acid science, seed oils, Fatty15, dose-response relationships.

**Date range:** 2015 — 2025

## How to Use

**For Claude Code / Cowork:** The skills in `pack/skills/` load automatically once the pack is installed to `${BRAINSFOR_HOME:-~/.brainsfor}/brains/bill-harris/`. Run `/brain bill-harris` to activate.

**For Cursor:** Add `brain-context.md` to your `.cursor/rules` or project instructions, then use the skill prompts as templates.

**For ChatGPT / Claude.ai:** Paste `brain-context.md` as your first message or system prompt, then describe which skill behavior you want (e.g. "respond as /advise would").

**For any other tool:** Load `brain-context.md` as context at the start of your session.

## Skill Workflows

Chain skills for deeper results (all can be prefixed with a brain slug or rely on the active brain):

- **Decide:** `/advise` → `/debate` → `/coach`
- **Learn:** `/teach` → `/evolve` → `/coach`
- **Create:** `/surprise` → `/connect` → `/predict`
- **Forecast:** `/predict` → `/debate` → `/advise`
- **Daily ritual:** `/surprise` each morning

## Cross-Brain Features

Install multiple brain packs and the unified skills auto-discover all of them via `${BRAINSFOR_HOME:-~/.brainsfor}/brains/index.json`:

- `/connect <slug-a> <slug-b> <topic>` — semantic bridges across two thinkers
- `/debate <slug-a> <slug-b> <position>` — stress-test from two worldviews
- `/board <question>` — a board of advisors: every installed brain answers **independently**, then a synthesis names where they agree and clash. Needs 2+ brains installed and a host that can run parallel sub-agents (Claude Code's Agent tool or Cowork). No MCP server required — each board member reads its brain's local pack files.
- `/brain list` — see everything installed
- `/brain <slug>` — switch active brain without reinstalling anything

## About Bill Harris

Dr. Bill Harris is the world's foremost authority on omega-3 fatty acids and cardiovascular health. He invented the Omega-3 Index — a blood biomarker measuring EPA+DHA levels in red blood cell membranes — and has spent four decades researching how omega-3 status predicts cardiovascular disease risk, cognitive decline, and all-cause mortality. He is the founder and Chief Science Officer of OmegaQuant Analytics, a laboratory he built to make omega-3 testing accessible and standardized. His work has shaped how clinicians, researchers, and informed consumers think about fish oil supplementation, dietary omega-3 sources, and the gap between what we eat and what our cells actually need.

## Sources & Ethics

This brain pack was built exclusively from **freely available, public sources** — interviews, podcasts, public talks, blog posts, free newsletters, YouTube videos, and publicly shared excerpts. No transcripts from commercial works (e.g., audiobooks, paid courses) or paywalled essays were used to derive this brain.

Where a thinker's book ideas appear in the knowledge graph, they are represented as they exist in the public discourse: book reviews, author interviews, press coverage, conference talks, and LLM-generated summaries of widely discussed concepts. Authors typically share their core ideas through extensive public appearances and media — those public representations are what this brain captures.

## Support

- Full setup guide: `SKILL.md`
- Website: [brainsforfree.com](https://brainsforfree.com)

---

**Load a genius into your AI.**
