import { ImageResponse } from "next/og";

// The share card IS the side-by-side — beta users arrive from X/HN/Discord
// links, so the delta has to be visible before the click. Statically
// generated at build time (no request-time APIs used).

export const alt =
  "Same prompt, two answers: Claude alone hedges; Claude with Elon Musk's brain loaded answers in his frameworks, with cited sources.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const INDIGO = "#6366f1";
const INDIGO_SOFT = "#c7d2fe";
const MUTED = "#94a3b8";

export default function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          background: "#0f0b1e",
          padding: "48px 56px",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", fontSize: 30, fontWeight: 600, color: "#ffffff" }}>
            brainsforagents
          </div>
          <div style={{ display: "flex", fontSize: 24, color: INDIGO_SOFT }}>
            Load a genius into your AI.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            marginTop: 36,
            fontSize: 27,
            color: "#e2e8f0",
          }}
        >
          &gt; Should I rewrite this module from scratch or keep patching it?
        </div>

        <div style={{ display: "flex", gap: 24, marginTop: 28, flexGrow: 1 }}>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              flex: 1,
              background: "#0f172a",
              borderRadius: 16,
              padding: "26px 30px",
            }}
          >
            <div style={{ display: "flex", fontSize: 20, color: MUTED }}>
              Claude — no brain
            </div>
            <div
              style={{
                display: "flex",
                marginTop: 18,
                fontSize: 24,
                lineHeight: 1.5,
                color: "#64748b",
              }}
            >
              It depends on several factors. Rewrites carry risk but reduce
              debt; patching is faster short-term. Consider weighing the
              trade-offs with your team&hellip;
            </div>
          </div>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              flex: 1,
              background: "#1a1432",
              border: `3px solid ${INDIGO}`,
              borderRadius: 16,
              padding: "26px 30px",
            }}
          >
            <div style={{ display: "flex", fontSize: 20, color: "#34d399" }}>
              Claude + 🚀 Elon Musk&rsquo;s brain
            </div>
            <div
              style={{
                display: "flex",
                marginTop: 18,
                fontSize: 24,
                lineHeight: 1.5,
                color: INDIGO_SOFT,
              }}
            >
              First make the requirements less dumb. Then try deleting the
              module outright. Rewrite only when the patches stop teaching you
              anything.
            </div>
            <div
              style={{
                display: "flex",
                marginTop: "auto",
                fontSize: 18,
                color: "#818cf8",
              }}
            >
              836 atoms · cited · SXSW 2013
            </div>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginTop: 32,
            fontSize: 21,
          }}
        >
          <div style={{ display: "flex", color: "#e2e8f0" }}>
            Free in beta — drop a zip into Claude Code, Cursor, or any agent.
          </div>
          <div style={{ display: "flex", color: INDIGO_SOFT }}>
            brainsforagents.com
          </div>
        </div>
      </div>
    ),
    { ...size },
  );
}
