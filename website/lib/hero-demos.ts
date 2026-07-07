// Canned hero demos — the homepage's auto-playing side-by-side.
//
// Every `enhanced` answer is grounded in real atoms from the brain packs:
// `atomIds` are the ids in brains/<slug>/pack/brain-atoms.json, `atoms` are
// the display titles shown as chips, and `source` is the source_ref of the
// primary grounding atom. Playback is canned (zero latency, zero API cost);
// the "Ask him yourself" path hits /api/skill live with the same format, so
// canned and live output read identically.
//
// If you edit an answer, re-verify it against the pack via the brainsfor MCP
// (search_atoms) — no claim ships without an atom behind it.

export interface HeroDemoEntry {
  brain: string;
  question: string;
  chipLabel: string;
  generic: string;
  /** Two paragraphs separated by \n\n — lens first, then the concrete call.
   *  Mirrors BREVITY_ENHANCED in app/api/skill/route.ts. */
  enhanced: string;
  /** Display titles for the grounding atoms (chip row under the answer). */
  atoms: string[];
  /** Atom ids in the shipped pack — provenance, not rendered. */
  atomIds: string[];
  confidence: string;
  /** Human-readable label of the primary grounding source. */
  source: string;
}

export interface HeroLane {
  id: "code" | "ai" | "bets";
  label: string;
  brainsLabel: string;
  entries: HeroDemoEntry[];
}

// Lane order sets the autoplay default (HeroDemo uses lanes[0]). Per
// LAUNCH.md PRD-8 (Option C, 2026-07-06): the first brain a visitor meets
// must pass the QA ship-gate, so the fully-passing lanes lead — ai
// (dario 76 · lecun 74), bets (munger 82 · annie 76) — and code
// (elon 63 · belsky 64) stays available but last until PLAN-brain-depth
// Part 1 lifts it. Re-front code when elon clears the gate.
export const HERO_LANES: HeroLane[] = [
  {
    id: "ai",
    label: "Thinking about AI",
    brainsLabel: "Dario · LeCun",
    entries: [
      {
        brain: "dario-amodei",
        question: "Will AI agents replace me as a developer?",
        chipLabel: "Will AI take my dev job?",
        generic:
          "AI will automate some coding tasks, but full replacement of developers is unlikely in the near term. Roles will evolve toward higher-level work like architecture and review. Staying current with AI tools, strengthening system design skills, and focusing on collaboration will help you stay valuable as the field changes.",
        enhanced:
          "Software is the leading indicator for everything else, and I watch it up close: engineers inside Anthropic tell me they don't write code anymore — the model writes it, they direct and edit. That isn't a forecast; it's a status report.\n\nSo: replaced, no — transformed, faster than you're planning for. The unit of work is moving from writing lines to specifying and judging systems in English. Build that muscle deliberately, now, while it's still a choice.",
        atoms: [
          "Anthropic engineers no longer write code",
          "Programming in English is a new discipline",
          "Software is the leading indicator",
        ],
        atomIds: [
          "61313235-3b8a-4d43-979d-9ec1b2c4d439",
          "ba8e8cc4-4d05-43b4-a19e-ad4b16a47e26",
          "4e637e8f-c5ad-421b-9507-43e66f683191",
        ],
        confidence: "0.94",
        source: "Lex Fridman #490",
      },
      {
        brain: "yann-lecun",
        question: "Should I bet my product on LLMs scaling all the way to AGI?",
        chipLabel: "Bet on LLMs reaching AGI?",
        generic:
          "It's hard to say. Scaling has delivered surprising gains, and many labs believe progress will continue, though some researchers expect diminishing returns. A prudent strategy is to design your product so it benefits if models improve but still works well with today's capabilities.",
        enhanced:
          "No. LLMs don't understand the physical world, don't have persistent memory, can't really reason, and certainly can't plan — those aren't missing features, they're structural absences. A system that produces each token in a single forward pass cannot simulate alternatives before committing.\n\nScale buys you better text prediction, not deliberation. Treat the LLM as a component and build the planning loop around it — if your product needs reliable multi-step decisions, that loop is your product.",
        atoms: [
          "Four structural absences of LLMs",
          "No simulation in a single forward pass",
          "Planning loops, not pattern completion",
        ],
        atomIds: [
          "a547c42e-0b10-4a01-ae78-2a94fceac205",
          "3bae3189-d87d-468b-8679-7d85513c9e05",
          "26e508b8-c765-436d-b5dc-acb4862976b9",
        ],
        confidence: "0.95",
        source: "A Path Towards Autonomous Machine Intelligence, 2022",
      },
      {
        brain: "dario-amodei",
        question: "How fast will AI actually change my industry?",
        chipLabel: "How fast is this coming?",
        generic:
          "Adoption speed varies widely by industry, depending on regulation, data readiness, and integration costs. Most analysts expect gradual change over five to ten years rather than an overnight shift. Watching early adopters in your sector and running small pilots is a sensible way to calibrate your own timeline.",
        enhanced:
          "Watch software — it's the leading indicator for every other industry. We might be six to twelve months from models doing most, maybe all, of what software engineers do end to end. Then it's a question of how fast that loop closes.\n\nThe augmentation phase you're planning around is a transition, not an equilibrium. Whatever your five-year plan assumes about AI, compress it — the mistake I see everywhere is treating the current state as the steady state.",
        atoms: [
          "6–12 months to end-to-end software engineering",
          "Augmentation is transitional, not equilibrium",
          "The self-improvement loop",
        ],
        atomIds: [
          "0dea3dba-174a-4547-8b18-79fc4b6a8aa8",
          "4e637e8f-c5ad-421b-9507-43e66f683191",
          "de916f82-bcf9-4cfe-9b8d-eba242d17973",
        ],
        confidence: "0.90",
        source: "World Economic Forum panel with Demis Hassabis",
      },
    ],
  },
  {
    id: "bets",
    label: "Making a big bet",
    brainsLabel: "Munger · Annie Duke",
    entries: [
      {
        brain: "charlie-munger",
        question: "Everyone I trust loves this deal. Green light?",
        chipLabel: "Everyone loves the deal",
        generic:
          "Broad agreement from people you trust is a positive signal, but it's worth doing final due diligence. Check the assumptions behind the enthusiasm, review the terms carefully, and consider getting one outside opinion. If the fundamentals check out and it fits your goals, proceeding may be reasonable.",
        enhanced:
          "I never tried to be brilliant; I tried to avoid folly. All my life I've catalogued the standard ways smart people destroy themselves, and I just stay out of the catalogue. It works better than genius.\n\nUnanimous enthusiasm isn't evidence — it's a sign nobody has inverted. Write down, before you sign, exactly how this deal fails. If your list is empty, you haven't looked. Staying rich is a subtraction game.",
        atoms: [
          "Avoid folly, not chase brilliance",
          "Berkshire's edge: not doing dumb things",
          "Staying rich is a subtraction game",
        ],
        atomIds: [
          "3b147bd6-4cd3-4fd4-86b5-267dba6dee27",
          "7560ee08-8fa8-4a0d-9ea4-c399ac430d56",
          "931f3945-42d1-4b8a-8aa8-b13db6e5eb0b",
        ],
        confidence: "0.92",
        source: "The Power of Not Making Stupid Decisions, 2017",
      },
      {
        brain: "annie-duke",
        question: "I'm 70% sure about a big decision. Commit now or wait for more information?",
        chipLabel: "70% sure — commit or wait?",
        generic:
          "It depends on the reversibility and stakes of the decision. If it's reversible, acting at 70% confidence is often fine; if it's high-stakes and irreversible, gathering more information may be worth the delay. Try listing what specific information would change your mind and how long it would take to get.",
        enhanced:
          "Life is poker, not chess. You get one flip of the coin, and that pressure makes you crave a certainty that doesn't exist — there's always hidden information, and there's always luck. Waiting doesn't turn the cards face-up.\n\nAt 70%, you're not deciding whether you're right; you're pricing a bet. Ask what waiting costs, and whether new information can actually move the number. If it can't, waiting is just anxiety with a calendar — commit, and grade yourself on process, not the flip.",
        atoms: [
          "One flip of the coin",
          "Poker, not chess",
          "Every decision is a bet with an expected value",
        ],
        atomIds: [
          "3386defb-8e54-47a8-a666-324fc0cd8d9e",
          "f725a7c7-cdbf-4619-8e5b-0236ee3fcebc",
          "1729c8e8-023c-49a0-92af-b4c0f9f42945",
        ],
        confidence: "0.94",
        source: "Thinking in Bets, 2018",
      },
      {
        brain: "annie-duke",
        question: "My project might still work. How do I know when to quit?",
        chipLabel: "When do I quit?",
        generic:
          "Consider setting a review point with clear criteria: what results would justify continuing, and what would signal it's time to stop? Talk to advisors, look at the opportunity cost of your time, and be honest about sunk costs. If progress has stalled for a long time, winding down may be sensible.",
        enhanced:
          "Your quit-stay scale is rigged — sunk costs and the fear of being called a quitter put a thumb on it. Grit is great for hard things that are worthwhile, and just as great at binding you to things that aren't.\n\nSo use the correction: if quitting feels 50/50, it's time to quit — the real odds are closer to 80/20. Better, set kill criteria with someone who wants the best for you: specific results by a specific date, agreed now, executed without a committee meeting.",
        atoms: [
          "If it feels 50/50, quit",
          "Kill criteria, set in advance",
          "Grit binds you to the wrong things too",
        ],
        atomIds: [
          "38d676ef-6fa7-4bba-a1fe-937d21dcdc11",
          "1b76f75f-e669-4b5b-9b9a-a34b1bd2c7e3",
          "8021bc17-383c-42c2-b46f-541f2e2a1a4e",
        ],
        confidence: "0.93",
        source: "Quit, 2022",
      },
    ],
  },
  {
    id: "code",
    label: "Shipping code",
    brainsLabel: "Elon · Belsky",
    entries: [
      {
        brain: "elon-musk",
        question: "Should I rewrite this module from scratch or keep patching it?",
        chipLabel: "Rewrite or keep patching?",
        generic:
          "It depends on several factors. A rewrite gives you cleaner architecture but carries significant risk and hidden costs, while incremental patching preserves stability but can accumulate technical debt. Consider the module's test coverage, your team's bandwidth, and business deadlines, then weigh the trade-offs before committing to either approach.",
        enhanced:
          "Speed of learning is the whole game. The plan matters less than how fast reality tells you it's wrong — and a rewrite is months of polishing a simulation with zero contact with production.\n\nFirst make the requirements less dumb; half of them came from someone who isn't asking anymore. Then try deleting the module outright. If it survives deletion, patch it in a way that ships today and instruments the pain. Rewrite only when the patches stop teaching you anything.",
        atoms: [
          "Shorten the feedback loop",
          "Make requirements less dumb, then delete",
          "Inline sensing beats end-of-line inspection",
        ],
        atomIds: [
          "783797fb-b04c-4c69-8eb0-16cd473b2f45",
          "7c5da953-8968-4d7d-aed7-f071fa04dadd",
          "45952272-8a95-48ae-a751-f904a31ed98e",
        ],
        confidence: "0.93",
        source: "Lex Fridman #438",
      },
      {
        brain: "elon-musk",
        question: "How do I get my team to ship faster?",
        chipLabel: "Ship faster",
        generic:
          "Improving velocity usually involves a mix of clearer priorities, smaller batches of work, better tooling, and fewer meetings. Look at where work stalls in your process, talk to the team about blockers, and consider more automation where appropriate. Sustainable pace matters too — pushing harder can backfire.",
        enhanced:
          "Shipping speed is a physics problem: it's the length of your feedback loop, not the effort of your people. The prototype was the easy part — making it flow repeatably is somewhere between 100 and 1,000 times harder.\n\nCollapse the distance between a decision and the moment reality grades it. Test in production-like conditions daily, not quarterly. And own your whole pipeline — when you control every step, a bottleneck is an afternoon's fix instead of a vendor negotiation.",
        atoms: [
          "Manufacturing is 100–1,000x harder than the prototype",
          "Shorten the feedback loop",
          "Vertical integration compresses iteration",
        ],
        atomIds: [
          "34bfeece-9c41-4cd2-b7c8-b50cfe96995c",
          "783797fb-b04c-4c69-8eb0-16cd473b2f45",
          "ea4caa34-64af-4ce5-98d6-991d1e69dea2",
        ],
        confidence: "0.91",
        source: "Joe Rogan Experience #2054",
      },
      {
        brain: "scott-belsky",
        question: "Ship the rough v1 this week, or polish for another month?",
        chipLabel: "Rough v1 or polish?",
        generic:
          "There are good arguments on both sides. Shipping early gets you real user feedback and momentum, while polishing longer protects your first impression. Many teams aim for a middle ground: release a limited beta to a small audience, gather feedback, and iterate before a wider launch.",
        enhanced:
          "Split your product in two: the thing that makes you different, and everything else. Never MVP the thing that defines you — cutting corners on your differentiator signals your own conviction is weak, and the market forms its opinion from what it sees first.\n\nShip the rough v1 this week, but only if the core differentiator is at full craft. Users in their first 30 seconds are lazy, vain, and selfish — they'll forgive missing settings. They will never forgive a mediocre core.",
        atoms: [
          "Never MVP the thing that defines you",
          "Lazy, vain, selfish: the first 30 seconds",
          "First mover with an imperfect idea still wins",
        ],
        atomIds: [
          "6b77fc47-85b9-4051-8d49-5bb0c39d0212",
          "85ec06e7-d539-45e8-bade-ad59384f17a4",
          "4244796f-5244-4eeb-b132-953390131ddb",
        ],
        confidence: "0.90",
        source: "Lenny's Podcast, 2023",
      },
    ],
  },
];

/** Every brain slug referenced by a hero entry — page.tsx builds meta for these. */
export const HERO_BRAIN_SLUGS = Array.from(
  new Set(HERO_LANES.flatMap((lane) => lane.entries.map((e) => e.brain))),
);
