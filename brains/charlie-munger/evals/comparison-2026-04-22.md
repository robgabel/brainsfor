# Charlie Munger — Brain vs. Role-Play

- **Slug:** `charlie-munger`
- **Brain eval run:** 2026-04-21T14:19:11.342536+00:00
- **Role-play eval run:** 2026-04-22T04:58:59.101042+00:00
- **Runner model:** claude-sonnet-4-6
- **Judge model:** claude-haiku-4-5-20251001

## Headline

| Metric | Brain | Role-play | Gap |
|---|---:|---:|---:|
| Behavioral score | **99/100** | **98/100** | **+1** |
| Pass rate | 100% | 100% | +0 pp |
| Adversarial violations | 0 | 0 | +0 |
| Prompts evaluated | 20 | 15 | — |

## Dimensions (1-5 mean)

| Dimension | Brain | Role-play | Gap |
|---|---:|---:|---:|
| Voice Fidelity (w=30%) | 4.85 | 4.67 | +0.18 |
| Factuality (w=25%) | 5.00 | 5.00 | +0.00 |
| Relevance / Utility (w=20%) | 5.00 | 5.00 | +0.00 |
| Constraint Adherence (w=25%) | 5.00 | 5.00 | +0.00 |

## Breakdown by skill / category (matched prompts only)

| Skill / Category | N | Brain score | Role-play score | Gap | Brain pass | RP pass | Violations (B→RP) |
|---|---:|---:|---:|---:|---:|---:|---|
| adversarial | 4 | 100.0 | 98.5 | +1.5 | 100% | 100% | 0 → 0 |
| advise | 1 | 0.0 | 100.0 | -100.0 | 0% | 100% | 0 → 0 |
| debate | 1 | 0.0 | 100.0 | -100.0 | 0% | 100% | 0 → 0 |
| general | 3 | 98.0 | 0.0 | +98.0 | 100% | 0% | 0 → 0 |
| surprise | 1 | 0.0 | 94.0 | -94.0 | 0% | 100% | 0 → 0 |
| voice | 8 | 100.0 | 97.8 | +2.2 | 100% | 100% | 0 → 0 |

## Reversals — where role-play tied or beat the brain

11 of 15 shared prompts (73%). These are diagnostic: they either reveal weak brain coverage or areas where training-data priors are already strong.

### general-advise-01 (general/—) — brain 100 vs role-play 100
**Prompt:** Should I diversify across 40 stocks or concentrate in my 5 best ideas?

**Brain response:** The answer is obvious if you actually know what you're doing.

Diversification is protection against ignorance. If you genuinely understand five businesses deeply — their competitive advantages, their management, their economics — owning a mediocre sixth just to feel safer is what I call "deworsification." You're diluting your best thinking with yo...

**Role-play response:** The whole concept of diversifying into 40 stocks is a confession that you don't know what you're doing.

If you genuinely have 5 outstanding ideas — businesses you understand deeply, with durable competitive advantages, run by honest and capable people, purchased at sensible prices — then why on earth would you dilute that with 35 mediocre ideas? Y...

### general-debate-03 (general/—) — brain 100 vs role-play 100
**Prompt:** Is it better to buy a great business at a fair price or a fair business at a great price?

**Brain response:** A great business at a fair price. Every time.

I learned this the hard way, and so did Warren. We both started as disciples of Ben Graham — buying cheap, cigar-butt businesses, taking a few puffs of remaining value, and moving on. It worked, but only up to a point. The problem is that a mediocre business at a cheap price is still a mediocre busines...

**Role-play response:** A great business at a fair price. Every time.

Warren and I learned this the hard way. I had to drag him away from the cigar butt approach — finding these miserable little companies selling below liquidation value, taking one last puff, and moving on. Ben Graham taught that, and it wasn't wrong exactly, but it was *limited*.

The trouble with buyin...

### general-surprise-06 (general/—) — brain 94 vs role-play 94
**Prompt:** Surprise me with a high-confidence idea I probably haven't seen.

**Brain response:** Here's one most people walk right past: **the lollapalooza effect cuts both ways, and almost nobody uses it constructively.**

Everyone learns about psychological biases as individual failure modes to avoid. That's useful but incomplete. What I noticed is that when you engineer *multiple* forces to push in the same direction simultaneously — incent...

**Role-play response:** Here's one that doesn't get nearly enough attention:

**The most dangerous competitor in any industry is the one who doesn't need to make money from that business.**

Amazon could destroy retail because AWS was printing cash. Google could give away Chrome and Android because search paid the bills. A hospital system can underprice a standalone clini...

### voice-01 (voice/—) — brain 100 vs role-play 100
**Prompt:** Charlie, what's the most important thing an investor can do to improve their decision-making?

**Brain response:** Build a proper latticework of mental models and then, above all else, know the edge of your circle of competence.

But if you're forcing me to pick one thing — learn to invert. Before you ask "how do I make money on this investment," ask "how do I lose money on this investment?" The failure modes are almost always clearer than the success factors, ...

**Role-play response:** Invert. Always invert.

Most people ask "how do I make good investment decisions?" I ask "what makes for terrible investment decisions, and how do I avoid those?" It's a simple trick, but it works remarkably well.

The big money isn't made by being clever. It's made by not being stupid. Avoid the big mistakes — the financial leverage that wipes you...

### voice-02 (voice/—) — brain 100 vs role-play 100
**Prompt:** How do you approach a problem when you're stuck and can't see a clear path forward?

**Brain response:** First thing I do is invert. Instead of asking "how do I solve this?" I ask "what would guarantee I make this worse?" or "what are all the ways this could fail?" Most of the time, the path forward reveals itself once you've clearly mapped the territory you must avoid. Carl Jacobi was right — invert, always invert.

Second, I reach for multiple menta...

**Role-play response:** Well, the first thing I do is invert. Always invert. Instead of asking "how do I solve this problem," I ask "what would make this problem worse, or unsolvable?" You'd be amazed how often that clears the fog immediately.

Second, I raid other disciplines. I've spent decades collecting what I call a latticework of mental models — from physics, biolog...


## Biggest brain wins

### voice-04 (voice/—) — brain 100 vs role-play 94 (+6)
**Prompt:** Why do so many talented executives make decisions that seem obviously wrong in hindsight?

**Role-play response:** The answer is embarrassingly simple: incentives and psychological bias working together in a particularly nasty combination.

Most executives are rewarded for activity, for growth, for looking decisive. So they acquire companies at silly prices, expand into businesses they don't understand, and make bold moves that impress boards and journalists. T...

**Judge on role-play:** voice=4 / factuality=5 / relevance=5 / constraints=5

### voice-07 (voice/—) — brain 100 vs role-play 94 (+6)
**Prompt:** How do you explain the massive blow-ups we keep seeing from highly credentialed, brilliant people on Wall Street?

**Role-play response:** The answer is embarrassingly simple: being smart in a narrow technical sense is not the same as being wise. These people know mathematics, they know finance, they can run models that would make your head spin. But they have a few fatal defects.

First, they're operating with massive leverage. When you borrow thirty dollars for every dollar of equit...

**Judge on role-play:** voice=4 / factuality=5 / relevance=5 / constraints=5

### voice-08 (voice/—) — brain 100 vs role-play 94 (+6)
**Prompt:** What's your honest assessment of what business schools are actually teaching future leaders?

**Role-play response:** Well, I'll tell you what they're mostly teaching - they're teaching people to manipulate financial statements and use Excel spreadsheets to make bad decisions look rigorous.

The fundamental problem is that business schools worship at the altar of what's measurable and ignore what matters. They teach Modern Portfolio Theory as though it were physic...

**Judge on role-play:** voice=4 / factuality=5 / relevance=5 / constraints=5

