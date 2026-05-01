# BrainsFor Integration Guide

How to load a brain pack into your AI agent so it guides decisions.

---

## What's in a Brain Pack

Every brain pack ships the same structure:

```
pack/
  brain-context.md      ~300KB   Full knowledge base — the file your AI loads
  brain-atoms.json      ~1MB     Structured data (atoms + typed connections + synthesis)
  SKILL.md              ~13KB    Setup guide + skill reference
  README.md             ~4KB     Quick start
  skills/               9 dirs   1 router + 8 reasoning modes (brain-agnostic)
```

| File | Who reads it | What it contains |
|------|-------------|-----------------|
| `brain-context.md` | Your AI agent | Synthesis of the thinker's worldview, all atoms with quotes and implications, persona rules, skill instructions |
| `brain-atoms.json` | Code / MCP server | Same atoms as structured JSON — topics, connections, confidence scores, source URLs |
| `skills/` | Claude Code / Cowork | 8 thinking modes (`/advise`, `/teach`, `/debate`, `/connect`, `/evolve`, `/surprise`, `/coach`, `/predict`) + 1 router (`/brain`) |

---

## Three Integration Paths

Pick the one that matches how you want the brain to work.

### Path A: CLAUDE.md Injection (Simplest — Always-On)

Paste `brain-context.md` into your project's `CLAUDE.md`. The brain becomes ambient context for every conversation.

**Best for:** "I want every decision in this project shaped by this thinker."

**Steps:**

1. Copy the brain pack to your project:
   ```bash
   cp -r path/to/dario-amodei/pack ./brain-pack
   ```

2. Add the brain context to your project's `CLAUDE.md`:
   ```bash
   echo "" >> CLAUDE.md
   echo "# Brain: Dario Amodei" >> CLAUDE.md
   echo "" >> CLAUDE.md
   cat brain-pack/brain-context.md >> CLAUDE.md
   ```

3. Open Claude Code in your project. The brain is now active — every conversation is informed by the thinker's frameworks, first principles, and guardrails.

**Verify it works:** Ask your agent a strategy question and check that the response cites specific ideas from the thinker, not generic advice.

**Tradeoff:** ~75K tokens of context loaded on every conversation. For a project where you always want this lens, that's a feature. For occasional use, Path B is lighter.

---

### Path B: MCP Server (Selective — On-Demand)

Register the BrainsFor MCP server. Your agent can query specific atoms when facing decisions relevant to the thinker's expertise.

**Best for:** "I want to consult the brain when relevant, not load it every time."

**Cost:** Zero. Fully local — no API keys, no hosting, no network calls. Just a Node.js process reading JSON files from disk.

**Steps:**

1. Install the brain pack(s) to the standard location:
   ```bash
   mkdir -p ~/.brainsfor/brains
   cp -r path/to/dario-amodei ~/.brainsfor/brains/dario-amodei
   ```

2. Build the MCP server (requires Node.js):
   ```bash
   cd path/to/brainsfor/packages/brainsfor-mcp
   npm install && npm run build
   ```

3. Register the MCP server in your project's `.mcp.json`:
   ```json
   {
     "brainsfor": {
       "command": "node",
       "args": ["/absolute/path/to/brainsfor-mcp/dist/index.js"],
       "env": {
         "BRAINSFOR_HOME": "/absolute/path/to/your/brainsfor"
       }
     }
   }
   ```
   `BRAINSFOR_HOME` should point to the directory containing `brains/` (where you copied the packs).

4. Restart Claude Code. The MCP server auto-starts and exposes 6 tools:

   | Tool | What it does |
   |------|-------------|
   | `list_brains` | Show all installed brains |
   | `get_synthesis` | Load a thinker's intellectual OS (~4KB) |
   | `query_atoms` | Filter atoms by topic, cluster, or confidence |
   | `search_atoms` | Full-text search across all atoms |
   | `get_connections` | Trace reasoning chains between atoms |
   | `get_atom` | Fetch a single atom by ID |

**Verify it works:** In Claude Code, ask "what brains do I have installed?" — the agent should call `list_brains` and show your installed packs.

**Tradeoff:** The agent must decide when to query the brain. It won't shape every response automatically — it queries on demand. Pair with a line in your `CLAUDE.md` like:

```
When making strategic decisions, consult the BrainsFor MCP server
for relevant atoms before recommending an approach.
```

---

### Path C: Skill Pack (Most Controlled — Explicit Invocation)

Install the 9 skill files. You invoke specific thinking modes by name.

**Best for:** "I want structured reasoning tools I can call when I need them."

**Steps:**

1. Copy the skills to your Claude Code skills directory:
   ```bash
   cp -r path/to/dario-amodei/pack/skills/* ~/.claude/skills/
   ```

2. Copy the brain pack to the standard location so skills can find it:
   ```bash
   mkdir -p ~/.brainsfor/brains
   cp -r path/to/dario-amodei ~/.brainsfor/brains/dario-amodei
   ```

3. Activate the brain in a Claude Code session:
   ```
   /brain dario-amodei
   ```

4. Use any thinking skill:
   ```
   /advise Should I raise a Series A now or bootstrap longer?
   /debate Is constitutional AI a competitive moat or a constraint?
   /predict What happens if we open-source our safety research?
   /surprise
   ```

**Verify it works:** Run `/brain list` — you should see your installed brain(s). Then run `/surprise` — you should get a specific atom from the thinker, not generic advice.

**Tradeoff:** Requires explicit invocation. The brain won't shape ambient decisions — you pull from it intentionally. Most precise, least overhead.

---

## Combining Paths

These paths aren't mutually exclusive. Common combos:

| Combo | Effect |
|-------|--------|
| **A + B** | Brain-context.md in CLAUDE.md for ambient guidance + MCP server for deep atom queries when the agent needs specifics |
| **B + C** | MCP for programmatic access + skills for structured reasoning modes |
| **A + C** | Always-on context + explicit skill invocations for targeted analysis |

---

## How Different Brains Produce Different Decisions

Same question: **"Should I launch this product now or wait until it's more polished?"**

### Scott Belsky (product craft, creative leadership)

> First principles: *Taste is the ultimate human moat. Agency beats optimization. Craft survives abundance.*

Belsky pushes you toward shipping — but with taste. He'd argue that waiting for perfection is a form of procrastination, that "the messy middle" is where real products are forged, and that the market rewards agency over polish. But he'd also challenge whether you're shipping *craft* or just shipping fast. Does your product have a point of view? Does it reflect taste? If yes, launch. If you're just shipping to ship, you're optimizing for speed when you should be optimizing for resonance.

### Dario Amodei (AI safety, scaling, responsible development)

> First principles: *Compute is the primary driver of AI progress. Safety and capability are complementary. Interpretability is the most important unsolved problem.*

Amodei would reframe the question entirely. He doesn't think in terms of "polished" — he thinks in terms of *what risks does launching create that you can't undo?* His framework is responsible scaling: launch when you've characterized the risks at the current capability level, not when the UI is pretty. He'd push you to define your evals, your red lines, and your rollback plan. If those exist, launch. If they don't, the product isn't unpolished — it's uncharacterized.

### Oprah Winfrey (authentic connection, audience empathy)

> First principles: *Every person fundamentally wants to know they matter. Your life speaks in whispers before it shouts. What you focus on expands.*

Oprah would ask who this product is *for* and whether it makes them feel seen. Polish is irrelevant if the product doesn't connect authentically. She'd challenge you: have you talked to the people who need this? Do you understand their story? If you're waiting to launch because you're afraid of judgment, that's ego — launch and listen. If you're waiting because you haven't figured out who it serves, that's wisdom — wait and learn.

**Three brains, three genuinely different answers** — because each has different first principles, different `does_not_believe` guardrails, and different atoms of actual thinking driving the response.

---

## Requirements

| Requirement | Path A | Path B | Path C |
|-------------|--------|--------|--------|
| Brain pack files | Yes | Yes | Yes |
| Node.js | No | Yes | No |
| Claude Code | Recommended | Yes | Yes |
| Network / API keys | No | No | No |
| Hosting | No | No | No |

All three paths run entirely on the customer's machine. No cloud services, no API keys beyond what the AI tool itself requires, no ongoing costs.

---

## For Other AI Tools

Brain packs aren't Claude Code-exclusive. The core asset — `brain-context.md` — works anywhere that accepts system prompts or context injection:

| Tool | How to load |
|------|------------|
| **Cursor** | Add `brain-context.md` to `.cursor/rules` or project instructions |
| **ChatGPT** | Paste into Custom Instructions or as the first message in a conversation |
| **Claude.ai** | Paste into the system prompt or Project Knowledge |
| **Windsurf / Cline** | Add to project rules or context files |
| **Any LLM API** | Pass as the system message |

The MCP server (Path B) and skills (Path C) are Claude Code-specific. Path A works everywhere.

---

## Support

- Brain pack catalog: [brainsforfree.com](https://brainsforfree.com)
- Each brain's `SKILL.md` has detailed setup and skill reference
- Each brain's `README.md` has a quick-start guide
