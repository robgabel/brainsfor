"use client";

import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import { track } from "@vercel/analytics";
import { HERO_LANES, type HeroDemoEntry, type HeroLane } from "@/lib/hero-demos";
import { BoardDemo } from "./BoardDemo";

export interface HeroBrainMeta {
  slug: string;
  name: string;
  firstName: string;
  emoji: string;
  atomCount: number;
  connectionCount: number;
}

interface BrainOption {
  slug: string;
  name: string;
  badge?: string;
  emoji?: string;
}

interface Citation {
  quote: string;
  url: string | null;
  date: string | null;
  preview: string;
}

interface HeroDemoProps {
  brainMeta: Record<string, HeroBrainMeta>;
  boardBrains: BrainOption[];
  defaultBoardBrains: string[];
}

// Shared with SkillsPlayground so the demo budget is one pool site-wide.
const DEMO_LIMIT = process.env.NODE_ENV === "development" ? 999 : 10;
const STORAGE_KEY = "bf-demo-count";
const OWNER_TOKEN_KEY = "bf-owner-token";

function safeTrack(name: string, props?: Record<string, string>) {
  try {
    track(name, props);
  } catch {
    // analytics must never break the page
  }
}

/** Hide the trailing "GROUNDED ON: ..." marker while the live answer streams. */
function stripGroundingMarker(text: string): string {
  const idx = text.search(/\bGROUNDED ON\b/i);
  if (idx < 0) return text;
  return text.slice(0, idx).trimEnd();
}

function Paragraphs({ text, className }: { text: string; className?: string }) {
  const parts = text.split(/\n{2,}/).filter(Boolean);
  return (
    <div className={className}>
      {parts.map((p, i) => (
        <p key={i} className={i > 0 ? "mt-3" : ""}>
          {p}
        </p>
      ))}
    </div>
  );
}

export function HeroDemo({ brainMeta, boardBrains, defaultBoardBrains }: HeroDemoProps) {
  // Drop entries whose brain isn't live/installed so a registry change can't
  // render a demo with no download target; drop lanes that end up empty.
  const lanes: HeroLane[] = useMemo(
    () =>
      HERO_LANES.map((lane) => ({
        ...lane,
        entries: lane.entries.filter((e) => brainMeta[e.brain]),
      })).filter((lane) => lane.entries.length > 0),
    [brainMeta],
  );

  const [tab, setTab] = useState<"solo" | "board">("solo");
  const [laneId, setLaneId] = useState<HeroLane["id"]>(lanes[0]?.id ?? "code");
  const [entryIdx, setEntryIdx] = useState(0);
  const [mode, setMode] = useState<"canned" | "live">("canned");

  // ─── Canned playback (typing effect) ───
  const [typedGeneric, setTypedGeneric] = useState(0);
  const [typedEnhanced, setTypedEnhanced] = useState(0);
  const firstPlaybackTracked = useRef(false);

  // ─── Live mode ───
  const [query, setQuery] = useState("");
  const [genericText, setGenericText] = useState("");
  const [enhancedText, setEnhancedText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [liveRan, setLiveRan] = useState(false);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [demoCount, setDemoCount] = useState(0);
  const [ownerToken, setOwnerToken] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const lane = lanes.find((l) => l.id === laneId) ?? lanes[0];
  const entry: HeroDemoEntry | undefined = lane?.entries[entryIdx] ?? lane?.entries[0];
  const meta = entry ? brainMeta[entry.brain] : undefined;

  const playbackDone =
    !!entry &&
    typedGeneric >= entry.generic.length &&
    typedEnhanced >= entry.enhanced.length;

  // Type both panels in parallel — the generic side runs faster and finishes
  // first, so the brain side visibly keeps going. Progress is derived from
  // elapsed time (not tick count) so a throttled background tab jumps to the
  // right position instead of crawling. Reduced motion renders instantly.
  useEffect(() => {
    if (!entry || tab !== "solo" || mode !== "canned") return;
    setTypedGeneric(0);
    setTypedEnhanced(0);
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setTypedGeneric(entry.generic.length);
      setTypedEnhanced(entry.enhanced.length);
      return;
    }
    const GENERIC_CPS = 220;
    const ENHANCED_CPS = 110;
    const start = performance.now();
    const timer = window.setInterval(() => {
      const dt = (performance.now() - start) / 1000;
      const g = Math.min(Math.floor(dt * GENERIC_CPS), entry.generic.length);
      const e = Math.min(Math.floor(dt * ENHANCED_CPS), entry.enhanced.length);
      setTypedGeneric(g);
      setTypedEnhanced(e);
      if (g >= entry.generic.length && e >= entry.enhanced.length) {
        window.clearInterval(timer);
      }
    }, 32);
    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entry?.question, tab, mode]);

  useEffect(() => {
    if (playbackDone && !firstPlaybackTracked.current) {
      firstPlaybackTracked.current = true;
      safeTrack("hero_demo_play", { brain: entry?.brain ?? "", question: entry?.question ?? "" });
    }
  }, [playbackDone, entry]);

  // Owner token + shared demo counter (same keys as SkillsPlayground).
  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const urlToken = params.get("token");
      if (urlToken) localStorage.setItem(OWNER_TOKEN_KEY, urlToken);
      const stored = localStorage.getItem(OWNER_TOKEN_KEY);
      if (stored) {
        setOwnerToken(stored);
        return;
      }
      const storedCount = localStorage.getItem(STORAGE_KEY);
      if (storedCount) setDemoCount(parseInt(storedCount, 10) || 0);
    } catch {
      // storage unavailable
    }
  }, []);

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsStreaming(false);
  }, []);

  useEffect(() => () => abortRef.current?.abort(), []);

  const limit = ownerToken ? 999 : DEMO_LIMIT;

  function switchLane(id: HeroLane["id"]) {
    cancelStream();
    setLaneId(id);
    setEntryIdx(0);
    setMode("canned");
    setLiveRan(false);
    setError(null);
    safeTrack("hero_lane_switch", { lane: id });
  }

  function pickEntry(i: number) {
    cancelStream();
    setEntryIdx(i);
    setMode("canned");
    setLiveRan(false);
    setError(null);
    safeTrack("hero_demo_chip", { question: lane?.entries[i]?.chipLabel ?? "" });
  }

  function openLive() {
    cancelStream();
    setMode("live");
    setError(null);
    safeTrack("hero_live_open", { brain: entry?.brain ?? "" });
    window.setTimeout(() => textareaRef.current?.focus(), 50);
  }

  async function runLive() {
    const q = query.trim();
    if (!q || isStreaming || !entry || demoCount >= limit) return;
    cancelStream();
    setGenericText("");
    setEnhancedText("");
    setCitations([]);
    setError(null);
    setLiveRan(true);
    setIsStreaming(true);
    safeTrack("hero_live_ask", { brain: entry.brain });

    if (!ownerToken) {
      const next = demoCount + 1;
      setDemoCount(next);
      try {
        localStorage.setItem(STORAGE_KEY, String(next));
      } catch {
        // ignore
      }
    }

    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const res = await fetch("/api/skill", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(ownerToken ? { "x-owner-bypass": ownerToken } : {}),
        },
        body: JSON.stringify({ brain: entry.brain, skill: "advise", query: q }),
        signal: controller.signal,
      });
      if (res.status === 429) {
        setError("Demo limit reached — install the brain for unlimited use.");
        setIsStreaming(false);
        return;
      }
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.error || "Something went wrong");
        setIsStreaming(false);
        return;
      }
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop()!;
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const msg = JSON.parse(line);
            if (msg.type === "generic") setGenericText((p) => p + msg.delta);
            else if (msg.type === "enhanced") setEnhancedText((p) => p + msg.delta);
            else if (msg.type === "citations" && Array.isArray(msg.citations))
              setCitations(msg.citations);
            else if (msg.type === "error") setError(msg.message || "LLM call failed");
          } catch {
            // skip malformed lines
          }
        }
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") {
        setError("Connection failed — please try again.");
      }
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }

  if (!lane || !entry || !meta) return null;

  const showLiveResult = mode === "live" && liveRan;
  const genericShown = showLiveResult ? genericText : entry.generic.slice(0, typedGeneric);
  const enhancedShown = showLiveResult
    ? stripGroundingMarker(enhancedText)
    : entry.enhanced.slice(0, typedEnhanced);
  const genericBusy = showLiveResult ? isStreaming : typedGeneric < entry.generic.length;
  const enhancedBusy = showLiveResult ? isStreaming : typedEnhanced < entry.enhanced.length;
  const questionShown = showLiveResult ? query.trim() : entry.question;
  const zipHref = `/brains/${meta.slug}/${meta.slug}-brain-pack.zip`;

  return (
    <div className="mx-auto max-w-[1040px]">
      {/* ─── Tabs: one mind / five minds ─── */}
      <div className="mb-4 flex items-center justify-center gap-2" role="tablist" aria-label="Demo mode">
        {(
          [
            { id: "solo", label: "One mind, live" },
            { id: "board", label: "Convene five minds" },
          ] as const
        ).map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => {
              setTab(t.id);
              safeTrack("hero_tab", { tab: t.id });
            }}
            className={`rounded-full px-4 py-1.5 font-mono text-[13px] transition-all ${
              tab === t.id
                ? "bg-brain-indigo text-white shadow-sm"
                : "bg-cool-surface text-label hover:bg-brain-indigo/10 hover:text-brain-indigo"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "board" ? (
        <BoardDemo brains={boardBrains} defaultBrains={defaultBoardBrains} />
      ) : (
        <>
          {/* ─── The demo card ─── */}
          <div className="rounded-2xl border border-border-indigo/60 bg-white p-4 shadow-brain md:p-5">
            <p className="mb-4 font-mono text-sm text-label">
              <span className="text-brain-indigo">&gt;</span> {questionShown}
            </p>

            <div className="grid gap-4 md:grid-cols-2">
              {/* Left: no brain */}
              <div className="rounded-xl bg-deep-ink p-5">
                <div className="mb-3 flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#94a3b8]" />
                  <span className="font-mono text-xs text-[#94a3b8]">Claude — no brain</span>
                </div>
                <div className="min-h-[200px] font-mono text-sm leading-relaxed text-[#cbd5e1]">
                  {genericShown ? (
                    <Paragraphs text={genericShown} />
                  ) : (
                    <span className="animate-pulse text-[#475569]">Generating…</span>
                  )}
                  {genericBusy && genericShown && (
                    <span className="ml-0.5 inline-block animate-pulse text-[#94a3b8]">|</span>
                  )}
                </div>
              </div>

              {/* Right: with the brain. On mobile it stacks FIRST — the payoff
                  leads, the generic hedge is the scroll-past. */}
              <div className="order-first rounded-xl border border-border-indigo bg-[#0f0b1e] p-5 md:order-none">
                <div className="mb-3 flex items-center gap-2">
                  <span
                    className={`h-2.5 w-2.5 rounded-full ${enhancedBusy ? "animate-pulse bg-amber-400" : "bg-success"}`}
                  />
                  <span className="font-mono text-xs text-success">
                    Claude + {meta.emoji} {meta.name}&rsquo;s brain
                  </span>
                </div>
                <div className="min-h-[200px] font-mono text-sm leading-relaxed text-[#c7d2fe]">
                  {enhancedShown ? (
                    <Paragraphs text={enhancedShown} />
                  ) : (
                    <span className="animate-pulse text-[#818cf8]">Loading brain context…</span>
                  )}
                  {enhancedBusy && enhancedShown && (
                    <span className="ml-0.5 inline-block animate-pulse text-brain-indigo">|</span>
                  )}
                </div>

                {/* Receipts: canned playback cites its grounding atoms */}
                {!showLiveResult && playbackDone && (
                  <div className="mt-4 border-t border-[#1e1b3a] pt-3">
                    <div className="flex flex-wrap gap-1.5">
                      {entry.atoms.map((a) => (
                        <span
                          key={a}
                          className="rounded-md border border-[#1e1b3a] bg-[#1a1432] px-2 py-1 font-mono text-[11px] text-[#c7d2fe]"
                        >
                          {a}
                        </span>
                      ))}
                      <span className="rounded-md border border-[#1e1b3a] bg-[#1a1432] px-2 py-1 font-mono text-[11px] text-[#818cf8]">
                        {entry.confidence}
                      </span>
                    </div>
                    <p className="mt-2 font-mono text-[11px] text-[#818cf8]">
                      cited · {entry.source}
                    </p>
                  </div>
                )}

                {/* Live citations: real URLs matched against the brain's atoms */}
                {showLiveResult && !isStreaming && citations.length > 0 && (
                  <div className="mt-4 border-t border-[#1e1b3a] pt-3">
                    <div className="flex flex-wrap gap-1.5">
                      {citations.map((c, i) =>
                        c.url ? (
                          <a
                            key={c.url + i}
                            href={c.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            title={c.quote}
                            className="inline-flex max-w-full items-center gap-1.5 rounded-md border border-[#1e1b3a] bg-[#1a1432] px-2 py-1 font-mono text-[11px] text-[#c7d2fe] transition-all hover:border-brain-indigo hover:text-white"
                          >
                            <span className="max-w-[240px] truncate">&ldquo;{c.preview}&rdquo;</span>
                            {c.date && <span className="text-[#818cf8]">{c.date.slice(0, 4)}</span>}
                            <span aria-hidden>&rarr;</span>
                          </a>
                        ) : (
                          <span
                            key={i}
                            title={c.quote}
                            className="inline-flex max-w-full items-center gap-1.5 rounded-md border border-[#1e1b3a] bg-[#1a1432] px-2 py-1 font-mono text-[11px] text-[#94a3b8]"
                          >
                            <span className="max-w-[240px] truncate">&ldquo;{c.preview}&rdquo;</span>
                          </span>
                        ),
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* ─── Question chips + live ask ─── */}
            {mode === "canned" ? (
              <div className="mt-4 flex flex-wrap items-center gap-2">
                {lane.entries.map((e, i) => (
                  <button
                    key={e.question}
                    onClick={() => pickEntry(i)}
                    aria-pressed={i === entryIdx}
                    className={`rounded-full px-3 py-1.5 text-xs transition-all ${
                      i === entryIdx
                        ? "bg-indigo-mist text-indigo-deep"
                        : "bg-cool-surface text-label hover:bg-brain-indigo/10 hover:text-brain-indigo"
                    }`}
                  >
                    {e.chipLabel}
                  </button>
                ))}
                <button
                  onClick={openLive}
                  className="rounded-full px-3 py-1.5 text-xs font-semibold text-brain-indigo transition-all hover:bg-brain-indigo/10"
                >
                  Ask {meta.firstName}{" "}yourself &rarr;
                </button>
              </div>
            ) : (
              <div className="mt-4">
                <div className="flex flex-col gap-2 sm:flex-row">
                  <textarea
                    ref={textareaRef}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        runLive();
                      }
                    }}
                    placeholder={`Ask ${meta.name} a real question…`}
                    rows={1}
                    maxLength={500}
                    disabled={demoCount >= limit}
                    className="flex-1 resize-none rounded-lg border border-border-default bg-white px-4 py-2.5 text-sm text-deep-ink placeholder:text-muted/60 focus:border-brain-indigo focus:outline-none focus:ring-2 focus:ring-brain-indigo/20"
                  />
                  <button
                    onClick={runLive}
                    disabled={!query.trim() || isStreaming || demoCount >= limit}
                    className="rounded-lg bg-brain-indigo px-5 py-2.5 font-mono text-[13px] font-semibold text-white shadow-brain-cta transition-all hover:bg-indigo-hover active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {isStreaming ? "Streaming…" : "Run /advise"}
                  </button>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => {
                      cancelStream();
                      setMode("canned");
                      setLiveRan(false);
                    }}
                    className="text-xs text-label hover:text-brain-indigo"
                  >
                    &larr; Back to examples
                  </button>
                  <span className="text-xs text-muted">
                    {ownerToken
                      ? "Owner — unlimited"
                      : demoCount >= limit
                        ? `Demo limit reached (${limit}/${limit}) — install the brain for unlimited use`
                        : `${limit - demoCount} of ${limit} live demos remaining`}
                  </span>
                </div>
                {error && (
                  <p className="mt-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                    {error}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* ─── Lane row ─── */}
          <div className="mt-5 grid gap-2 sm:grid-cols-3" role="group" aria-label="Pick your situation">
            {lanes.map((l) => (
              <button
                key={l.id}
                onClick={() => switchLane(l.id)}
                aria-pressed={l.id === laneId}
                className={`rounded-lg border px-4 py-2.5 text-left transition-all ${
                  l.id === laneId
                    ? "border-brain-indigo bg-brain-indigo/5"
                    : "border-border-default bg-white hover:border-indigo-soft"
                }`}
              >
                <span className={`block text-sm font-semibold ${l.id === laneId ? "text-indigo-deep" : "text-deep-ink"}`}>
                  {l.label}
                </span>
                <span className={`block text-xs ${l.id === laneId ? "text-brain-indigo" : "text-body"}`}>
                  {l.brainsLabel}
                </span>
              </button>
            ))}
          </div>

          {/* ─── The ask, at the moment of value ─── */}
          <div className="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <a
              href={zipHref}
              download
              onClick={() => safeTrack("download_click", { slug: meta.slug, position: "hero" })}
              className="rounded-lg bg-brain-indigo px-7 py-3 text-[15px] font-semibold text-white shadow-brain-cta transition-all hover:bg-indigo-hover active:scale-[0.98]"
            >
              Get {meta.firstName}&rsquo;s brain — free &darr;
            </a>
            <p className="text-sm text-body">
              A zip you drop into Claude Code, Cursor, or any agent. No signup.
            </p>
          </div>

          {/* ─── Receipts strip ─── */}
          <p className="mt-4 text-center font-mono text-[13px] text-label">
            {meta.atomCount.toLocaleString()} atoms &middot; {meta.connectionCount.toLocaleString()}{" "}
            connections &middot; every line cites a dated, real source&nbsp;
            <Link
              href={`/brains/${meta.slug}`}
              onClick={() => safeTrack("hero_graph_link", { slug: meta.slug })}
              className="font-semibold text-brain-indigo hover:underline"
            >
              see the whole graph &rarr;
            </Link>
          </p>
        </>
      )}
    </div>
  );
}
