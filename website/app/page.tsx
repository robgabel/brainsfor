import { BRAINS, SKILLS, getLiveBrains } from "@/lib/brains";
import { getAllDemos } from "@/lib/skill-demos";
import { BrainCard } from "@/components/BrainCard";
import { InstallCommand } from "@/components/InstallCommand";
import { RequestBrainForm } from "@/components/RequestBrainForm";
import { LivePlayground } from "@/components/LivePlayground";
import { SkillCatalog } from "@/components/SkillCatalog";
import Link from "next/link";

export default function Home() {
  const liveBrains = getLiveBrains().map((b) => ({
    slug: b.slug,
    name: b.name,
    badge: b.badge,
    emoji: b.emoji,
  }));
  const demos = getAllDemos();
  // Default the homepage to Scott Belsky — he's the showcase brain. Falls back
  // to the first live brain if Belsky isn't installed.
  const preferredHero =
    liveBrains.find((b) => b.slug === "scott-belsky")?.slug ??
    liveBrains[0]?.slug ??
    "";
  // Seed the Board tab with five strong, diverse voices when available.
  const defaultBoardBrains = [
    "scott-belsky",
    "charlie-munger",
    "paul-graham",
    "steve-jobs",
    "peter-attia",
  ].filter((s) => liveBrains.some((b) => b.slug === s));

  return (
    <>
      {/* ─── Hero ─── */}
      <section className="px-6 pb-12 pt-20 md:pt-28">
        <div className="mx-auto max-w-[900px] text-center">
          <h1 className="font-display text-4xl font-light leading-[1.05] tracking-[-1.5px] text-deep-ink md:text-[56px]">
            Load a genius into your AI.
          </h1>
          <p className="mx-auto mt-5 max-w-[640px] text-lg leading-relaxed text-body">
            The reasoning a prompt can&rsquo;t fake. The taste a model can&rsquo;t learn.
          </p>

          <div className="mt-8 flex flex-col items-center gap-4">
            <InstallCommand />
            <p className="font-mono text-xs text-muted">
              Works with Claude Code, Hermes, OpenClaw, Cursor and more
            </p>
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <a
              href="#try-it"
              className="rounded-lg bg-brain-indigo px-6 py-3 text-[15px] font-semibold text-white shadow-brain-cta transition-all hover:bg-indigo-hover active:scale-[0.98]"
            >
              Try it live &darr;
            </a>
            <Link
              href="/brains"
              className="rounded-lg border-[1.5px] border-indigo-soft bg-transparent px-6 py-3 text-[15px] font-semibold text-brain-indigo transition-all hover:bg-brain-indigo/5 hover:border-brain-indigo"
            >
              Browse {liveBrains.length} brains
            </Link>
          </div>
        </div>
      </section>

      {/* ─── Brain Catalog Preview ─── */}
      <section className="bg-warm-paper px-6 py-20">
        <div className="mx-auto max-w-[1140px]">
          <h2 className="text-center font-display text-3xl font-normal tracking-[-0.75px] text-deep-ink md:text-4xl">
            {liveBrains.length} minds, ready to install
          </h2>
          <p className="mx-auto mt-3 max-w-[640px] text-center text-base text-body">
            The same atoms a brain uses to answer &mdash; visible to you before you install.
          </p>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {BRAINS.map((brain) => (
              <BrainCard key={brain.slug} brain={brain} />
            ))}
          </div>

          <div className="mt-8 text-center">
            <Link href="/brains" className="text-sm font-semibold text-brain-indigo hover:underline">
              View all brains &rarr;
            </Link>
          </div>
        </div>
      </section>

      {/* ─── Skill Showcase ─── */}
      <section className="px-6 py-20">
        <SkillCatalog />
      </section>

      {/* ─── Live Playground (3 tabs: voice / evolve / board) ─── */}
      <section id="try-it" className="px-6 pb-20 pt-4 scroll-mt-20">
        <div className="mx-auto mb-10 max-w-[900px] text-center">
          <h2 className="font-display text-3xl font-normal tracking-[-0.75px] text-deep-ink md:text-4xl">
            Three things your LLM can&rsquo;t do.
          </h2>
          <p className="mx-auto mt-3 max-w-[680px] text-base text-body">
            Each tab below is a different proof point. None of them are imitations of vanilla
            Claude with a clever prompt &mdash; they rely on the knowledge graph, the temporal data,
            or the multi-brain orchestration that ships with every brain pack.
          </p>
        </div>

        <LivePlayground
          brains={liveBrains}
          skills={SKILLS}
          demos={demos}
          defaultBrain={preferredHero}
          defaultBoardBrains={defaultBoardBrains}
        />
      </section>

      {/* ─── How It Works ─── */}
      <section className="bg-warm-paper px-6 py-20">
        <div className="mx-auto max-w-[1140px]">
          <h2 className="text-center font-display text-3xl font-normal tracking-[-0.75px] text-deep-ink md:text-4xl">
            Three steps to install.
          </h2>

          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {[
              {
                step: "01",
                title: "Browse & choose",
                desc: "Explore the full knowledge graph. See every atom, connection, and insight before you install.",
              },
              {
                step: "02",
                title: "Install with one command",
                desc: "One line in your terminal. Works with Claude Code, Cursor, Gemini CLI, and any AI tool that supports skills.",
                code: "npx skills add brainsfor/scott-belsky",
              },
              {
                step: "03",
                title: "Use 8 thinking skills + /board",
                desc: "From /advise for decisions to /surprise for daily inspiration, plus /board to convene multiple brains. Chain skills into workflows.",
              },
            ].map((item) => (
              <div key={item.step} className="rounded-xl bg-white p-6 shadow-brain">
                <span className="font-mono text-xs font-semibold text-brain-indigo">{item.step}</span>
                <h3 className="mt-3 font-display text-xl font-normal tracking-tight text-deep-ink">{item.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-body">{item.desc}</p>
                {item.code && (
                  <>
                    <div className="mt-4 rounded-lg bg-deep-ink px-4 py-3 font-mono text-xs text-success">
                      $ {item.code}
                    </div>
                    <p className="mt-2 text-xs text-muted">
                      Launching next week —{" "}
                      <a
                        href="/brains/scott-belsky/scott-belsky-brain-pack.zip"
                        download
                        className="font-medium text-brain-indigo hover:underline"
                      >
                        download the zip
                      </a>{" "}
                      in the meantime.
                    </p>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Sources & Ethics ─── */}
      <section className="px-6 py-12">
        <div className="mx-auto max-w-[720px] rounded-xl border border-border-default bg-cool-surface p-6 text-center">
          <h3 className="font-display text-lg font-normal tracking-tight text-deep-ink">
            Built from public sources only
          </h3>
          <p className="mx-auto mt-2 max-w-[560px] text-sm leading-relaxed text-body">
            Every brain is derived exclusively from freely available, public resources &mdash; interviews, podcasts,
            free newsletters, talks, and blog posts. No commercial transcripts or paywalled content.
            Where book ideas appear, they come from public discourse: reviews, author interviews, and press coverage.
          </p>
        </div>
      </section>

      {/* ─── Request a Brain ─── */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-[640px] text-center">
          <h2 className="font-display text-3xl font-normal tracking-[-0.75px] text-deep-ink md:text-4xl">
            Who should we build next?
          </h2>
          <p className="mt-3 text-base text-body">
            Request a thinker. When a brain hits 50 requests, we build it.
          </p>
          <div className="mt-8">
            <RequestBrainForm />
          </div>
        </div>
      </section>
    </>
  );
}
