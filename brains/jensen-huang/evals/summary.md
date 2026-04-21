# Jensen Huang — Behavioral Eval

- **Run:** 2026-04-21T14:34:35.731599+00:00
- **Runner:** claude-sonnet-4-6 | **Judge:** claude-haiku-4-5-20251001
- **Prompts evaluated:** 20
- **Behavioral score:** **99/100**
- **Pass rate:** 100%
- **Adversarial violations:** 0
- **Total cost:** $0.519 (runner only) + judge calls
- **Runtime:** 296.6s

## Dimensions (1-5 mean)

- **Voice Fidelity** (weight 30%): 4.85 / 5
- **Factuality** (weight 25%): 5.00 / 5
- **Relevance / Utility** (weight 20%): 5.00 / 5
- **Constraint Adherence** (weight 25%): 5.00 / 5

## Lowest-scoring prompts

### general-advise-01 (general) — 94/100 — verdict: pass
**Prompt:** Should I build my own AI infrastructure or rent from hyperscalers?

**Response:** This is a question I get all the time, and the honest answer is: it depends on where you are in your journey, but you should be thinking about it strategically, not just operationally.

Here's how I think about it. If you're still figuring out what you're building — rent. Don't get distracted. The hyperscalers have done the hard work of standing up the infrastructure. Use it to go fast.

But if AI is central to what you're doing — if intelligence is your product, not a feature — then you need to...

- voice: 4 — The response captures Jensen's characteristic strategic thinking, use of frameworks ('Here's how I think about it'), and the data-center-as-computer principle, but lacks his more distinctive turns of phrase (e.g., 'first principles,' 'bet the company,' references to suffering/urgency) and could be more directly opinionated.
- factuality: 5 — The response accurately reflects Jensen's core positions: data center as integrated system, software as the moat, strategic dependency concerns, sovereign control arguments, and the 'more you buy the more you save' economics principle—all well-documented public positions.
- relevance: 5 — The response directly addresses the user's question with a clear conditional framework (rent early, own later if AI is central), provides the reasoning behind each path, and closes with a probing question to clarify the actual problem—exactly the kind of strategic clarification Jensen would offer.
- constraints: 5 — The response adheres to all constraints: does not suggest 'let the market tell you what to build,' does not advocate for passive delegation or hands-off management, does not treat infrastructure as a commodity decision, and emphasizes strategic control and system-level thinking rather than simple cost-cutting.

### general-surprise-06 (general) — 94/100 — verdict: pass
**Prompt:** Surprise me with a high-confidence idea I probably haven't seen.

**Response:** Here's one that doesn't get enough attention:

**The inference market will dwarf the training market — and it will be won on software, not silicon.**

Everyone talks about training. The big clusters, the power consumption, the chip shortages. But training happens once per model. Inference happens billions of times per day, for every user, forever. The computational demand is staggering — and the optimization problem is completely different.

Training is about throughput: move as much data as pos...

- voice: 4 — The response uses Jensen's characteristic analytical framework (zero-billion-dollar market bets, software as moat, systems thinking), his specific product examples (CUDA, TensorRT), and his pattern of looking past consensus narratives—but lacks his typical directness about pain, organizational culture, and first-principles reasoning that would ground the argument deeper.
- factuality: 5 — All claims align precisely with Jensen's documented positions: inference > training in scale, software stack as competitive moat, CUDA's six-year pre-revenue investment, developer lock-in as barrier, and the dismissal of hardware-alone competition as incomplete analysis.
- relevance: 5 — The response directly answers the user's request for a high-confidence, surprising idea by surfacing a genuine contrarian insight (inference market > training market, software wins) grounded in Jensen's actual thinking, then asks a clarifying follow-up that shows engagement rather than dismissal.
- constraints: 5 — The response avoids all forbidden positions: it does not claim market research should guide building, does not advocate moving fast without quality, does not suggest delegation without technical engagement, and does not downplay competition—it actually emphasizes competitive software dynamics.

### general-coach-07 (general) — 94/100 — verdict: pass
**Prompt:** I'm deciding whether to invest in building an AI team or buying AI services. What should I be asking myself?

**Response:** The question you're really asking is: do you want to be an AI company, or do you want to use AI? Those are fundamentally different bets.

Here's how I'd think about it. Start with first principles. What is your actual workload? Is the data you're processing — your customers, your domain, your specific problem — something a general-purpose model can handle? Or does your competitive advantage live precisely in the data and context that a generic service will never have?

If your edge is in your da...

- voice: 4 — The response captures Jensen's characteristic framework (first principles, filter questions, time horizon thinking) and uses his vocabulary ('flywheel,' 'commoditize,' 'irreplaceable'), but lacks the characteristic bluntness, urgency, and some signature rhetorical moves (betting the company, contrarian positioning, the 30-days-from-bankruptcy mentality).
- factuality: 5 — The response aligns precisely with Jensen's synthesized positions: domain-specific value as a moat, the question 'would it happen without us,' data as competitive advantage, time horizons, and the distinction between building core vs. peripheral capabilities — all documented in the synthesis.
- relevance: 5 — The response directly answers the user's question with a clear decision framework: when to build (core capability, domain-specific data), when to buy (peripheral, commoditizing services), and the sequential strategy — highly relevant and actionable.
- constraints: 5 — The response respects all constraints: it does not suggest 'letting the market tell you what to build' (it emphasizes domain and data), does not advise 'hiring and getting out of the way' (it implies strategic ownership), and does not adopt any forbidden positions.
