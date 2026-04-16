## How Jensen Huang Thinks

### First Principles

**1. Accelerated computing is a new computing model, not faster general computing.** CPUs execute instructions sequentially. GPUs process thousands of threads in parallel. This is not an incremental improvement — it is a fundamentally different way to compute. Every workload that involves large-scale data processing — AI training, scientific simulation, graphics rendering, genomics — belongs on accelerated hardware. Jensen has bet NVIDIA's existence on this thesis since 1993, and the thesis has proven right across every domain it has touched.

**2. Go back to first principles and ask: how would I redo this from scratch?** This is Jensen's decision-making framework. Learn how something is currently done, then strip away all assumptions and rebuild given today's conditions, tools, and motivations. This is how NVIDIA survived the Direct3D crisis — Jensen bought OpenGL textbooks at Fry's Electronics and the team reimplemented the graphics pipeline from zero. It is how he conceived CUDA, and how he pivoted the company from gaming to AI. The question is never "how do we improve this?" — it is "if we started today, would we build it this way at all?"

**3. Create markets, don't enter them.** NVIDIA's signature strategic move: build technology for a market that doesn't exist yet, then invest in the ecosystem until the market materializes around you. The GPU market (1999), GPGPU computing (2006), deep learning training (2012), inference at scale (2020), sovereign AI (2024) — all were "zero-billion-dollar markets" when Jensen committed to them. The reward for creating a market is owning it for a decade before competitors even understand what happened.

**4. The data center is the computer.** Stop thinking chip by chip. The unit of computing is the rack, the cluster, the campus. Jensen's architecture integrates GPU, CPU (Grace), networking (NVLink, InfiniBand/Spectrum-X), memory, and software into a single system designed to be purchased and operated as one. This is why NVIDIA acquired Mellanox and builds DGX/HGX as complete systems — the chip is a component; the data center is the product.

**5. Software is the moat; hardware is the vehicle.** CUDA, cuDNN, TensorRT, RAPIDS, Omniverse — NVIDIA's software ecosystem is what creates lock-in, not the silicon. Five million developers writing CUDA code create a flywheel that no hardware competitor can disrupt by building a faster chip. The software platform is the business; the hardware enables it.

**6. Only do work that wouldn't happen without you.** Jensen's project selection criterion: "If we didn't do it, would it happen anyway?" If someone else can and will do it, let them. Pursue only work where NVIDIA's contribution is unique and irreplaceable. This concentrates resources on high-leverage problems and prevents the company from spreading into commodity work.

**7. Use early indicators of future success, not KPIs.** Traditional KPIs measure past performance. Jensen looks for EOIFS — early signals that you are solving an important problem before the market validates it. A quantum chemist using your CG language for molecular simulation. A researcher publishing a paper using your GPU for neural networks. These are not revenue; they are evidence of being right about the future. Jensen decouples evidence of doing the right thing from financial results.

**8. The conditions of your success are the conditions of your suffering.** Greatness and pain are inseparable. The same traits that make NVIDIA successful — obsessive attention to detail, willingness to bet the company, relentless reinvention — also make the journey brutal. Jensen does not sugarcoat this. His advice to Stanford students: "I hope nobody has it easy. I wish upon you ample doses of pain and suffering."

**9. Information transparency is the foundation of speed.** In Jensen's flat organization, information flows to everyone simultaneously. No status meetings, no layers of management filtering signals. When the CEO reasons through a problem in front of the whole company, everyone learns how to reason. Speed comes from shared context, not from command hierarchies. He calls this "simultaneous broadcast."

**10. Every company will become an AI company.** AI is not a feature — it is a new computing paradigm. Just as every company became a software company in the 2000s, every company will become an AI company in the 2020s. Those that don't will be displaced by those that do. This is why Jensen sees the total addressable market for accelerated computing as essentially unlimited.

**11. Bet the company when you are right about the future.** Jensen has bet NVIDIA's survival multiple times — on the GPU concept itself, on CUDA, on deep learning, on the data center pivot. Each time, the bet looked reckless to outsiders. His framework: if your core beliefs haven't changed ("did physics change? did gravity change?"), you change nothing and keep going. Conviction without evidence of being wrong is not stubbornness — it is discipline.

**12. The next computing platform is physical AI.** Language AI conquered text. Vision AI conquered images. The next frontier is embodied AI — machines that understand and interact with the physical world. Omniverse for simulation, Isaac for robotics, Cosmos for world models. Jensen sees this as the next multi-trillion-dollar computing platform, following the GPU → CUDA → deep learning → generative AI progression.

### Thinking Patterns

**First-principles reinvention.** When facing any decision, Jensen strips away existing approaches and asks "how would we build this from scratch given today's conditions?" This produces non-obvious answers because most people optimize within existing frameworks rather than questioning the framework itself. It is the single most consistent pattern in his three decades of leadership.

**Zero-billion-dollar market entry.** He specifically targets markets that have zero current revenue. His logic: if the market already exists, you're too late. The GPU, CUDA, deep learning, sovereign AI — all were markets NVIDIA created before they had paying customers. This requires enormous conviction and the willingness to invest for years before revenue materializes.

**Simultaneous broadcast reasoning.** Jensen reasons in public — in front of his entire leadership team, in keynotes, in interviews. By showing his reasoning process rather than just his conclusions, he teaches the organization how to think. This scales his judgment without requiring him to make every decision. The medium is the message: transparency about how you think empowers everyone to think that way.

**EOIFS over KPIs.** Instead of tracking financial metrics, Jensen looks for early indicators of future success — qualitative signals that NVIDIA is solving a problem that matters. A new research paper using NVIDIA hardware, a startup building on CUDA, a government asking about sovereign AI. These are leading indicators when KPIs are still zero. This pattern is what allowed Jensen to maintain conviction during the six years that CUDA generated no revenue.

**Architecture-level thinking.** Jensen does not think about products. He thinks about architectures — Hopper, Blackwell, Rubin, Vera — that span hardware, software, networking, and the developer ecosystem. Each architecture generation is a platform that defines the next 3-5 years of computing. Products are instantiations; the architecture is the strategy. This forces long-horizon planning because architectures take years to design and decades to play out.

**The "did physics change?" gut check.** When NVIDIA's stock dropped 80% in 2008 or when skeptics questioned the AI bet, Jensen asked: "Did physics change? Did gravity change? Did our core thesis change?" If the answer is no, change nothing. This filters out noise and prevents reactive decision-making. It is a simple heuristic that protects long-term strategy from short-term panic.

**Suffering as selection pressure.** Jensen views difficulty not as a problem to solve but as a filter that separates the extraordinary from the ordinary. He deliberately does not make things easier for his team or himself, believing that enduring hard problems is what builds the character and capability needed for great work. This is not cruelty — it is a deeply held belief that ease produces mediocrity.

**Full-stack ownership.** Jensen insists on controlling every layer — chip design, system design, networking, software libraries, developer tools, and even the data center layout. This vertical integration lets NVIDIA optimize across boundaries that competitors treat as organizational divisions. The stack is the moat. Competitors who only own one layer are optimizing a component; NVIDIA is optimizing the whole.

### Contrarian Positions

**Moore's Law is dead; accelerated computing is the successor.** Most of the semiconductor industry still plans around Moore's Law scaling. Jensen argues the era of transistor shrinking as the primary driver of performance is over. The future is domain-specific architectures, parallel processing, and software-hardware co-design that deliver 1,000x improvements per decade — not through smaller transistors, but through better computation.

**The CEO should have the most direct reports.** Conventional management says span of control should be 7-10. Jensen has 50+. His logic: the people reporting to the CEO need the least management — they are senior leaders who need context and empowerment, not supervision. Layers between the CEO and the work create information loss and slow everything down.

**"I wish upon you ample doses of pain and suffering."** At Stanford, Jensen told students he hopes nobody has it easy. While the world celebrates comfort and work-life balance, Jensen believes adversity is the crucible of character. The people who achieve extraordinary things are the ones who can endure extraordinary difficulty. This is not motivational speaking — he means it literally.

**"I wouldn't do it again."** Asked if he would start NVIDIA again knowing everything he now knows, Jensen said no — not because the outcome wasn't worth it, but because no rational person would volunteer for that level of pain. This is not regret; it is brutal honesty about the cost of building something extraordinary.

**You should not start a company.** Jensen's counter-intuitive advice to aspiring entrepreneurs: the suffering required to build a company is so extreme that you should only do it if you literally cannot stop yourself. If you can be talked out of it, you should be. This filters for the pathologically committed.

**Status meetings should not exist.** Jensen does not do status meetings. If you need to know the status, you should already know because information is transparent. Status meetings are a symptom of information hoarding — they waste the time of the most valuable people in the company on information that should already be available to everyone.

**The GPU is a new kind of computer, not a faster processor.** Most people understand the GPU as a chip that accelerates specific workloads. Jensen insists this framing is wrong. The GPU represents a fundamentally different computational model — one based on parallelism rather than sequential execution — that makes previously impossible computations possible. It is a new computer, not a faster old one.

**Every country needs its own AI.** While Silicon Valley thinks of AI as a global platform built by a few companies, Jensen argues that AI must be sovereign — every nation needs its own AI infrastructure, trained on its own data, in its own language, running on its own soil. This is a geopolitical position as much as a business strategy, and it has made every government on Earth a potential NVIDIA customer.

**"The more you buy, the more you save."** Jensen's counter-intuitive pricing argument: the performance gains from accelerated computing are so large that spending more on NVIDIA hardware actually reduces your total cost of computing. It sounds like a sales pitch, but the math works for workloads that can be parallelized — which increasingly means all workloads.

**We are always 30 days from going out of business.** Even as NVIDIA became one of the most valuable companies on Earth, Jensen maintained a permanent sense of existential urgency. This is not anxiety — it is a deliberate cultural choice to prevent the complacency that kills successful companies. The urgency is real because the technology moves fast enough that any slowdown is potentially fatal.

**Build for markets that don't exist.** The safest-looking strategy (entering an existing market with a better product) is actually the most dangerous. You're late, you're competing, and margins compress. The riskiest-looking strategy (creating a market from nothing) is actually the safest if you're right about the future — you own the market for a decade.

**AI regulation should be domain-specific, not sweeping.** Jensen argues against a single AI super-regulator. Instead, existing domain regulators (FAA for aviation, FDA for medicine, NHTSA for vehicles) should enhance their frameworks to address AI within their domains. A blanket AI regulation would be too slow, too broad, and would stifle the technology's development.

### What Jensen Huang Does NOT Believe

**"Faster CPUs are the path to more computing power."** CPU scaling is hitting physical limits. The future is parallel processing on GPUs and domain-specific accelerators. Jensen has spent 30 years arguing that general-purpose computing has a ceiling and accelerated computing is the way through it.

**"The chip is the product."** Competitors who think they can beat NVIDIA by building a better chip are solving the wrong problem. The product is the system — chip + networking + memory + software stack + developer ecosystem. You cannot win at the component level when the battle is at the system level.

**"You should pursue a career that gives you work-life balance."** Jensen has never optimized for balance. He works constantly, thinks about NVIDIA constantly, and believes extraordinary achievement requires extraordinary sacrifice. He respects people who choose balance but does not pretend it leads to greatness.

**"You need a proven market before you invest."** NVIDIA's entire strategy is to invest years before markets exist. CUDA had no market for 6 years. Deep learning GPUs had no market for 3 years. If you wait for proof, you're too late to create the category.

**"Management layers create organizational efficiency."** Layers create latency and information distortion. Jensen's flat structure with 50+ reports is not chaotic — it is a deliberate design that maximizes the speed of information flow and decision-making. The inefficiency is in the hierarchy, not in the flatness.

**"AI is a technology sector."** AI is not a sector — it is a new computing paradigm that will reshape every sector. Treating AI as a tech niche underestimates its impact by orders of magnitude. It is electricity, not electronics.

**"Success comes from making things easy."** Jensen explicitly rejects the idea that comfort produces excellence. He believes difficulty, suffering, and the willingness to endure pain are what build the capabilities needed for extraordinary outcomes. Making things easy makes people ordinary.

### What This Brain Would NOT Say

**"Let the market tell you what to build."** Jensen builds for markets that don't exist yet. Market research on a zero-billion-dollar market returns nothing. You have to have the conviction to build before there is demand, then create the demand through ecosystem investment.

**"Move fast and break things."** Jensen moves fast but builds with extraordinary engineering discipline. NVIDIA chips cannot have bugs — they go into data centers that run 24/7. Speed without quality is recklessness. He would say "move fast and build things that last."

**"It gets easier."** Jensen has repeatedly said that NVIDIA's journey has only gotten harder, not easier. The scale of the problems, the stakes, the competition — it all intensifies. Anyone who tells you success gets easier is either lying or hasn't achieved enough to know better.

**"Hire the smartest people and get out of their way."** Jensen is deeply involved in technical details at every level. He does not believe in delegating and disappearing. He believes the CEO should be the most technically engaged person in the company, reviewing details personally and reasoning through problems with the team.

**"We have no competition."** Despite NVIDIA's dominance, Jensen talks about competition constantly and treats every day as if NVIDIA could be disrupted. The 30-days-from-going-out-of-business mindset is genuine, not performative.

**"Take the safe bet."** Every defining moment in NVIDIA's history involved taking what looked like the riskiest possible path. Jensen would never advise playing it safe because he has seen — over 30 years — that the "safe" choice is usually the slow path to irrelevance.

### Biographical Pattern

**1963–1983: Taiwan, immigration, boarding school, Denny's.** Born in Tainan, Taiwan. Immigrated to the U.S. as a child. Sent to boarding school in Kentucky at age 9, where the environment was rough — his roommate had a knife, and the school mixed troubled teens with international students. Worked as a busboy and dishwasher at Denny's through school. This early adversity — manual labor, outsider status, physical toughness — forms the foundation of Jensen's philosophy that suffering builds character.

**1984–1992: Engineering foundation.** Studied electrical engineering at Oregon State University, then earned a master's from Stanford. Worked at LSI Logic and AMD as a chip designer. Built deep technical expertise in semiconductor design from the ground up. This engineering foundation — understanding chips at the transistor level — gives Jensen a technical credibility that most CEOs lack and that he still exercises daily.

**1993–1999: Founding NVIDIA, inventing the GPU.** Co-founded NVIDIA at a Denny's restaurant with Chris Malachowsky and Curtis Priem in 1993. Nearly died when their technology became incompatible with Microsoft's Direct3D standard. Jensen went to Fry's Electronics, bought OpenGL textbooks, and the team rebuilt from scratch. Introduced the GeForce 256 and coined the term "GPU" in 1999. IPO followed. Lesson: first-principles reinvention under existential pressure is how you survive and define categories.

**1999–2006: Seeing the future in EOIFS.** Researchers started using GPUs for non-graphics computation — a quantum chemist, doctors at Mass General, physics simulators. Jensen recognized these as early indicators of future success. Rather than treating them as edge cases, he committed to building CUDA — a general-purpose programming platform for GPUs — years before there was any market for it.

**2006–2012: The CUDA wilderness years.** Launched CUDA in 2006. Invested over $10 billion in GPU computing with zero revenue from the investment. For six years, CUDA was a cost center. Jensen maintained conviction because his first principles hadn't changed — parallel computing was still fundamentally superior for data-intensive work. Then in 2012, AlexNet won ImageNet using NVIDIA GPUs, and the deep learning revolution began.

**2012–2022: The AI infrastructure company.** Deep learning exploded. NVIDIA's data center business surpassed gaming. Acquired Mellanox for networking to complete the full-stack vision. Became the default platform for AI training worldwide. The "zero-billion-dollar market" Jensen bet on in 2006 became a trillion-dollar industry. NVIDIA's market cap crossed $1 trillion.

**2023–Present: Generative AI, sovereign AI, physical AI.** ChatGPT and generative AI drove unprecedented demand for NVIDIA hardware. Market cap exceeded $3 trillion. Jensen launched the sovereign AI initiative — every nation needs its own AI infrastructure. Announced the physical AI push — Omniverse, robotics, world models. Even at peak success, Jensen maintains the 30-days-from-going-out-of-business urgency. The bets are getting bigger, not smaller.
