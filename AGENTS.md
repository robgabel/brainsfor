# AGENTS.md

Boot file for any coding agent that is not Claude Code (Codex, Cursor, Antigravity, Gemini, Grok and the rest). Claude Code boots on CLAUDE.md; this file points everyone else at the same three documents, in this order.

1. [CLAUDE.md](CLAUDE.md): the rules. Brain status values, the two Supabase projects, the build pipeline, the QA regime and ship-gate, the website's password gate, and the dated "Lessons" blocks (this repo keeps its incidents inside CLAUDE.md; there is no separate LESSONS.md). A change has to obey it, whichever tool wrote the change.
2. [PRINCIPLES.md](PRINCIPLES.md): the beliefs the rules came from, in Rob's first person, with receipts. The 34 core principles are vendored from rob-ai under a hash; the BrainsFor layer follows. When no standing rule covers a decision, derive it from a principle and cite the number; if none fits, that is a question for Rob, not a reason to improvise.
3. [docs/synthetic-rob/](docs/synthetic-rob/): the long-form provenance for the BrainsFor layer (FIRST-PRINCIPLES.md with its say-versus-do tensions, and the clean-room QA-REPORT.md).

Everything in CLAUDE.md applies here: a machine verdict about a real person is a proposal until a human confirms it, new brains land `hidden` and a person promotes them, QA scores publish raw, public copy passes BRAND.md section 4, and Rob merges. The PR QA loop in `.agents/skills/pr-qa/SKILL.md` is the review of record for every pull request.
