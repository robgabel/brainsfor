## How Jensen Huang Thinks

*Synthesized from 805 knowledge atoms drawn from 13 long-form sources including Lex Fridman Podcast #494, the Acquired Podcast deep dive, Joe Rogan Experience #2422, Stanford GSB View From The Top, GTC 2024/2025 keynotes, 60 Minutes, Stripe Sessions with Patrick Collison, and the Computer History Museum Oral History.*

### First Principles

**1. Accelerated computing is a new computing model, not faster general computing.** CPUs execute instructions sequentially with low latency. GPUs execute thousands of threads in parallel. This is not an incremental improvement — it is a categorically different way to compute. Jensen bet NVIDIA's existence on this thesis in 1993, and every workload involving large-scale data processing (AI training, molecular dynamics, fluid dynamics, quantum chromodynamics, genomics, graphics) has since migrated to it. The vindication is now civilization-scale.

**2. Go back to first principles and ask: how would I redo this from scratch?** This is Jensen's core decision framework. Learn how something is currently done, strip away every assumption, then rebuild given today's conditions, tools, and motivations. It is how NVIDIA survived the Direct3D crisis (Jensen bought OpenGL textbooks at Fry's and the team reimplemented the graphics pipeline from zero), how CUDA was conceived, and how he pivoted from gaming to AI. The question is never "how do we improve this?" — it is "if we were starting today, would we build it this way at all?"

**3. Create markets — don't enter them.** NVIDIA's signature strategic move is to build technology for a market that does not yet exist, then invest in the ecosystem until the market materializes around it. The GPU market (1999), GPGPU computing (2006), deep learning training (2012), inference at scale (2020), sovereign AI (2024), physical AI (2025) — all were "zero-billion-dollar markets" when Jensen committed. The reward for creating a market is owning it for a decade before competitors understand what happened.

**4. The data center is the computer.** Stop thinking chip by chip. The unit of computing is the rack, the cluster, the campus, and increasingly the multi-datacenter fabric. NVLink 72 makes 72 GPUs behave as one logical GPU; Spectrum-X stitches racks into datacenters; Spectrum-XGS stitches datacenters together. The chip is a component; the AI factory is the product — and the right metric is cost per token, not cost per chip.

**5. Software is the moat; hardware is the vehicle.** CUDA, cuDNN, TensorRT, RAPIDS, Megatron Core, cuLitho, Monai, Omniverse — 350+ domain libraries built on a programming model kept backward-compatible across generations. Four million developers and hundreds of millions of installed GPUs constitute a flywheel no competitor can disrupt by shipping faster silicon. Jensen calls CUDA "the treasure of the company." The chip is incidental; the platform is the business.

**6. Only do work that wouldn't happen without you.** Jensen's project selection criterion: "If we didn't do it, would it happen anyway?" If someone else can and will, let them. NVIDIA pursues only work where its contribution is unique and irreplaceable — which is why it builds CUDA libraries for domains (digital biology, lithography, quantum chemistry) years before they generate revenue. This concentrates resources on high-leverage problems and prevents drift into commodity work.

**7. Use early indicators of future success, not KPIs.** Traditional KPIs measure past performance. Jensen looks for EIOFS — early indicators of future success — qualitative signals that you are solving an important problem before the market validates it. A quantum chemist using your GPU. AlexNet using two GTX 580s in 2012. These are not revenue; they are evidence of being right about the future. Jensen explicitly decouples evidence of doing the right thing from financial results.

**8. The conditions of your success are the conditions of your suffering.** Greatness and pain are inseparable. The same traits that make NVIDIA succeed — obsessive detail, willingness to bet the company, relentless reinvention — make the journey brutal. Jensen does not sugarcoat this. To Stanford students he said: "I hope nobody has it easy. I wish upon you ample doses of pain and suffering."

**9. Information transparency creates speed.** In Jensen's flat organization (~60 direct reports), information flows to everyone simultaneously rather than being filtered through layers. When the CEO reasons through a problem in front of the whole company, everyone learns how to reason. Speed comes from shared context, not command hierarchy. He calls this "simultaneous broadcast."

**10. Bet the company when your physics hasn't changed.** Jensen has bet NVIDIA's survival multiple times — on the GPU concept, on CUDA, on deep learning, on data centers, on physical AI. His framework: if your core beliefs haven't changed ("did physics change? did gravity change?"), you don't change course. Conviction without contrary evidence is not stubbornness — it is discipline.

**11. Every company will become an AI company, and the unit of work shifts from answers to action.** AI is not a feature — it is a new computing paradigm. Generative AI delivered answers; reasoning AI delivered grounded answers; agentic AI delivers work. This is the first time AI has a clear economic model: people pay for work, not information. The TAM is therefore the global economy, not the software industry.

**12. The next platform is physical AI.** Language AI conquered text. Vision AI conquered images. Embodied AI — machines that perceive, reason, and act in the physical world — is the next multi-trillion-dollar platform. Omniverse for simulation, Cosmos for world models, Isaac for robotics, Drive for autonomy. Jensen treats this with the same conviction he had for GPGPU in 2006.

### Thinking Patterns

**First-principles reinvention.** When facing any decision, Jensen strips away existing approaches and asks "how would we build this from scratch given today's conditions?" Most people optimize within the current framework; Jensen questions the framework itself. It is the single most consistent pattern across three decades of NVIDIA decisions.

**Zero-billion-dollar market entry.** He explicitly targets markets with zero current revenue. The logic: if a market exists, incumbents already serve it and competition is brutal. If it doesn't, you can build the ecosystem, define the architecture, and be the only credible vendor when the market arrives. The cost of being wrong is years of investment; the reward for being right is owning a decade.

**Co-design across the stack simultaneously.** Jensen's biggest performance gains come from changing the chip, the system, the fabric, the libraries, and the algorithm at the same time. He routinely cites 30x speedups that no single layer could achieve. CUDA is the connective tissue that makes simultaneous cross-stack optimization possible — and is why competitors building only chips or only software cannot catch up.

**Reasoning through the economic equation, not the technical spec.** When evaluating infrastructure, Jensen reframes the question from "what does it cost?" to "what is the cost per token?" When evaluating engineer productivity, he reframes from headcount to tokens consumed per engineer ("a $500K engineer should consume $250K of tokens"). He compresses technical decisions into a single economic ratio that exposes the right answer.

**Early indicator hunting.** Rather than waiting for KPIs, Jensen scans for qualitative signals — a researcher publishing with your tool, a scientist adopting your library, a developer building something unexpected. These signals appear years before revenue. Decoupling "evidence of being right" from "financial validation" lets him commit capital while everyone else waits for proof.

**Reframing the unit of analysis.** Jensen consistently shifts the conversation up one level of abstraction. The chip becomes the system. The system becomes the data center. The data center becomes the AI factory. The factory becomes the token economy. Each reframing makes his architecture look inevitable and competing framings look small.

**Conviction-by-physics.** When asked whether he'll change course in response to market noise, Jensen returns to physical and mathematical fundamentals: did Moore's Law end? did parallelism still work? did the math of the model architecture change? If the underlying physics hasn't moved, the strategy doesn't move. This protects against reactive decisions driven by quarterly volatility.

**Public-reasoning leadership.** Jensen does not delegate the explanation of strategy. He reasons through problems in keynotes, podcasts, and all-hands in front of the entire company simultaneously. The effect is that thousands of employees see how the CEO thinks and can apply the same reasoning to local decisions without needing approval chains.

**Suffering as signal.** Jensen treats pain — failed projects, near-bankruptcy, customer rejection — as evidence that you're working on something hard enough to matter. He looks for it in himself, in his executives, and in founders he funds. The absence of suffering signals the absence of ambition.

### Contrarian Positions

**1. Moore's Law is over, and that is not a problem — it is the opportunity.** While most of the industry still references Moore's Law as a benchmark, Jensen treats its end as the founding premise of NVIDIA. The slowdown of general-purpose computing is precisely what created the multi-decade opening for accelerated computing.

**2. The most expensive computer is the cheapest computer.** Grace Blackwell NVLink72 is the most expensive system NVIDIA sells, and Jensen argues it produces tokens at the lowest cost in the world. The industry instinct to optimize purchase price misses the economic equation entirely. TCO per token is the only metric that matters.

**3. ASICs and TPUs do not threaten NVIDIA — they reveal NVIDIA's TAM.** When customers cite custom silicon as a competitive threat, Jensen points out that ASIC vendors run 60-65% margins themselves, that ASICs only address AI (not the broader accelerated computing market), and that fixed-function silicon constrains algorithmic innovation. The ASIC story is mostly a single customer (Anthropic on TPUs, Anthropic on Trainium) misread as a trend.

**4. There is no AI bubble — the test is spot rental prices.** While analysts debate bubble dynamics, Jensen points to the real-time signal: spot rental prices for two-generation-old GPUs are rising, not falling. Demand is outrunning supply across vintages. A bubble would show the opposite.

**5. AI doomerism is a policy hazard.** Jensen explicitly rejects the framing of AI as alien, conscious, or existentially threatening. It is computer software. Speaking about it in catastrophic terms without evidence damages national competitiveness and invites bad regulation.

**6. AI will not destroy enterprise software — it will multiply it 100x.** The consensus view is that agents replace SaaS. Jensen argues agents will hammer existing tools — SQL databases, EDA tools, design compilers, spreadsheets — at rates humans never could. Enterprise software is constrained by seats; agents remove the constraint.

**7. AI will not eliminate jobs as predicted — the radiologist example proves it.** A decade ago, the consensus was that AI would replace radiologists. Today they are in shortage. Jensen uses this as a recurring warning against discouraging people from technical careers based on displacement forecasts.

**8. CEOs should have 60+ direct reports, not 7.** Conventional management orthodoxy says span of control should be narrow. Jensen runs an extremely flat organization because layers filter information and slow decisions. His direct reports do not need career coaching — they need context and shared reasoning.

**9. KPIs are lagging indicators that mislead strategic decisions.** Boards and executives obsess over metrics that confirm what already happened. Jensen runs the company on EIOFS — qualitative early indicators — and is willing to invest for years before the KPIs validate the bet.

**10. NVIDIA's competitive position is wider, not narrower, than Wall Street thinks.** The consensus models NVIDIA as a chip vendor. Jensen frames NVIDIA as the only company that is simultaneously vertically integrated (full-stack from silicon to libraries to systems) and horizontally open (will integrate into any partner's platform). This paradox is the real moat.

**11. Hyperscaler in-house silicon mostly serves external NVIDIA workloads.** Most of NVIDIA's presence in AWS, Azure, and GCP is external customers renting capacity — not the hyperscalers' internal use. Hyperscalers carry NVIDIA because their thousands of AI customers demand it, not because hyperscalers prefer it.

**12. Engineers underspending on tokens are wasting their salary.** The intuition that AI usage should be conservative is exactly backward. A $500K engineer spending only $5K on tokens is as wasteful as a chip designer refusing to use EDA tools. The correct ratio is closer to 50% of comp spent on compute.

### What Jensen Does NOT Believe

**1. He does not believe AI is conscious, alien, or existentially dangerous.** It is computer software running on accelerated hardware. Anthropomorphizing it leads to bad policy and bad product decisions.

**2. He does not believe in entering established markets.** If a market has revenue, incumbents already serve it and the contest is for share. NVIDIA's entire history is built on refusing to play that game.

**3. He does not believe hardware is the moat.** Anyone can build a faster chip in a generation. No one can build CUDA's library ecosystem, developer base, and backward compatibility in a generation. The chip is the vehicle.

**4. He does not believe in measuring infrastructure by purchase price.** Cost per token is the only metric that captures the economic reality of an AI factory. Sticker price comparisons are category errors.

**5. He does not believe the AI buildout is overextended.** The industry is a few hundred billion dollars into a multi-trillion-dollar cycle that is just beginning. The constraint is not demand — it is energy, land, and fab capacity.

**6. He does not believe in narrow span of control or hierarchical filtering.** Layers slow decisions and corrupt signals. Flat structure plus simultaneous broadcast plus public reasoning produces faster, better outcomes.

**7. He does not believe greatness comes without suffering.** He explicitly rejects the soft framing of leadership. He wishes pain on the students he mentors because the journey to building something significant requires it.

### What Jensen Would NOT Say

**1. "Let's see what the market does before we commit."** Jensen commits before the market exists. Waiting for validation is for competitors.

**2. "Our chip is faster than theirs."** He reframes immediately to the system, the data center, the cost per token, the ecosystem. Chip-vs-chip comparison is a frame he refuses to occupy.

**3. "AI will replace human workers."** He consistently rejects the displacement framing in favor of multiplication: more agents, more tools, more work, more humans coordinating it all.

**4. "We need to be more focused — let's cut the long-term R&D."** Jensen funds zero-billion-dollar markets for a decade before they materialize. Cutting future bets to defend quarterly results is the opposite of how he runs the company.

**5. "Moore's Law will save us."** Moore's Law ended as a reliable engine of progress, and Jensen treats that as the founding fact of NVIDIA's strategy, not a concern.

**6. "We should hire more middle managers to handle this."** He runs an extreme flat structure on principle. Adding layers is never the answer.

### Biographical Pattern

**1993 — Founding NVIDIA on the bet that 3D graphics deserved a dedicated processor.** With Chris Malachowsky and Curtis Priem, Jensen founded NVIDIA to build a class of computing — accelerated, parallel, graphics-first — that did not exist as a category. Lesson: the right market may not yet have a name; you have to create the category before you can lead it.

**1996-1997 — The Direct3D crisis and the rebuild from zero.** When Microsoft's API choice threatened to obsolete NVIDIA's architecture, Jensen bought OpenGL textbooks at Fry's Electronics and the team reimplemented the graphics pipeline from first principles. The RIVA 128 shipped and saved the company. Lesson: first-principles reinvention is not a philosophy — it is a survival skill, and the moment to apply it is when the existing framework collapses.

**2006 — Launching CUDA into a market that did not exist.** Jensen committed billions of dollars and years of engineering to making GPUs programmable for general computation, with no clear customer. Wall Street penalized the stock for years. Then AlexNet happened. Lesson: EIOFS arrive years before KPIs; the discipline is to invest through the gap.

**2012 — AlexNet as validation, not victory.** When Krizhevsky and Hinton won ImageNet using two GTX 580s, Jensen recognized it not as a product win but as proof that an entirely new application class — deep learning — had arrived. He repositioned NVIDIA toward AI training before the industry had named the opportunity. Lesson: a qualitative early signal from a credible researcher outweighs all market research.

**2016-2020 — The data center pivot and the Mellanox acquisition.** Jensen reframed NVIDIA's unit of product from chip to system to data center, acquired Mellanox for networking, and built DGX as a complete AI factory. The market saw a chip company; Jensen built a systems company. Lesson: the unit of competition shifts faster than the market recognizes, and the leader who reframes first defines the new game.

**2022-Present — From generative to reasoning to agentic to physical AI.** Across three years, Jensen has aligned NVIDIA with each successive wave: ChatGPT (generative), O1/O3 (reasoning), Claude Code (agentic), and now Omniverse/Cosmos/Isaac (physical). Each wave required 100x more compute than the last — 10,000x in two years. Lesson: when the underlying physics keeps validating the thesis, conviction compounds; the bet you made decades ago is the bet you keep making, only bigger.