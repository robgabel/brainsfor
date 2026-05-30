// Deployed to Supabase project uzediwokyshjbsymevtp as edge function `embed-brain`.
// Generalized brain-atom embedder. Embeds rows in any <slug>_atoms table whose
// embedding IS NULL, using OpenAI text-embedding-3-large (1536-dim, matching the
// VECTOR(1536) column + search_brain_atoms RPC). Server-side so the OpenAI key
// (Supabase secret OPENAI_API_KEY) never leaves the backend. Called by
// scripts/finalize-supabase.py in a loop until embedded=0.
//
// Body: { table: "scott_belsky_atoms", limit?: 200 }
// Table name is allowlist-validated (^[a-z][a-z0-9_]+_atoms$) before any query.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const EMBEDDING_MODEL = "text-embedding-3-large";
const EMBEDDING_DIMS = 1536;
const BATCH_SIZE = 20;
const TABLE_RE = /^[a-z][a-z0-9_]{1,60}_atoms$/;

async function embedText(text: string, openaiKey: string): Promise<number[]> {
  const resp = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${openaiKey}` },
    body: JSON.stringify({ model: EMBEDDING_MODEL, input: text, dimensions: EMBEDDING_DIMS }),
  });
  if (!resp.ok) throw new Error(`OpenAI ${resp.status}: ${await resp.text()}`);
  const data = await resp.json();
  return data.data[0].embedding;
}

Deno.serve(async (req: Request) => {
  try {
    const openaiKey = Deno.env.get("OPENAI_API_KEY");
    if (!openaiKey) throw new Error("OPENAI_API_KEY not set");
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    );

    let table = "";
    let limit = 200;
    try {
      const body = await req.json();
      table = body.table || "";
      limit = body.limit || 200;
    } catch { /* */ }

    if (!TABLE_RE.test(table)) {
      return new Response(JSON.stringify({ error: `invalid table name: ${table}` }), {
        status: 400, headers: { "Content-Type": "application/json" },
      });
    }

    const { data: atoms, error: fetchError } = await supabase
      .from(table)
      .select("id, content, original_quote")
      .is("embedding", null)
      .limit(limit);
    if (fetchError) throw new Error(`Fetch error: ${fetchError.message}`);
    if (!atoms || atoms.length === 0) {
      return new Response(JSON.stringify({ message: "No atoms need embedding", embedded: 0, remaining: 0 }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    let embedded = 0, errors = 0;
    const errorDetails: string[] = [];
    for (let i = 0; i < atoms.length; i += BATCH_SIZE) {
      const batch = atoms.slice(i, i + BATCH_SIZE);
      const results = await Promise.allSettled(
        batch.map(async (atom: { id: string; content: string; original_quote: string | null }) => {
          const text = [atom.content, atom.original_quote].filter(Boolean).join("\n\n");
          const embedding = await embedText(text, openaiKey);
          const { error: updateError } = await supabase
            .from(table)
            .update({ embedding: `[${embedding.join(",")}]` })
            .eq("id", atom.id);
          if (updateError) throw new Error(`Update ${atom.id}: ${updateError.message}`);
          return atom.id;
        }),
      );
      for (const r of results) {
        if (r.status === "fulfilled") embedded++;
        else { errors++; errorDetails.push(r.reason?.message || "unknown"); }
      }
    }

    return new Response(JSON.stringify({
      message: `Embedded ${embedded}${errors ? `, ${errors} errors` : ""}`,
      embedded, errors, errorDetails: errorDetails.slice(0, 5), processed: atoms.length,
    }), { headers: { "Content-Type": "application/json" } });
  } catch (err) {
    return new Response(JSON.stringify({ error: (err as Error).message }), {
      status: 500, headers: { "Content-Type": "application/json" },
    });
  }
});
