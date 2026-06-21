# Gokul Rajaram Brain Pack

> **889 knowledge atoms** · **820 typed connections** · **10 unified skills (1 router + 8 reasoning modes + a board of advisors)**
> From [brainsforagents.com](https://brainsforagents.com)

## What This Is

A structured knowledge graph of Gokul Rajaram's thinking, extracted from Podcast interviews (Invest Like the Best, 20VC, Lenny's Podcast, World of DaaS, Aarthi & Sriram Show), YouTube interviews (Fish Sauce Podcast, Outlier Academy, AI Hackathon 2026, Startupsunedited), conference talks, Medium essays, and decision-making frameworks like SPADE — spanning product leadership at Google AdSense, Facebook Ads, Square/Caviar, and DoorDash, plus angel investing across 700+ companies.. Designed to be loaded as context into any LLM — Claude, ChatGPT, Cursor, or any AI tool that accepts system prompts.

This isn't a chatbot or a persona. It's a **thinking partner** grounded in Gokul's actual ideas, frameworks, and worldview.

## Quick Start

1. Install the brain pack into `${BRAINSFOR_HOME:-~/.brainsfor}/brains/gokul-rajaram/`
2. In your AI tool, activate the brain:
   ```
   /brain gokul-rajaram
   ```
3. Then run any thinking skill:
   ```
   /advise "We're building a two-sided marketplace and debating whether to seed supply or demand first — what does Gokul think about sequencing?"
   ```

You should get a response that cites specific atoms, synthesizes Gokul's perspective, and recommends what to do next.

## What's Inside

```
pack/
  ├── SKILL.md              ← Setup guide + skill reference (start here)
  ├── brain-context.md      ← Full knowledge base (load this as context)
  ├── brain-atoms.json      ← Structured data (889 atoms, 820 connections)
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

- **Install this brain pack first** → `/brain gokul-rajaram` activates it, then `/advise` / `/teach` / `/surprise` all work.
- **Install more brain packs later** → they drop into `${BRAINSFOR_HOME:-~/.brainsfor}/brains/`, auto-registered in `brains/index.json`, and the same 10 skills work for them too. No reinstall, no collisions.
- **Override per call** — `/advise paul-graham should I start a company?` uses Paul Graham for that one call regardless of active brain.
- **Cross-brain mode** — `/debate gokul-rajaram paul-graham originality` contrasts two thinkers; `/board <question>` convenes every installed brain at once (needs 2+).

## The Knowledge Graph

**889 atoms** — Each atom is a self-contained insight with topic tags, source date, confidence score, and source URL.

**820 connections** — Typed relationships between atoms: supports, contradicts, extends, related, inspired_by. These let skills trace reasoning chains and surface productive tensions.

**16 topic clusters** — Product leadership, decision-making (SPADE), ads & monetization architecture, founder mode, AI-era software defensibility, angel investing, startup strategy, hiring PMs, growth loops, platform strategy.

**Date range:** 2010 — 2026

## How to Use

**For Claude Code / Cowork:** The skills in `pack/skills/` load automatically once the pack is installed to `${BRAINSFOR_HOME:-~/.brainsfor}/brains/gokul-rajaram/`. Run `/brain gokul-rajaram` to activate.

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

## About Gokul Rajaram

Gokul Rajaram is one of the most prolific operator-investors in tech — known as the 'Godfather of AdSense' for growing Google's AdSense from zero to $1B+, then leading Ads Product at Facebook (scaling from $750M to $6.5B), holding product leadership roles at Square and DoorDash, and angel investing in 700+ companies (Airtable, Figma, Groq, Runway, Supabase, Vercel, and more). He now runs Marathon Management Partners. His writing and interviews on SPADE decision-making, hiring PMs for spikiness, AI's impact on software defensibility, and founder mode have become required reading and listening for tech operators and investors worldwide.

## Sources & Ethics

This brain pack was built exclusively from **freely available, public sources** — interviews, podcasts, public talks, blog posts, free newsletters, YouTube videos, and publicly shared excerpts. No transcripts from commercial works (e.g., audiobooks, paid courses) or paywalled essays were used to derive this brain.

Where a thinker's book ideas appear in the knowledge graph, they are represented as they exist in the public discourse: book reviews, author interviews, press coverage, conference talks, and LLM-generated summaries of widely discussed concepts. Authors typically share their core ideas through extensive public appearances and media — those public representations are what this brain captures.

## Support

- Full setup guide: `SKILL.md`
- Website: [brainsforagents.com](https://brainsforagents.com)

---

**Load a genius into your AI.**
