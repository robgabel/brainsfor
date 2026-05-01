# Paul Graham — Brain vs. Role-Play

- **Slug:** `paul-graham`
- **Brain eval run:** 2026-04-21T14:24:11.668996+00:00
- **Role-play eval run:** 2026-04-22T04:58:59.101295+00:00
- **Runner model:** claude-sonnet-4-6
- **Judge model:** claude-haiku-4-5-20251001

## Headline

| Metric | Brain | Role-play | Gap |
|---|---:|---:|---:|
| Behavioral score | **98/100** | **98/100** | **+0** |
| Pass rate | 100% | 100% | +0 pp |
| Adversarial violations | 0 | 0 | +0 |
| Prompts evaluated | 20 | 15 | — |

## Dimensions (1-5 mean)

| Dimension | Brain | Role-play | Gap |
|---|---:|---:|---:|
| Voice Fidelity (w=30%) | 4.65 | 4.73 | -0.08 |
| Factuality (w=25%) | 5.00 | 5.00 | +0.00 |
| Relevance / Utility (w=20%) | 4.95 | 5.00 | -0.05 |
| Constraint Adherence (w=25%) | 5.00 | 5.00 | +0.00 |

## Breakdown by skill / category (matched prompts only)

| Skill / Category | N | Brain score | Role-play score | Gap | Brain pass | RP pass | Violations (B→RP) |
|---|---:|---:|---:|---:|---:|---:|---|
| adversarial | 4 | 98.5 | 98.5 | +0.0 | 100% | 100% | 0 → 0 |
| advise | 1 | 0.0 | 100.0 | -100.0 | 0% | 100% | 0 → 0 |
| debate | 1 | 0.0 | 100.0 | -100.0 | 0% | 100% | 0 → 0 |
| general | 3 | 98.0 | 0.0 | +98.0 | 100% | 0% | 0 → 0 |
| surprise | 1 | 0.0 | 100.0 | -100.0 | 0% | 100% | 0 → 0 |
| voice | 8 | 98.5 | 97.8 | +0.7 | 100% | 100% | 0 → 0 |

## Reversals — where role-play tied or beat the brain

14 of 15 shared prompts (93%). These are diagnostic: they either reveal weak brain coverage or areas where training-data priors are already strong.

### general-surprise-06 (general/—) — brain 94 vs role-play 100
**Prompt:** Surprise me with a high-confidence idea I probably haven't seen.

**Brain response:** Here's one that hits me: **the most dangerous competition you'll ever face is from companies that don't yet exist.**

Everyone worries about incumbents. But incumbents are actually the least threatening competitors, because they're structurally incapable of attacking you correctly — they'd have to cannibalize their existing business to do it. The r...

**Role-play response:** Here's one: **The most dangerous career mistake smart people make is optimizing for impressiveness rather than interestingness.**

Impressiveness is legible to others. Interestingness is only legible to you. So ambitious people systematically drift toward impressive work — work that wins awards, gets written up, sounds good at dinner parties — and ...

### general-advise-01 (general/—) — brain 100 vs role-play 100
**Prompt:** Should I drop out of college to work on my startup?

**Brain response:** The short answer is: probably not yet, and almost certainly not for the reasons you think.

The question isn't really "should I drop out" — it's "am I in a situation where the opportunity cost of college exceeds its value?" That's a much harder question.

Here's what I actually believe: at 20, you should be doing breadth-first search. College is on...

**Role-play response:** The question isn't really "should I drop out?" The question is "do I have something worth dropping out for?"

Most people asking this question don't yet. If you're asking it abstractly, as a career move or because you admire famous dropouts, that's a bad sign. The founders who drop out and succeed aren't making a lifestyle choice — they drop out be...

### general-debate-03 (general/—) — brain 100 vs role-play 100
**Prompt:** Is it better to build something a lot of people kind of want, or something a few people really want?

**Brain response:** The answer is clear, and most people get it backwards: a small number of people who desperately want what you've built is infinitely more valuable than a large number who mildly appreciate it.

I've put it as: it's better to have a hundred people who love you than a million who sort of like you.

Here's why this matters in practice. The hundred who...

**Role-play response:** Something a few people really want. This is one of those things that sounds obvious when you say it but that most founders get backwards in practice.

The reason is that "a lot of people kind of want" something is often a signal that you've sanded off all the interesting edges trying to appeal to everyone. You've built something inoffensive and for...

### voice-01 (voice/—) — brain 100 vs role-play 100
**Prompt:** What's the single most important thing a first-time founder should focus on in the first six months?

**Brain response:** Talk to users and make something they actually want. Everything else is secondary.

I've seen so many first-time founders spend their first six months optimizing the wrong things — the pitch deck, the office setup, the hiring plan, the brand. None of that matters if you haven't figured out whether you're building something people genuinely need.

T...

**Role-play response:** Talk to users. That's it.

Everything else — the architecture decisions, the office space, the business cards, the pitch deck — is a form of procrastination unless you're doing it in direct service of learning what users actually want.

The brutal truth is that most first-time founders have a theory about what people want, and that theory is wrong ...

### voice-02 (voice/—) — brain 100 vs role-play 100
**Prompt:** How should I come up with a good startup idea? I've been sitting in coffee shops trying to brainstorm and nothing feels right.

**Brain response:** The problem is you're approaching it backwards. The verb you want is *notice*, not *think up*. 

Stop trying to brainstorm startup ideas. When you make a conscious effort to generate ideas that way, the ones you come up with will be bad in a particularly dangerous way — bad but plausible-sounding. They'll fool you.

The right approach is to become ...

**Role-play response:** The problem is right there in what you said: you're *trying* to brainstorm. That's almost exactly backwards.

The best startup ideas don't come from sitting down to think of startup ideas. They come from noticing problems in your own life — things that seem broken, workarounds you've built for yourself, moments where you think "why doesn't this exi...


## Biggest brain wins

### voice-05 (voice/—) — brain 100 vs role-play 94 (+6)
**Prompt:** I'm a self-taught programmer applying for jobs and interviewers keep dismissing me because I don't have a CS degree. Should I just go back to school?

**Role-play response:** The degree question is mostly a filter problem, not a knowledge problem. And filters are beatable.

The reason interviewers dismiss you isn't really about the degree — it's that they're using the degree as a proxy for ability because they're lazy or risk-averse. Your job is to make that proxy irrelevant by presenting undeniable evidence of what you...

**Judge on role-play:** voice=4 / factuality=5 / relevance=5 / constraints=5

