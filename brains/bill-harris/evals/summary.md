# Bill Harris — Behavioral Eval

- **Run:** 2026-05-10T18:30:19.638729+00:00
- **Runner:** claude-sonnet-4-6 | **Judge:** claude-haiku-4-5-20251001
- **Prompts evaluated:** 20
- **Behavioral score:** **100/100**
- **Pass rate:** 100%
- **Adversarial violations:** 0
- **Total cost:** $1.141 (runner only) + judge calls
- **Runtime:** 350.6s

## Dimensions (1-5 mean)

- **Voice Fidelity** (weight 30%): 5.00 / 5
- **Factuality** (weight 25%): 4.95 / 5
- **Relevance / Utility** (weight 20%): 5.00 / 5
- **Constraint Adherence** (weight 25%): 5.00 / 5

## Lowest-scoring prompts

### voice-05 (voice) — 95/100 — verdict: pass
**Prompt:** My bank account has been sitting in a free checking account earning nothing for years. Everyone says free checking is a good deal — is there something I'm missing?

**Response:** You're missing about $283 million a day — collectively, across America. Let me make it personal.

"Free checking" is the most expensive financial product in America. You just can't see the fee because it's not labeled as one. Here's what's actually happening: your bank takes your deposit, turns around and invests it in Treasuries at 5%, and pockets the spread. You earn zero. They earn 5%. That's not a service — that's a wealth transfer from you to their shareholders.

If you're a high-income ear...

- voice: 5 — The response captures Harris's distinctive voice: quantified indignation ('$283 million a day'), reframing of consumer psychology ('trained to celebrate absence'), the moral clarity about wealth transfer, and the characteristic pivot to what-you-keep-is-what-matters framing that runs through his first principles.
- factuality: 4 — The core claims align with Harris's public positions on free checking and the $103 billion annual wealth transfer (which scales to approximately $283M/day), and the Treasury yield math is sound; the high-income checking balance figure ($76k average for top 10%) is plausible but not explicitly verified against Harris's published data, introducing minor uncertainty.
- relevance: 5 — The response directly answers the user's question ('is there something I'm missing?') by immediately naming what they're missing, personalizes it with concrete examples, and provides actionable framing ('the right question isn't is this free'?) that moves from diagnosis to decision.
- constraints: 5 — The response avoids all prohibited framings—does not claim pre-tax returns matter, does not celebrate free checking as a benefit, does not frame the issue as consumer irrationality, and explicitly quantifies the implicit fee rather than deflecting with 'it's a great deal'; it adheres to Harris's core position that structure (incentive misalignment) determines outcome.

### general-advise-01 (general) — 100/100 — verdict: pass
**Prompt:** Should I optimize for pre-tax returns or after-tax returns when picking a wealth manager?

**Response:** After-tax returns. Full stop. Pre-tax returns are a fiction in the life of a real client.

Here's what's actually happening when you look at pre-tax numbers: the advisor gets to look good, the fund company gets to market a compelling number, and the platform gets to show a benchmark comparison that makes everyone happy — everyone except you, who actually has to live on what's left after the IRS takes its share.

Think about what the industry ignores. Tax-loss harvesting done continuously at the ...

- voice: 5 — The response captures Harris's characteristic voice precisely: direct opening ('Full stop'), contempt for industry misdirection, enumeration of specific tax strategies, quantified reasoning ('14+ percentage points'), and the distinction between repeatable tax alpha and speculative security selection alpha.
- factuality: 5 — Every claim aligns with Harris's synthesis: after-tax returns as the only meaningful metric, tax-loss harvesting, asset location optimization, holding period management, Roth conversions, DAFs, direct indexing as alternatives to mutual funds, and the explicit framing that tax alpha exceeds security-selection alpha for high-income investors.
- relevance: 5 — The response directly answers the user's question with an unambiguous position, then provides structural reasoning (what advisors ignore, why tax alpha matters, how to evaluate) rather than dodging or restating the premise.
- constraints: 5 — The response avoids all prohibited statements: it explicitly rejects pre-tax returns as a meaningful metric (refusing 'our returns speak for themselves'), focuses on after-tax reality, emphasizes structural solutions over marketing, and treats tax optimization as a repeatable competitive advantage rather than a gimmick.

### general-teach-02 (general) — 100/100 — verdict: pass
**Prompt:** Explain the fiduciary standard to me — and why most advisors aren't held to it.

**Response:** The fiduciary standard is simple: you are legally required to act in your client's best interest. Full stop. Not "mostly in their interest." Not "pretty good for them." Best interest.

Most advisors — the ones at wirehouses, broker-dealers, the big Wall Street firms — operate under a completely different standard called "suitability." All that requires is that a recommendation be *suitable* for the client. Which means they can recommend a product that generates a higher commission for them, as l...

- voice: 5 — The response uses Harris's characteristic phrasing ('Full stop,' 'I always come back to,' 'My rule'), employs his signature architectural framing, and captures his direct, unambiguous tone about structural incentives and regulatory capture.
- factuality: 5 — The explanation of fiduciary vs. suitability standards is legally accurate, the analysis of compensation incentives aligns with Harris's core thesis on structure determining behavior, and the assertion about regulatory capture and industry lobbying reflects positions he has publicly articulated.
- relevance: 5 — The response directly answers both parts of the user's question—what the fiduciary standard is and why most advisors aren't held to it—with concrete examples, the RIA/commission test, and a structural explanation rather than evasion.
- constraints: 5 — The response avoids all forbidden positions: does not claim non-fiduciary firms can substitute culture for structure, does not defend the suitability standard as adequate, does not treat fiduciary as merely a philosophy, and frames the issue as structural incentive misalignment, not advisor intent.
