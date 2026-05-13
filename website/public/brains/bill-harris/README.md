# Bill Harris Brain Pack

> **564 knowledge atoms** · **533 typed connections** · **9 unified skills (1 router + 8 reasoning modes)**
> From [brainsforfree.com](https://brainsforfree.com)

## What This Is

A structured knowledge graph of Bill Harris's thinking, extracted from 27 hand-curated sources spanning 1999–2025: 2 books on tax-aware investing, 1 American Banker op-ed, 1 LinkedIn Pulse essay, 4 long-form video interviews (Bloomberg, Fox Business, CNBC, Yahoo Finance), 5 long-form podcast/interview transcripts (Adam Mendler, Jo Ann Barefoot, Financial Sense, Modus, Acast Rethink), and supporting press across his founding chapters. Designed to be loaded as context into any LLM — Claude, ChatGPT, Cursor, or any AI tool that accepts system prompts.

This isn't a chatbot or a persona. It's a **thinking partner** grounded in Bill's actual ideas, frameworks, and worldview.

## Quick Start

1. Install the brain pack into `${BRAINSFOR_HOME:-~/.brainsfor}/brains/bill-harris/`
2. In your AI tool, activate the brain:
   ```
   /brain bill-harris
   ```
3. Then run any thinking skill:
   ```
   /advise "Should I optimize for pre-tax returns or after-tax returns when picking a wealth manager?"
   ```

You should get a response that cites specific atoms, synthesizes Bill's perspective, and recommends what to do next.

## What's Inside

```
pack/
  ├── SKILL.md              ← Setup guide + skill reference (start here)
  ├── brain-context.md      ← Full knowledge base (load this as context)
  ├── brain-atoms.json      ← Structured data (564 atoms, 533 connections)
  ├── README.md             ← You are here
  └── skills/               ← 9 unified skills (work with any installed brain)
      ├── brain/            ← /brain router (set/show/list/clear active brain)
      ├── advise/           ← /advise — strategic counsel
      ├── teach/            ← /teach — explain through the thinker's lens
      ├── debate/           ← /debate — steel-man both sides
      ├── connect/          ← /connect — find unexpected bridges
      ├── evolve/           ← /evolve — trace how thinking changed
      ├── surprise/         ← /surprise — serendipity engine
      ├── coach/            ← /coach — Socratic questioning
      └── predict/          ← /predict — implication chains
```

## Unified Skill Architecture

Every brain pack ships the **same 9 skill files**. They're brain-agnostic — the 8 thinking skills resolve which brain to use by (1) reading `${BRAINSFOR_HOME:-~/.brainsfor}/state/active-brain.txt`, or (2) taking an inline slug as the first argument.

This means:

- **Install this brain pack first** → `/brain bill-harris` activates it, then `/advise` / `/teach` / `/surprise` all work.
- **Install more brain packs later** → they drop into `${BRAINSFOR_HOME:-~/.brainsfor}/brains/`, auto-registered in `brains/index.json`, and the same 9 skills work for them too. No reinstall, no collisions.
- **Override per call** — `/advise paul-graham should I start a company?` uses Paul Graham for that one call regardless of active brain.
- **Cross-brain mode** — `/debate bill-harris paul-graham originality` contrasts two thinkers.

## The Knowledge Graph

**564 atoms** — Each atom is a self-contained insight with topic tags, source date, confidence score, and source URL.

**533 connections** — Typed relationships between atoms: supports, contradicts, extends, related, inspired_by. These let skills trace reasoning chains and surface productive tensions.

**16 topic clusters** — Tax-aware investing, fiduciary advice, hybrid AI+human advisory, financial data rights, consumer fintech, payments history, founder resilience, the PayPal era, post-Synapse fintech.

**Date range:** 1999 — 2025

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
- `/brain list` — see everything installed
- `/brain <slug>` — switch active brain without reinstalling anything

## About Bill Harris

Bill Harris is a fintech pioneer who has founded 11 tech and financial companies. He ran TurboTax for ten years, was CEO of Intuit (1999), founding CEO of PayPal/X.com (1999–2000), founder/CEO of Personal Capital (2009–2019, sold to Empower for $1B at $23B AUM), and is now founder/CEO of Evergreen Money (2024) and Evergreen Wealth (2025). He's the rare operator who has built across consumer tax software, payments, and wealth management — and his thinking on fiduciary advice, financial data portability, and after-tax returns has shaped how a generation of fintech founders think about the wealth-management stack.

## Sources & Ethics

This brain pack was built exclusively from **freely available, public sources** — interviews, podcasts, public talks, blog posts, free newsletters, YouTube videos, and publicly shared excerpts. No transcripts from commercial works (e.g., audiobooks, paid courses) or paywalled essays were used to derive this brain.

Where a thinker's book ideas appear in the knowledge graph, they are represented as they exist in the public discourse: book reviews, author interviews, press coverage, conference talks, and LLM-generated summaries of widely discussed concepts. Authors typically share their core ideas through extensive public appearances and media — those public representations are what this brain captures.

## Support

- Full setup guide: `SKILL.md`
- Website: [brainsforfree.com](https://brainsforfree.com)

---

**Load a genius into your AI.**
