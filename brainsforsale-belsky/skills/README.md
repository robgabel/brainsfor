# Brain Skills Pack — 10 Thinking Skills

All 10 specialized skills for this brain are ready to use. Each skill activates a different reasoning mode, grounded in the thinker's actual ideas, frameworks, and worldview.

## Quick Reference

| Skill | Command | Purpose |
|-------|---------|---------|
| **Advise** | `/advise` | Strategic counsel on decisions — pulls relevant atoms, synthesizes perspective, cites sources |
| **Teach** | `/teach` | Learn a concept through the thinker's own vocabulary and mental models |
| **Debate** | `/debate` | Stress-test your position with counterarguments from this thinker's worldview |
| **Connect** | `/connect` | Find unexpected connections between your topic and ideas in the brain |
| **Evolve** | `/evolve` | Trace how the thinker's perspective on a topic has developed over time |
| **Apply** | `/apply` | Take a named framework and apply it step-by-step to your specific situation |
| **Mashup** | `/mashup` | Synthesize multiple ideas into something new — also works cross-brain with 2+ installed brains |
| **Brainfight** | `/brainfight` | Pit two ideas (or two brains) head-to-head and find agreements, contradictions, and unique angles |
| **Deep-dive** | `/deep-dive` | Exhaustive treatment — everything this brain knows about a topic, with connections and synthesis |
| **Surprise** | `/surprise` | Random serendipity — surface a high-confidence atom you probably haven't seen |

## Workflows

Skills are designed to chain together. Pick a workflow or freestyle:

- **Decision:** `/advise` → `/debate` (stress-test) → `/apply` (make it real)
- **Learning:** `/teach` → `/deep-dive` (go deeper) → `/evolve` (see how thinking changed)
- **Creative:** `/surprise` (inspiration) → `/connect` (link to your work) → `/apply` (use it)
- **Research:** `/deep-dive` → `/mashup` (cross-brain) → `/brainfight` (find disagreements)
- **Daily ritual:** `/surprise` each morning — 30 seconds of strategic inspiration

## Data Sources

All skills reference two files in the brain pack:

- **brain-atoms.json** — Structured knowledge atoms with topics, sources, dates, and confidence scores
- **brain-context.md** — Full narrative knowledge base organized by topic cluster

Load `brain-context.md` at the start of your session for best results. The atoms JSON is for programmatic access and filtering.

## Cross-Brain Features

If you have 2+ brain packs installed:

- `/mashup` auto-discovers other `brainsforsale-*` packages in your skill directory
- `/brainfight` can compare thinkers head-to-head on any topic
- No configuration needed — just install another brain and the skills detect it

## Quick Start

```
/advise "I'm facing [your decision]. What would this thinker recommend?"
```

You should get a response that cites specific atoms, synthesizes a perspective, and suggests a next skill.

## Troubleshooting

- **Skills not loading?** — Make sure `brain-context.md` is in your working directory or loaded as context
- **Responses feel generic?** — The LLM may not have the brain context loaded. Re-read `brain-context.md`
- **Want to go deeper?** — See the main `SKILL.md` in the pack root for full setup instructions

---

**[brainsforsale.com](https://brainsforsale.com)** — Load a genius into your AI.
