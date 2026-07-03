import { getLiveBrains } from "@/lib/brains";
import { HERO_BRAIN_SLUGS } from "@/lib/hero-demos";
import { HeroDemo, type HeroBrainMeta } from "@/components/HeroDemo";
import { BetaBand } from "@/components/BetaBand";
import Link from "next/link";

// Homepage = the first mile. One auto-playing side-by-side demo, a lane
// switcher, the download at the moment of value, receipts, install, beta.
// Everything else (full catalog, skill catalog, request form) lives on
// /brains and /skills. Spec: ../PRD-homepage-first-mile.md
export default function Home() {
  const liveBrains = getLiveBrains();

  const brainMeta: Record<string, HeroBrainMeta> = {};
  for (const slug of HERO_BRAIN_SLUGS) {
    const b = liveBrains.find((x) => x.slug === slug);
    if (!b) continue;
    brainMeta[slug] = {
      slug: b.slug,
      name: b.name,
      firstName: b.name.split(" ")[0],
      emoji: b.emoji,
      atomCount: b.atomCount,
      connectionCount: b.connectionCount,
    };
  }

  const boardBrains = liveBrains.map((b) => ({
    slug: b.slug,
    name: b.name,
    badge: b.badge,
    emoji: b.emoji,
  }));
  const defaultBoardBrains = [
    "scott-belsky",
    "charlie-munger",
    "paul-graham",
    "steve-jobs",
    "elon-musk",
  ].filter((s) => boardBrains.some((b) => b.slug === s));

  // One row of minds the demo didn't already show, biggest first.
  const moreBrains = liveBrains
    .filter((b) => !brainMeta[b.slug])
    .sort((a, b) => b.atomCount - a.atomCount)
    .slice(0, 6);

  return (
    <>
      {/* ─── Beat 1: the demo IS the hero ─── */}
      <section className="px-6 pb-16 pt-12 md:pt-16">
        <h1 className="text-center font-display text-4xl font-light leading-[1.05] tracking-[-1.5px] text-deep-ink md:text-[56px]">
          Load a genius into your AI.
        </h1>
        <div className="mt-8">
          <HeroDemo
            brainMeta={brainMeta}
            boardBrains={boardBrains}
            defaultBoardBrains={defaultBoardBrains}
          />
        </div>
      </section>

      {/* ─── Beat 5a: install in two minutes ─── */}
      <section className="bg-warm-paper px-6 py-14">
        <div className="mx-auto max-w-[860px] text-center">
          <h2 className="font-display text-2xl font-normal tracking-[-0.5px] text-deep-ink">
            Install in two minutes.
          </h2>
          <p className="mx-auto mt-5 inline-block rounded-lg bg-deep-ink px-5 py-3 font-mono text-[13px] text-[#e2e8f0]">
            <span className="text-success">1</span>{" "}download the pack&nbsp;&nbsp;&rarr;&nbsp;&nbsp;
            <span className="text-success">2</span>{" "}drop it into your project&nbsp;&nbsp;&rarr;&nbsp;&nbsp;
            <span className="text-success">3</span>{" "}/advise
          </p>
          <p className="mt-3 text-sm text-body">
            Works with Claude Code, Cursor, Gemini CLI, and any agent that supports skills.
          </p>
          <p className="mt-1 text-xs text-muted">
            The zip works today. The npx one-command install ships soon.
          </p>
        </div>
      </section>

      {/* ─── Beat 5b: the beta deal ─── */}
      <section className="px-6 py-14">
        <BetaBand />
      </section>

      {/* ─── Beat 5c: the other minds ─── */}
      <section className="px-6 pb-20">
        <div className="mx-auto max-w-[860px] text-center">
          <div className="flex flex-wrap items-center justify-center gap-2">
            {moreBrains.map((b) => (
              <Link
                key={b.slug}
                href={`/brains/${b.slug}`}
                className="rounded-full border border-border-default bg-white px-3.5 py-1.5 text-sm text-label transition-all hover:border-indigo-soft hover:text-brain-indigo"
              >
                <span aria-hidden className="mr-1.5">{b.emoji}</span>
                {b.name}
              </Link>
            ))}
            <Link
              href="/brains"
              className="px-2 text-sm font-semibold text-brain-indigo hover:underline"
            >
              Browse all {liveBrains.length}{" "}brains &rarr;
            </Link>
          </div>
          <p className="mt-4 text-xs text-muted">
            Built from public sources only — every brain shows you its atoms before you install.
          </p>
        </div>
      </section>
    </>
  );
}
