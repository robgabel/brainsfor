# Loading the Charlie Munger Brain Pack into Your AI Agent

How to install this brain pack so it guides your agent's decisions.

---

## What's in This Pack

```
pack/
  brain-context.md         ~300KB   Full knowledge base — the file your AI loads
  brain-atoms.json         ~1MB     Structured data (1066 atoms, 1045 typed connections)
  SKILL.md                 ~13KB    Setup guide + skill reference
  README.md                ~4KB     Quick start
  INTEGRATION-GUIDE.md              You are here
  skills/                  10 dirs  1 router + 8 reasoning modes + /board (brain-agnostic)
```

| File | Who reads it | What it contains |
|------|-------------|-----------------|
| `brain-context.md` | Your AI agent | Charlie's synthesized worldview, all 1066 atoms with original quotes and implications, persona rules, skill instructions |
| `brain-atoms.json` | Code / MCP server | Same atoms as structured JSON — topics, connections, confidence scores, source URLs |
| `skills/` | Claude Code / Cowork | 8 thinking modes (`/advise`, `/teach`, `/debate`, `/connect`, `/evolve`, `/surprise`, `/coach`, `/predict`) + 1 router (`/brain`) + `/board` (multi-brain advisory; needs 2+ brains installed) |

---

## Three Integration Paths

Pick the one that matches how you want Charlie's brain to work in your agent.

### Path A: CLAUDE.md Injection (Simplest — Always-On)

Paste `brain-context.md` into your project's `CLAUDE.md`. Every conversation in that project gets shaped by Charlie's thinking.

**Best for:** "I want every decision in this project filtered through Charlie's lens."

**Steps:**

1. Copy this pack's contents into your project:
   ```bash
   cp -r path/to/charlie-munger/pack ./brain-pack
   ```

2. Append the brain context to your project's `CLAUDE.md`:
   ```bash
   echo "" >> CLAUDE.md
   echo "# Brain: Charlie Munger" >> CLAUDE.md
   echo "" >> CLAUDE.md
   cat brain-pack/brain-context.md >> CLAUDE.md
   ```

3. Open Claude Code in your project. The brain is now active — every conversation is informed by Charlie's frameworks, first principles, and guardrails.

**Verify it works:** Ask your agent a strategy question and check that the response cites specific ideas from Charlie, not generic advice. Try `I'm sitting on a great business I understand that's slightly overpriced, or a mediocre business I barely understand that's cheap. Which should I buy?`.

**Tradeoff:** ~75K tokens of context loaded on every conversation. For a project where you always want this lens, that's a feature. For occasional use, Path B is lighter.

---

### Path B: MCP Server (Selective — On-Demand)

Register the BrainsFor MCP server. Your agent queries specific atoms when facing decisions relevant to Charlie's expertise.

**Best for:** "I want to consult Charlie's brain when relevant, not load it on every message."

**Cost:** Zero. Fully local — no API keys, no hosting, no network calls. A Node.js process reads JSON files from disk.

**Steps:**

1. Install this brain pack to the standard location:
   ```bash
   mkdir -p ~/.brainsfor/brains
   cp -r path/to/charlie-munger ~/.brainsfor/brains/charlie-munger
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
   | `get_synthesis` | Load Charlie's intellectual OS (~4KB) |
   | `query_atoms` | Filter atoms by topic, cluster, or confidence |
   | `search_atoms` | Full-text search across all atoms |
   | `get_connections` | Trace reasoning chains between atoms |
   | `get_atom` | Fetch a single atom by ID |

**Verify it works:** In Claude Code, ask "what brains do I have installed?" — the agent should call `list_brains` and show `charlie-munger`.

**Tradeoff:** The agent must decide when to query the brain. It won't shape every response automatically. Pair with a line in your `CLAUDE.md` like:

```
When making strategic decisions, consult the BrainsFor MCP server
for relevant atoms from Charlie Munger before recommending an approach.
```

---

### Path C: Skill Pack (Most Controlled — Explicit Invocation)

Install the 9 skill files. You invoke specific thinking modes by name.

**Best for:** "I want structured reasoning tools I can call when I need them."

**Steps:**

1. Copy the skills to your Claude Code skills directory:
   ```bash
   cp -r path/to/charlie-munger/pack/skills/* ~/.claude/skills/
   ```

2. Copy the brain pack to the standard location so skills can find it:
   ```bash
   mkdir -p ~/.brainsfor/brains
   cp -r path/to/charlie-munger ~/.brainsfor/brains/charlie-munger
   ```

3. Activate the brain in a Claude Code session:
   ```
   /brain charlie-munger
   ```

4. Use any thinking skill:
   ```
   /advise I'm thinking about making a large concentrated bet on a single company I've studied deeply. Am I being bold or reckless?
   /debate Is it better to be a specialist who knows one industry deeply or a generalist with a latticework of mental models?
   /predict What are the second and third-order effects of AI replacing large categories of knowledge work?
   /surprise
   ```

**Verify it works:** Run `/brain list` — you should see `charlie-munger`. Then run `/surprise` — you should get a specific atom from Charlie, not generic advice.

**Tradeoff:** Requires explicit invocation. The brain won't shape ambient decisions — you pull from it intentionally. Most precise, least overhead.

---

## Combining Paths

These paths aren't mutually exclusive. Common combos:

| Combo | Effect |
|-------|--------|
| **A + B** | brain-context.md in CLAUDE.md for ambient Charlie guidance + MCP server for deep atom queries when the agent needs specifics |
| **B + C** | MCP for programmatic access + skills for structured reasoning modes |
| **A + C** | Always-on context + explicit skill invocations for targeted analysis |

---

## Why Brains Aren't Interchangeable

The same question produces genuinely different answers depending on which brain you load. Each brain encodes different first principles, different `does_not_believe` guardrails, and different atoms of actual thinking.

**Same question: "Should I launch this product now or wait until it's more polished?"**

- **Scott Belsky** (taste, agency, craft) → Push you toward shipping, but interrogate whether you're shipping with taste or just shipping fast.
- **Dario Amodei** (compute scaling, responsible AI) → Reframe as "what risks does launching create?" — define your evals, red lines, and rollback plan first.
- **Oprah Winfrey** (authentic connection, audience empathy) → Ask who this is *for* and whether it makes them feel seen. Polish is irrelevant if it doesn't connect.

This is why installing multiple brains gives you genuinely different perspectives — and why the cross-brain skills work. Charlie Munger brings a specific worldview to your decisions; pair with other brains for productive tension.

**The two cross-brain skills (both ship in `pack/skills/`):**

- `/debate <brain-a> <brain-b> <position>` — two thinkers attack the same position from opposite worldviews. Works from the pack files alone; nothing extra to install.
- `/board <question>` — a **board of advisors**: every installed brain answers the question *independently* (no brain sees another's answer), then a synthesis names the agreements and the splits. This needs:
  - **2 or more brains installed** under `${BRAINSFOR_HOME:-~/.brainsfor}/brains/` (a board of one is just `/advise`), and
  - **a host that can run parallel sub-agents** — Claude Code's Agent/Task tool or Cowork. The independence is the point: it's what stops the brains from converging into one averaged answer.
  - It does **not** require the MCP server — each board member reads its brain's local `brain-context.md` / `brain-atoms.json`. (If MCP is installed, members can use it for selective retrieval instead.)

  > Heads-up: with only **one** brain installed, `/board` will tell you to add another from [brainsforagents.com](https://brainsforagents.com) rather than convene a board of one.

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
