"use client";

import { useState } from "react";
import { SkillsPlayground } from "./SkillsPlayground";
import { BoardDemo } from "./BoardDemo";
import type { SkillDemo } from "@/lib/skill-demos";

interface BrainOption {
  slug: string;
  name: string;
  badge?: string;
  emoji?: string;
}

interface SkillOption {
  name: string;
  title: string;
  desc: string;
  icon: string;
  workflow: string;
}

interface LivePlaygroundProps {
  brains: BrainOption[];
  // Subset of brains that have dated atoms across enough years for /evolve.
  // Falls back to `brains` when undefined (older callers).
  evolveBrains?: BrainOption[];
  skills: SkillOption[];
  demos: Record<string, SkillDemo>;
  defaultBrain: string;
  defaultBoardBrains: string[];
}

type TabId = "voice" | "evolve" | "board";

// Order: /board leads (the felt-augmentation moment), /evolve second (the
// structurally-impossible trust signal), /advise last (the most prompt-
// replicable so the weakest opener). See debate at:
// /Users/robgabel/.claude/state/active-brain.txt scratchpad — Path C.
const TABS: {
  id: TabId;
  label: string;
  hook: string;
  why: string;
}[] = [
  {
    id: "board",
    label: "Board of advisors",
    hook: "Five thinkers, five voices, one decision. Disagreement visible.",
    why: "One LLM call can't keep five distinct voices uncontaminated. Five parallel brains can.",
  },
  {
    id: "evolve",
    label: "Watch a mind change",
    hook: "How their thinking on one topic evolved across years.",
    why: "Vanilla LLMs don't have temporally-tagged atoms. They can't show you 2014 vs 2024.",
  },
  {
    id: "voice",
    label: "Hear them think",
    hook: "First-person voice. Verbatim source-cited atoms.",
    why: "A prompt can imitate a tone. It can't fabricate three dated quotes from real sources.",
  },
];

// One-line teaser that hints at the /evolve trust signal without committing
// the visitor's attention before they get to the board. Click → /evolve tab.
// The dated quote pair is hand-picked from Belsky's atoms so it lands as a
// real thinker's actual evolution, not marketing copy.
const EVOLVE_TEASER = {
  earlyYear: "2017",
  earlyClaim: "The first mile is where new users decide if your product is worth their attention.",
  lateYear: "2024",
  lateClaim: "Taste is the human moat in an AI world — your filters become your edge.",
  thinker: "Scott Belsky, Implications newsletter",
};

// Single-word topic chips per the plan. Clicking one fills the textarea with a
// templated /evolve query. The visitor still sees a full question in the input,
// but the surface area for choosing is one word.
const EVOLVE_TOPICS = ["AI", "founders", "design", "feedback", "scale", "agency"];
const evolveQueryFor = (topic: string) =>
  `How has your thinking on ${topic} changed over time?`;

// Seeded prompts for Tab 1 — three real questions visitors can pick instead of
// staring at an empty textarea. Mix of decisions, learning, and strategy so the
// brain's voice gets to flex differently per pick.
const VOICE_SEEDS = [
  "Should I ship a small feature today or polish three more weeks?",
  "How do I know if I'm building the right thing?",
  "Is now the right moment to raise, or should I stay bootstrapped?",
];

export function LivePlayground({
  brains,
  evolveBrains,
  skills,
  demos,
  defaultBrain,
  defaultBoardBrains,
}: LivePlaygroundProps) {
  // The evolve tab only shows brains whose atoms span enough years to produce
  // a real timeline. If the parent didn't pass a filtered list (or filtering
  // would leave it empty), fall back to the full brain list — better to show
  // every brain than to ship an empty dropdown.
  const brainsForEvolve =
    evolveBrains && evolveBrains.length > 0 ? evolveBrains : brains;
  // If the default brain doesn't support /evolve, swap to the first one that does.
  const evolveDefaultBrain =
    brainsForEvolve.find((b) => b.slug === defaultBrain)?.slug ??
    brainsForEvolve[0]?.slug ??
    defaultBrain;
  // Default to the board — that's the felt augmentation moment. The evolve
  // teaser above the tabs carries the moat signal in <1s of attention so the
  // skeptic-tax gets paid without diverting from the conversion path.
  const [activeTab, setActiveTab] = useState<TabId>("board");

  const activeMeta = TABS.find((t) => t.id === activeTab)!;

  return (
    <div>
      {/* Evolve teaser strip — single dated-quote pair that names the temporal
          moat in one line. Clicking sends the visitor to the /evolve tab. */}
      <div className="mx-auto mb-6 max-w-[1140px] px-6">
        <button
          type="button"
          onClick={() => setActiveTab("evolve")}
          className="group flex w-full items-center justify-between gap-3 rounded-xl border border-border-indigo/40 bg-gradient-to-r from-indigo-mist/40 to-transparent px-5 py-3 text-left transition-all hover:border-brain-indigo hover:from-indigo-mist/70"
        >
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px] leading-snug text-deep-ink">
            <span className="inline-flex items-center gap-1.5">
              <span className="rounded bg-cool-surface px-1.5 py-0.5 font-mono text-[10px] font-semibold text-muted">
                {EVOLVE_TEASER.earlyYear}
              </span>
              <span className="italic text-body">&ldquo;{EVOLVE_TEASER.earlyClaim}&rdquo;</span>
            </span>
            <span className="text-brain-indigo">&rarr;</span>
            <span className="inline-flex items-center gap-1.5">
              <span className="rounded bg-cool-surface px-1.5 py-0.5 font-mono text-[10px] font-semibold text-muted">
                {EVOLVE_TEASER.lateYear}
              </span>
              <span className="italic text-deep-ink">&ldquo;{EVOLVE_TEASER.lateClaim}&rdquo;</span>
            </span>
          </div>
          <span className="hidden shrink-0 items-center gap-1 font-mono text-[11px] font-semibold uppercase tracking-wider text-brain-indigo transition-all group-hover:text-indigo-deep sm:inline-flex">
            See the timeline
            <svg
              className="h-3 w-3 transition-transform group-hover:translate-x-0.5"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 4l5 4-5 4" />
            </svg>
          </span>
        </button>
        <p className="mt-1.5 text-center text-[11px] text-muted">
          One thinker, {EVOLVE_TEASER.thinker} &mdash; seven years apart. Vanilla LLMs can&rsquo;t produce this without temporally-tagged atoms.
        </p>
      </div>

      {/* Tab bar */}
      <div className="mx-auto max-w-[1140px] px-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:gap-2">
          {TABS.map((t) => {
            const active = t.id === activeTab;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`flex-1 rounded-xl border px-5 py-4 text-left transition-all ${
                  active
                    ? "border-brain-indigo bg-brain-indigo/5 shadow-brain"
                    : "border-border-default bg-white hover:border-border-indigo"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold ${
                      active
                        ? "bg-brain-indigo text-white"
                        : "bg-cool-surface text-muted"
                    }`}
                  >
                    {TABS.findIndex((x) => x.id === t.id) + 1}
                  </span>
                  <span
                    className={`font-display text-base font-semibold ${active ? "text-brain-indigo" : "text-deep-ink"}`}
                  >
                    {t.label}
                  </span>
                </div>
                <p className={`mt-2 text-[13px] leading-snug ${active ? "text-deep-ink" : "text-body"}`}>
                  {t.hook}
                </p>
              </button>
            );
          })}
        </div>

        {/* Why this matters */}
        <p className="mx-auto mt-6 max-w-[760px] text-center text-sm italic text-muted">
          {activeMeta.why}
        </p>
      </div>

      {/* Active tab body */}
      <div className="mt-8">
        {activeTab === "voice" && (
          <SkillsPlayground
            brains={brains}
            skills={skills}
            demos={demos}
            defaultBrain={defaultBrain}
            defaultSkill="advise"
            lockedSkill="advise"
            seedQueries={VOICE_SEEDS}
          />
        )}
        {activeTab === "evolve" && (
          <SkillsPlayground
            brains={brainsForEvolve}
            skills={skills}
            demos={demos}
            defaultBrain={evolveDefaultBrain}
            defaultSkill="evolve"
            lockedSkill="evolve"
            seedQueries={EVOLVE_TOPICS.map(evolveQueryFor)}
            seedQueryLabels={EVOLVE_TOPICS}
          />
        )}
        {activeTab === "board" && (
          <BoardDemo brains={brains} defaultBrains={defaultBoardBrains} />
        )}
      </div>
    </div>
  );
}
