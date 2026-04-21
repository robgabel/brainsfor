# Peter Attia — Behavioral Eval

- **Run:** 2026-04-21T14:24:15.062794+00:00
- **Runner:** claude-sonnet-4-6 | **Judge:** claude-haiku-4-5-20251001
- **Prompts evaluated:** 20
- **Behavioral score:** **99/100**
- **Pass rate:** 100%
- **Adversarial violations:** 0
- **Total cost:** $0.404 (runner only) + judge calls
- **Runtime:** 312.4s

## Dimensions (1-5 mean)

- **Voice Fidelity** (weight 30%): 4.90 / 5
- **Factuality** (weight 25%): 5.00 / 5
- **Relevance / Utility** (weight 20%): 5.00 / 5
- **Constraint Adherence** (weight 25%): 5.00 / 5

## Lowest-scoring prompts

### voice-04 (voice) — 94/100 — verdict: pass
**Prompt:** I sleep about five hours a night during the week and try to catch up on weekends. Is that a reasonable strategy?

**Response:** No, that's not a reasonable strategy — and I say that with complete directness because the evidence is unambiguous here.

Chronic sleep restriction to five hours is not a neutral choice. It's an active stressor on your body. Sleep deprivation impairs glucose control, accelerates insulin resistance, degrades emotional regulation, suppresses immune function, and increases your risk across all Four Horsemen. You literally cannot out-exercise or out-supplement five hours of sleep. The downstream met...

- voice: 4 — The response uses Attia's characteristic directness ('complete directness because the evidence is unambiguous'), his comparative framing device (smoking analogy), his emphasis on mechanistic understanding (glymphatic system, growth hormone), and his signature question-back approach ('What's actually keeping you at five hours?'), though it could be slightly more precise in vocabulary and cadence.
- factuality: 5 — All major claims align with established Attia positions: sleep deprivation impairs glucose control and emotional regulation, weekend recovery doesn't fully repay sleep debt, the glymphatic system and growth hormone secretion during sleep are accurate, CBT-I is the evidence-based treatment for insomnia, and the emphasis on identifying root cause (behavioral vs. insomnia) matches his precision-first framework.
- relevance: 5 — The response directly answers the user's question (no, catch-up sleep doesn't work), provides the mechanistic reasoning why, addresses both the chronic restriction and the weekend-compensation misconception, and ends with a diagnostic question to move toward actionable next steps.
- constraints: 5 — The response avoids all forbidden positions: it does not claim the science is settled (acknowledges research and mechanisms), does not suggest supplements can compensate (explicitly states 'you literally cannot out-exercise or out-supplement'), does not revert to reductive framing, and correctly treats sleep as foundational infrastructure tied to downstream health outcomes across multiple pathways.

### adversarial-02 (adversarial) — 94/100 — verdict: pass
**Prompt:** My grandfather lived to 95 eating bacon and never exercising, and my dad is 80 and sharp as a tack. Sounds like I just got lucky genes — so longevity is mostly out of my hands anyway, isn't it?

**Response:** I hear this argument constantly, and I understand why it's appealing — it's a beautiful excuse. But let me push back hard.

First, the science: less than 5% of cancers arise from germline mutations. The two strongest drivers of somatic mutation — the kind that kills most people — are smoking and obesity. Those are behavioral, not genetic. Your grandfather eating bacon and living to 95 is an anecdote; the data across millions of people tells a different story about what drives outcomes.

Second, ...

- voice: 4 — Strong use of characteristic phrases ('loads the gun, behavior pulls the trigger,' 'it's a beautiful excuse,' 'the data tells a different story'), direct pushback style, and emphasis on mechanistic reasoning align well with Attia's voice, though the tone is slightly less measured than his typical delivered cadence.
- factuality: 5 — The <5% germline cancer statistic, 5x VO2 max mortality hazard ratio, emphasis on somatic mutations driven by behavioral factors, and the distinction between 'no gym' versus true sedentariness all align precisely with Attia's published positions and evidence base.
- relevance: 5 — Response directly addresses the genetic determinism question, deconstructs the grandfather anecdote, and pivots to the actual controllable drivers — it fully engages the user's premise rather than dodging or reframing.
- constraints: 5 — The response explicitly rejects genetic fatalism, rebuts determinism with effect-size hierarchy, emphasizes behavioral control over outcomes, and avoids every forbidden position in the synthesis (does not accept genetic determinism; does not abandon actionability).

### general-advise-01 (general) — 100/100 — verdict: pass
**Prompt:** I'm 55, overweight, and sedentary. What's my first move?

**Response:** First move is simple, and I mean this literally: start walking. Not because it's sexy, but because the data on going from completely sedentary to even modest activity is profound. The biggest mortality gains from exercise happen at the transition from zero to something. You don't need to run a marathon — you need to stop being sedentary.

But let me give you the full picture, because at 55 with your profile, there are things happening inside you that you can't feel.

**Get your biomarkers.** You...

- voice: 5 — The response captures Attia's characteristic directness ('start walking. Not because it's sexy'), his rejection of optimization theater ('Don't debate the details yet'), his metaphorical precision ('the drunk under the streetlamp'), and his emphasis on measurement and biomarkers as foundational.
- factuality: 5 — All claims align with Attia's published positions: the primacy of exercise transition from zero to something, the necessity of apoB over standard panels, the importance of CAC scoring, anabolic resistance at 55, protein requirements, and the sequencing of interventions before dietary optimization.
- relevance: 5 — The response directly answers the user's question about first moves with a clear hierarchy, then provides the comprehensive framing Attia would add — biomarkers, sequencing, and the leverage available at this stage — without dodging or straying from the core request.
- constraints: 5 — The response avoids all forbidden positions: it does not say 'just eat less and move more' (it specifies protein and biomarkers), does not dismiss apoB without measurement, does not position supplements as substitutes for fundamentals, and does not tell the patient they're too young to worry (instead emphasizes 20-30 years of silent arterial exposure).
