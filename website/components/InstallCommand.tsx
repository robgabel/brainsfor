// The npx registry isn't published yet, so this component must never present
// the command as a working install path (a first action that fails kills
// trust in the first mile). The zip download is the primary path everywhere;
// this renders the future command as a clearly-labeled preview.
export function InstallCommand({
  command = "npx skills add brainsfor/steve-jobs",
  size = "lg",
}: {
  command?: string;
  size?: "sm" | "lg";
}) {
  const padding = size === "lg" ? "px-6 py-4" : "px-4 py-3";
  const textSize = size === "lg" ? "text-[15px]" : "text-sm";
  const isSm = size === "sm";

  return (
    <div className={`flex flex-col gap-2 ${isSm ? "w-full" : "inline-flex items-center"}`}>
      <div
        aria-label="Planned install command — not available yet"
        className={`rounded-xl bg-deep-ink/60 ${padding} font-mono ${textSize} text-[#e2e8f0]/60 ${isSm ? "flex w-full flex-col items-start gap-2" : "inline-flex items-center gap-3"}`}
      >
        {/* Command scrolls horizontally on narrow cards so the slug never breaks mid-word */}
        <span className={`flex items-center gap-3 ${isSm ? "w-full overflow-x-auto" : ""}`}>
          <span className="shrink-0 text-success/60">$</span>
          <span className="whitespace-nowrap">{command}</span>
        </span>
        <span className={`shrink-0 rounded-md bg-white/10 px-2 py-1 text-xs text-white/50 ${isSm ? "self-end" : "ml-2"}`}>
          Soon
        </span>
      </div>
      <p className="text-xs text-muted">
        One-command install isn&rsquo;t live yet — the free download above is
        the full pack, working today.
      </p>
    </div>
  );
}
