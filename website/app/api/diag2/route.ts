import { fetchBrainAtoms } from "@/lib/brain-atoms-db";

export const dynamic = "force-dynamic";

// TEMP diagnostic — does the Supabase atom fetch work in the deployed function?
export async function GET() {
  let count = -1;
  let err: string | null = null;
  try {
    const atoms = await fetchBrainAtoms("elon-musk");
    count = atoms.length;
  } catch (e) {
    err = (e as Error).message;
  }
  return new Response(
    JSON.stringify({
      ok: true,
      elonAtomCount: count,
      error: err,
      hasUrl: !!process.env.NEXT_PUBLIC_SUPABASE_URL,
      hasAnonKey: !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
      urlPrefix: (process.env.NEXT_PUBLIC_SUPABASE_URL || "").slice(0, 20),
    }),
    { headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } },
  );
}
