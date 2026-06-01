import { fetchBrainAtoms } from "@/lib/brain-atoms-db";

// TEMP diagnostic — confirms whether the Supabase atom fetch works inside the
// deployed serverless function. Remove after verifying.
export async function GET() {
  let count = -1;
  let err: string | null = null;
  try {
    const atoms = await fetchBrainAtoms("elon-musk");
    count = atoms.length;
  } catch (e) {
    err = (e as Error).message;
  }
  return Response.json({
    elonAtomCount: count,
    error: err,
    hasUrl: !!process.env.NEXT_PUBLIC_SUPABASE_URL,
    hasAnonKey: !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  });
}
