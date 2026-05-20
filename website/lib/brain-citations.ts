import fs from "fs";
import path from "path";

/**
 * Match the verbatim "..." quoted strings in a model's response back to atoms
 * in a brain's brain-atoms.json. Returns a list of citations the UI can render
 * as clickable links — closing the gap between "this looks like a quote" and
 * "this IS the quote, here's the URL to the original."
 *
 * The brain-atoms.json files are big (several MB for some brains), so we cache
 * a slim per-slug index of just {original_quote, source_ref, source_date}.
 */

interface AtomLike {
  id?: string;
  original_quote?: string;
  content?: string;
  source_ref?: string;
  source_date?: string;
  confidence?: number;
}

export interface Citation {
  quote: string;
  url: string | null;
  date: string | null;
  /** A truncated quote suitable for chip display. */
  preview: string;
}

interface AtomIndexEntry {
  normalized: string; // normalized for fuzzy match
  quote: string;
  url: string | null;
  date: string | null;
}

const BRAINS_DIR = fs.existsSync(
  path.join(process.cwd(), "..", "brains", "index.json"),
)
  ? path.join(process.cwd(), "..", "brains")
  : path.join(process.cwd(), "public", "brains");

const indexCache = new Map<string, AtomIndexEntry[]>();

function normalize(s: string): string {
  return s
    .toLowerCase()
    .replace(/[‘’“”]/g, "'")
    .replace(/[^a-z0-9' ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function validateSlug(slug: string): void {
  if (/[./\\]/.test(slug)) {
    throw new Error(`Invalid slug: ${slug}`);
  }
}

function loadAtomIndex(slug: string): AtomIndexEntry[] {
  validateSlug(slug);
  const cached = indexCache.get(slug);
  if (cached) return cached;

  // Local dev pack location, then public/ fallback for Vercel.
  const localPath = path.join(BRAINS_DIR, slug, "pack", "brain-atoms.json");
  const vercelPath = path.join(BRAINS_DIR, slug, "brain-atoms.json");
  const filePath = fs.existsSync(localPath)
    ? localPath
    : fs.existsSync(vercelPath)
      ? vercelPath
      : null;

  if (!filePath) {
    indexCache.set(slug, []);
    return [];
  }

  try {
    const raw = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    const atoms: AtomLike[] = Array.isArray(raw.atoms) ? raw.atoms : [];
    const index: AtomIndexEntry[] = atoms
      .map((a) => {
        const q = a.original_quote ?? a.content ?? "";
        if (!q) return null;
        return {
          normalized: normalize(q),
          quote: q,
          url: a.source_ref ?? null,
          date: a.source_date ?? null,
        };
      })
      .filter((x): x is AtomIndexEntry => x !== null);
    indexCache.set(slug, index);
    return index;
  } catch {
    indexCache.set(slug, []);
    return [];
  }
}

/**
 * Extract verbatim atom quotes from the response. Preferred path: a single
 * "GROUNDED ON:" marker line emitted by the model with quotes joined by " || ".
 * Fallback path (for older callers and skills): scan the whole response for
 * any "...quoted string..." longer than 12 chars.
 */
function extractQuotedStrings(text: string): string[] {
  const markerIdx = text.search(/^\s*GROUNDED ON:/im);
  if (markerIdx >= 0) {
    // Take everything after the marker on its line (and any continuation).
    const after = text.slice(markerIdx).replace(/^\s*GROUNDED ON:\s*/i, "");
    // Split on " || " (any spacing) into segments, strip quotes around each.
    const segments = after.split(/\s*\|\|\s*/).map((s) => s.trim());
    const out: string[] = [];
    for (const seg of segments) {
      // Pull the first "..." (or "...") out of the segment.
      const m = seg.match(/["“]([^"“”]{8,400})["”]/);
      if (m) out.push(m[1].trim());
    }
    if (out.length > 0) return out;
  }

  // Fallback: inline quotes anywhere in the response.
  const matches: string[] = [];
  const re = /["“]([^"“”]{12,400})["”]/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    matches.push(m[1].trim());
  }
  return matches;
}

/**
 * Strip the "GROUNDED ON: ..." marker (and anything after it) from a response
 * so the visible answer doesn't include the attribution shim. The marker is
 * for internal citation matching — the user sees clickable source chips
 * rendered separately by the UI.
 */
export function stripGroundingMarker(text: string): string {
  const idx = text.search(/^\s*GROUNDED ON:/im);
  if (idx < 0) return text;
  return text.slice(0, idx).trimEnd();
}

/**
 * For each quoted snippet in the response, look up the best-matching atom.
 * Uses normalized prefix/substring matching — a 30-char prefix is enough to
 * uniquely identify an atom in practice, and tolerates the model trimming or
 * lightly paraphrasing the tail. Returns at most 5 citations, deduped by URL.
 */
export function findCitations(slug: string, responseText: string): Citation[] {
  const index = loadAtomIndex(slug);
  if (index.length === 0) return [];

  const quotes = extractQuotedStrings(responseText);
  if (quotes.length === 0) return [];

  const seenUrls = new Set<string>();
  const citations: Citation[] = [];

  for (const q of quotes) {
    const nq = normalize(q);
    // Strong prefix or strong substring match. We pick the longest matched atom
    // to avoid spurious short-substring collisions.
    let best: AtomIndexEntry | null = null;
    let bestScore = 0;
    for (const entry of index) {
      let score = 0;
      if (entry.normalized.startsWith(nq.slice(0, 40))) {
        score = nq.length * 2; // prefix match — strong signal
      } else if (entry.normalized.includes(nq.slice(0, 40))) {
        score = nq.length;
      } else if (nq.startsWith(entry.normalized.slice(0, 40))) {
        score = entry.normalized.length;
      }
      if (score > bestScore) {
        bestScore = score;
        best = entry;
      }
    }
    if (best && bestScore >= 30) {
      const url = best.url ?? "";
      if (url && seenUrls.has(url)) continue;
      if (url) seenUrls.add(url);
      citations.push({
        quote: best.quote,
        url: best.url,
        date: best.date,
        preview: best.quote.length > 90 ? best.quote.slice(0, 87) + "…" : best.quote,
      });
    }
    if (citations.length >= 5) break;
  }

  return citations;
}
