---
name: pr-qa
description: Independent QA pass on a BrainsFor pull request by a SEPARATE agent. Read-only; reports findings, fixes nothing. The builder spawns a fresh subagent and hands it this file's path plus the PR number.
disable-model-invocation: true
---

# PR QA (the separate reviewer)

## Why this exists

The agent that wrote a change is the worst judge of it: it reviews its own intent, not its own diff (core principle 14 in [PRINCIPLES.md](../../../PRINCIPLES.md)). Every PR on this repo gets a second agent with no memory of the build session, whose only input is the PR and the repo. Loop: build, draft PR, independent QA, builder applies fixes and re-runs QA, until `VERDICT: PASS` or three consecutive minor-only rounds; then Rob merges. A finding that changes a printed fact about a real person is never minor.

## Who runs it

The builder spawns it with the Agent tool (`subagent_type: general-purpose`) once the draft PR exists, with only the PR number, this file's path and a fresh, empty scratchpad folder. No pre-briefing with what the builder "meant" to build.

## What the QA agent does (read-only)

1. Read the PR over REST (`gh api repos/robgabel/brainsfor/pulls/<n>`, `.../pulls/<n>/files --paginate`, and `-H "Accept: application/vnd.github.diff"`), or the GitHub MCP tools. Read every touched file in full, not just hunks. Judge the diff, not the story around it.
2. Run the locks that apply, from a fresh worktree of the PR head merged into `origin/main`:
   - Any PR: `node --test scripts/test/principles-core-vendored.test.ts` (the vendored core was not edited in place).
   - A PR touching `brains/**`: `python3 scripts/audit-brains.py --brain <slug>` for each touched brain; `python3 scripts/publish-qa-scores.py --dry-run` if `brains/index.json` changed. A `status` flip to `live` needs the ship-gate in CLAUDE.md (persona-QA >= 70, zero high-severity numeric defects, voice >= 0.60 or panel-authenticity >= 80); a flip without a fresh `evals/persona-qa-*.json` is a finding.
   - A PR touching `website/**`: `cd website && npm ci && npm run lint && npm run build` (prebuild regenerates `public/brains` from `../brains`; a build that cannot see `../brains` is a setup error, not a pass).
   - A PR touching `scripts/*.py`: `python3 -m py_compile` on each touched script, and `--dry-run` on any script that has one.
3. Judge against the repo's own rules, in this order of severity:
   - **Correctness:** does the diff do what the body claims? Trace one input through it.
   - **Truth about real people (blocker class):** a `false` or `contested` verdict, a reattributed `source_ref`, a stripped `original_quote`, or a changed hard figure in any `brains/*/pack/` or `brain.json` needs the human-gate record in the PR (who confirmed it, when); machine verdicts never auto-publish (CLAUDE.md, verify-facts HARD LESSON). Quotes must be corpus-verifiable; a provenance warning on a brain whose transcripts are not fetched locally is not fabrication (CLAUDE.md 2026-07-04 lesson).
   - **Registry drift:** `brains/index.json`, the shipped `pack/brain-atoms.json` and Supabase counts must agree; a PR that changes one without the others is a finding (core principle 9).
   - **Principles:** a diff that works against a numbered principle in `PRINCIPLES.md` is a finding that cites the number; a new standing rule the PR adds to CLAUDE.md names the principle it serves, or the PR says none does (that is a question for Rob).
   - **Public copy:** anything user-facing passes BRAND.md section 4 (banned words, no em dashes, no "AI clone", specifics over superlatives) and section 11 (never imply the thinker endorsed the brain; never hide the data).
   - **Fail-closed posture:** a new API route keeps the rate limiter fail-closed; a new Supabase RPC is slug-allowlisted and capped; no service key in client code.
   - **Docs:** CLAUDE.md updated if the PR added a script, a pipeline phase, a table, an env var, a workflow or a brain status rule. A missing update is a finding, not a nit.
4. Verify claims, don't trust them. "Re-exported" means `pack/brain-context.md` matches `pack/brain-atoms.json` on the same head (PR #61 shipped a stale export once).

## What the QA agent must NOT do

Edit, commit, push, comment on the PR, mark it ready, enable auto-merge, or merge. Guess at Rob's intent; an ambiguous spec is itself a finding. Pad the report; zero findings is a valid result, say so in one line.

## Report format

```
VERDICT: PASS | FINDINGS
CHECKS RUN: <each lock and its result, with the head sha>

F1 [severity: blocker|major|minor] <one-line claim>
   file:line
   Failure scenario: <concrete input -> wrong output>
   Evidence: <what you ran or read>
```

Severity: blocker = ships a wrong fact about a real person, loses pack data, breaks a page, or opens a security hole; major = a real bug on a real path, or a missing lock/doc for a new rule; minor = style, naming, a nit. Rob sees all of them.
