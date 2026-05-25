import { NextResponse, type NextRequest } from "next/server";

// Path-to-regexp matcher with a single negative lookahead at the start. Any
// path prefix listed here bypasses the password gate entirely. Public agent
// surface (AGENTS.md, llms.txt, /brains/* assets, and the live agent
// endpoints) MUST stay exempt — see public/AGENTS.md for the contract. Each
// endpoint has its own protections (rate limits, CORS, slug allowlists).
export const config = {
  matcher: [
    "/((?!_next/|favicon\\.ico|api/skill|api/board|AGENTS\\.md|llms\\.txt|brains/).*)",
  ],
};

function constantTimeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

export function middleware(req: NextRequest) {
  const expected = process.env.SITE_PASSWORD;
  if (!expected) return NextResponse.next();

  const auth = req.headers.get("authorization");
  if (auth?.startsWith("Basic ")) {
    try {
      const decoded = atob(auth.slice(6));
      const idx = decoded.indexOf(":");
      const user = idx === -1 ? decoded : decoded.slice(0, idx);
      const pass = idx === -1 ? "" : decoded.slice(idx + 1);
      if (user === "friend" && constantTimeEqual(pass, expected)) {
        return NextResponse.next();
      }
    } catch {
      // fall through to 401
    }
  }
  return new NextResponse("Authentication required", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="BrainsFor", charset="UTF-8"',
      "Content-Type": "text/plain",
    },
  });
}
