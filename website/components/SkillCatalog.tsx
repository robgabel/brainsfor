import { SKILLS } from "@/lib/brains";

// Single source of truth for the 8+1 skill catalog block.
// Used on landing (`/`), `/skills`, and brain detail pages.
// Renders the inner content only — each page wraps in its own <section>
// to control background and vertical rhythm.
type Props = { showBoardTile?: boolean };

export function SkillCatalog({ showBoardTile = true }: Props) {
  const title = showBoardTile
    ? "8 thinking skills + 1 board skill per brain"
    : "8 thinking skills per brain";
  const subtitle = showBoardTile
    ? "Interactive reasoning modes that chain into workflows — plus /board, which fans out across brains."
    : "Interactive reasoning modes that chain into workflows.";

  return (
    <div className="mx-auto max-w-[1140px]">
      <h2 className="text-center font-display text-3xl font-normal tracking-[-0.75px] text-deep-ink md:text-4xl">
        {title}
      </h2>
      <p className="mx-auto mt-3 max-w-[640px] text-center text-base text-body">
        {subtitle}
      </p>

      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {SKILLS.map((skill) => (
          <div
            key={skill.name}
            className="group rounded-lg border border-border-default bg-white p-4 transition-all hover:border-border-indigo hover:shadow-brain"
          >
            <div className="text-2xl">{skill.icon}</div>
            <p className="mt-2 font-mono text-sm font-medium text-deep-ink">/{skill.name}</p>
            <p className="mt-1 text-xs leading-relaxed text-body">{skill.desc}</p>
            <span className="mt-2 inline-block rounded-full bg-cool-surface px-2 py-0.5 text-[10px] font-semibold text-muted">
              {skill.workflow}
            </span>
          </div>
        ))}

        {showBoardTile && (
          <div
            key="board"
            className="group rounded-lg border-2 border-brain-indigo bg-indigo-soft/20 p-4 shadow-brain transition-all hover:shadow-brain-cta"
          >
            <div className="text-2xl">&#x1F3DB;&#xFE0F;</div>
            <p className="mt-2 font-mono text-sm font-semibold text-brain-indigo">/board</p>
            <p className="mt-1 text-xs leading-relaxed text-body">
              Convene 3&ndash;5 brains on one question. Each reasons in isolation, then a chair synthesizes.
            </p>
            <span className="mt-2 inline-block rounded-full bg-brain-indigo px-2 py-0.5 text-[10px] font-semibold text-white">
              Multi-brain
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
