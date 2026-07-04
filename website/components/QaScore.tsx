import type { BrainQA } from "@/lib/brains";

// Color tiers for the 0-100 persona-QA score. Uses DESIGN.md tokens:
// success green >= 75, brain indigo 60-74, knowledge gold below.
export function qaTier(score: number): { text: string; bg: string; bar: string } {
  if (score >= 75)
    return { text: "text-success", bg: "bg-[rgba(5,150,105,0.1)]", bar: "bg-success" };
  if (score >= 60)
    return { text: "text-indigo-deep", bg: "bg-indigo-mist", bar: "bg-brain-indigo" };
  return { text: "text-[#d97706]", bg: "bg-[rgba(217,119,6,0.1)]", bar: "bg-[#d97706]" };
}

const DIMENSIONS: { key: keyof BrainQA["dimensions"]; label: string; caption: string }[] = [
  { key: "authenticity", label: "Authenticity", caption: "Would they recognize themselves in it?" },
  { key: "rigor", label: "Rigor", caption: "Their actual reasoning — no generic AI filler." },
  { key: "coverage", label: "Coverage", caption: "The failures and the mess, not just the highlight reel." },
  { key: "calibration", label: "Calibration", caption: "Claims sized to the evidence behind them." },
];

export function QaScoreCard({ qa, brainName }: { qa: BrainQA; brainName: string }) {
  const tier = qaTier(qa.score);
  return (
    <div className="rounded-xl border border-border-indigo bg-white p-6 shadow-brain">
      <div className="flex flex-col gap-8 md:flex-row">
        {/* Overall */}
        <div className="shrink-0 md:w-[180px]">
          <div className="flex items-baseline gap-1">
            <span className={`font-display text-6xl font-light tracking-tight ${tier.text}`}>
              {qa.score}
            </span>
            <span className="text-lg text-muted">/100</span>
          </div>
          <div className="mt-1 text-xs text-muted">
            Panel run {qa.as_of}
            {qa.confidence ? ` · ${qa.confidence} confidence` : ""}
          </div>
          {qa.numeric_defects !== undefined && (
            <div className="mt-3 text-xs text-body">
              <strong className="text-label">{qa.numeric_defects}</strong> factual-number defects
            </div>
          )}
          {qa.voice !== undefined && (
            <div className="mt-1 text-xs text-body">
              <strong className="text-label">{Math.round(qa.voice * 100)}%</strong> verbatim-voice coverage
            </div>
          )}
        </div>

        {/* Dimension bars */}
        <div className="min-w-0 flex-1 space-y-4">
          {DIMENSIONS.map((d) => {
            const value = qa.dimensions[d.key];
            if (value === undefined) return null;
            return (
              <div key={d.key}>
                <div className="flex items-baseline justify-between">
                  <span className="text-sm font-medium text-label">{d.label}</span>
                  <span className="font-mono text-sm text-deep-ink">{value}</span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-cool-surface">
                  <div
                    className={`h-full rounded-full ${qaTier(value).bar}`}
                    style={{ width: `${value}%` }}
                  />
                </div>
                <p className="mt-1 text-xs text-muted">{d.caption}</p>
              </div>
            );
          })}
        </div>
      </div>

      <details className="mt-6 border-t border-border-default pt-4">
        <summary className="cursor-pointer text-sm font-medium text-brain-indigo hover:underline">
          How this score is computed
        </summary>
        <p className="mt-3 text-sm leading-relaxed text-body">
          Every brain is graded by a panel of four independent AI judges — one per dimension —
          chaired by a calibration judge, against {brainName}&rsquo;s own stated principles
          and public record. No judge sees another&rsquo;s verdict. Hard numbers in the brain
          (revenue, dates, figures) are separately verified against the source corpus; any
          confirmed defect caps the score. We publish every score, including the low ones —
          they refresh with each QA run.
        </p>
      </details>
    </div>
  );
}

export function QaScorePill({ qa }: { qa: BrainQA }) {
  const tier = qaTier(qa.score);
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-wide ${tier.bg} ${tier.text}`}
      title={`Quality score ${qa.score}/100 — independent AI judge panel${qa.as_of ? `, ${qa.as_of}` : ""}`}
    >
      QA {qa.score}
    </span>
  );
}
