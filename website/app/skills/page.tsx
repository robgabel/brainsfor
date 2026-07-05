import { getLiveBrains, SKILLS } from "@/lib/brains";
import { getAllDemos } from "@/lib/skill-demos";
import { SkillJobs } from "@/components/SkillJobs";
import Link from "next/link";
import { SITE } from "@/lib/site-config";

export const metadata = {
  title: `Skills — ${SITE.name}`,
  description:
    "Eight thinking skills organized by the job: decide, create, learn — plus /board to convene five minds. Try them live.",
};

// Skills page = the homepage's second mile. Same rules: demo leads, text
// follows, skills are organized by the visitor's job (not our inventory),
// and the page ends on the same free-brain ask as the homepage.
export default function SkillsPage() {
  const liveBrains = getLiveBrains().map((b) => ({
    slug: b.slug,
    name: b.name,
    badge: b.badge,
    emoji: b.emoji,
  }));
  const demos = getAllDemos();
  const defaultBoardBrains = [
    "scott-belsky",
    "charlie-munger",
    "paul-graham",
    "steve-jobs",
    "elon-musk",
  ].filter((s) => liveBrains.some((b) => b.slug === s));

  return (
    <>
      {/* ─── The jobs, demo-first ─── */}
      <section className="px-6 pb-16 pt-12 md:pt-16">
        <h1 className="text-center font-display text-4xl font-light leading-[1.05] tracking-[-1.2px] text-deep-ink md:text-[48px]">
          Eight skills. Three jobs. One board.
        </h1>
        <div className="mt-8">
          <SkillJobs
            brains={liveBrains}
            skills={SKILLS}
            demos={demos}
            defaultBoardBrains={defaultBoardBrains}
          />
        </div>
      </section>

      {/* ─── Skills chain ─── */}
      <section className="bg-warm-paper px-6 py-14">
        <div className="mx-auto max-w-[860px] text-center">
          <h2 className="font-display text-2xl font-normal tracking-[-0.5px] text-deep-ink">
            Skills chain.
          </h2>
          <div className="mx-auto mt-5 inline-block rounded-lg bg-deep-ink px-6 py-4 text-left font-mono text-[13px] leading-7 text-[#e2e8f0]">
            <p>
              <span className="text-success">big decision</span>&nbsp;&nbsp;&rarr;&nbsp; /advise
              &rarr; /debate &rarr; /board
            </p>
            <p>
              <span className="text-success">blank page</span>&nbsp;&nbsp;&nbsp;&nbsp;&rarr;&nbsp; /surprise
              &rarr; /connect
            </p>
            <p>
              <span className="text-success">going deep</span>&nbsp;&nbsp;&nbsp;&nbsp;&rarr;&nbsp; /teach
              &rarr; /evolve &rarr; /predict
            </p>
          </div>
          <p className="mt-3 text-sm text-body">
            Every skill works in every brain. Chain them &mdash; the output of one is the input of the next.
          </p>
        </div>
      </section>

      {/* ─── Same ask as the homepage ─── */}
      <section className="px-6 py-16">
        <div className="mx-auto max-w-[640px] text-center">
          <h2 className="font-display text-2xl font-normal tracking-[-0.5px] text-deep-ink">
            The skills are the interface. The brain is the product.
          </h2>
          <div className="mt-6">
            <Link
              href="/brains"
              className="inline-block rounded-lg bg-brain-indigo px-7 py-3 text-[15px] font-semibold text-white shadow-brain-cta transition-all hover:bg-indigo-hover active:scale-[0.98]"
            >
              Browse all {liveBrains.length}{" "}brains &mdash; free in beta
            </Link>
          </div>
          <p className="mt-3 text-sm text-body">
            A zip you drop into Claude Code, Cursor, or any agent. No signup.
          </p>
        </div>
      </section>
    </>
  );
}
