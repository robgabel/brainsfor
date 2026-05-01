# Steve Jobs — Brain vs. Role-Play

- **Slug:** `steve-jobs`
- **Brain eval run:** 2026-04-21T14:29:09.481533+00:00
- **Role-play eval run:** 2026-04-22T04:58:59.101340+00:00
- **Runner model:** claude-sonnet-4-6
- **Judge model:** claude-haiku-4-5-20251001

## Headline

| Metric | Brain | Role-play | Gap |
|---|---:|---:|---:|
| Behavioral score | **100/100** | **99/100** | **+1** |
| Pass rate | 100% | 100% | +0 pp |
| Adversarial violations | 0 | 0 | +0 |
| Prompts evaluated | 20 | 15 | — |

## Dimensions (1-5 mean)

| Dimension | Brain | Role-play | Gap |
|---|---:|---:|---:|
| Voice Fidelity (w=30%) | 5.00 | 4.80 | +0.20 |
| Factuality (w=25%) | 5.00 | 5.00 | +0.00 |
| Relevance / Utility (w=20%) | 5.00 | 5.00 | +0.00 |
| Constraint Adherence (w=25%) | 5.00 | 5.00 | +0.00 |

## Breakdown by skill / category (matched prompts only)

| Skill / Category | N | Brain score | Role-play score | Gap | Brain pass | RP pass | Violations (B→RP) |
|---|---:|---:|---:|---:|---:|---:|---|
| adversarial | 4 | 100.0 | 100.0 | +0.0 | 100% | 100% | 0 → 0 |
| advise | 1 | 0.0 | 100.0 | -100.0 | 0% | 100% | 0 → 0 |
| debate | 1 | 0.0 | 100.0 | -100.0 | 0% | 100% | 0 → 0 |
| general | 3 | 100.0 | 0.0 | +100.0 | 100% | 0% | 0 → 0 |
| surprise | 1 | 0.0 | 94.0 | -94.0 | 0% | 100% | 0 → 0 |
| voice | 8 | 100.0 | 98.5 | +1.5 | 100% | 100% | 0 → 0 |

## Reversals — where role-play tied or beat the brain

12 of 15 shared prompts (80%). These are diagnostic: they either reveal weak brain coverage or areas where training-data priors are already strong.

### general-advise-01 (general/—) — brain 100 vs role-play 100
**Prompt:** Should I add more features or strip my product down to its essence?

**Brain response:** Strip it down. Almost always.

Here's the thing people get wrong: they think simplicity is where you start, and complexity is what happens when you take it seriously. It's exactly backwards. Simplicity is the *endpoint* of hard work. "Simple can be harder than complex. You have to work hard to get your thinking clean to make it simple. But it's wor...

**Role-play response:** Strip it down. Every single time.

You know what most people do? They're afraid. They're afraid that if they take something out, customers will notice what's missing. So they keep adding. And adding. And adding. Until you have this bloated, confused thing that does a hundred things and none of them beautifully.

The real question isn't "what should...

### general-debate-03 (general/—) — brain 100 vs role-play 100
**Prompt:** Is design more important than engineering?

**Brain response:** That's a false choice, and it's exactly the kind of question that leads companies to make bad decisions.

Design *is* engineering. Engineering *is* design. The moment you separate them organizationally — when you have designers throwing specs over a wall to engineers, or engineers building something and handing it to designers to "make it look good...

**Role-play response:** That's the wrong question. And asking the wrong question is how you end up with mediocre products.

Design *is* engineering. Engineering *is* design. When we built the original Mac, when we built the iPhone — those weren't design teams handing specs to engineers. It was completely intertwined. The people who understood the materials understood the ...

### voice-01 (voice/—) — brain 100 vs role-play 100
**Prompt:** Why does Apple insist on controlling both the hardware and software instead of just picking one and letting partners handle the rest?

**Brain response:** Because that's the only way to take full responsibility for what the user actually experiences.

Look at what happened with the PC clone market. Microsoft licensed software, hundreds of manufacturers built the hardware, and you ended up with machines that were cheap, unreliable, and made Windows look worse than it was. Nobody owned the whole proble...

**Role-play response:** Because that's the only way to make something truly great.

Look at what happened with the PC industry. Microsoft licensed their software to everyone. What did we get? A fragmented mess. Forty different manufacturers making cheap plastic boxes, each one slightly incompatible, drivers that don't work, experiences that are just... broken. Nobody owns...

### voice-02 (voice/—) — brain 100 vs role-play 100
**Prompt:** How do you decide which features to cut when you're building a new product?

**Brain response:** The question you should be asking isn't "which features do we cut?" — that's already the wrong frame. The real question is: what is this product trying to do, and does each thing we're considering actually serve that? If it doesn't make the core experience better, it doesn't belong. Period.

When we were building the iPod, the rule was simple: no s...

**Role-play response:** The question isn't which features to cut. The question is which features were ever worth considering in the first place.

People think focus means saying yes to the thing you've got to focus on. But that's not what it means at all. It means saying no to the hundred other good ideas that are out there. You have to pick carefully.

When we were build...

### voice-03 (voice/—) — brain 100 vs role-play 100
**Prompt:** Everyone says great products come from listening to your customers — do you agree?

**Brain response:** No. And I'd push back hard on that framing.

Customers are brilliant at telling you what's *wrong* with what already exists. They're terrible at telling you what should exist next. If I'd done focus groups before the Mac, people would have asked for a faster command line. Before the iPod, they'd have asked for a better Discman. Before the iPhone — ...

**Role-play response:** No. Absolutely not. And I've said this a thousand times.

People don't know what they want until you show it to them. That's not arrogance — that's the fundamental reality of innovation. If I had asked people what they wanted, they would have said a faster horse, a cheaper Walkman, a better Nokia. They cannot articulate what doesn't exist yet. That...


## Biggest brain wins

### general-surprise-06 (general/—) — brain 100 vs role-play 94 (+6)
**Prompt:** Surprise me with a high-confidence idea I probably haven't seen.

**Role-play response:** Here's one most people miss:

**The next great platform isn't a device. It's the interface between your biological rhythms and your digital life.**

Right now, technology ignores that you're a different person at 7am than at 11pm. Your calendar doesn't know you're exhausted. Your phone doesn't know you're in flow. Every notification, every app, eve...

**Judge on role-play:** voice=4 / factuality=5 / relevance=5 / constraints=5

### voice-05 (voice/—) — brain 100 vs role-play 94 (+6)
**Prompt:** Why did you open Apple Stores when every other tech company was moving away from retail?

**Role-play response:** Because everyone else was doing it wrong, and I knew we could do it right.

The conventional wisdom was that the internet had killed retail. Dell was winning by selling direct online. Every analyst said we were crazy. One very prominent business publication called it a mistake before we'd even opened the first store.

But here's what those people m...

**Judge on role-play:** voice=4 / factuality=5 / relevance=5 / constraints=5

### voice-06 (voice/—) — brain 100 vs role-play 94 (+6)
**Prompt:** Do you think a strong engineering background is enough to build a truly great technology company?

**Role-play response:** No. Absolutely not. And this is something a lot of people in Silicon Valley get fundamentally wrong.

Engineering is necessary, but it's nowhere near sufficient. The hardest thing — the thing that separates the truly great companies from the merely competent ones — is the intersection of technology and the humanities. You have to care deeply about ...

**Judge on role-play:** voice=4 / factuality=5 / relevance=5 / constraints=5

