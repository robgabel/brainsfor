# Jensen Huang Brain Pack

> **253 knowledge atoms** · **1000 typed connections** · **9 unified skills (1 router + 8 reasoning modes)**
> From [brainsforfree.com](https://brainsforfree.com)

## What This Is

A structured knowledge graph of Jensen Huang's thinking, extracted from Lex Fridman Podcast #494, Acquired Podcast NVIDIA episode, Joe Rogan Experience #2422, Computer History Museum Oral History, Stanford GSB View From The Top, GTC 2024/2025 Keynotes, 60 Minutes profile, Stripe Sessions with Patrick Collison, All-In Podcast, Dwarkesh Patel interview, Stanford SIEPR Economic Summit, and Hoover Institution interview. Designed to be loaded as context into any LLM — Claude, ChatGPT, Cursor, or any AI tool that accepts system prompts.

This isn't a chatbot or a persona. It's a **thinking partner** grounded in Jensen's actual ideas, frameworks, and worldview.

## Quick Start

1. Install the brain pack into `${BRAINSFOR_HOME:-~/.brainsfor}/brains/jensen-huang/`
2. In your AI tool, activate the brain:
   ```
   /brain jensen-huang
   ```
3. Then run any thinking skill:
   ```
   /advise "Should I build my own AI infrastructure or rent from hyperscalers?"
   ```

You should get a response that cites specific atoms, synthesizes Jensen's perspective, and recommends what to do next.

## What's Inside

```
pack/
  ├── SKILL.md              ← Setup guide + skill reference (start here)
  ├── brain-context.md      ← Full knowledge base (load this as context)
  ├── brain-atoms.json      ← Structured data (253 atoms, 1000 connections)
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

- **Install this brain pack first** → `/brain jensen-huang` activates it, then `/advise` / `/teach` / `/surprise` all work.
- **Install more brain packs later** → they drop into `${BRAINSFOR_HOME:-~/.brainsfor}/brains/`, auto-registered in `brains/index.json`, and the same 9 skills work for them too. No reinstall, no collisions.
- **Override per call** — `/advise paul-graham should I start a company?` uses Paul Graham for that one call regardless of active brain.
- **Cross-brain mode** — `/debate jensen-huang paul-graham originality` contrasts two thinkers.

## The Knowledge Graph

**253 atoms** — Each atom is a self-contained insight with topic tags, source date, confidence score, and source URL.

**1000 connections** — Typed relationships between atoms: supports, contradicts, extends, related, inspired_by. These let skills trace reasoning chains and surface productive tensions.

**16 topic clusters** — accelerated computing, CUDA, first-principles thinking, AI factories, sovereign AI, organizational design, resilience, supply chain strategy, physical AI, market creation.

**Date range:** 1993 — April 2026

## How to Use

**For Claude Code / Cowork:** The skills in `pack/skills/` load automatically once the pack is installed to `${BRAINSFOR_HOME:-~/.brainsfor}/brains/jensen-huang/`. Run `/brain jensen-huang` to activate.

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

## About Jensen Huang

Jensen Huang is the co-founder and CEO of NVIDIA, which he has led since its founding at a Denny's restaurant in 1993. Under his leadership, NVIDIA invented the GPU, created the CUDA programming platform, and transformed from a gaming graphics company into the engine behind the AI revolution — becoming one of the most valuable companies in the world. He is known for first-principles thinking, an unusually flat organizational structure with 50+ direct reports, and the conviction to bet the entire company on markets that don't yet exist.

## Sources & Ethics

This brain pack was built exclusively from **freely available, public sources** — interviews, podcasts, public talks, blog posts, free newsletters, YouTube videos, and publicly shared excerpts. No transcripts from commercial works (e.g., audiobooks, paid courses) or paywalled essays were used to derive this brain.

Where a thinker's book ideas appear in the knowledge graph, they are represented as they exist in the public discourse: book reviews, author interviews, press coverage, conference talks, and LLM-generated summaries of widely discussed concepts. Authors typically share their core ideas through extensive public appearances and media — those public representations are what this brain captures.

## Support

- Full setup guide: `SKILL.md`
- Website: [brainsforfree.com](https://brainsforfree.com)

---

**Load a genius into your AI.**
