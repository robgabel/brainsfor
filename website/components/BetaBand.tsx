"use client";

import { track } from "@vercel/analytics";

// Beta loop: downloads become people we can talk to. The ask is one email —
// high-touch on purpose at this scale. Swap the address for an alias when one
// exists; the mailto keeps this zero-infrastructure for the first cohort.
const BETA_MAILTO =
  "mailto:robgabel@gmail.com?subject=" +
  encodeURIComponent("BrainsFor beta — what my agent did") +
  "&body=" +
  encodeURIComponent(
    "Which brain did you install?\n\nWhat did your agent do better with it?\n\nWhat broke or felt off?\n",
  );

export function BetaBand() {
  return (
    <div className="mx-auto max-w-[720px] rounded-xl border border-indigo-soft bg-white p-6 text-center shadow-brain">
      <p className="font-display text-lg font-normal tracking-tight text-deep-ink">
        We&rsquo;re in beta — every brain is free while we learn.
      </p>
      <p className="mx-auto mt-2 max-w-[520px] text-sm leading-relaxed text-body">
        The trade: after you install one, email Rob one thing your agent did better.
        That&rsquo;s the whole deal.
      </p>
      <a
        href={BETA_MAILTO}
        onClick={() => {
          try {
            track("beta_email_click");
          } catch {
            // analytics must never break the page
          }
        }}
        className="mt-4 inline-block rounded-lg border-[1.5px] border-indigo-soft px-5 py-2.5 text-sm font-semibold text-brain-indigo transition-all hover:border-brain-indigo hover:bg-brain-indigo/5"
      >
        Email what happened
      </a>
    </div>
  );
}
