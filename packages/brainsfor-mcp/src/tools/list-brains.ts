import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { getLiveBrains } from "../loaders/index-loader.js";

export function registerListBrains(server: McpServer, brainsDir: string) {
  server.registerTool(
    "list_brains",
    {
      title: "List Installed Brains",
      description:
        "List all installed BrainsFor brain packs with metadata. Returns slug, name, source, atom count, and connection count for each brain.",
      inputSchema: z.object({}).strict(),
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
      },
    },
    async () => {
      const brains = getLiveBrains(brainsDir);

      if (brains.length === 0) {
        return {
          content: [
            {
              type: "text" as const,
              text: "No brain packs installed. Install one with: npx skills add brainsfor/<slug>",
            },
          ],
        };
      }

      const summary = brains.map((b) => ({
        slug: b.slug,
        name: b.name,
        source: b.source,
        atoms: b.atom_count,
        connections: b.connection_count,
      }));

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(summary, null, 2),
          },
        ],
      };
    }
  );
}
