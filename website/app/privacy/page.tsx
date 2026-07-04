import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy — brainsforagents",
  description:
    "What brainsforagents collects, what it doesn't, and how to get your data deleted.",
  alternates: { canonical: "/privacy" },
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

export default function PrivacyPage() {
  return (
    <section className="px-6 pb-24 pt-16 md:pt-20">
      <div className="mx-auto max-w-[720px]">
        <h1 className="font-display text-4xl font-light tracking-[-1.2px] text-deep-ink">
          Privacy Policy
        </h1>
        <p className="mt-2 text-sm text-muted">Effective July 4, 2026</p>

        <P>
          The short version: you can download every brain without an account. If
          you sign in, we store your email. We run aggregate analytics to see
          what works. We don&rsquo;t sell your data, we don&rsquo;t run ad
          trackers, and we don&rsquo;t share anything beyond the services that
          keep the site running.
        </P>

        <H2>What we collect</H2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-[15px] leading-relaxed text-body">
          <li>
            <span className="font-medium text-deep-ink">Account data.</span>{" "}
            If you sign in with a magic link, your email address. If you sign in
            with GitHub, the name, email, and avatar GitHub shares. Stored in
            Supabase, used only to run your account.
          </li>
          <li>
            <span className="font-medium text-deep-ink">Session cookies.</span>{" "}
            Essential cookies that keep you signed in. No third-party
            advertising cookies, ever.
          </li>
          <li>
            <span className="font-medium text-deep-ink">Things you submit.</span>{" "}
            Brain requests and votes, tied to your account.
          </li>
          <li>
            <span className="font-medium text-deep-ink">Demo questions.</span>{" "}
            Questions you type into the live demos are sent to Anthropic (and,
            for retrieval, OpenAI) to generate the answer, and your IP address
            is counted transiently for rate limiting. Don&rsquo;t put sensitive
            personal information in a demo question.
          </li>
          <li>
            <span className="font-medium text-deep-ink">Analytics.</span>{" "}
            Vercel Analytics — aggregate page views and product events (a demo
            played, a download clicked). No cross-site tracking, no profiles.
          </li>
          <li>
            <span className="font-medium text-deep-ink">Email you send us.</span>{" "}
            The beta feedback loop is literally email. We keep what you send.
          </li>
        </ul>

        <H2>Who processes it</H2>
        <P>
          We use a small set of infrastructure providers, each only for what
          they&rsquo;re named for: Supabase (authentication and database),
          Vercel (hosting and analytics), Anthropic and OpenAI (generating demo
          answers), and Upstash (rate limiting). Each receives only what it
          needs to do its job.
        </P>

        <H2>What we don&rsquo;t do</H2>
        <P>
          We don&rsquo;t sell or rent your data. We don&rsquo;t run advertising
          networks or tracking pixels. We don&rsquo;t require an account to
          download a brain, and downloads are not tied to your identity unless
          you&rsquo;re signed in.
        </P>

        <H2>Retention and deletion</H2>
        <P>
          Account data is kept while your account exists. Email{" "}
          <a href={`mailto:${CONTACT}`} className="text-brain-indigo hover:underline">
            {CONTACT}
          </a>{" "}
          from your account address and we&rsquo;ll delete your account and
          associated data within 30 days.
        </P>

        <H2>Changes</H2>
        <P>
          If this policy changes materially, we&rsquo;ll update the effective
          date above and note the change on the site.
        </P>

        <H2>Contact</H2>
        <P>
          Questions about this policy:{" "}
          <a href={`mailto:${CONTACT}`} className="text-brain-indigo hover:underline">
            {CONTACT}
          </a>
          .
        </P>
      </div>
    </section>
  );
}
