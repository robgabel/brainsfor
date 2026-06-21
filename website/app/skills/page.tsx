import { getLiveBrains, SKILLS } from "@/lib/brains";
import { getAllDemos, getDefaultDemo } from "@/lib/skill-demos";
import { SkillsPlayground } from "@/components/SkillsPlayground";
import { SkillCatalog } from "@/components/SkillCatalog";
import Link from "next/link";

export const metadata = {
  title: "Skills \u2014 brainsforagents",
  description:
    "Try 8 AI thinking skills powered by the world\u2019s best thinkers. See the difference structured knowledge makes.",
};

export default function SkillsPage() {
  const liveBrains = getLiveBrains().map((b) => ({
    slug: b.slug,
    name: b.name,
    badge: b.badge,
    emoji: b.emoji,
  }));
  const demos = getAllDemos();
  const defaultDemo = getDefaultDemo();

  return (
    <>
      {/* \u2500\u2500\u2500 Hero \u2500\u2500\u2500 */}
      <section className="px-6 pb-8 pt-20 md:pt-28">
        <div className="mx-auto max-w-[900px] text-center">
          <h1 className="font-display text-4xl font-light leading-[1.05] tracking-[-1.2px] text-deep-ink md:text-[48px]">
            Pick a brain. Pick a skill.
          </h1>
          <p className="mx-auto mt-5 max-w-[640px] text-lg leading-relaxed text-body">
            See what only a knowledge graph can do &mdash; temporal evolution,
            typed connections, and source-cited voice that no prompt alone can fake.
          </p>
        </div>
      </section>

      {/* \u2500\u2500\u2500 Skill Catalog (info first, demo after) \u2500\u2500\u2500 */}
      <section className="bg-warm-paper px-6 py-20">
        <SkillCatalog />
      </section>

      {/* \u2500\u2500\u2500 Interactive Playground \u2500\u2500\u2500 */}
      <section className="pb-20 pt-20">
        <SkillsPlayground
          brains={liveBrains}
          skills={SKILLS}
          demos={demos}
          defaultBrain={defaultDemo.brain}
          defaultSkill={defaultDemo.skill}
        />
      </section>

      {/* \u2500\u2500\u2500 CTA \u2500\u2500\u2500 */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-[640px] text-center">
          <h2 className="font-display text-3xl font-normal tracking-[-0.75px] text-deep-ink md:text-4xl">
            Ready to load a brain?
          </h2>
          <p className="mt-3 text-base text-body">
            Install in seconds. Works with Claude Code, Cursor, Gemini CLI, and
            more.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/brains"
              className="rounded-lg bg-brain-indigo px-6 py-3 text-[15px] font-semibold text-white shadow-brain-cta transition-all hover:bg-indigo-hover active:scale-[0.98]"
            >
              Browse Brains
            </Link>
            <Link
              href="/pricing"
              className="rounded-lg border-[1.5px] border-indigo-soft bg-transparent px-6 py-3 text-[15px] font-semibold text-brain-indigo transition-all hover:border-brain-indigo hover:bg-brain-indigo/5"
            >
              View Pricing
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
