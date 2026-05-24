import type { Metadata } from "next";
import { Space_Grotesk, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/Nav";
import { Footer } from "@/components/Footer";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "brainsforfree — Load a genius into your AI",
  description:
    "Knowledge graphs of the world's best thinkers, packaged as 8 AI skills you actually use. Think better in seconds.",
  openGraph: {
    title: "brainsforfree — Load a genius into your AI",
    description:
      "Knowledge graphs of the world's best thinkers, packaged as 8 AI skills you actually use.",
    siteName: "brainsforfree",
  },
  other: {
    "theme-color": "#ffffff",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${inter.variable} ${jetbrainsMono.variable} antialiased`}
    >
      <head>
        {/* Agent-discovery: well-behaved AI agents look for an alternate
            Markdown representation. Mirror at /llms.txt via next.config rewrites. */}
        <link
          rel="alternate"
          type="text/markdown"
          href="/AGENTS.md"
          title="AGENTS.md — interface for AI agents"
        />
      </head>
      <body className="bg-background text-foreground">
        <Nav />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
