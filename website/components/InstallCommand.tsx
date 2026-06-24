"use client";

import { useState } from "react";

export function InstallCommand({
  command = "npx skills add brainsfor/steve-jobs",
  size = "lg",
}: {
  command?: string;
  size?: "sm" | "lg";
}) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const padding = size === "lg" ? "px-6 py-4" : "px-4 py-3";
  const textSize = size === "lg" ? "text-[15px]" : "text-sm";

  // Derive the slug from the command (e.g. "npx skills add brainsfor/steve-jobs" → "steve-jobs")
  // so the zip fallback link always points at the same brain the user is about to install.
  const slugMatch = command.match(/brainsfor\/([a-z0-9-]+)/);
  const zipSlug = slugMatch?.[1];

  const isSm = size === "sm";

  return (
    <div className={`flex flex-col gap-2 ${isSm ? "w-full" : "inline-flex items-center"}`}>
      <button
        onClick={handleCopy}
        className={`group relative rounded-xl bg-deep-ink ${padding} font-mono ${textSize} text-[#e2e8f0] transition-all hover:shadow-brain-elevated ${isSm ? "flex w-full flex-col items-start gap-2" : "inline-flex items-center gap-3"}`}
      >
        {/* Command scrolls horizontally on narrow cards so the slug never breaks mid-word */}
        <span className={`flex items-center gap-3 ${isSm ? "w-full overflow-x-auto" : ""}`}>
          <span className="shrink-0 text-success">$</span>
          <span className="whitespace-nowrap">{command}</span>
        </span>
        <span className={`shrink-0 rounded-md bg-white/10 px-2 py-1 text-xs text-white/60 transition-colors group-hover:text-white/90 ${isSm ? "self-end" : "ml-2"}`}>
          {copied ? "Copied!" : "Copy"}
        </span>
      </button>
      {zipSlug && (
        <p className="text-xs text-muted">
          Works today —{" "}
          <a
            href={`/brains/${zipSlug}/${zipSlug}-brain-pack.zip`}
            download
            className="font-medium text-brain-indigo hover:underline"
          >
            download the pack
          </a>
          . The one-command install ships soon.
        </p>
      )}
    </div>
  );
}
