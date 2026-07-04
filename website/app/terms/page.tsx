import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms of Use — brainsforagents",
  description:
    "The terms for using brainsforagents: what brain packs are and aren't, your license, and how takedowns work.",
  alternates: { canonical: "/terms" },
};

const CONTACT = "robgabel@gmail.com";

function H2({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="mt-10 font-display text-xl font-normal tracking-tight text-deep-ink">
      {children}
    </h2>
  );
}

function P({ children }: { children: React.ReactNode }) {
  return <p className="mt-3 text-[15px] leading-relaxed text-body">{children}</p>;
}

export default function TermsPage() {
  return (
    <section className="px-6 pb-24 pt-16 md:pt-20">
      <div className="mx-auto max-w-[720px]">
        <h1 className="font-display text-4xl font-light tracking-[-1.2px] text-deep-ink">
          Terms of Use
        </h1>
        <p className="mt-2 text-sm text-muted">Effective July 4, 2026</p>

        <P>
          The short version: everything is free during beta and provided as-is.
          Brain packs are our structured analysis of what a thinker has said
          publicly — they are not the person, and outputs from them are
          AI-generated interpretations that can be wrong. Use them to think
          better, not as professional advice. If you&rsquo;re one of the
          thinkers and want your brain changed or removed, email us and
          we&rsquo;ll act promptly.
        </P>

        <H2>The service, during beta</H2>
        <P>
          brainsforagents.com and the brain packs it distributes are in beta.
          Everything is free, provided as-is and as-available, and may change,
          break, or pause without notice. Packs you have already downloaded are
          yours to keep using under the license below, whatever we change later.
        </P>

        <H2>Your account</H2>
        <P>
          You don&rsquo;t need an account to download brains. If you create
          one, keep your email accurate — it&rsquo;s how we reach you and how
          you prove the account is yours. We may suspend accounts that abuse
          the service.
        </P>

        <H2>What a brain pack is — and isn&rsquo;t</H2>
        <P>
          Each brain pack is built from publicly available sources: interviews,
          essays, talks, podcasts, and other published material. We decompose
          that material into structured knowledge — atoms, connections,
          synthesis — which is transformative editorial analysis, not a
          reproduction of the underlying works.
        </P>
        <P>
          Unless a brain is explicitly marked as verified or claimed, it is{" "}
          <span className="font-medium text-deep-ink">
            not affiliated with, endorsed by, or reviewed by its subject
          </span>
          . The extraction is AI-assisted and can contain errors,
          misattributions, or statements the person would phrase differently
          today. Where we can, we tag each atom&rsquo;s epistemic status —
          opinion, fact, prediction — and whether it has been verified.
        </P>
        <P>
          Outputs generated with a brain pack are AI interpretations, not the
          person&rsquo;s words. The Peter Attia brain is not your physician.
          The Charlie Munger brain is not your financial advisor. Nothing here
          is medical, legal, financial, or other professional advice.
        </P>

        <H2>Your license</H2>
        <P>
          Downloaded packs may be used for personal purposes and internal
          business purposes — load them into your AI tools, build workflows on
          them, quote outputs with attribution. You may not resell or
          redistribute the packs themselves as a competing catalog, and you may
          not present pack outputs as actual statements made by the subject.
        </P>

        <H2>Acceptable use</H2>
        <P>
          Don&rsquo;t use the site or packs for anything illegal, don&rsquo;t
          impersonate a brain&rsquo;s subject to deceive people, and don&rsquo;t
          circumvent rate limits or automate the live demos at scale — the
          packs are free to download if you want the data.
        </P>

        <H2>For the thinkers</H2>
        <P>
          If a brain is built from your public work and you want corrections,
          context, or removal, email{" "}
          <a href={`mailto:${CONTACT}`} className="text-brain-indigo hover:underline">
            {CONTACT}
          </a>
          . We take these requests seriously and act promptly — our goal is
          removal or correction within seven days. We&rsquo;d rather work with
          you: a claiming program (verify, curate, share revenue) is on the
          roadmap.
        </P>

        <H2>Intellectual property</H2>
        <P>
          The structure, curation, synthesis, and software of brainsforagents
          are ours. The underlying ideas and quotations belong to their
          authors and are used with attribution as analysis and commentary.
        </P>

        <H2>Disclaimers and liability</H2>
        <P>
          The service is provided without warranties of any kind, express or
          implied. To the maximum extent permitted by law, our total liability
          for any claim arising from the service or the packs is limited to
          the greater of $100 or the amount you paid us in the past twelve
          months (during beta: $0, so $100).
        </P>

        <H2>Governing law</H2>
        <P>
          These terms are governed by the laws of the State of California,
          USA, without regard to conflict-of-law rules.
        </P>

        <H2>Changes</H2>
        <P>
          If these terms change materially, we&rsquo;ll update the effective
          date above and note the change on the site. Continued use after a
          change means you accept it.
        </P>

        <H2>Contact</H2>
        <P>
          Questions:{" "}
          <a href={`mailto:${CONTACT}`} className="text-brain-indigo hover:underline">
            {CONTACT}
          </a>
          . See also our <Link href="/privacy" className="text-brain-indigo hover:underline">Privacy Policy</Link>.
        </P>
      </div>
    </section>
  );
}
