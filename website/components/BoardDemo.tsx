"use client";

import { useState, useRef, useCallback, useEffect } from "react";

interface BrainOption {
  slug: string;
  name: string;
  badge?: string;
}

interface BoardDemoProps {
  brains: BrainOption[];
  defaultBrains?: string[];
}

interface BrainResponse {
  slug: string;
  name: string;
  text: string;
  done: boolean;
  error?: string;
  /** When the brain decided this question is outside its domain. The target
   *  is the name of whoever it deferred to (e.g. "Peter Attia"). */
  deferredTo?: string;
}

// Seed questions chosen to surface genuine disagreement across the default
// board (Belsky, Munger, Graham, Jobs, Attia). Consensus on ship-vs-polish or
// raise-vs-bootstrap is too easy — these put taste vs evidence, ambition vs
// longevity, and intuition vs data in direct conflict.
const SEED_QUESTIONS = [
  "I have a $5M acqui-hire offer for a startup I think could be a $500M company. Take it or hold?",
  "I'm 40 with a young family. Start a venture-backed company now, or build a profitable lifestyle business instead?",
  "Should I trust the data my users are giving me, or trust my own product taste when they conflict?",
];

const STORAGE_KEY = "bf-board-count";
const OWNER_TOKEN_KEY = "bf-owner-token";
const DEFAULT_LIMIT = process.env.NODE_ENV === "development" ? 999 : 4;
const MAX_BRAINS = 5;
const MIN_BRAINS = 2;

export function BoardDemo({ brains, defaultBrains }: BoardDemoProps) {
  const [selectedSlugs, setSelectedSlugs] = useState<string[]>(() => {
    if (defaultBrains && defaultBrains.length >= MIN_BRAINS) {
      return defaultBrains.slice(0, MAX_BRAINS);
    }
    return brains.slice(0, Math.min(4, brains.length)).map((b) => b.slug);
  });
  const [query, setQuery] = useState("");
  const [responses, setResponses] = useState<Record<string, BrainResponse>>({});
  const [isRunning, setIsRunning] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [count, setCount] = useState(0);
  const [ownerToken, setOwnerToken] = useState<string | null>(null);
  const [synthesis, setSynthesis] = useState("");
  const [synthesisDone, setSynthesisDone] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  // On mount: capture ?token= → localStorage, then read it. With a token
  // present we wipe the legacy bf-board-count so stale "used X" UI doesn't
  // linger after the bypass ships.
  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const urlToken = params.get("token");
      if (urlToken) {
        localStorage.setItem(OWNER_TOKEN_KEY, urlToken);
      }
      const stored = localStorage.getItem(OWNER_TOKEN_KEY);
      if (stored) {
        setOwnerToken(stored);
        localStorage.removeItem(STORAGE_KEY);
        setCount(0);
        return;
      }
      const storedCount = localStorage.getItem(STORAGE_KEY);
      if (storedCount) setCount(parseInt(storedCount, 10) || 0);
    } catch {
      // SSR
    }
  }, []);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const toggleBrain = (slug: string) => {
    setSelectedSlugs((prev) => {
      if (prev.includes(slug)) {
        if (prev.length <= MIN_BRAINS) return prev;
        return prev.filter((s) => s !== slug);
      }
      if (prev.length >= MAX_BRAINS) return prev;
      return [...prev, slug];
    });
  };

  const handleRun = useCallback(async () => {
    if (!query.trim() || isRunning || count >= DEFAULT_LIMIT) return;
    if (selectedSlugs.length < MIN_BRAINS) return;

    abortRef.current?.abort();
    setShowResult(true);
    setError(null);
    setIsRunning(true);
    setSynthesis("");
    setSynthesisDone(false);

    // Seed empty cards for each chosen brain so they render immediately.
    const seeded: Record<string, BrainResponse> = {};
    for (const slug of selectedSlugs) {
      const meta = brains.find((b) => b.slug === slug);
      seeded[slug] = {
        slug,
        name: meta?.name ?? slug,
        text: "",
        done: false,
      };
    }
    setResponses(seeded);

    if (!ownerToken) {
      const newCount = count + 1;
      setCount(newCount);
      try {
        localStorage.setItem(STORAGE_KEY, String(newCount));
      } catch {
        // ignore
      }
    }

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch("/api/board", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(ownerToken ? { "x-owner-bypass": ownerToken } : {}),
        },
        body: JSON.stringify({
          brains: selectedSlugs,
          query: query.trim(),
        }),
        signal: controller.signal,
      });

      if (res.status === 429) {
        setError("Board limit reached — install a brain pack to keep going.");
        setIsRunning(false);
        return;
      }
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.error || "Board call failed");
        setIsRunning(false);
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
            if (msg.type === "delta") {
              setResponses((prev) => ({
                ...prev,
                [msg.slug]: {
                  ...prev[msg.slug],
                  slug: msg.slug,
                  name: msg.name,
                  text: (prev[msg.slug]?.text ?? "") + msg.delta,
                  done: false,
                },
              }));
            } else if (msg.type === "done_brain") {
              setResponses((prev) => ({
                ...prev,
                [msg.slug]: { ...prev[msg.slug], done: true },
              }));
            } else if (msg.type === "defer_brain") {
              setResponses((prev) => ({
                ...prev,
                [msg.slug]: {
                  ...(prev[msg.slug] ?? {
                    slug: msg.slug,
                    name: msg.name,
                    text: "",
                    done: false,
                  }),
                  deferredTo: msg.target,
                },
              }));
            } else if (msg.type === "synthesis_delta") {
              setSynthesis((prev) => prev + msg.delta);
            } else if (msg.type === "synthesis_done") {
              setSynthesisDone(true);
              if (msg.text) setSynthesis(msg.text);
            } else if (msg.type === "error_brain") {
              setResponses((prev) => ({
                ...prev,
                [msg.slug]: {
                  ...(prev[msg.slug] ?? {
                    slug: msg.slug,
                    name: msg.name,
                    text: "",
                    done: true,
                  }),
                  done: true,
                  error: msg.message,
                },
              }));
            }
          } catch {
            // skip malformed
          }
        }
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") {
        setError("Connection failed — please try again.");
      }
    } finally {
      setIsRunning(false);
      abortRef.current = null;
    }
  }, [brains, count, isRunning, ownerToken, query, selectedSlugs]);

  const remaining = DEFAULT_LIMIT - count;
  const canRun =
    query.trim().length > 0 &&
    !isRunning &&
    (ownerToken !== null || count < DEFAULT_LIMIT) &&
    selectedSlugs.length >= MIN_BRAINS;

  return (
    <div className="mx-auto max-w-[1140px] px-6">
      {/* Brain picker */}
      <div className="mb-6">
        <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-muted">
          Pick {MIN_BRAINS}–{MAX_BRAINS} advisors ({selectedSlugs.length} selected)
        </label>
        <div className="flex flex-wrap gap-2">
          {brains.map((b) => {
            const active = selectedSlugs.includes(b.slug);
            const atCap = !active && selectedSlugs.length >= MAX_BRAINS;
            return (
              <button
                key={b.slug}
                onClick={() => toggleBrain(b.slug)}
                disabled={atCap}
                className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[13px] font-medium transition-all ${
                  active
                    ? "border-brain-indigo bg-brain-indigo/5 text-brain-indigo shadow-sm"
                    : atCap
                      ? "border-border-default bg-cool-surface text-muted/50 cursor-not-allowed"
                      : "border-border-default bg-white text-body hover:border-border-indigo hover:text-deep-ink"
                }`}
              >
                {b.name}
                {b.badge && (
                  <span className="inline-flex items-center rounded-full bg-gradient-to-r from-brain-indigo to-[#8b5cf6] px-1.5 py-0.5 text-[9px] font-bold uppercase leading-none tracking-wider text-white">
                    {b.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Seed-question chips */}
      <div className="mb-3 flex flex-wrap gap-2">
        {SEED_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => setQuery(q)}
            className="rounded-full bg-cool-surface px-3 py-1 text-xs text-label transition-all hover:bg-brain-indigo/10 hover:text-brain-indigo"
          >
            {q.length > 60 ? q.slice(0, 57) + "…" : q}
          </button>
        ))}
      </div>

      {/* Decision input */}
      <div className="mb-6">
        <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-muted">
          What's the decision?
        </label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && canRun) {
              e.preventDefault();
              handleRun();
            }
          }}
          placeholder="Type a real decision you're facing…"
          rows={2}
          className="w-full resize-none rounded-lg border border-border-default bg-white px-4 py-3 text-[15px] text-deep-ink placeholder:text-muted/60 focus:border-brain-indigo focus:outline-none focus:ring-2 focus:ring-brain-indigo/20"
          disabled={!ownerToken && count >= DEFAULT_LIMIT}
        />
        <div className="mt-3 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
          <button
            onClick={handleRun}
            disabled={!canRun}
            className="rounded-lg bg-brain-indigo px-6 py-3 font-mono text-[14px] font-semibold text-white shadow-brain-cta transition-all hover:bg-indigo-hover active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 sm:w-auto"
          >
            {isRunning ? (
              <span className="flex items-center gap-2">
                <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Convening board…
              </span>
            ) : (
              <>Convene board ({selectedSlugs.length})</>
            )}
          </button>
          <span className="text-xs text-muted">
            {ownerToken ? (
              <span className="text-brain-indigo">Owner — unlimited</span>
            ) : count >= DEFAULT_LIMIT ? (
              <span className="text-amber-600">
                Board limit reached — install a brain pack for unlimited boards
              </span>
            ) : (
              <>
                {remaining} of {DEFAULT_LIMIT} board sessions remaining
              </>
            )}
          </span>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Result cards */}
      {showResult && (
        <div className="mt-4">
          <p className="mb-4 font-mono text-xs text-muted">
            <span className="text-deep-ink">&gt;</span> /board {query.trim()}
          </p>

          {/* Board synthesis — runs after all brains complete. Always produces
              two lines: (1) Consensus/Disagreement label + framing, (2) a single
              opinionated Recommendation that synthesizes the board's input. */}
          {synthesis &&
            (() => {
              const isConsensus = /^\s*consensus\s*:/i.test(synthesis);
              // Split the response into the framing line and the recommendation.
              const recIdx = synthesis.search(/\bRecommendation\s*:/i);
              const framingRaw =
                recIdx >= 0 ? synthesis.slice(0, recIdx) : synthesis;
              const recommendationRaw =
                recIdx >= 0
                  ? synthesis.slice(recIdx).replace(/^\s*Recommendation\s*:\s*/i, "")
                  : "";
              const framing = framingRaw
                .replace(/^\s*(Consensus|Disagreement)\s*:\s*/i, "")
                .trim();
              const recommendation = recommendationRaw.trim();
              return (
                <div
                  className={`mb-5 overflow-hidden rounded-xl border ${
                    isConsensus
                      ? "border-success/30 bg-success/5"
                      : "border-amber-200 bg-amber-50"
                  }`}
                >
                  <div
                    className={`flex items-center gap-2 px-5 pt-4 text-[10px] font-bold uppercase tracking-wider ${
                      isConsensus ? "text-success" : "text-amber-900"
                    }`}
                  >
                    <span>{isConsensus ? "Consensus" : "Where the board disagrees"}</span>
                    {!synthesisDone && (
                      <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-current opacity-60" />
                    )}
                  </div>
                  <p
                    className={`px-5 pb-3 pt-1 text-sm leading-relaxed ${
                      isConsensus ? "text-success/90" : "text-amber-900"
                    }`}
                  >
                    {framing}
                  </p>
                  {recommendation && (
                    <div
                      className={`border-t px-5 py-3 ${
                        isConsensus ? "border-success/20 bg-success/[0.04]" : "border-amber-200/70 bg-amber-100/40"
                      }`}
                    >
                      <div
                        className={`mb-1 text-[10px] font-bold uppercase tracking-wider ${
                          isConsensus ? "text-success" : "text-amber-900"
                        }`}
                      >
                        Board recommendation
                      </div>
                      <p
                        className={`text-sm leading-relaxed ${
                          isConsensus ? "text-deep-ink" : "text-deep-ink"
                        }`}
                      >
                        {recommendation}
                      </p>
                    </div>
                  )}
                </div>
              );
            })()}


          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {selectedSlugs.map((slug) => {
              const r = responses[slug];
              const meta = brains.find((b) => b.slug === slug);
              const name = meta?.name ?? slug;
              const isDeferral = !!r?.deferredTo;

              // Deferral card — muted, signals self-awareness rather than failure.
              if (isDeferral) {
                return (
                  <div
                    key={slug}
                    className="flex flex-col rounded-xl border border-dashed border-border-default bg-cool-surface/40 p-5"
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <span className="font-display text-base font-semibold text-muted">
                        {name}
                      </span>
                      <span
                        className="rounded-full bg-cool-surface px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-muted"
                        title="This advisor recognized the question is outside their domain"
                      >
                        Deferred
                      </span>
                    </div>
                    <div className="font-mono text-[12px] leading-relaxed text-muted">
                      <p>
                        Not my domain. Defer to{" "}
                        <span className="font-semibold text-deep-ink">
                          {r?.deferredTo}
                        </span>
                        .
                      </p>
                    </div>
                  </div>
                );
              }

              return (
                <div
                  key={slug}
                  className="flex flex-col rounded-xl border border-border-indigo bg-[#0f0b1e] p-5"
                >
                  <div className="mb-3 flex items-center justify-between">
                    <span className="font-display text-base font-semibold text-white">
                      {name}
                    </span>
                    <span
                      className={`h-2 w-2 rounded-full ${
                        r?.error
                          ? "bg-red-400"
                          : r?.done
                            ? "bg-success"
                            : "animate-pulse bg-amber-400"
                      }`}
                    />
                  </div>
                  <div className="font-mono text-[13px] leading-relaxed text-[#c7d2fe]">
                    {r?.error ? (
                      <span className="text-red-300">Error: {r.error}</span>
                    ) : r?.text ? (
                      // Reasoning streams visibly while the model thinks.
                      // When VERDICT: lands at the end, it gets promoted to
                      // the top of the card in bold — the punchline appears
                      // above the work that produced it. GROUNDED ON marker
                      // is stripped entirely.
                      (() => {
                        const raw = r.text;
                        // Cut off everything from GROUNDED ON onward.
                        const grIdx = raw.search(/\bGROUNDED ON\b/i);
                        const beforeGrounding = grIdx >= 0 ? raw.slice(0, grIdx) : raw;

                        // Split on VERDICT — anything after is the punchline.
                        const vMatch = beforeGrounding.match(/\bVERDICT\s*:\s*([\s\S]*)/i);
                        const reasoning = vMatch
                          ? beforeGrounding.slice(0, vMatch.index).trim()
                          : beforeGrounding.trim();
                        const verdict = vMatch ? vMatch[1].trim() : "";

                        const reasoningParagraphs = reasoning
                          .split(/\n+/)
                          .map((p) => p.trim())
                          .filter(Boolean);

                        if (!reasoning && !verdict) {
                          return (
                            <span className="animate-pulse text-[#818cf8]">
                              {name} is reasoning…
                            </span>
                          );
                        }

                        return (
                          <>
                            {verdict && (
                              <div className="mb-3 rounded-md bg-brain-indigo/15 px-3 py-2 text-[14px] font-semibold leading-snug text-white animate-in fade-in slide-in-from-top-1 duration-300">
                                {verdict}
                              </div>
                            )}
                            {reasoningParagraphs.map((p, i) => (
                              <p
                                key={i}
                                className={i > 0 ? "mt-2" : ""}
                              >
                                {p}
                              </p>
                            ))}
                            {!verdict && r?.text && !r.done && (
                              <p className="mt-3 text-[11px] italic text-[#6366f1] animate-pulse">
                                Working toward a verdict…
                              </p>
                            )}
                          </>
                        );
                      })()
                    ) : (
                      <span className="animate-pulse text-[#818cf8]">
                        Loading {name}…
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
