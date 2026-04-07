"use client";

import { useState } from "react";

export function InstallCommand({
  command = "npx skills add brainsforsale/steve-jobs",
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

  return (
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
  );
}
