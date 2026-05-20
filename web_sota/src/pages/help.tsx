import { Book, Code, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

const RING_MCP_VERSION = "1.0.3";
const FASTMCP_TARGET = "3.2+";
const WEB_PORT = "10728";
const API_PORT = "10729";

export function Help() {
  const apiBase = api.getBaseUrl();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Help & documentation
          </h2>
          <p className="text-slate-400">
            Fleet layout, ports, and how this UI talks to Ring
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Book className="h-5 w-5 text-emerald-500" />
              <CardTitle className="text-white">Getting started</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-slate-400">
            <p>
              This UI is the <span className="text-slate-200">Ring MCP</span>{" "}
              fleet console. It calls the REST API (same machine) to list
              devices, arm/disarm, chime, streams, and WebRTC signaling.
            </p>
            <p className="font-medium text-slate-300">Checklist</p>
            <ul className="list-inside list-disc space-y-1">
              <li>
                Run <code className="text-slate-200">web_sota\start.ps1</code>{" "}
                or start <code className="text-slate-200">ring-mcp-http</code>{" "}
                on port {API_PORT}.
              </li>
              <li>
                Open this app on{" "}
                <code className="text-slate-200">
                  http://127.0.0.1:{WEB_PORT}
                </code>
                .
              </li>
              <li>
                In <span className="text-slate-200">Settings</span>, save Ring
                email/password, then test connection. Invalid Ring passwords
                return <code className="text-slate-200">401</code> from Ring
                (not a UI bug).
              </li>
              <li>
                Use <span className="text-slate-200">Logger</span> for recent
                HTTP and server log lines.
              </li>
            </ul>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Code className="h-5 w-5 text-blue-500" />
              <CardTitle className="text-white">Developer notes</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-slate-400">
            <p>
              MCP stdio server: <code className="text-slate-200">ring-mcp</code>{" "}
              (Claude Desktop). HTTP API for this UI:{" "}
              <code className="text-slate-200">ring-mcp-http</code> — FastAPI +
              uvicorn, fleet default port {API_PORT}.
            </p>
            <div className="rounded border border-slate-800 bg-slate-900 p-3 font-mono text-xs text-slate-300">
              <p>Vite dev (this UI): {WEB_PORT}</p>
              <p>REST API (backend): {API_PORT}</p>
              <p>API base (browser): {apiBase}</p>
            </div>
            <p>
              Dependency target:{" "}
              <span className="text-slate-200">fastmcp &gt;= 3.2.0</span> (see
              repo <code className="text-slate-200">pyproject.toml</code>
              ).
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Info className="h-5 w-5 text-purple-500" />
            <CardTitle className="text-white">System information</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <table className="w-full text-left text-sm text-slate-400">
            <tbody className="divide-y divide-slate-800">
              <tr>
                <td className="py-2 font-medium text-slate-300">
                  Ring MCP (package)
                </td>
                <td className="py-2 font-mono text-slate-200">
                  {RING_MCP_VERSION}
                </td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-300">
                  FastMCP (target)
                </td>
                <td className="py-2 font-mono text-slate-200">
                  {FASTMCP_TARGET}
                </td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-300">
                  This UI (fleet)
                </td>
                <td className="py-2 font-mono text-slate-200">
                  http://127.0.0.1:{WEB_PORT}
                </td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-300">
                  REST API (fleet)
                </td>
                <td className="py-2 font-mono text-slate-200">
                  http://127.0.0.1:{API_PORT}
                </td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-300">
                  Configured API base
                </td>
                <td className="py-2 font-mono text-xs break-all text-slate-200">
                  {apiBase}
                </td>
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
