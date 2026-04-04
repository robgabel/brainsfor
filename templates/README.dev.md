# Brain Pack Template System — Developer Guide

## Architecture

```
brainsforsale/
  brains/                    ← Brain configs (one per thinker)
    belsky.json
    {slug}.json
  templates/                 ← Shared templates (never edit per-brain)
    SKILL.md.template
    README.md.template
    skills/
      advise.md.template
      teach.md.template
      ... (10 total)
  scripts/
    export-brain.py          ← Generic export pipeline
  brainsforsale-{slug}/      ← Rendered output (ships to customers)
```

## How It Works

1. Brain config (`brains/{slug}.json`) provides all per-brain values
2. Supabase stores atoms + connections + brain metadata
3. `export-brain.py` reads data + config → renders templates → outputs a complete brain pack

One command, any brain:

```bash
python scripts/export-brain.py --brain belsky --from-files atoms.json connections.json
```

## Template Variables

Templates use `{{variable}}` syntax. Nested keys use dots: `{{skill_examples.advise}}`.

### Core Variables

| Variable | Example (Belsky) | Used In |
|----------|-------------------|---------|
| `brain_name` | Scott Belsky | All files |
| `brain_first_name` | Scott | All files |
| `brain_last_name` | Belsky | All skill files |
| `brain_slug` | belsky | SKILL.md, README.md |
| `brain_possessive` | his | SKILL.md |
| `brain_source_description` | "Implications" newsletter | SKILL.md |
| `brain_source_url` | implications.com | brain-context.md |
| `brain_source_detail` | 77 editions of the Implications newsletter | SKILL.md, README.md |
| `brain_tagline` | a curated collection of... | SKILL.md |
| `brain_bio` | Full bio paragraph | SKILL.md, README.md |
| `atom_count` | 284 | All files |
| `connection_count` | 161 | SKILL.md, README.md |
| `topic_examples` | Superhumanity, originality, AI agents... | SKILL.md, README.md |
| `example_topic` | emergence | SKILL.md |
| `date_range` | May 2014 — April 2026 | README.md, brain-context.md |
| `quick_start_prompt` | I'm thinking about whether to... | SKILL.md |

### Skill Examples (per-skill one-liner)

| Variable | Used In |
|----------|---------|
| `skill_examples.advise` | SKILL.md |
| `skill_examples.debate` | SKILL.md |
| `skill_examples.apply` | SKILL.md |
| `skill_examples.teach` | SKILL.md |
| `skill_examples.deep_dive` | SKILL.md |
| `skill_examples.connect` | SKILL.md |
| `skill_examples.brainfight` | SKILL.md |
| `skill_examples.mashup` | SKILL.md |
| `skill_examples.evolve` | SKILL.md |

### Workflow Examples

| Variable | Used In |
|----------|---------|
| `workflow_examples.learning` | SKILL.md |
| `workflow_examples.research` | SKILL.md |

### Cluster Config

`clusters` — JSON object mapping cluster keys to `{name, description}`. Used by export script to generate brain-context.md and brain-atoms.json.

`cluster_order` — JSON array of cluster keys in display order.

## Adding a New Brain

### 1. Create brain config

Copy `brains/belsky.json` as a starting point:

```bash
cp brains/belsky.json brains/{newslug}.json
```

Edit all values. The key authoring work is:
- `brain_bio` — 2-3 sentence bio
- `brain_tagline` — One-line description of the source material
- `skill_examples.*` — One-liner examples using this thinker's frameworks
- `workflow_examples.*` — Workflow narratives for this thinker's domains
- `quick_start_prompt` — A prompt that tests the brain's core thinking
- `clusters` — Topic taxonomy for this brain's atoms
- `cluster_order` — Display order

### 2. Create Supabase tables

```sql
-- Atoms table (same schema as belsky_atoms)
CREATE TABLE {slug}_atoms (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content text NOT NULL,
  source_type text,
  source_ref text,
  source_date timestamptz,
  confidence float,
  topics text[],
  cluster text,
  embedding vector(1536),
  created_at timestamptz DEFAULT now()
);

-- Connections table
CREATE TABLE {slug}_connections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  atom_id_1 uuid REFERENCES {slug}_atoms(id),
  atom_id_2 uuid REFERENCES {slug}_atoms(id),
  relationship text CHECK (relationship IN ('supports','contradicts','extends','related','inspired_by')),
  confidence float,
  created_at timestamptz DEFAULT now()
);

-- Brain metadata row
INSERT INTO brain_metadata (slug, name, ..., atoms_table, connections_table, status)
VALUES ('{slug}', '{Name}', ..., '{slug}_atoms', '{slug}_connections', 'draft');
```

### 3. Ingest atoms

Load the source material, extract atoms, assign clusters, generate embeddings, create connections. (Ingestion pipeline is brain-specific — see individual brain build notes.)

### 4. Export

```bash
# From local files
python scripts/export-brain.py --brain {slug} --from-files atoms.json connections.json

# Output appears in brainsforsale-{slug}/
```

### 5. Verify

- `brain-atoms.json` — correct atom/connection counts, all clusters assigned, connections inline
- `brain-context.md` — all clusters present, atoms organized by date
- `SKILL.md` — all template vars rendered, no `{{}}` remaining
- `skills/*.md` — name references match, atom counts correct

## Supabase Schema

### brain_metadata

Stores one row per brain. All config values from `brains/{slug}.json` are mirrored here. The flat file is used for local exports; Supabase is source of truth.

Key fields:
- `slug` (unique) — Brain identifier
- `atoms_table` — Name of the Supabase table holding this brain's atoms
- `connections_table` — Name of the connections table
- `status` — `draft` | `active` | `archived`
- `clusters` (jsonb) — Full cluster metadata
- `skill_examples` (jsonb) — Per-skill example prompts

### {slug}_atoms

One row per knowledge atom. Schema matches `knowledge_atoms` but separated per brain.

### {slug}_connections

Typed relationships between atoms within this brain.

### cross_connections

Cross-brain connections (e.g., Rob's atoms linked to Belsky's). Uses atom IDs from different brain tables.

## Pipeline Flow

```
Source Material (newsletter, book, podcast, etc.)
  ↓
Ingestion (extract atoms, assign topics, generate embeddings)
  ↓
Supabase ({slug}_atoms + {slug}_connections)
  ↓
export-brain.py --brain {slug}
  ↓
brainsforsale-{slug}/
  ├── brain-atoms.json      (from Supabase data)
  ├── brain-context.md      (from Supabase data)
  ├── SKILL.md              (from template + config)
  ├── README.md             (from template + config)
  └── skills/*.md           (from templates + config)
  ↓
npx skills add brainsforsale-{slug}
```
