"use client";

import { useState, useRef, useEffect } from "react";

interface BrainOption {
  slug: string;
  name: string;
  badge?: string;
  emoji?: string;
}

interface BrainDropdownProps {
  brains: BrainOption[];
  selected: string;
  onChange: (slug: string) => void;
  label?: string;
}

/**
 * Custom brain selector. Replaces the 16-button wrap-row that was creating
 * too much visual noise above the actual demo. Closed state shows the active
 * brain as a single styled trigger; open state reveals all brains in a
 * scrollable panel with badges preserved.
 */
export function BrainDropdown({
  brains,
  selected,
  onChange,
  label = "Choose a brain",
}: BrainDropdownProps) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);

  const activeBrain = brains.find((b) => b.slug === selected) ?? brains[0];

  // Close on outside click + Escape.
  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKey);
    };
  }, [open]);

  return (
    <div ref={wrapRef} className="relative">
      <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-muted">
        {label}
      </label>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className={`group flex w-full max-w-[420px] items-center justify-between gap-3 rounded-xl border bg-white px-4 py-3 text-left transition-all ${
          open
            ? "border-brain-indigo shadow-brain"
            : "border-border-default hover:border-border-indigo hover:shadow-sm"
        }`}
      >
        <span className="flex items-center gap-2 min-w-0">
          {activeBrain?.emoji && (
            <span aria-hidden className="shrink-0 text-base leading-none">{activeBrain.emoji}</span>
          )}
          <span className="font-display text-[15px] font-semibold text-deep-ink truncate">
            {activeBrain?.name ?? "Pick one"}
          </span>
          {activeBrain?.badge && (
            <span className="inline-flex shrink-0 items-center rounded-full bg-gradient-to-r from-brain-indigo to-[#8b5cf6] px-1.5 py-0.5 text-[9px] font-bold uppercase leading-none tracking-wider text-white">
              {activeBrain.badge}
            </span>
          )}
        </span>
        <svg
          className={`h-4 w-4 shrink-0 text-muted transition-transform ${open ? "rotate-180 text-brain-indigo" : ""}`}
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M4 6l4 4 4-4" />
        </svg>
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute left-0 right-0 z-30 mt-2 max-h-[360px] w-full max-w-[420px] overflow-y-auto rounded-xl border border-border-indigo bg-white p-1 shadow-brain-elevated"
        >
          {brains.map((b) => {
            const active = b.slug === selected;
            return (
              <button
                key={b.slug}
                role="option"
                aria-selected={active}
                onClick={() => {
                  onChange(b.slug);
                  setOpen(false);
                  triggerRef.current?.focus();
                }}
                className={`flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-left transition-colors ${
                  active
                    ? "bg-brain-indigo/10 text-brain-indigo"
                    : "text-deep-ink hover:bg-cool-surface"
                }`}
              >
                <span className="flex items-center gap-2 min-w-0">
                  {b.emoji && (
                    <span aria-hidden className="shrink-0 text-base leading-none">{b.emoji}</span>
                  )}
                  <span className="font-display text-[14px] font-medium truncate">
                    {b.name}
                  </span>
                  {b.badge && (
                    <span className="inline-flex shrink-0 items-center rounded-full bg-gradient-to-r from-brain-indigo to-[#8b5cf6] px-1.5 py-0.5 text-[9px] font-bold uppercase leading-none tracking-wider text-white">
                      {b.badge}
                    </span>
                  )}
                </span>
                {active && (
                  <svg
                    className="h-4 w-4 shrink-0 text-brain-indigo"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M3 8.5l3.5 3.5L13 5" />
                  </svg>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
