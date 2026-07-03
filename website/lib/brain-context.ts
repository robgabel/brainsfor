import fs from "fs";
import path from "path";

// Same resolution pattern as lib/brains.ts
const BRAINS_DIR = fs.existsSync(
  path.join(process.cwd(), "..", "brains", "index.json"),
)
  ? path.join(process.cwd(), "..", "brains")
  : path.join(process.cwd(), "public", "brains");

const contextCache = new Map<string, string>();

function validateSlug(slug: string): void {
  if (/[./\\]/.test(slug)) {
    throw new Error(`Invalid slug: ${slug}`);
  }
}

export function loadBrainContext(slug: string): string {
  validateSlug(slug);

  const cacheKey = `context:${slug}`;
  const cached = contextCache.get(cacheKey);
  if (cached) return cached;

  // Local dev: ../brains/{slug}/pack/brain-context.md
  // Vercel: public/brains/{slug}/brain-context.md
  const localPath = path.join(BRAINS_DIR, slug, "pack", "brain-context.md");
  const vercelPath = path.join(BRAINS_DIR, slug, "brain-context.md");

  const filePath = fs.existsSync(localPath) ? localPath : vercelPath;
  const content = fs.readFileSync(filePath, "utf-8");
  contextCache.set(cacheKey, content);
  return content;
}

// Synthesis-section headings emitted by export-brain.py ahead of the atom
// dump. Everything from the first heading NOT in this set onward is the
// per-cluster atom dump (the bulk of the file).
const SYNTHESIS_HEADING_RE =
  /^## (LLM Usage Rules|How .+ Thinks|First Principles|Thinking Patterns|Contrarian Positions|What .+ Does NOT Believe|What .+ Would NOT Say|Biographical Pattern|Hard Lessons)/;

// The synthesis slice of brain-context.md: usage rules + how-they-think
// (first principles, patterns, contrarian positions, guardrails, biography)
// WITHOUT the multi-hundred-KB atom dump. The API routes pair this with the
// question-relevant atoms from retrieveRelevantAtoms(), which is the whole
// point of retrieval — sending the full dump on every call cost ~150-220K
// input tokens per request and re-anchored the model on the headline thesis
// the ANTI-DEFAULT rule fights.
export function loadBrainContextLite(slug: string): string {
  validateSlug(slug);

  const cacheKey = `lite:${slug}`;
  const cached = contextCache.get(cacheKey);
  if (cached) return cached;

  const full = loadBrainContext(slug);
  const lines = full.split("\n");
  let cutAt = lines.length;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.startsWith("## ") && !SYNTHESIS_HEADING_RE.test(line)) {
      cutAt = i;
      break;
    }
  }
  const lite =
    lines.slice(0, cutAt).join("\n").trimEnd() +
    "\n\n(The full atom knowledge base is omitted here — the atoms most relevant to the current question are provided separately in the RELEVANT ATOMS FOR THIS QUESTION block.)\n";
  contextCache.set(cacheKey, lite);
  return lite;
}

// Returns the brain's first-person voice intro (the "hear them think" snippet
// shown above the fold on /brains/[slug]). Returns null when no intro.md has
// been authored yet — caller falls back to brain.bio.
export function loadBrainIntro(slug: string): string | null {
  validateSlug(slug);

  const cacheKey = `intro:${slug}`;
  const cached = contextCache.get(cacheKey);
  if (cached !== undefined) return cached || null;

  const localPath = path.join(BRAINS_DIR, slug, "pack", "intro.md");
  const vercelPath = path.join(BRAINS_DIR, slug, "intro.md");
  const filePath = fs.existsSync(localPath)
    ? localPath
    : fs.existsSync(vercelPath)
      ? vercelPath
      : null;

  if (!filePath) {
    contextCache.set(cacheKey, "");
    return null;
  }

  const content = fs.readFileSync(filePath, "utf-8").trim();
  contextCache.set(cacheKey, content);
  return content || null;
}

export function loadSkillPrompt(slug: string, skill: string): string {
  validateSlug(slug);
  validateSlug(skill);

  const cacheKey = `skill:${slug}:${skill}`;
  const cached = contextCache.get(cacheKey);
  if (cached) return cached;

  // Local dev: two naming conventions exist:
  //   ../brains/{slug}/pack/skills/{skill}.md/SKILL.md (belsky, jobs, attia)
  //   ../brains/{slug}/pack/skills/{skill}/SKILL.md (pg, greens, sun-tzu)
  // Vercel: public/brains/{slug}/skills/{skill}.md (flattened by sync script)
  const localPathDotMd = path.join(
    BRAINS_DIR,
    slug,
    "pack",
    "skills",
    `${skill}.md`,
    "SKILL.md",
  );
  const localPathPlain = path.join(
    BRAINS_DIR,
    slug,
    "pack",
    "skills",
    skill,
    "SKILL.md",
  );
  const vercelPath = path.join(BRAINS_DIR, slug, "skills", `${skill}.md`);

  const filePath = fs.existsSync(localPathDotMd)
    ? localPathDotMd
    : fs.existsSync(localPathPlain)
      ? localPathPlain
      : vercelPath;
  const content = fs.readFileSync(filePath, "utf-8");
  contextCache.set(cacheKey, content);
  return content;
}
