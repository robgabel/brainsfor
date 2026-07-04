"use client";

import { useState } from "react";
import { track } from "@vercel/analytics";
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
  uniqueToBrains?: boolean;
}

interface SkillJobsProps {
  brains: BrainOption[];
  skills: SkillOption[];
  demos: Record<string, SkillDemo>;
  defaultBoardBrains: string[];
}

// Skills organized by the job the visitor is hiring them for, not by our
// inventory. The three jobs map to the persona stack (personas.md): Decide =
// operators/team leads, Create = content creators, Learn = students/true
// fans. Convene = /board, the multi-brain surface — same component as the
// homepage's second tab. Seed questions are per-skill (a /debate seed makes
// no sense under /evolve) and auto-run on click: the moment of intent is the
// most precious event in the funnel — never meet it with an empty textarea.
interface JobDef {
  id: string;
  label: string;
  blurb: string;
  skills: string[];
  defaultBrain: string;
  seeds: Record<string, string[]>;
}

const JOBS: JobDef[] = [
  {
    id: "decide",
    label: "Decide",
    blurb:
      "Pressure-test a real call — pricing, hiring, ship dates — with thinkers who've made it before.",
    skills: ["advise", "debate", "coach"],
    defaultBrain: "annie-duke",
    seeds: {
      advise: [
        "Should I raise my prices 20% or grandfather existing customers?",
        "First key hire: senior engineer or designer?",
      ],
      debate: [
        "Our roadmap should follow our biggest customer's requests.",
        "We should delay launch until the product feels perfect.",
      ],
      coach: ["I keep putting off shutting down our second product."],
    },
  },
  {
    id: "create",
    label: "Create",
    blurb:
      "Fresh angles when the page is blank — atoms and bridges you wouldn't reach on your own.",
    skills: ["surprise", "connect"],
    defaultBrain: "scott-belsky",
    seeds: {
      surprise: ["Show me something I haven't seen."],
      connect: ["Connect taste to hiring.", "Bridge poker to product roadmaps."],
    },
  },
  {
    id: "learn",
    label: "Learn",
    blurb:
      "Deeper than a summary — how a thinker reasons, and how their mind changed over time.",
    skills: ["teach", "evolve", "predict"],
    defaultBrain: "charlie-munger",
    seeds: {
      teach: ["Explain moats like I'm a first-time founder."],
      evolve: ["How has your thinking on technology changed?"],
      predict: ["What happens if code becomes free?"],
    },
  },
];

function safeTrack(name: string, props?: Record<string, string>) {
  try {
    track(name, props);
  } catch {
    // analytics must never break the page
  }
}

export function SkillJobs({ brains, skills, demos, defaultBoardBrains }: SkillJobsProps) {
  const [jobId, setJobId] = useState<string>("decide");
  const job = JOBS.find((j) => j.id === jobId);

  const tabs = [...JOBS.map((j) => ({ id: j.id, label: j.label })), { id: "board", label: "Convene" }];

  const jobSkills = job ? skills.filter((s) => job.skills.includes(s.name)) : [];
  const jobDefaultBrain =
    job && brains.some((b) => b.slug === job.defaultBrain)
      ? job.defaultBrain
      : brains[0]?.slug ?? "";

  return (
    <div>
      {/* ─── Job tabs (same pill pattern as the homepage demo tabs) ─── */}
      <div className="flex flex-wrap items-center justify-center gap-2" role="tablist" aria-label="Pick your job">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={jobId === t.id}
            onClick={() => {
              setJobId(t.id);
              safeTrack("skills_job_switch", { job: t.id });
            }}
            className={`rounded-full px-4 py-1.5 font-mono text-[13px] transition-all ${
              jobId === t.id
                ? "bg-brain-indigo text-white shadow-sm"
                : "bg-cool-surface text-label hover:bg-brain-indigo/10 hover:text-brain-indigo"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <p className="mx-auto mt-3 max-w-[560px] text-center text-sm text-body">
        {job
          ? job.blurb
          : "One question, up to five independent minds, disagreement visible — then a chair synthesizes."}
      </p>

      <div className="mt-8">
        {job ? (
          <SkillsPlayground
            key={job.id}
            brains={brains}
            skills={jobSkills}
            demos={demos}
            defaultBrain={jobDefaultBrain}
            defaultSkill={job.skills[0]}
            seedsBySkill={job.seeds}
          />
        ) : (
          <BoardDemo brains={brains} defaultBrains={defaultBoardBrains} />
        )}
      </div>
    </div>
  );
}
