# Loading the Scott Belsky Brain Pack into Your AI Agent

How to install this brain pack so it guides your agent's decisions.

---

## What's in This Pack

```
pack/
  brain-context.md         ~300KB   Full knowledge base — the file your AI loads
  brain-atoms.json         ~1MB     Structured data (1086 atoms, 1174 typed connections)
  SKILL.md                 ~13KB    Setup guide + skill reference
  README.md                ~4KB     Quick start
  INTEGRATION-GUIDE.md              You are here
  skills/                  9 dirs   1 router + 8 reasoning modes (brain-agnostic)
```

| File | Who reads it | What it contains |
|------|-------------|-----------------|
| `brain-context.md` | Your AI agent | Scott's synthesized worldview, all 1086 atoms with original quotes and implications, persona rules, skill instructions |
| `brain-atoms.json` | Code / MCP server | Same atoms as structured JSON — topics, connections, confidence scores, source URLs |
| `skills/` | Claude Code / Cowork | 8 thinking modes (`/advise`, `/teach`, `/debate`, `/connect`, `/evolve`, `/surprise`, `/coach`, `/predict`) + 1 router (`/brain`) |

---

## Three Integration Paths

Pick the one that matches how you want Scott's brain to work in your agent.

### Path A: CLAUDE.md Injection (Simplest — Always-On)

Paste `brain-context.md` into your project's `CLAUDE.md`. Every conversation in that project gets shaped by Scott's thinking.

**Best for:** "I want every decision in this project filtered through Scott's lens."

**Steps:**

1. Copy this pack's contents into your project:
   ```bash
   cp -r path/to/scott-belsky-v2/pack ./brain-pack
   ```

2. Append the brain context to your project's `CLAUDE.md`:
   ```bash
   echo "" >> CLAUDE.md
   echo "# Brain: Scott Belsky" >> CLAUDE.md
   echo "" >> CLAUDE.md
   cat brain-pack/brain-context.md >> CLAUDE.md
   ```

3. Open Claude Code in your project. The brain is now active — every conversation is informed by Scott's frameworks, first principles, and guardrails.

**Verify it works:** Ask your agent a strategy question and check that the response cites specific ideas from Scott, not generic advice. Try `I'm building a creative tool and trying to decide whether to optimize for power users or beginners. What would Scott think?`.

**Tradeoff:** ~75K tokens of context loaded on every conversation. For a project where you always want this lens, that's a feature. For occasional use, Path B is lighter.

---

### Path B: MCP Server (Selective — On-Demand)

Register the BrainsFor MCP server. Your agent queries specific atoms when facing decisions relevant to Scott's expertise.

**Best for:** "I want to consult Scott's brain when relevant, not load it on every message."

**Cost:** Zero. Fully local — no API keys, no hosting, no network calls. A Node.js process reads JSON files from disk.

**Steps:**

1. Install this brain pack to the standard location:
   ```bash
   mkdir -p ~/.brainsfor/brains
   cp -r path/to/scott-belsky-v2 ~/.brainsfor/brains/scott-belsky-v2
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
   `BRAINSFOR_HOME` should point to the directory containing `brains/` (where you copied this pack).

4. Restart Claude Code. The MCP server auto-starts and exposes 6 tools:

   | Tool | What it does |
   |------|-------------|
   | `list_brains` | Show all installed brains |
   | `get_synthesis` | Load Scott's intellectual OS (~4KB) |
   | `query_atoms` | Filter atoms by topic, cluster, or confidence |
   | `search_atoms` | Full-text search across all atoms |
   | `get_connections` | Trace reasoning chains between atoms |
   | `get_atom` | Fetch a single atom by ID |

**Verify it works:** In Claude Code, ask "what brains do I have installed?" — the agent should call `list_brains` and show `scott-belsky-v2`.

**Tradeoff:** The agent must decide when to query the brain. It won't shape every response automatically. Pair with a line in your `CLAUDE.md` like:

```
When making strategic decisions, consult the BrainsFor MCP server
for relevant atoms from Scott Belsky before recommending an approach.
```

---

### Path C: Skill Pack (Most Controlled — Explicit Invocation)

Install the 9 skill files. You invoke specific thinking modes by name.

**Best for:** "I want structured reasoning tools I can call when I need them."

**Steps:**

1. Copy the skills to your Claude Code skills directory:
   ```bash
   cp -r path/to/scott-belsky-v2/pack/skills/* ~/.claude/skills/
   ```

2. Copy the brain pack to the standard location so skills can find it:
   ```bash
   mkdir -p ~/.brainsfor/brains
   cp -r path/to/scott-belsky-v2 ~/.brainsfor/brains/scott-belsky-v2
   ```

3. Activate the brain in a Claude Code session:
   ```
   /brain scott-belsky-v2
   ```

4. Use any thinking skill:
   ```
   /advise Should I optimize my product for breadth of users or depth of engagement?
   /debate Is taste something you're born with or can it be trained?
   /predict What happens to the creative industry when AI can generate anything on demand?
   /surprise
   ```

**Verify it works:** Run `/brain list` — you should see `scott-belsky-v2`. Then run `/surprise` — you should get a specific atom from Scott, not generic advice.

**Tradeoff:** Requires explicit invocation. The brain won't shape ambient decisions — you pull from it intentionally. Most precise, least overhead.

---

## Combining Paths

These paths aren't mutually exclusive. Common combos:

| Combo | Effect |
|-------|--------|
| **A + B** | brain-context.md in CLAUDE.md for ambient Scott guidance + MCP server for deep atom queries when the agent needs specifics |
| **B + C** | MCP for programmatic access + skills for structured reasoning modes |
| **A + C** | Always-on context + explicit skill invocations for targeted analysis |

---

## Why Brains Aren't Interchangeable

The same question produces genuinely different answers depending on which brain you load. Each brain encodes different first principles, different `does_not_believe` guardrails, and different atoms of actual thinking.

**Same question: "Should I launch this product now or wait until it's more polished?"**

- **Scott Belsky** (taste, agency, craft) → Push you toward shipping, but interrogate whether you're shipping with taste or just shipping fast.
- **Dario Amodei** (compute scaling, responsible AI) → Reframe as "what risks does launching create?" — define your evals, red lines, and rollback plan first.
- **Oprah Winfrey** (authentic connection, audience empathy) → Ask who this is *for* and whether it makes them feel seen. Polish is irrelevant if it doesn't connect.

This is why installing multiple brains gives you genuinely different perspectives — and why `/board` (multi-brain advisory) and `/debate <brain-a> <brain-b>` (cross-brain) work. Scott Belsky brings a specific worldview to your decisions; pair with other brains for productive tension.

Browse the full catalog at [brainsforagents.com](https://brainsforagents.com).

---

## Requirements

| Requirement | Path A | Path B | Path C |
|-------------|--------|--------|--------|
| This brain pack | Yes | Yes | Yes |
| Node.js | No | Yes | No |
| Claude Code | Recommended | Yes | Yes |
| Network / API keys | No | No | No |
| Hosting | No | No | No |

All three paths run entirely on your machine. No cloud services, no API keys beyond what your AI tool itself requires, no ongoing costs.

---

## For Other AI Tools

This brain pack isn't Claude Code-exclusive. The core asset — `brain-context.md` — works anywhere that accepts system prompts or context injection:

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

- This pack's `SKILL.md` has detailed setup and skill reference
- This pack's `README.md` has a quick-start guide
- Full brain catalog: [brainsforagents.com](https://brainsforagents.com)
