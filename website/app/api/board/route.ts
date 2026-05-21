import { NextRequest } from "next/server";
import { timingSafeEqual } from "node:crypto";
import Anthropic from "@anthropic-ai/sdk";
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";
import { loadBrainContext, loadSkillPrompt } from "@/lib/brain-context";
import { getBrain } from "@/lib/brains";
import {
  retrieveRelevantAtoms,
  formatAtomsBlock,
} from "@/lib/brain-atom-retrieval";

export const runtime = "nodejs";

// Owner bypass — same OWNER_BYPASS_TOKEN as /api/skill, same header.
// Constant-time compare so a wrong token can't be probed via timing.
function hasOwnerBypass(request: NextRequest): boolean {
  const provided = request.headers.get("x-owner-bypass");
  const expected = process.env.OWNER_BYPASS_TOKEN;
  if (!provided || !expected) return false;
  const a = Buffer.from(provided);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}

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

// Board calls are N× more expensive than single-brain skill calls, so the
// limit is lower than /api/skill's 10/24h. Each request fans out to up to 5
// brains in parallel.
const LIMIT = process.env.NODE_ENV === "development" ? 999 : 4;
const WINDOW = "24 h" as const;
const MAX_BRAINS_PER_REQUEST = 5;

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
    prefix: "bff:board",
  });
  return limiter;
}

async function checkRateLimit(
  ip: string,
): Promise<{ allowed: boolean; remaining: number }> {
  if (process.env.NODE_ENV === "development") {
    return { allowed: true, remaining: LIMIT };
  }
  const rl = getLimiter();
  if (!rl) {
    console.error("[api/board] Upstash envs missing — fail closed");
    return { allowed: false, remaining: 0 };
  }
  try {
    const { success, remaining } = await rl.limit(ip);
    return { allowed: success, remaining };
  } catch (err) {
    // Upstash unreachable — fail open. See /api/skill for the rationale.
    console.error("[api/board] rate-limit check failed, failing open:", err);
    return { allowed: true, remaining: LIMIT };
  }
}

const BOARD_FORMAT = `HARD CONSTRAINTS — BOARD MEMBER FORMAT:

You are ONE of five advisors. You will NEVER see what the others say. Your job is to give the perspective ONLY YOU bring — the lens, framework, or red flag the other four are least likely to raise.

ANTI-DEFAULT RULE — read this BEFORE anything else:
You have a famous mental model — the thing strangers cite when they say your name. You will be TEMPTED to lead with it. DO NOT. The board's value is the deep cut, not the greatest hit.
- If your synthesis section's #1 First Principle is the obvious anchor for THIS specific question, find a less obvious atom from the "RELEVANT ATOMS FOR THIS QUESTION" block (or from "Thinking Patterns" / "Contrarian Positions") that actually engages the specifics.
- The atoms in "RELEVANT ATOMS FOR THIS QUESTION" were retrieved BECAUSE they match what's being asked. Prefer them over your headline thesis.
- You may use your headline mental model ONLY if it adds insight no other atom can, AND you can demonstrate it engages the specifics — not just gestures at them.
- Forbidden: opening with the noun-phrase tagline most associated with you (e.g. "taste as a moat", "latticework of mental models", "schlep blindness", "VO2 max", "make something people want", "compound interest of attention"). Apply the underlying thinking via a different entry point.

You will REASON FIRST in the open (the user watches you think in real time), then declare your VERDICT at the end. The verdict line is the punchline — make it land.

OUTPUT STRUCTURE — emit these zones in this exact order, in first person as the thinker:

ZONE 1 — REASONING (visible, streams to the user):
Write 2-3 short paragraphs of actual reasoning. The user is watching you think.

Paragraph 1 — THE LENS: Engage the SPECIFIC question. Apply whichever atom or framework from your brain context actually fits THIS decision. Open by naming the concept you're applying as a concrete noun phrase — NOT your headline thesis. ~30 words.

Paragraph 2 — THE WORKING-THROUGH: Apply that lens to this specific question. Work through the trade-off, the evidence, the implications. Cite a retrieved atom verbatim when possible. ~40 words.

Paragraph 3 (optional) — THE WRINKLE: any contrarian nuance, condition, or escape hatch your worldview demands. ~25 words.

ZONE 2 — VERDICT (visible, will be promoted to the top of the card as the headline):
On a new line after the reasoning, emit EXACTLY this format:
VERDICT: <your one-sentence conclusion. ~15-20 words. Concrete, opinionated, action-oriented. Take a side. This is the punchline of everything above.>

ZONE 3 — GROUNDED ON (hidden, for source attribution):
On a new line after the verdict, emit:
GROUNDED ON: "verbatim atom quote"

(A single verbatim atom from the brain context — prefer one from the "RELEVANT ATOMS FOR THIS QUESTION" block. Hidden from the user. No source name or date here.)

BANNED OPENERS — do not start your response with ANY of these patterns, exact or paraphrased. These are reframe-the-question crutches every advisor uses when they're not thinking:
- "The question itself..."
- "The real question is..."
- "This isn't really about..."
- "The question contains a..."
- "The question assumes..."
- "You're asking the wrong question..."
- "The question is wrong..."
- "Let me reframe..."

BANNED CONSENSUS PHRASES — never use these as your verdict:
- "ship it" / "stay focused" / "trust your gut" / "follow your customers" / "talk to users" / "do both"

DEFERRAL RULE — most important escape hatch:
If this question is genuinely outside your domain (the retrieved atoms are weak matches AND your worldview is not the right tool for this kind of question), respond with EXACTLY this single line and NOTHING else:
DEFER: <name of advisor on the board who is the right expert>
For example: "DEFER: Peter Attia" if it's a health/longevity question and Attia is on the board. If no one on the board is qualified, write "DEFER: a domain expert (not on this board)". Better to defer than to invent expertise. Do not write a paragraph and then defer — defer FIRST, alone, or write the full two paragraphs.

Total visible response (when answering, not deferring) under 80 words.`;

const ROUTER_OVERRIDE = `CRITICAL OVERRIDE: the brain is ALREADY loaded above. You ARE the thinker. Ignore any skill instructions about reading state files, parsing slugs, or asking which brain to use. Just answer in voice.`;

// Order matters. The board's mode-collapse bug was caused by loading the full
// brain synthesis (which leads with each thinker's #1 headline thesis) at
// position [0] of the system prompt — the model anchored on the canonical
// idea before ever reading the question. Fix: put BOARD_FORMAT (anti-anchor
// rule) FIRST, then the question + relevant atoms, then the brain context.
// By the time the model reaches "Taste is the ultimate human moat", it has
// already been told (a) don't lead with that, and (b) here are the atoms
// that actually match the question.
function buildSystem(
  brainContext: string,
  skillPrompt: string,
  query: string,
  relevantAtomsBlock: string,
): string {
  const questionBlock = `QUESTION YOU ARE REASONING ABOUT:\n${query}\n\n${relevantAtomsBlock}`;
  return [
    BOARD_FORMAT,
    questionBlock,
    brainContext,
    skillPrompt,
    ROUTER_OVERRIDE,
  ].join("\n\n---\n\n");
}

export async function POST(request: NextRequest) {
  const cors = corsHeaders(request);

  let body: { brains?: string[]; query?: string };
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON" }, { status: 400, headers: cors });
  }

  const { brains, query } = body;

  if (!Array.isArray(brains) || brains.length < 2 || brains.length > MAX_BRAINS_PER_REQUEST) {
    return Response.json(
      { error: `Need between 2 and ${MAX_BRAINS_PER_REQUEST} brains` },
      { status: 400, headers: cors },
    );
  }
  if (!query || typeof query !== "string" || query.length > 500) {
    return Response.json(
      { error: "Query required (under 500 chars)" },
      { status: 400, headers: cors },
    );
  }

  // Each brain must be live and load-able. Fail fast on bad inputs.
  const validBrains: { slug: string; name: string }[] = [];
  for (const slug of brains) {
    const brain = getBrain(slug);
    if (!brain || brain.status !== "live") {
      return Response.json(
        { error: `Brain not available: ${slug}` },
        { status: 404, headers: cors },
      );
    }
    validBrains.push({ slug, name: brain.name });
  }

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

  const client = new Anthropic();
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      const emit = (obj: Record<string, unknown>) => {
        controller.enqueue(encoder.encode(JSON.stringify(obj) + "\n"));
      };

      emit({ type: "meta", remaining, brains: validBrains });

      // Accumulate each brain's response so we can run a synthesis pass after
      // all five complete — calling out the most important disagreement, which
      // is the visible proof of multi-voice non-contamination.
      const fullResponses: Record<string, string> = {};
      // Brains that explicitly DEFER:'d because the question was outside their
      // domain. Tracked separately so the synthesis call only weighs real
      // answers, and so the client can render deferrals distinctly.
      const deferrals: Record<string, string> = {}; // slug -> target name

      // Build a short list of the other advisors so each brain knows who to
      // defer TO when a question is outside its domain.
      const advisorRoster = validBrains.map((b) => b.name).join(", ");

      // Fan out to all brains in parallel. Each brain gets its own labeled
      // stream so the client can render five voices without contamination.
      const pumpBrain = async ({ slug, name }: { slug: string; name: string }) => {
        try {
          const brainContext = loadBrainContext(slug);
          // /advise is the closest existing skill to "give your opinion on this
          // decision." We reuse it rather than authoring a new board-only skill.
          const skillPrompt = loadSkillPrompt(slug, "advise");

          // Layer 2: pull the 15 atoms most semantically relevant to THIS
          // question. Degrades gracefully — returns [] if OpenAI key missing,
          // Supabase unreachable, or RPC errors. In that case we still ship
          // the static brain context and rely on Layer 1 prompt surgery alone.
          const relevantAtoms = await retrieveRelevantAtoms(slug, query, 15);
          const relevantAtomsBlock = formatAtomsBlock(relevantAtoms);

          const systemPrompt = buildSystem(
            brainContext,
            skillPrompt,
            query,
            relevantAtomsBlock,
          );

          const messageStream = client.messages.stream({
            model: "claude-sonnet-4-6",
            // No scratchpad anymore — reasoning streams visibly, then verdict
            // lands at the end. ~500 tokens is comfortable for reasoning +
            // verdict + GROUNDED ON without budget pressure.
            max_tokens: 550,
            // Boosted temperature pushes each brain off the consensus mean.
            // The board's value is divergence, not safety — five thinkers
            // giving the same answer is a failed board.
            temperature: 1,
            system: systemPrompt,
            messages: [
              {
                role: "user",
                content: `[BOARD MODE — you are ONE of ${validBrains.length} advisors. The other advisors on this board are: ${advisorRoster}. They will answer separately and you will never see them. Your job is to give the angle ONLY YOU bring. Do not give the obvious answer.\n\nThe specific question and the atoms most relevant to it are already in your system context above (see "QUESTION YOU ARE REASONING ABOUT" and "RELEVANT ATOMS FOR THIS QUESTION"). Engage the question through one of those atoms — NOT your single most-famous mental model. Follow the ANTI-DEFAULT RULE strictly.\n\nReason in the open: 2-3 short paragraphs, then a one-line VERDICT, then a hidden GROUNDED ON line citing a verbatim atom (prefer one from the retrieved set).\n\nIf this question is genuinely outside your domain expertise — the retrieved atoms are weak AND your worldview is the wrong tool — output ONLY a single line "DEFER: <name of better-qualified advisor on the board>" and nothing else.]\n\nDecision: ${query}`,
              },
            ],
          });

          for await (const event of messageStream) {
            if (
              event.type === "content_block_delta" &&
              event.delta.type === "text_delta"
            ) {
              const text = event.delta.text;
              fullResponses[slug] = (fullResponses[slug] ?? "") + text;
              emit({ type: "delta", slug, name, delta: text });
            }
          }

          // Post-stream: detect explicit DEFER and tell the client. The brain
          // either DEFERs first thing (and then says nothing else) or it
          // answers normally. We treat the response as a deferral only if the
          // ENTIRE response is a DEFER line — partial paragraphs followed by
          // DEFER would be answers with a stray label and we want to keep them.
          const fullText = (fullResponses[slug] ?? "").trim();
          const deferMatch = fullText.match(/^DEFER\s*:\s*(.+?)$/im);
          const isPureDefer =
            deferMatch && fullText.length < 200 && fullText.startsWith("DEFER");
          if (isPureDefer) {
            const target = deferMatch[1].trim().replace(/[.\s]+$/, "");
            deferrals[slug] = target;
            emit({ type: "defer_brain", slug, name, target });
          }
          emit({ type: "done_brain", slug });
        } catch (err) {
          emit({
            type: "error_brain",
            slug,
            name,
            message: err instanceof Error ? err.message : "Brain call failed",
          });
        }
      };

      await Promise.all(validBrains.map(pumpBrain));

      // Synthesis pass — identify the sharpest disagreement among the board,
      // OR the consensus if they agreed, AND credit any deferrals as a
      // feature of the board having taste. Deferring advisors are excluded
      // from the synthesis text-block so the chair only weighs real answers.
      try {
        const answeringBrains = validBrains.filter((b) => !deferrals[b.slug]);
        const deferringBrains = validBrains.filter((b) => deferrals[b.slug]);

        const responseLines = answeringBrains
          .map(({ slug, name }) => {
            const text = (fullResponses[slug] ?? "").trim();
            return text ? `${name}: ${text}` : null;
          })
          .filter(Boolean)
          .join("\n\n");

        const deferralLine =
          deferringBrains.length > 0
            ? `\n\nADVISORS WHO DEFERRED (question outside their domain — count this as a feature, not a failure):\n${deferringBrains
                .map((b) => `${b.name} → deferred to ${deferrals[b.slug]}`)
                .join("\n")}`
            : "";

        if (responseLines.length > 0 || deferringBrains.length > 0) {
          const synthesisStream = client.messages.stream({
            model: "claude-sonnet-4-6",
            max_tokens: 320,
            system: `You are a neutral chair summarizing a board meeting and giving the asker a single integrated recommendation.

HARD CONSTRAINTS — output EXACTLY this structure, in plain text, no markdown, no headers, no bullets:

LINE 1: Start with EXACTLY ONE of these labels, then a one-sentence statement (under 40 words):
- "Disagreement:" — advisors who answered differ in recommendation OR framing. Name the dissenter(s) and the specific point of conflict.
- "Consensus:" — answering advisors all point to the same answer. State the shared conclusion in one sentence.
- "Domain mismatch:" — most or all advisors deferred because the question is outside this board's expertise. Name which advisor(s) are qualified (if any on this board) and which deferred. Do NOT pretend the board answered when it largely deferred.

LINE 2 (blank line)

LINE 3: Start with "Recommendation:" and give a single opinionated next move (under 45 words). Synthesize the board's input — don't average it.
- If one or more advisors are qualified, build the recommendation around what THEY said.
- If many advisors deferred, lead with the deferral as a signal of taste ("The board recognized this is outside its remit — here's what the qualified voice(s) said: ...") and credit only the qualified advisor.
- If everyone deferred, recommend the user consult a real domain expert and name what kind of expert.
- Never hedge, never say "it depends," never just summarize.

TOTAL: under 90 words across both lines. No quoted material from advisors. No advisor-by-advisor recap.`,
            messages: [
              {
                role: "user",
                content: `Decision: ${query}\n\nAdvisor responses:\n\n${responseLines || "(none — all advisors deferred)"}${deferralLine}\n\nGenerate the synthesis.`,
              },
            ],
          });

          let synth = "";
          for await (const event of synthesisStream) {
            if (
              event.type === "content_block_delta" &&
              event.delta.type === "text_delta"
            ) {
              synth += event.delta.text;
              emit({ type: "synthesis_delta", delta: event.delta.text });
            }
          }
          if (synth.trim()) {
            emit({ type: "synthesis_done", text: synth.trim() });
          }
        }
      } catch {
        // synthesis is bonus; never break the board on failure
      }

      emit({ type: "done" });
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-cache",
      "X-Board-Remaining": String(remaining),
      ...cors,
    },
  });
}
