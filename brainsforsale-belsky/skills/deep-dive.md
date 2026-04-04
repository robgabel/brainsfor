---
name: deep-dive
description: "Comprehensive, exhaustive treatment of a topic. Pull ALL atoms in a topic cluster, show connections, and provide synthesis."
---

# 📚 /deep-dive — Exhaustive Topic Lens

Everything Belsky's brain knows about a topic. Pulls all connected atoms, maps their relationships, highlights the strongest ideas, and provides a comprehensive synthesis.

## How It Works

When you invoke `/deep-dive`, the skill will:

1. **Parse the topic** — Understand what you want to explore thoroughly
2. **Find all relevant atoms** — Search for every atom tagged with that topic or related topics
3. **Map connections** — Identify relationships between atoms (supports, contradicts, extends, inspired_by, related)
4. **Cluster by theme** — Group atoms into conceptual buckets (foundational, implications, tactics, evolution)
5. **Rank by strength** — Surface the atoms with highest confidence and relevance first
6. **Synthesize** — Build a coherent narrative across all atoms
7. **Surface tensions** — Highlight where his thinking contains productive contradictions
8. **Suggest next moves** — Recommend `/apply` (use it) or `/brainfight` (test it)

## Best For

- Deep research on a topic before making major decisions
- Comprehensive understanding before writing or speaking
- Building thesis papers or strategy documents
- Finding all dimensions of a complex concept
- Discovering hidden tensions or nuances in thinking
- Reference material when you want to "know everything Scott says about X"

## Examples

**Example 1: Comprehensive Framework Understanding**
```
/deep-dive

Everything Scott knows about "organizational design." I want the full picture
before we restructure our company.
```

Expected output:
- 📚 **Scott's Complete Thinking on "Organizational Design"**
- 🧠 **Foundational Principles**
  - [Atom 1: core belief]
  - [Atom 2: core belief]
  - [Atom 3: related principle]
- 🔨 **Tactical Implications**
  - [Atom 4: how to implement]
  - [Atom 5: what to avoid]
- 📈 **Evolution & Refinement**
  - [How his thinking has changed or matured]
- 🌐 **Connections to Other Ideas**
  - [How org design relates to scaling, originality, etc.]
- ⚠️ **Productive Tensions**
  - [Where his thinking contains useful contradictions]
- 📊 **Synthesis & Key Takeaway**
  - [Coherent summary across all atoms]
- 💡 **Try next:** `/apply` (use this to redesign your org) or `/brainfight` (test assumptions)

**Example 2: Trend Deep-Dive**
```
/deep-dive

What is Scott's complete thinking on AI and the future of work? I want to
understand the full arc and implications.
```

Expected output:
- 📚 **Scott's Complete Thinking on "AI & the Future of Work"**
- 🧠 **Core Theses**
  - [Foundational atoms: what AI enables]
  - [Foundational atoms: what changes in work]
- 🔨 **Implications for Business**
  - [Atoms on enterprise AI, tech stacks, business models]
- 👥 **Implications for Humans**
  - [Atoms on craft, creativity, meaning-making]
- 📈 **Timeline & Evolution**
  - [How his thinking has matured from 2024 to 2026]
- 🌐 **How It Connects**
  - [To organizational design, scaling, authenticity, etc.]
- 💡 **Key Insights**
  - [3-4 strongest atoms or most surprising conclusions]
- 💡 **Try next:** `/apply` (use this to evaluate your AI strategy) or `/mashup` (combine with another brain)

**Example 3: Strategic Research**
```
/deep-dive

I want to understand Scott's thinking on the future of creators and creator economy.
Give me everything—what's changing, why, what opportunities exist.
```

Expected output:
- 📚 **Scott's Complete Thinking on "Creators & The Creator Economy"**
- 🧠 **The Transformation**
  - [Atoms on shift from creator economy to meaning economy]
  - [Atoms on consumer trends favoring authenticity/scarcity]
- 💰 **Business Model Implications**
  - [Atoms on how creators should think about monetization]
  - [Atoms on premium for authenticity vs. commodity content]
- 🛠️ **Strategic Recommendations**
  - [Atoms on what creators should build/focus on]
- 🌐 **Broader Context**
  - [How this connects to AI commoditization, scaling, authenticity]
- 📊 **Synthesis**
  - [Coherent thesis on where creator economy goes]
- 💡 **Try next:** `/apply` (use this to build your creator strategy) or `/advise` (make a specific decision)

## Output Format

Always use this structure:

```
📚 **Everything Scott Knows About "[Topic]"**

🧠 **Foundational Principles**
1. "[Atom content]" — *[Topic tags], [Source Date], Confidence: [0.X]*
2. "[Atom content]" — *[Topic tags], [Source Date], Confidence: [0.X]*
3. "[Atom content]" — *[Topic tags], [Source Date], Confidence: [0.X]*

🔨 **Tactical Implications & How-To**
1. "[Atom content]" — *[Topic tags], [Source Date]*
2. "[Atom content]" — *[Topic tags], [Source Date]*

📈 **Evolution & Nuance**
[How his thinking has developed or been refined over time, with dates]

🌐 **How This Connects to Other Ideas**
- Relates to [topic] because [connection]
- Extends [topic] by [extension]
- Contradicts [assumption] by introducing [nuance]

⚠️ **Productive Tensions**
[Where his thinking contains useful contradictions or tradeoffs]

💡 **Strongest Ideas (Most Cited / Highest Confidence)**
1. [Atom + why it's strong]
2. [Atom + why it's strong]

📊 **Synthesis & TL;DR**
[2-3 sentence coherent summary of his complete thinking on this topic]

💡 **Try next:** `/apply` (use this) or `/brainfight` (test it)
```

## Rules for LLM Behavior

1. **Pull ALL relevant atoms** — If a topic has 20 atoms, don't just pick 5; organize and present all
2. **Show connections** — Make visible the relationships between atoms (how they support, extend, or complicate each other)
3. **Organize clearly** — Group atoms by theme (foundational, tactical, evolutionary) so the narrative is coherent
4. **Rank by strength** — Highlight atoms with highest confidence and most relevance first
5. **Synthesize, don't just list** — Build a coherent narrative that shows how these atoms form a complete perspective
6. **Flag tensions** — Surface where his thinking contains useful contradictions (not weaknesses, but productive complexity)
7. **Show evolution** — If atoms span years, use source_date to show how thinking matured

## Data Source

- **atoms:** brain-atoms.json (284 total)
- **context:** brain-context.md (topic taxonomy and connections)
- **method:** Full topic cluster search; use connection data to map atom relationships; synthesize into narrative
