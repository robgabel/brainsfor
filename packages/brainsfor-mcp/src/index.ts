#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { resolveBrainsDir } from "./loaders/index-loader.js";
import { registerListBrains } from "./tools/list-brains.js";
import { registerGetSynthesis } from "./tools/get-synthesis.js";
import { registerQueryAtoms } from "./tools/query-atoms.js";
import { registerSearchAtoms } from "./tools/search-atoms.js";
import { registerGetConnections } from "./tools/get-connections.js";
import { registerGetAtom } from "./tools/get-atom.js";

const server = new McpServer({
  name: "brainsfor",
  version: "0.1.0",
});

const brainsDir = resolveBrainsDir();
console.error(`[brainsfor-mcp] Brains directory: ${brainsDir}`);

// Register all tools
registerListBrains(server, brainsDir);
registerGetSynthesis(server, brainsDir);
registerQueryAtoms(server, brainsDir);
registerSearchAtoms(server, brainsDir);
registerGetConnections(server, brainsDir);
registerGetAtom(server, brainsDir);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[brainsfor-mcp] Server running via stdio");
}

main().catch((error) => {
  console.error("[brainsfor-mcp] Fatal error:", error);
  process.exit(1);
});

process.on("SIGINT", async () => {
  await server.close();
  process.exit(0);
});
