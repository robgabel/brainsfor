import { NextRequest } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";
import { loadBrainContext, loadSkillPrompt } from "@/lib/brain-context";
import { SKILLS, getBrain } from "@/lib/brains";

export const runtime = "nodejs";

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
  const { success, remaining } = await rl.limit(ip);
  return { allowed: success, remaining };
}

// --- System prompts ---
const BREVITY_GENERIC = `HARD CONSTRAINT: Respond in exactly 4-5 sentences of plain prose. No markdown, no bold, no headers, no bullet points. Plain text only.`;

const BREVITY_ENHANCED = `HARD CONSTRAINTS — FORMAT:
- Output ONE short answer (1 sentence, 25 words max) in first person as the thinker, followed by EXACTLY 3 direct quotes.
- Each quote MUST be verbatim from an atom's original_quote in the brain context above. Never fabricate or paraphrase.
- Pick the 3 quotes MOST RELEVANT to the user's question, not the most famous ones.
- Cite each quote in this exact format: "quote text here" — Source Name, Year.
- Separate the answer and each quote with a period and a space so they render as distinct paragraphs.
- No markdown, no bold, no headers, no bullet points, no numbering. Plain text only.
- The answer sentence must be opinionated and specific, channeling the thinker's actual worldview — no hedging, no generic filler.`;

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

function buildEnhancedSystem(brainContext: string, skillPrompt: string): string {
  return `${brainContext}\n\n---\n\n${skillPrompt}\n\n---\n\n${ROUTER_OVERRIDE}\n\n---\n\n${BREVITY_ENHANCED}`;
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

  // Rate limit — Upstash Redis, keyed on client IP. No header bypasses.
  const ip =
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
  const { allowed, remaining } = await checkRateLimit(ip);
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

      const pump = async (
        systemPrompt: string,
        type: "generic" | "enhanced",
      ) => {
        try {
          const userMessage =
            type === "enhanced"
              ? `[DEMO MODE: Answer in ONE short sentence (25 words max) in first person as the thinker, then quote the 3 atoms most relevant to this question verbatim. Each quote followed by "— Source, Year." Plain text only, no markdown.]\n\n${query}`
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
              emit({ type, delta: event.delta.text });
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

      const enhancedSystem = buildEnhancedSystem(brainContext, skillPrompt);

      await Promise.all([
        pump(GENERIC_SYSTEM, "generic"),
        pump(enhancedSystem, "enhanced"),
      ]);

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
