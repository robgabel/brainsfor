import { ImageResponse } from "next/og";
import { SITE } from "@/lib/site-config";

// The share card IS the side-by-side — beta users arrive from X/HN/Discord
// links, so the delta has to be visible before the click. Statically
// generated at build time (no request-time APIs used).

// Card content mirrors the hero's autoplay default (HERO_LANES[0].entries[0]
// in lib/hero-demos.ts) — keep the two in sync when the default lane changes.
export const alt =
  "Same prompt, two answers: Claude alone hedges; Claude with Dario Amodei's brain loaded answers in his frameworks, with cited sources.";
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
            {SITE.name}
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
          &gt; Will AI agents replace me as a developer?
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
              AI will automate some coding tasks, but full replacement is
              unlikely in the near term. Roles will evolve toward
              architecture and review. Staying current will help&hellip;
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
              Claude + 🧪 Dario Amodei&rsquo;s brain
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
              Engineers inside Anthropic tell me they don&rsquo;t write code
              anymore — the model writes it, they direct and edit. Replaced,
              no. Transformed, faster than you&rsquo;re planning for.
            </div>
            <div
              style={{
                display: "flex",
                marginTop: "auto",
                fontSize: 18,
                color: "#818cf8",
              }}
            >
              1,000 atoms · cited · Lex Fridman #490
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
            {SITE.origin.replace('https://', '')}
          </div>
        </div>
      </div>
    ),
    { ...size },
  );
}
