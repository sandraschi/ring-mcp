import { useQuery } from "@tanstack/react-query";
import { Pause, Play, RefreshCw, ScrollText } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";

export function Logger() {
  const [paused, setPaused] = useState(false);
  const logsQuery = useQuery({
    queryKey: ["ring-logs"],
    queryFn: () => api.getLogs(300),
    refetchInterval: paused ? false : 2000,
  });

  const entries = logsQuery.data?.logs ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Server log
          </h2>
          <p className="text-slate-400">
            Recent HTTP and Ring MCP lines from the API process (in-memory
            buffer, max ~500 lines).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="border-slate-700 text-slate-200"
            onClick={() => setPaused((p) => !p)}
          >
            {paused ? (
              <>
                <Play className="mr-2 h-4 w-4" /> Resume
              </>
            ) : (
              <>
                <Pause className="mr-2 h-4 w-4" /> Pause
              </>
            )}
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="border-slate-700 text-slate-200"
            onClick={() => logsQuery.refetch()}
            disabled={logsQuery.isFetching}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${logsQuery.isFetching ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
        </div>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="flex items-center gap-2">
            <ScrollText className="h-5 w-5 text-amber-500" />
            <CardTitle className="text-white">Live tail</CardTitle>
          </div>
          <span className="text-xs text-slate-500">{entries.length} lines</span>
        </CardHeader>
        <CardContent>
          {logsQuery.isError ? (
            <p className="text-sm text-red-400">
              Could not load logs. Is the API running at {api.getBaseUrl()}?
            </p>
          ) : (
            <ScrollArea className="h-[min(70vh,520px)] w-full rounded-md border border-slate-800 bg-slate-900/40 p-3">
              <pre className="font-mono text-xs leading-relaxed text-slate-300 whitespace-pre-wrap break-all">
                {entries.length === 0
                  ? logsQuery.isLoading
                    ? "Loading…"
                    : "No log lines yet. Use the app or Settings to generate traffic."
                  : entries
                      .map((e) => `${e.ts} [${e.level}] ${e.message}`)
                      .join("\n")}
              </pre>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
