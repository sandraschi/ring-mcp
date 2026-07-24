import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type HealthResponse, type LogEntry, api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { Activity, HardDrive, KeyRound, Shield, Timer } from "lucide-react";
import { Link } from "react-router-dom";

function logLineTone(level: string): string {
  const u = level.toUpperCase();
  if (u === "ERROR" || u === "CRITICAL") return "text-red-400";
  if (u === "WARNING" || u === "WARN") return "text-amber-400";
  if (u === "INFO") return "text-slate-300";
  return "text-slate-500";
}

export function Dashboard() {
  const healthQuery = useQuery({
    queryKey: ["ring-health"],
    queryFn: async () => {
      const t0 = performance.now();
      const health = await api.getHealth();
      const healthRoundTripMs = Math.round(performance.now() - t0);
      return { health, healthRoundTripMs };
    },
    refetchInterval: 30_000,
  });

  const logsQuery = useQuery({
    queryKey: ["ring-logs-overview"],
    queryFn: () => api.getLogs(40),
    refetchInterval: 8_000,
  });

  const health = healthQuery.data?.health;
  const healthMs = healthQuery.data?.healthRoundTripMs;
  const isLoading = healthQuery.isLoading;
  const isError = healthQuery.isError;

  const backendOk = health?.success === true;
  const hs = health?.health_status;
  const deviceCount = hs?.devices_accessible ?? 0;
  const ringSignedIn = hs?.authentication_valid === true;
  const overviewLogs = (logsQuery.data?.logs ?? []).slice(-20);

  const healthMessage = (h: HealthResponse | undefined) => {
    const m = h?.message?.trim();
    if (!m) return "No message from /api/v1/health.";
    return m.length > 160 ? `${m.slice(0, 157)}…` : m;
  };

  return (
    <div className="space-y-6" data-testid="dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Ring MCP Dashboard
          </h2>
          <p className="text-slate-400">
            System overview (data from this HTTP API only)
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-backend">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Backend
            </CardTitle>
            <Shield
              data-testid="backend-dot"
              className={`h-4 w-4 ${isError ? "text-red-500" : backendOk ? "text-emerald-500" : "text-slate-500"}`}
            />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {isLoading
                ? "…"
                : isError
                  ? "Unreachable"
                  : backendOk
                    ? "Up"
                    : "Degraded"}
            </div>
            <p className="text-xs text-slate-400">
              {isError
                ? `Could not reach ${api.getBaseUrl()}`
                : backendOk
                  ? `${deviceCount} device(s) visible to Ring`
                  : (health?.message ?? "See Status card").slice(0, 80)}
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-ring-account">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Ring account
            </CardTitle>
            <KeyRound
              className={`h-4 w-4 ${ringSignedIn ? "text-emerald-500" : "text-slate-500"}`}
            />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {isLoading
                ? "…"
                : isError
                  ? "—"
                  : ringSignedIn
                    ? "Signed in"
                    : "Not signed in"}
            </div>
            <p className="text-xs text-slate-400">
              From <span className="font-mono">authentication_valid</span> on
              last health check
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-health-round-trip">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Health round-trip
            </CardTitle>
            <Timer className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {isLoading ? "…" : isError ? "—" : `${healthMs ?? "—"} ms`}
            </div>
            <p className="text-xs text-slate-400">
              Browser → GET /api/v1/health (not Ring cloud latency)
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-server-check-time">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Server check time
            </CardTitle>
            <Activity className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-white font-mono leading-tight">
              {isLoading ? "…" : isError ? "—" : (hs?.last_check ?? "—")}
            </div>
            <p className="text-xs text-slate-400">
              <span className="font-mono">last_check</span> from health JSON
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-white">Recent Logs</CardTitle>
            <Link
              to="/logger"
              className="text-xs font-medium text-sky-400 hover:text-sky-300"
            >
              Open Logger
            </Link>
          </CardHeader>
          <CardContent>
            <div className="h-[200px] font-mono text-xs p-3 overflow-y-auto border border-slate-800 rounded-md bg-slate-900/50 space-y-0.5">
              {logsQuery.isError ? (
                <p className="text-red-400">
                  Could not load logs. Check API at {api.getBaseUrl()}.
                </p>
              ) : logsQuery.isLoading ? (
                <p className="text-slate-500">Loading…</p>
              ) : overviewLogs.length === 0 ? (
                <p className="text-slate-500">
                  No log lines yet. Traffic from this API appears here (same
                  buffer as Logger).
                </p>
              ) : (
                overviewLogs.map((e: LogEntry, i: number) => (
                  <p
                    key={`${e.ts}-${i}`}
                    className={`break-all leading-snug ${logLineTone(e.level)}`}
                  >
                    {e.ts} [{e.level}] {e.message}
                  </p>
                ))
              )}
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3 border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Health summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start">
                <HardDrive className="h-4 w-4 text-slate-400 mr-2 mt-0.5 shrink-0" />
                <div className="ml-2 space-y-1 min-w-0">
                  <p className="text-sm font-medium leading-none text-white">
                    API message
                  </p>
                  <p className="text-xs text-slate-400 break-words">
                    {isLoading ? "Loading…" : healthMessage(health)}
                  </p>
                </div>
              </div>
              <div className="flex items-start">
                <Activity className="h-4 w-4 text-slate-400 mr-2 mt-0.5 shrink-0" />
                <div className="ml-2 space-y-1 min-w-0">
                  <p className="text-sm font-medium leading-none text-white">
                    stdio MCP
                  </p>
                  <p className="text-xs text-slate-400">
                    This page only talks to the HTTP API. A separate stdio MCP
                    process may still be running; it is not probed from the
                    browser.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
