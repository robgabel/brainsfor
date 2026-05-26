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

  return (
    <div className="inline-flex flex-col items-center gap-2">
      <button
        onClick={handleCopy}
        className={`group relative inline-flex items-center gap-3 rounded-xl bg-deep-ink ${padding} font-mono ${textSize} text-[#e2e8f0] transition-all hover:shadow-brain-elevated`}
      >
        <span className="text-success">$</span>
        <span>{command}</span>
        <span className="ml-2 rounded-md bg-white/10 px-2 py-1 text-xs text-white/60 transition-colors group-hover:text-white/90">
          {copied ? "Copied!" : "Copy"}
        </span>
      </button>
      {zipSlug && (
        <p className="text-xs text-muted">
          Launching next week —{" "}
          <a
            href={`/brains/${zipSlug}/${zipSlug}-brain-pack.zip`}
            download
            className="font-medium text-brain-indigo hover:underline"
          >
            download the zip
          </a>{" "}
          in the meantime.
        </p>
      )}
    </div>
  );
}
