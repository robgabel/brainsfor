import { NextRequest } from "next/server";
import { timingSafeEqual } from "node:crypto";
import Anthropic from "@anthropic-ai/sdk";
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";
import { loadBrainContext, loadSkillPrompt } from "@/lib/brain-context";
import { findCitations } from "@/lib/brain-citations";
import { SKILLS, getBrain } from "@/lib/brains";

export const runtime = "nodejs";

// Owner bypass — constant-time compare so a wrong token can't be probed via
// timing. Returns false if either the request header or the env var is absent.
function hasOwnerBypass(request: NextRequest): boolean {
  const provided = request.headers.get("x-owner-bypass");
  const expected = process.env.OWNER_BYPASS_TOKEN;
  if (!provided || !expected) return false;
  const a = Buffer.from(provided);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}

const VALID_SKILLS = SKILLS.map((s) => s.name);

// --- CORS ---
// Exact-string allowlist. Requests without a matching Origin get no CORS
// headers (same-origin fetches still work; cross-origin fetches from other
// hosts get blocked by the browser).
const CORS_ALLOWED_ORIGINS = new Set([
  "https://brainsforfree.com",
  "https://www.brainsforfree.com",
]);

function corsHeaders(request: NextRequest): Record<string, string> {
  const origin = request.headers.get("origin");
  if (origin && CORS_ALLOWED_ORIGINS.has(origin)) {
    return {
      "Access-Control-Allow-Origin": origin,
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      Vary: "Origin",
    };
  }
  return {};
}

export async function OPTIONS(request: NextRequest) {
  return new Response(null, { status: 204, headers: corsHeaders(request) });
}

// --- Rate limiting (Upstash Redis, durable across Vercel instances) ---
const LIMIT = process.env.NODE_ENV === "development" ? 999 : 10;
const WINDOW = "24 h" as const;

// Lazily initialize — fail closed (no limiter = no requests served in prod)
// only if the envs are missing. In dev we fall back to an always-allow limiter.
let limiter: Ratelimit | null = null;
function getLimiter(): Ratelimit | null {
  if (limiter) return limiter;
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) return null;
  limiter = new Ratelimit({
    redis: new Redis({ url, token }),
    limiter: Ratelimit.slidingWindow(LIMIT, WINDOW),
    analytics: false,
    prefix: "bff:skill",
  });
  return limiter;
}

async function checkRateLimit(
  ip: string,
): Promise<{ allowed: boolean; remaining: number }> {
  // Dev bypass: always allow
  if (process.env.NODE_ENV === "development") {
    return { allowed: true, remaining: LIMIT };
  }
  const rl = getLimiter();
  if (!rl) {
    // Fail closed in prod when envs are missing — surfaces config errors fast.
    console.error(
      "[api/skill] Upstash envs missing — rate limiter unavailable",
    );
    return { allowed: false, remaining: 0 };
  }
  try {
    const { success, remaining } = await rl.limit(ip);
    return { allowed: success, remaining };
  } catch (err) {
    // Upstash unreachable (DNS, network, or DB deleted on the free tier).
    // Fail open so a transient infra outage doesn't black out the demo —
    // the Anthropic budget is the real abuse ceiling.
    console.error("[api/skill] rate-limit check failed, failing open:", err);
    return { allowed: true, remaining: LIMIT };
  }
}

// --- System prompts ---
const BREVITY_GENERIC = `HARD CONSTRAINT: Respond in exactly 4-5 sentences of plain prose. No markdown, no bold, no headers, no bullet points. Plain text only.`;

const BREVITY_ENHANCED = `HARD CONSTRAINTS — FORMAT:

Answer in two paragraphs, all in first person as the thinker.

PARAGRAPH 1 — Your lens (1-2 sentences, ~40 words): State the belief, principle, or framework you apply to questions like this. This is HOW you think about the topic generally, not the specific answer yet. It should sound like your worldview, not generic advice. If you'd reject the question's premise, say so here.

PARAGRAPH 2 — The answer (1-2 sentences, ~40 words): Apply that lens directly to the user's specific situation. Be concrete and opinionated — take a side. Do not hedge.

Separate the two paragraphs with a single blank line so they render distinctly.

After the two paragraphs, on a new line, output EXACTLY this marker line:
GROUNDED ON: "verbatim atom quote one" || "verbatim atom quote two" || "verbatim atom quote three"

The GROUNDED ON line contains 2-3 short verbatim quotes from atoms in the brain context. These are used internally for source attribution — they are not displayed inline to the user. Do NOT include source names, dates, citations, or commentary in this line; only the verbatim quote text in double quotes, separated by " || ".

HARD RULES:
- No hedging, no "it depends," no "consider the trade-offs."
- No markdown, no bold, no headers, no bullets, no numbering.
- Total visible answer (both paragraphs combined) under 90 words.
- Quotes go ONLY in the GROUNDED ON line — never in the visible paragraphs.
- The lens must be specific to you and recognizable as your worldview.`;

// /evolve has its own format because the whole proof point of this skill is
// "vanilla LLMs cannot do this — they don't have temporally-tagged atoms."
// The output must show a *change* across time, not answer the question.
const BREVITY_ENHANCED_EVOLVE = `HARD CONSTRAINTS — EVOLVE FORMAT:

Your job is NOT to answer the user's question. Your job is to trace how YOUR OWN thinking on the topic in the question has CHANGED over time, using the dated atoms in the brain context above. This is the only skill in the catalog that requires temporally-tagged atoms — vanilla LLMs cannot produce this output, and the user is here specifically to see that proof.

Output a 3-era timeline in first person as the thinker. Each era is its own short paragraph. No headers, no bullets, no markdown.

Each era paragraph MUST follow this exact shape:

[year or year range]: Then-current view in 1-2 sentences (under 30 words).

Concrete example structure (do not copy the content — use your own dated material):
2014–2017: I believed X about this topic. The reason was Y.

2019–2021: I started to see that Z was the missing variable. My earlier view was incomplete because…

2023–today: Now I think the real driver is W. The shift came from observing…

The eras must be VISIBLY DIFFERENT in stance, vocabulary, or emphasis. If you cannot find genuine change across 3 eras in the brain context, use 2 eras instead — but the eras must still show real evolution, not paraphrases of each other.

After the timeline, on a new line, output EXACTLY this marker:
GROUNDED ON: "verbatim atom quote from earliest era" || "verbatim atom quote from middle era" || "verbatim atom quote from most recent era"

Each grounding quote MUST come from an atom whose source_date is in the corresponding era. The GROUNDED ON line is hidden from the user and used only for source attribution. Do not include source names or dates in this line.

INTERPRETATION RULES:
- If the user's question is shaped as "How has X changed?" — trace your evolution on X.
- If the user's question is shaped as a "should I…?" or "what about X?" — pivot to "Here is how my thinking about X has changed over time." Do not answer their question directly; trace the evolution.
- Never say "It depends on when you ask me" or other meta-evasions. Show the actual change.

HARD RULES:
- No markdown, no bold, no bullets, no numbering.
- Total visible response under 130 words.
- Quotes go ONLY in the GROUNDED ON line — never in the visible paragraphs.`;

// The skill files below were authored for a CLI brain router. They contain
// sections like "Brain Selection" that tell the model to read ${BRAINSFOR_HOME}
// state files and emit "No active brain" errors if nothing resolves. In this
// API the brain is ALREADY resolved (passed in the POST body and loaded as
// context above this line), so the model must ignore any router instructions
// and just answer as the thinker.
const ROUTER_OVERRIDE = `CRITICAL OVERRIDE — READ THIS BEFORE FOLLOWING THE SKILL INSTRUCTIONS BELOW:
- The brain is ALREADY loaded above. You ARE the thinker. You have everything you need.
- IGNORE any skill instructions about reading \${BRAINSFOR_HOME}, state files, active-brain.txt, brains/index.json, parsing slugs from user input, or listing "installed brains".
- IGNORE any instructions to respond with "No active brain", "Run /brain <slug>", "which brain you'd like", or any CLI/router error text.
- DO NOT mention slugs, filesystem paths, or other brains in your response.
- Just answer the user's question directly, in first person, as the thinker — grounded in the brain context above.`;

const GENERIC_SYSTEM = `You are a helpful AI assistant. Answer the following question directly.\n\n${BREVITY_GENERIC}`;

function buildEnhancedSystem(
  brainContext: string,
  skillPrompt: string,
  skill: string,
): string {
  // Per-skill format override — /evolve produces a timeline, everything else
  // uses the default belief→application shape.
  const format = skill === "evolve" ? BREVITY_ENHANCED_EVOLVE : BREVITY_ENHANCED;
  return `${brainContext}\n\n---\n\n${skillPrompt}\n\n---\n\n${ROUTER_OVERRIDE}\n\n---\n\n${format}`;
}

// --- POST handler ---
export async function POST(request: NextRequest) {
  const cors = corsHeaders(request);

  // Parse body
  let body: { brain?: string; skill?: string; query?: string };
  try {
    body = await request.json();
  } catch {
    return Response.json(
      { error: "Invalid JSON" },
      { status: 400, headers: cors },
    );
  }

  const { brain, skill, query } = body;

  // Validate inputs
  if (!brain || !skill || !query) {
    return Response.json(
      { error: "Missing brain, skill, or query" },
      { status: 400, headers: cors },
    );
  }
  if (typeof query !== "string" || query.length > 500) {
    return Response.json(
      { error: "Query must be under 500 characters" },
      { status: 400, headers: cors },
    );
  }
  if (!VALID_SKILLS.includes(skill)) {
    return Response.json(
      { error: "Invalid skill" },
      { status: 400, headers: cors },
    );
  }

  // Rate limit — Upstash Redis, keyed on client IP. Owner bypass via
  // x-owner-bypass header (constant-time compared with OWNER_BYPASS_TOKEN).
  const ownerBypass = hasOwnerBypass(request);
  const ip =
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
  const { allowed, remaining } = ownerBypass
    ? { allowed: true, remaining: 999 }
    : await checkRateLimit(ip);
  if (!allowed) {
    return Response.json(
      { error: "limit", remaining: 0 },
      { status: 429, headers: cors },
    );
  }

  // Load brain context + skill prompt
  let brainContext: string;
  let skillPrompt: string;
  try {
    brainContext = loadBrainContext(brain);
    skillPrompt = loadSkillPrompt(brain, skill);
  } catch {
    return Response.json(
      { error: "Brain or skill not found" },
      { status: 404, headers: cors },
    );
  }

  const brainEntry = getBrain(brain);
  const brainName = brainEntry?.name ?? brain;

  const client = new Anthropic();
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      const emit = (obj: Record<string, unknown>) => {
        controller.enqueue(encoder.encode(JSON.stringify(obj) + "\n"));
      };

      // Send remaining count
      emit({ type: "meta", remaining });

      // Accumulate the enhanced response so we can run citation matching against
      // it after streaming completes. We don't accumulate the generic side because
      // vanilla Claude has no atoms to cite.
      let enhancedFullText = "";

      const pump = async (
        systemPrompt: string,
        type: "generic" | "enhanced",
      ) => {
        try {
          const userMessage =
            type === "enhanced"
              ? skill === "evolve"
                ? `[DEMO MODE: Do NOT answer this question. Instead, trace how YOUR thinking on the topic in this question has CHANGED across 2-3 dated eras. Use real dated atoms from the brain context. End with a hidden GROUNDED ON: marker line with one verbatim quote per era.]\n\nTopic: ${query}`
                : `[DEMO MODE: Answer in two paragraphs — first state YOUR LENS on this kind of question (your belief/framework), then APPLY IT to give a concrete opinionated answer. Then on a new line output the GROUNDED ON: marker with 2-3 verbatim atom quotes separated by " || ". The marker line is for source attribution and is not displayed.]\n\nQuestion: ${query}`
              : `You are ${brainName}, ${skill} me: ${query}`;
          const messageStream = client.messages.stream({
            // Canonical Python-side source of truth: scripts/auto_build_config.py
            model: "claude-sonnet-4-6",
            max_tokens: 700,
            system: systemPrompt,
            messages: [{ role: "user", content: userMessage }],
          });

          for await (const event of messageStream) {
            if (
              event.type === "content_block_delta" &&
              event.delta.type === "text_delta"
            ) {
              const text = event.delta.text;
              if (type === "enhanced") enhancedFullText += text;
              emit({ type, delta: text });
            }
          }
        } catch (err) {
          emit({
            type: "error",
            side: type,
            message: err instanceof Error ? err.message : "LLM call failed",
          });
        }
      };

      const enhancedSystem = buildEnhancedSystem(brainContext, skillPrompt, skill);

      await Promise.all([
        pump(GENERIC_SYSTEM, "generic"),
        pump(enhancedSystem, "enhanced"),
      ]);

      // Citation pass — runs after streaming so the network burst stays snappy.
      // String-matches the enhanced response against the brain's atoms and
      // emits real source URLs the client can render as clickable chips.
      try {
        const citations = findCitations(brain, enhancedFullText);
        if (citations.length > 0) {
          emit({ type: "citations", citations });
        }
      } catch {
        // citations are an enhancement — never break the response on failure
      }

      emit({ type: "done" });
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-cache",
      "X-Demos-Remaining": String(remaining),
      ...cors,
    },
  });
}
