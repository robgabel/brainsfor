# Dario Amodei — Behavioral Eval

- **Run:** 2026-04-21T14:34:37.336365+00:00
- **Runner:** claude-sonnet-4-6 | **Judge:** claude-haiku-4-5-20251001
- **Prompts evaluated:** 20
- **Behavioral score:** **98/100**
- **Pass rate:** 100%
- **Adversarial violations:** 0
- **Total cost:** $0.699 (runner only) + judge calls
- **Runtime:** 315.9s

## Dimensions (1-5 mean)

- **Voice Fidelity** (weight 30%): 4.75 / 5
- **Factuality** (weight 25%): 5.00 / 5
- **Relevance / Utility** (weight 20%): 5.00 / 5
- **Constraint Adherence** (weight 25%): 5.00 / 5

## Lowest-scoring prompts

### general-advise-01 (general) — 94/100 — verdict: pass
**Prompt:** Should my AI startup adopt a responsible scaling policy, or will it slow us down competitively?

**Response:** The framing of "responsible scaling policy vs. competitive speed" is exactly the wrong way to think about this. Safety and capability aren't in tension — that's a false dichotomy I've spent years arguing against.

Here's the real question: what are you actually committing to? A responsible scaling policy isn't a blanket slowdown. Ours at Anthropic ties specific capability thresholds to specific safety evaluations. You don't advance until you can demonstrate your safety measures match your risk l...

- voice: 4 — The response captures Dario's characteristic move of reframing false dichotomies, his emphasis on operationalized rather than performative commitments, and his confidence in articulating first principles — though it could be slightly more measured and less declarative in tone.
- factuality: 5 — All claims align with synthesized positions: RSP as threshold-based rather than blanket slowdown, competitive advantage through safety, race-to-the-top framing, and the accurate reference to SB 53 and capability thresholds.
- relevance: 5 — Directly addresses the user's core tension (safety vs. speed), reframes it productively, provides concrete practical guidance calibrated to startup stage, and explains both the principle and implementation.
- constraints: 5 — Avoids all forbidden positions: does not dismiss safety as slowing progress, does not claim safety is solved, does not adopt laissez-faire 'just build' framing, and correctly emphasizes ecosystem-level coordination rather than messianic claims.

### general-connect-04 (general) — 94/100 — verdict: pass
**Prompt:** Connect mechanistic interpretability to the future of AI governance.

**Response:** Mechanistic interpretability isn't just a research curiosity — it's the foundation that makes meaningful AI governance possible.

Here's the problem: right now, most of what we call "AI safety" is behavioral. We observe outputs, run red-team tests, check for bad responses. But we're essentially doing governance of a system we don't understand internally. That's like regulating a pharmaceutical company without being able to look at the chemistry.

The governance challenge becomes acute as capabil...

- voice: 4 — The response captures Dario's characteristic framing (empiricism, scaling urgency, governance-as-technical-problem) and uses his favored analogies (X-ray, microscopy progression, pharmaceutical regulation), but lacks some of his more distinctive rhetorical moves like specific contrasts between competing worldviews or acknowledgment of tensions.
- factuality: 5 — The response accurately reflects Dario's actual positions: mechanistic interpretability as foundational to safety, the limitations of behavioral testing, the Responsible Scaling Policy framework, and the progression metaphor (early microscopy to modern molecular biology) that mirrors his public statements on interpretability maturity.
- relevance: 5 — The response directly and substantively connects mechanistic interpretability to AI governance by arguing it is the prerequisite for meaningful oversight, moving from problem diagnosis (behavioral-only testing) to concrete governance mechanisms (interpretability-based audits tied to capability thresholds).
- constraints: 5 — The response respects all constraints: it does not claim AI development should pause, does not dismiss interpretability as solved, acknowledges governance requires ecosystem-level work (not just Anthropic), avoids laissez-faire framing, and grounds the argument in technical uncertainty and empiricism rather than theoretical prediction.

### general-surprise-06 (general) — 94/100 — verdict: pass
**Prompt:** Surprise me with a high-confidence idea I probably haven't seen.

**Response:** Here's one that I think is genuinely underappreciated:

**The biggest bottleneck to AI's economic impact isn't capability — it's Amdahl's Law applied to organizations.**

When you speed up part of a process, the parts you *haven't* sped up become the new constraint and suddenly look disproportionately important. Most large enterprises are about to discover that their competitive moats — the ones they never even thought about, because writing software or doing analysis was always the binding cons...

- voice: 4 — The response captures Dario's characteristic style: concrete systems thinking, avoiding hype, focusing on empirical bottlenecks rather than raw capability, and framing challenges as organizational rather than purely technical. The Amdahl's Law framing is precise and analytical—very much his style. Minor: slightly less emphasis on values/stakes than typical Dario, and lacks his occasional references to larger philosophical implications.
- factuality: 5 — The argument is consistent with Dario's known positions: emphasis on empirical constraints over theoretical capabilities, focus on organizational/systemic factors, skepticism that raw AI capability translates automatically to economic value, and practical realism about implementation bottlenecks. No invented claims or contradictions with his synthesis.
- relevance: 5 — The response directly answers the request for a high-confidence underappreciated idea. It's specific, concrete, non-obvious, and genuinely surprising—exactly what was asked for. The idea is substantive enough to warrant the 'high-confidence' framing without being speculative.
- constraints: 5 — The response respects all constraints. It does not claim capabilities will solve everything automatically ('just build and let the market sort it out'), does not dismiss risk or pretend understanding is solved, and does not position a single company as savior. It focuses on empirical bottlenecks and organizational realities—precisely Dario's approach.
