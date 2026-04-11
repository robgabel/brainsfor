"use client";

import Link from "next/link";
import { useState } from "react";

export function Nav() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--border-whisper)] bg-white/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1140px] items-center justify-between px-6 py-4">
        {/* Logo */}
        <Link href="/" className="font-display text-xl font-semibold tracking-tight text-deep-ink">
          brainsfor<span className="text-brain-indigo">.dev</span>
        </Link>

        {/* Desktop links */}
        <div className="hidden items-center gap-8 md:flex">
          <Link href="/brains" className="text-[15px] font-medium text-body hover:text-deep-ink transition-colors">
            Brains
          </Link>
          <Link href="/skills" className="text-[15px] font-medium text-body hover:text-deep-ink transition-colors">
            Skills
          </Link>
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="flex h-11 w-11 items-center justify-center rounded-lg border border-[var(--border-default)] text-body hover:text-deep-ink md:hidden"
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileOpen}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            {mobileOpen ? (
              <>
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </>
            ) : (
              <>
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </>
            )}
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="border-t border-[var(--border-default)] bg-white/98 backdrop-blur-xl px-6 py-4 md:hidden">
          <div className="flex flex-col gap-2">
            <Link
              href="/brains"
              className="rounded-lg px-4 py-3 text-base font-medium text-body hover:bg-brain-indigo/5 min-h-[44px]"
              onClick={() => setMobileOpen(false)}
            >
              Brains
            </Link>
            <Link
              href="/skills"
              className="rounded-lg px-4 py-3 text-base font-medium text-body hover:bg-brain-indigo/5 min-h-[44px]"
              onClick={() => setMobileOpen(false)}
            >
              Skills
            </Link>
            <Link
              href="/brains"
              className="mt-2 rounded-lg bg-brain-indigo px-4 py-3 text-center text-[15px] font-semibold text-white shadow-brain-cta min-h-[44px]"
              onClick={() => setMobileOpen(false)}
            >
              Browse Brains
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
