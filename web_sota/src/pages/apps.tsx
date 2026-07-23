import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Box, ExternalLink, Grid, Loader2, Wifi, WifiOff } from "lucide-react";
import { useEffect, useState } from "react";

interface AppEntry {
  name: string;
  port: number;
  description: string;
  healthPath: string;
}

const apps: AppEntry[] = [
  {
    name: "Ring MCP",
    port: 10729,
    description: "Doorbell & security monitoring",
    healthPath: "/api/v1/health",
  },
  {
    name: "SDR MCP",
    port: 10886,
    description: "Radio frequency analysis",
    healthPath: "/api/v1/health",
  },
  {
    name: "Reversing MCP",
    port: 10888,
    description: "Binary instrumentation hub",
    healthPath: "/api/v1/health",
  },
  {
    name: "Obsidian MCP",
    port: 10892,
    description: "Knowledge base bridge",
    healthPath: "/api/v1/health",
  },
];

export function Apps() {
  const [statuses, setStatuses] = useState<Record<string, boolean | null>>({});
  const [scanning, setScanning] = useState(true);

  const scan = async () => {
    setScanning(true);
    const results: Record<string, boolean | null> = {};
    await Promise.allSettled(
      apps.map(async (app) => {
        try {
          const r = await fetch(
            `http://127.0.0.1:${app.port}${app.healthPath}`,
            { signal: AbortSignal.timeout(3000) },
          );
          results[app.name] = r.ok;
        } catch {
          results[app.name] = false;
        }
      }),
    );
    setStatuses(results);
    setScanning(false);
  };

  useEffect(() => {
    scan();
    const interval = setInterval(scan, 30000);
    return () => clearInterval(interval);
  }, []);

  const onlineCount = Object.values(statuses).filter(Boolean).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            App Hub
          </h2>
          <p className="text-slate-400">
            {scanning ? "Scanning…" : `${onlineCount}/${apps.length} online`}
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {apps.map((app) => {
          const status = statuses[app.name];
          const online = status === true;
          const checking = status === undefined || scanning;
          return (
            <Card
              key={app.name}
              className={`border-slate-800 bg-slate-950/50 hover:bg-slate-900/50 transition-colors group ${online ? "cursor-pointer" : "opacity-60"}`}
              onClick={() =>
                online && window.open(`http://localhost:${app.port}`, "_blank")
              }
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-200">
                  {app.name}
                </CardTitle>
                <div className="flex items-center gap-2">
                  {checking ? (
                    <Loader2 className="h-4 w-4 text-slate-500 animate-spin" />
                  ) : online ? (
                    <Wifi className="h-4 w-4 text-green-500" />
                  ) : (
                    <WifiOff className="h-4 w-4 text-red-500" />
                  )}
                  <Box
                    className={`h-4 w-4 ${online ? "text-blue-500 group-hover:scale-110 transition-transform" : "text-slate-600"}`}
                  />
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-400 mb-4">{app.description}</p>
                <div className="flex items-center text-xs font-medium">
                  {online ? (
                    <span className="text-green-400">
                      localhost:{app.port}{" "}
                      <ExternalLink className="h-3 w-3 ml-1 inline" />
                    </span>
                  ) : (
                    <span className="text-slate-500">
                      localhost:{app.port} — offline
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="border-slate-800 bg-slate-950/50 border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-8 text-center">
          <Grid className="h-8 w-8 text-slate-700 mb-3" />
          <h3 className="text-sm font-medium text-slate-300">
            Auto-refresh every 30s
          </h3>
          <p className="text-xs text-slate-500 max-w-sm">
            Ports are probed via HTTP health checks. Green = reachable, red = no
            response.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
