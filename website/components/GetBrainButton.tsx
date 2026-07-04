"use client";

import { useMemo } from "react";
import { track } from "@vercel/analytics";
import { createClient } from "@/lib/supabase-browser";

export function GetBrainButton({ brainSlug }: { brainSlug: string }) {
  // Degrade gracefully if the Supabase client can't be created (missing env):
  // the download must work with zero infrastructure.
  const supabase = useMemo(() => {
    try {
      return createClient();
    } catch {
      return null;
    }
  }, []);

  // Best-effort side effects on download: analytics + recording ownership in
  // brain_access for signed-in users (this is what populates the dashboard's
  // "My Brains"). Neither may ever block or fail the download itself.
  function onDownload() {
    try {
      track("download_click", { slug: brainSlug, position: "brain_page" });
    } catch {
      // analytics must never break the page
    }
    if (!supabase) return;
    void (async () => {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser();
        if (!user) return;
        const { data: existing } = await supabase
          .from("brain_access")
          .select("id")
          .eq("user_id", user.id)
          .eq("brain_slug", brainSlug)
          .limit(1);
        if (existing && existing.length > 0) return;
        await supabase
          .from("brain_access")
          .insert({ user_id: user.id, brain_slug: brainSlug });
      } catch {
        // the download is the product; the claim is bookkeeping
      }
    })();
  }

  return (
    <a
      href={`/brains/${brainSlug}/${brainSlug}-brain-pack.zip`}
      download
      onClick={onDownload}
      className="block w-full rounded-lg bg-brain-indigo py-3 text-center text-[15px] font-semibold text-white shadow-brain-cta transition-all hover:bg-indigo-hover active:scale-[0.98]"
    >
      Get this brain — free
    </a>
  );
}
