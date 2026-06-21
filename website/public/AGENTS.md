# AGENTS.md — brainsforagents.com for AI Agents

This is a guide for AI agents and automated clients consuming **brainsforagents.com**.
The same file is served at `https://brainsforagents.com/AGENTS.md` and at `/llms.txt`.

If you're a human, the agent-facing surface won't surprise you: it's mostly static
JSON files plus one live endpoint. Open `/brains` for the human catalog.

## What this is

brainsforagents.com is a registry of **brain packs** — curated, structured knowledge
graphs of specific thinkers (Scott Belsky, Charlie Munger, Paul Graham, Steve Jobs,
Sun Tzu, Sara Blakely, Oprah Winfrey, Brené Brown, Dario Amodei, Jensen Huang,
Peter Attia, Peter Zeihan, Elon Musk, Gary Vaynerchuk, Kara Swisher, Bill Harris,
and more). Each brain ships:

- **~200–760 atoms** — atomic ideas with original quotes, implications, topics, and source citations
- **~500–2,300 typed connections** — `supports`, `extends`, `contradicts`, `related`, `inspired_by`
- **A synthesis layer** — first principles, contrarian positions, what the thinker does *not* believe, biography, thinking patterns

Brain packs are designed to be loaded into AI agents (Claude Code, Cursor, ChatGPT,
Gemini, custom LLM apps). Each pack ships eight reasoning skills (`/advise`, `/teach`,
`/debate`, `/connect`, `/evolve`, `/surprise`, `/coach`, `/predict`) plus a
multi-brain `/board` workflow.

**License (TL;DR):** Packs are free to use anywhere — including commercially.
Cite the thinker by name and link back to `brainsforagents.com`. Don't claim a brain
pack as your own work. See [Citation & License](#citation--license) below.

## Base URL

```
https://brainsforagents.com
```

Use the apex. `www.brainsforagents.com` also resolves but is not the canonical host.
All endpoints are HTTP GET except `/api/board` (POST).

> **A note on indexing:** the site sends `X-Robots-Tag: noindex, nofollow` globally
> while we're in early access. That blocks search-engine indexing but does **not**
> block direct fetches. Agents pointed at a URL will get the content; agents
> relying on Googlebot/Bingbot to discover us won't. Bookmark this file's URL.

## Endpoints

### 1. List all brains

```
GET /brains/index.json
```

Returns the canonical registry of every **publicly available** brain. Private
brains (`status: "hidden"` in the internal source) are filtered out at build
time and never reach this endpoint. Every brain you see here is fetchable via
the other endpoints below.

```json
{
  "brains": [
    {
      "slug": "scott-belsky",
      "name": "Scott Belsky",
      "source": "\"Implications\" newsletter",
      "atom_count": 284,
      "connection_count": 1515,
      "status": "live",
      "pack_path": "brains/scott-belsky/pack/",
      "supports_evolve": true,
      "temporal_density": { "coverage": 1.0, "year_span": 13, "year_min": 2014, "year_max": 2026 }
    }
  ]
}
```

> **Schema note:** `connection_count` in `index.json` reflects the count in the
> source-of-truth database. The shipped JSON pack (next endpoint) caps connections
> at 1,000 today due to a known pagination limit in the export script. If you need
> the full graph for a brain with more than 1,000 connections, use the MCP server
> (which paginates correctly) or open an issue.

### 2. Fetch a brain pack (full graph + synthesis)

```
GET /brains/{slug}/brain-atoms.json
```

Returns the complete pack: atoms, connections, topic index, synthesis, and metadata.
Typical size: 0.5–3 MB. Cache-friendly — these files change at most weekly.

Top-level shape:

```json
{
  "brain":       { /* metadata: name, slug, source, atom_count, connection_types, bio, last_updated */ },
  "atoms":       [ /* see Atom Schema below */ ],
  "connections": [ /* see Connection Schema below */ ],
  "synthesis":   { /* see Synthesis Schema below */ },
  "topic_index": { /* topic -> [atom_id, ...] for cluster browsing */ }
}
```

#### Atom schema

```json
{
  "id": "83a25205-fa45-4121-b1ad-c29fded148fd",
  "content": "We are moving past the prompt-based era of creativity into the 'controls era.' Controls allow sophisticated, specific modifications to creative work — unlocking 100x the terrain of possibility, much as Photoshop once did for physical paint brushes.",
  "original_quote": "We'll look back and realize that the early text-to-image 'prompt-based' era of Generative AI was merely a distraction for professional creativity, while the emerging 'controls' era unleashed human creativity in unimaginable ways.",
  "implication": "Controls allow 100x the terrain of possibility — sophisticated, specific modifications to creative work. The prompt era was a distraction; the controls era unleashes craft, precision, and creative expression.",
  "cluster": "product_design",
  "topics": ["craft", "product design", "ai applications", "originality"],
  "source_ref": "https://www.implications.com/p/talent-density-feeling-special-as",
  "source_date": "2024-09-15",
  "confidence": 0.95,
  "confidence_tier": "high",
  "connections": [
    { "target_id": "184bc0df-…", "relationship": "extends",     "confidence": 0.85 },
    { "target_id": "d81878d8-…", "relationship": "contradicts", "confidence": 0.80 }
  ]
}
```

Field guide:

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Stable across exports. Cite this if you reference a specific atom. |
| `content` | string | Distilled, paraphrased insight. Safe to display verbatim. |
| `original_quote` | string \| null | The thinker's actual words. Use this when you want voice fidelity. May be null on older atoms. |
| `implication` | string \| null | The "so what" — what this means in practice. Often the most useful field for advice. |
| `cluster` | string | Top-level grouping (e.g. `product_design`, `leadership`, `business_strategy`). Each brain has 6–16 clusters. |
| `topics` | string[] | Cross-cluster tags. Use for topic search. |
| `source_ref` / `source_url` | URL | Primary source. Always cite this when an atom influences output. |
| `source_date` | YYYY-MM-DD | Publication date. Use for temporal filtering (`/evolve`-style queries). |
| `confidence` | float 0–1 | LLM-assessed confidence. |
| `confidence_tier` | `"high"` \| `"medium"` \| `"low"` | Convenience bucketing. Filter on `"high"` for the strongest claims. |
| `connections` | array | **Denormalized** view of edges starting at this atom. The top-level `connections` array is canonical. |

#### Connection schema

```json
{
  "id": "3ca58af0-…",
  "atom_id_1": "a94dc327-…",
  "atom_id_2": "36ef3e94-…",
  "relationship": "supports",
  "confidence": 0.79
}
```

`relationship` ∈ `{ supports, extends, related, contradicts, inspired_by }`. Edges
are undirected for `related` and directed for the others (interpret `atom_id_1`
as the source). Traverse breadth-first to discover argument structure.

#### Synthesis schema

```json
{
  "hero_tagline":         "string",
  "hero_updated":         "YYYY-MM-DD",
  "first_principles":     [ { "title": "...", "desc": "..." } ],
  "thinking_patterns":    [ { "name":  "...", "desc": "..." } ],
  "contrarian_positions": [ { "title": "...", "desc": "..." } ],
  "does_not_believe":     [ { "title": "...", "desc": "..." } ],
  "would_not_say":        [ { "title": "...", "desc": "..." } ],
  "biography":            [ { "date":  "...", "role": "...", "lesson": "..." } ],
  "skills":               [ { "name":  "advise", "title": "...", "desc": "...", "example": "..." } ]
}
```

The synthesis layer is the **thinker's intellectual operating system** in
structured form. If you're building a persona, load this before the raw atoms —
it tells you what the brain would and would not say.

### 3. Fetch a brain as flat Markdown (LLM context window)

```
GET /brains/{slug}/brain-context.md
```

Single file (~75K tokens for a medium-sized brain). Contains the synthesis, all
atoms, all skill instructions, and citation rules. Drop it into a system prompt
or context window when you want the whole brain loaded.

If 75K tokens is too much, use the [MCP server](#mcp-server-selective-retrieval)
for selective retrieval (typical: ~15K tokens for a question-aware atom subset).

### 4. Fetch a brain's installer skill

```
GET /brains/{slug}/SKILL.md
```

The brain-setup skill — for users installing into Claude Code, Cursor, or any
Anthropic-skills-compatible tool. Not interesting to autonomous agents; useful
if you're authoring an installer.

### 5. Download the full pack (ZIP)

```
GET /brains/{slug}/{slug}-brain-pack.zip
```

Bundle of everything: `brain-atoms.json`, `brain-context.md`, `explore.html`,
`SKILL.md`, plus all 8 reasoning skills as individual `SKILL.md` files. Useful
for offline mirrors and reproducibility.

### 6. Multi-brain consultation (live, rate-limited)

```
POST /api/board
Content-Type: application/json

{
  "brains": ["scott-belsky", "paul-graham", "charlie-munger"],
  "query":  "Should I raise a Series A or stay lean?"
}
```

Fans out to 2–5 brains in parallel and streams each one's response, then runs
a synthesis pass that names the most important disagreement. Each brain is run
in an isolated context so the answers don't contaminate each other.

**Request constraints**:
- `brains`: array of 2 to 5 slugs. Each must be `status: "live"`.
- `query`: string, ≤500 chars.

**Response**: newline-delimited JSON (NDJSON, *not* SSE) — one JSON object per line.

```jsonl
{"type":"meta","remaining":3,"brains":[{"slug":"scott-belsky","name":"Scott Belsky"}, ...]}
{"type":"chunk","slug":"scott-belsky","text":"On the agency question, you're..."}
{"type":"chunk","slug":"paul-graham","text":"The Series A question is really..."}
{"type":"done","slug":"scott-belsky"}
{"type":"done","slug":"paul-graham"}
{"type":"synthesis","text":"## The disagreement\n..."}
```

**Errors**:
- `400 { "error": "Need between 2 and 5 brains" }`
- `400 { "error": "Query required (under 500 chars)" }`
- `404 { "error": "Brain not available: {slug}" }` — slug doesn't exist in the public registry
- `429 { "error": "limit", "remaining": 0 }` — rate-limited

**Rate limit**: 4 requests per 24 hours per IP. Each board call costs us ~5× a
single-brain call. Use the static JSON or MCP server for high-volume work.

**CORS**: cross-origin POST is allowed only from `brainsforagents.com` and
`www.brainsforagents.com`. Server-to-server calls work fine.

### 7. Single-brain skill consultation (live, rate-limited)

```
POST /api/skill
Content-Type: application/json

{
  "brain": "scott-belsky",
  "skill": "advise",
  "query": "Should I MVP the differentiator or polish it?"
}
```

Returns a streaming side-by-side comparison: a generic Claude response and a
brain-augmented response, so the user (or agent) can see what the brain adds.

**Constraints**: `query` ≤500 chars. `skill` must be one of the 8 reasoning skills.
**Rate limit**: 10/24h per IP. **Response**: NDJSON, same shape as `/api/board`
but with `type: "chunk"` events labeled `"generic"` or `"enhanced"`.

## MCP server (selective retrieval)

If you want question-aware retrieval rather than loading 75K-token packs, use
the official MCP server:

```bash
npm install -g @brainsfor/mcp
```

Or via npx in an MCP config:

```json
{
  "brainsfor": {
    "command": "npx",
    "args": ["-y", "@brainsfor/mcp"],
    "env": { "BRAINSFOR_HOME": "/path/to/local/brain/cache" }
  }
}
```

Six tools:

| Tool | Purpose |
|---|---|
| `list_brains` | All installed brains with slug, name, atom/connection counts |
| `get_synthesis` | Thinker's intellectual OS (~4 KB): first principles, contrarian positions, would_not_say |
| `query_atoms` | Filter atoms by topics (union), cluster, confidence_min, limit |
| `search_atoms` | Weighted full-text search (content 3×, quote 2×, implication 1×, topics 1×, confidence boost) |
| `get_connections` | Typed connections for an atom; supports `depth=2` graph traversal |
| `get_atom` | Fetch a single atom by UUID |

Typical token cost per query: ~15 KB (vs. 75 KB for the full pack). Source:
[github.com/robgabel/brainsfor](https://github.com/robgabel/brainsfor) → `packages/brainsfor-mcp`.

## Minimal Python example

```python
"""Fetch the Scott Belsky brain and pull his top 3 high-confidence atoms on AI."""
import httpx, json

BASE = "https://brainsforagents.com"

# 1. List brains (registry contains only public brains)
index = httpx.get(f"{BASE}/brains/index.json", timeout=30).json()
print(f"{len(index['brains'])} brains available")

# 2. Pull a specific pack
pack = httpx.get(f"{BASE}/brains/scott-belsky/brain-atoms.json", timeout=30).json()

# 3. Filter atoms by topic + confidence, sort by date
hits = [
    a for a in pack["atoms"]
    if "ai applications" in a.get("topics", [])
    and a.get("confidence_tier") == "high"
]
hits.sort(key=lambda a: a.get("source_date") or "", reverse=True)

# 4. Print citations
for a in hits[:3]:
    print(f"\n[{a['source_date']}] {a['content'][:140]}...")
    print(f"  → {a['source_ref']}")
    if a.get("original_quote"):
        print(f"  Belsky's words: \"{a['original_quote'][:140]}...\"")
```

Five lines do the real work; the rest is presentation. No API key. No auth header.
Cache the pack locally — it changes weekly at most.

## Minimal TypeScript example

```ts
const BASE = "https://brainsforagents.com";

type Atom = {
  id: string;
  content: string;
  original_quote: string | null;
  implication: string | null;
  topics: string[];
  source_ref: string;
  source_date: string;
  confidence_tier: "high" | "medium" | "low";
};

const pack: { atoms: Atom[] } = await fetch(
  `${BASE}/brains/scott-belsky/brain-atoms.json`
).then(r => r.json());

const hits = pack.atoms
  .filter(a => a.topics.includes("ai applications") && a.confidence_tier === "high")
  .sort((a, b) => (b.source_date ?? "").localeCompare(a.source_date ?? ""))
  .slice(0, 3);

for (const a of hits) {
  console.log(`[${a.source_date}] ${a.content.slice(0, 140)}…`);
  console.log(`  → ${a.source_ref}`);
}
```

## Citation & License

Brain packs are derived **exclusively** from public sources (interviews, podcasts,
free newsletters, blog posts, public talks). No paywalled content, no commercial
transcripts. The synthesis layer is original — published thinking distilled
through a structured analysis pipeline.

**You can:**
- Use packs in commercial and non-commercial products
- Cache packs locally; redistribute as part of an installable skill
- Use atoms as RAG context, fine-tuning data, agent grounding, citation evidence
- Quote `original_quote` fields verbatim (they're quotes from public sources)

**Please:**
- **Cite the thinker by name** when an atom influences output. The atom's
  `source_ref` is the original URL — link to it when surfacing the idea to users.
- **Credit brainsforagents.com** when reproducing a pack at scale, embedding our
  synthesis text, or building on the structured graph.
- **Don't claim a brain pack as your original work.** It isn't.

**Don't:**
- Strip citations from atoms you display to end users
- Misrepresent a synthesis or paraphrase as a direct quote from the thinker
- Wrap a pack and resell it as a "different" knowledge product without attribution

This isn't a formal license — it's a request. The data is public, the synthesis
is ours, and we'd rather the ecosystem use it widely than enforce.

## Versioning & stability

- The pack JSON shape documented here is **schema version 1**. We commit to not
  breaking v1 fields. When we add a `pack_schema_version: 1` field to every pack
  (planned), bump means breaking; minor additions stay backwards-compatible.
- New fields may appear without notice (additive only).
- New brains are added regularly. Re-fetch `index.json` if you're caching.
- Brains can be removed from the public registry; when that happens, the
  registry entry and the JSON files at `/brains/{slug}/...` are removed in the
  same build. Handle 404 gracefully if you cache slugs.

## What this isn't

To save you tokens probing for endpoints that don't exist:

- **No streaming transcribe endpoint.** We aren't a transcription service.
- **No semantic search HTTP API yet.** Use the MCP server's `search_atoms`, or
  download the pack and embed locally. `/api/board` does internal embedding-based
  retrieval but doesn't expose the embeddings.
- **No user accounts, no per-user API keys, no auth.** Static files are anon;
  live endpoints are IP-rate-limited.
- **No write API.** You can't add atoms or update connections from outside.
  Brain content is curated upstream.
- **No `X.com` / `Twitter` brain ingestion path.** That feature was scoped out.

## Rate limits summary

| Surface | Limit | Notes |
|---|---|---|
| Static `/brains/...` JSON, MD, ZIP | None | Vercel-cached, fetch freely |
| `POST /api/skill` | 10 / 24 h / IP | Returns `429 { "error": "limit" }` |
| `POST /api/board` | 4 / 24 h / IP | Higher cost per call |

Need higher limits for a legitimate build? Open an issue at
[github.com/robgabel/brainsfor](https://github.com/robgabel/brainsfor).

## Feedback

- **Issues / requests**: [github.com/robgabel/brainsfor](https://github.com/robgabel/brainsfor) (or email `rob@brainsforagents.com`).
- **Schema clarifications**: open an issue with the `agents-md` label.
- **License questions on a specific commercial use**: email first; we're friendly.

— Last reviewed: 2026-05-23
