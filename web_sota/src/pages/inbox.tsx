import { useQuery } from "@tanstack/react-query";
import { Bell, CheckCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, type RingEvent } from "@/lib/api";

const DISMISSED_KEY = "ring-inbox-dismissed";
const PAGE_SIZE = 20;

function readDismissed(): Set<string> {
  try {
    const raw = JSON.parse(localStorage.getItem(DISMISSED_KEY) || "[]");
    return new Set(
      Array.isArray(raw) ? raw.filter((x) => typeof x === "string") : [],
    );
  } catch {
    return new Set();
  }
}

export function Inbox() {
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState("all");
  const [newestFirst, setNewestFirst] = useState(true);
  const [page, setPage] = useState(1);
  const [dismissed, setDismissed] = useState<Set<string>>(readDismissed);

  const eventsQuery = useQuery({
    queryKey: ["ring-inbox"],
    queryFn: () => api.getEventsRecent(200),
    refetchInterval: 15_000,
  });

  const kinds = useMemo(() => {
    const set = new Set<string>();
    for (const e of eventsQuery.data?.events ?? []) {
      if (e.kind) set.add(e.kind);
    }
    return ["all", ...[...set].sort()];
  }, [eventsQuery.data]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = (eventsQuery.data?.events ?? []).filter((e: RingEvent) => {
      const id = e.id ?? `${e.device_id}-${e.created_at}`;
      if (dismissed.has(id)) return false;
      if (kind !== "all" && e.kind !== kind) return false;
      if (
        q &&
        !`${e.device_name ?? ""} ${e.kind ?? ""} ${e.created_at ?? ""}`
          .toLowerCase()
          .includes(q)
      ) {
        return false;
      }
      return true;
    });
    list.sort((a, b) =>
      newestFirst
        ? (b.created_at ?? "").localeCompare(a.created_at ?? "")
        : (a.created_at ?? "").localeCompare(b.created_at ?? ""),
    );
    return list;
  }, [eventsQuery.data, dismissed, kind, newestFirst, query]);

  const total = (eventsQuery.data?.events ?? []).length;
  const pages = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const safePage = Math.min(page, pages);
  const pageItems = visible.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE,
  );

  const dismiss = (id: string) => {
    setDismissed((prev) => {
      const next = new Set(prev);
      next.add(id);
      try {
        localStorage.setItem(DISMISSED_KEY, JSON.stringify([...next]));
      } catch {
        /* private mode */
      }
      return next;
    });
  };

  return (
    <div className="space-y-6" data-testid="inbox-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Inbox
          </h2>
          <p className="text-slate-400" data-testid="inbox-summary">
            {visible.length} of {total} events
            {eventsQuery.isError ? " (feed unreachable - showing cached)" : ""}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="grid gap-1">
          <Label className="text-slate-300" htmlFor="inbox-search">
            Search
          </Label>
          <Input
            id="inbox-search"
            data-testid="inbox-search"
            className="h-9 w-56 border-slate-700 bg-slate-900 text-slate-200"
            placeholder="Device, kind, time…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="grid gap-1">
          <Label className="text-slate-300" htmlFor="inbox-kind">
            Kind
          </Label>
          <select
            id="inbox-kind"
            data-testid="inbox-kind"
            className="h-9 rounded-md border border-slate-700 bg-slate-900 px-2 text-sm text-slate-200"
            value={kind}
            onChange={(e) => {
              setKind(e.target.value);
              setPage(1);
            }}
          >
            {kinds.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
        </div>
        <div className="grid gap-1">
          <Label className="text-slate-300" htmlFor="inbox-sort">
            Sort
          </Label>
          <select
            id="inbox-sort"
            data-testid="inbox-sort"
            className="h-9 rounded-md border border-slate-700 bg-slate-900 px-2 text-sm text-slate-200"
            value={newestFirst ? "new" : "old"}
            onChange={(e) => {
              setNewestFirst(e.target.value === "new");
              setPage(1);
            }}
          >
            <option value="new">Newest first</option>
            <option value="old">Oldest first</option>
          </select>
        </div>
      </div>

      {eventsQuery.isLoading ? (
        <p className="text-slate-500">Loading events…</p>
      ) : pageItems.length === 0 ? (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardContent className="pt-6">
            <p className="text-slate-400">
              No events match. Arm motion detection or ring the doorbell, then
              refresh.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2" data-testid="inbox-list">
          {pageItems.map((e) => {
            const id = e.id ?? `${e.device_id}-${e.created_at}`;
            return (
              <Card key={id} className="border-slate-800 bg-slate-950/50">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm font-medium text-slate-200">
                    <Bell className="h-4 w-4 text-slate-400" />
                    {e.device_name ?? "Unknown device"} · {e.kind ?? "event"}
                  </CardTitle>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    data-testid={`inbox-dismiss-${id}`}
                    className="border-slate-700 text-slate-300"
                    onClick={() => dismiss(id)}
                  >
                    <CheckCheck className="mr-1 h-3 w-3" /> Dismiss
                  </Button>
                </CardHeader>
                <CardContent>
                  <p className="font-mono text-xs text-slate-400">
                    {e.created_at ?? "unknown time"}
                    {e.answered ? " · answered" : ""}
                    {e.recording_status
                      ? ` · recording ${e.recording_status}`
                      : ""}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <div
        className="flex items-center gap-2 text-sm text-slate-400"
        data-testid="inbox-pager"
      >
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={safePage <= 1}
          className="border-slate-700 text-slate-200"
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Prev
        </Button>
        <span>
          Page {safePage} of {pages}
        </span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={safePage >= pages}
          className="border-slate-700 text-slate-200"
          onClick={() => setPage((p) => Math.min(pages, p + 1))}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
