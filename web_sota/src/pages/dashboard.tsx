import { useQuery } from "@tanstack/react-query";
import { Activity, HardDrive, KeyRound, Shield, Timer } from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type HealthResponse, type LogEntry } from "@/lib/api";
import { isOnboarded, MOCK_DEVICES, MOCK_KPIS } from "@/lib/mockOnboarding";

function logLineTone(level: string): string {
  const u = level.toUpperCase();
  if (u === "ERROR" || u === "CRITICAL") return "text-red-400";
  if (u === "WARNING" || u === "WARN") return "text-amber-400";
  if (u === "INFO") return "text-slate-300";
  return "text-slate-300";
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
  const onboarded =
    !isLoading && !isError && isOnboarded(hs?.authentication_valid);

  const healthMessage = (h: HealthResponse | undefined) => {
    const m = h?.message?.trim();
    if (!m) return "No message from /api/v1/health.";
    return m.length > 160 ? `${m.slice(0, 157)}â€¦` : m;
  };

  return (
    <div className="space-y-6" data-testid="dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Ring MCP Dashboard
          </h2>
          <p className="text-slate-300">
            System overview (data from this HTTP API only)
          </p>
        </div>
      </div>

      {!onboarded && !isLoading ? (
        <div className="space-y-4">
          <Link
            to="/settings"
            data-testid="onboarding-cue"
            className="block w-full rounded-lg bg-red-600 px-4 py-3 text-center text-base font-semibold text-white hover:bg-red-500"
          >
            Complete onboarding â€” connect Ring
          </Link>
          <div
            data-testid="mock-data-banner"
            className="rounded-lg border border-dashed border-rose-700 bg-rose-950/20 px-4 py-2 text-sm text-rose-200"
          >
            Sample data below is mocked (connect Ring in Settings to clear it).
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {MOCK_KPIS.map((kpi) => (
              <Card
                key={kpi.testid}
                data-testid={kpi.testid}
                className="border-dashed border-rose-700 bg-slate-950/50"
              >
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-200">
                    {kpi.label}
                  </CardTitle>
                  <span
                    data-testid="mock-badge"
                    className="rounded bg-rose-900 px-1.5 py-0.5 text-sm font-bold text-rose-100"
                  >
                    MOCK
                  </span>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">
                    {kpi.value}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {MOCK_DEVICES.map((d) => (
              <Card
                key={d.id}
                data-testid={`mock-device-${d.id}`}
                className="border-dashed border-rose-700 bg-slate-950/50"
              >
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-200">
                    {d.name}
                  </CardTitle>
                  <span
                    data-testid="mock-badge"
                    className="rounded bg-rose-900 px-1.5 py-0.5 text-sm font-bold text-rose-100"
                  >
                    MOCK
                  </span>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-300">
                    {d.type} Â· {d.online ? "Online" : "Offline"}
                    {d.battery !== null ? ` Â· ${d.battery}%` : ""}
                  </p>
                  <p className="mt-1 text-sm text-slate-300">{d.note}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-backend"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Backend
            </CardTitle>
            <Shield
              data-testid="backend-dot"
              className={`h-4 w-4 ${isError ? "text-red-500" : backendOk ? "text-emerald-500" : "text-slate-300"}`}
            />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {isLoading
                ? "â€¦"
                : isError
                  ? "Unreachable"
                  : backendOk
                    ? "Up"
                    : "Degraded"}
            </div>
            <p className="text-sm text-slate-300">
              {isError
                ? `Could not reach ${api.getBaseUrl()}`
                : backendOk
                  ? `${deviceCount} device(s) visible to Ring`
                  : (health?.message ?? "See Status card").slice(0, 80)}
            </p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-ring-account"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Ring account
            </CardTitle>
            <KeyRound
              className={`h-4 w-4 ${ringSignedIn ? "text-emerald-500" : "text-slate-300"}`}
            />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {isLoading
                ? "â€¦"
                : isError
                  ? "â€”"
                  : ringSignedIn
                    ? "Signed in"
                    : "Not signed in"}
            </div>
            <p className="text-sm text-slate-300">
              From <span className="font-mono">authentication_valid</span> on
              last health check
            </p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-health-round-trip"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Health round-trip
            </CardTitle>
            <Timer className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {isLoading ? "â€¦" : isError ? "â€”" : `${healthMs ?? "â€”"} ms`}
            </div>
            <p className="text-sm text-slate-300">
              Browser â†’ GET /api/v1/health (not Ring cloud latency)
            </p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-server-check-time"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Server check time
            </CardTitle>
            <Activity className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-white font-mono leading-tight">
              {isLoading ? "â€¦" : isError ? "â€”" : (hs?.last_check ?? "â€”")}
            </div>
            <p className="text-sm text-slate-300">
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
              className="text-sm font-medium text-sky-400 hover:text-sky-300"
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
                <p className="text-slate-300">Loadingâ€¦</p>
              ) : overviewLogs.length === 0 ? (
                <p className="text-slate-300">
                  No log lines yet. Traffic from this API appears here (same
                  buffer as Logger).
                </p>
              ) : (
                overviewLogs.map((e: LogEntry) => (
                  <p
                    key={`${e.ts}-${e.level}-${e.message}`}
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
                <HardDrive className="h-4 w-4 text-slate-300 mr-2 mt-0.5 shrink-0" />
                <div className="ml-2 space-y-1 min-w-0">
                  <p className="text-sm font-medium leading-none text-white">
                    API message
                  </p>
                  <p className="text-sm text-slate-300 break-words">
                    {isLoading ? "Loadingâ€¦" : healthMessage(health)}
                  </p>
                </div>
              </div>
              <div className="flex items-start">
                <Activity className="h-4 w-4 text-slate-300 mr-2 mt-0.5 shrink-0" />
                <div className="ml-2 space-y-1 min-w-0">
                  <p className="text-sm font-medium leading-none text-white">
                    stdio MCP
                  </p>
                  <p className="text-sm text-slate-300">
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
