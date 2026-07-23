import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type RingDevice, api } from "@/lib/api";
import {
  Activity,
  CheckCircle,
  Loader2,
  Settings,
  Shield,
  Video,
  Wrench,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";

interface ToolCard {
  name: string;
  icon: typeof Video | typeof Shield | typeof Settings;
  iconColor: string;
  description: string;
  endpoint: string;
}

const toolDefs: ToolCard[] = [
  {
    name: "Video Proxy",
    icon: Video,
    iconColor: "text-emerald-500",
    description: "Stream snapshots and live video threads",
    endpoint: "/api/v1/health",
  },
  {
    name: "Security Control",
    icon: Shield,
    iconColor: "text-blue-500",
    description: "Arm/disarm and motion management",
    endpoint: "/api/v1/status",
  },
  {
    name: "Device Config",
    icon: Settings,
    iconColor: "text-purple-500",
    description: "Manage doorbell chimes and alerts",
    endpoint: "/api/v1/devices",
  },
];

export function Tools() {
  const [devices, setDevices] = useState<RingDevice[]>([]);
  const [health, setHealth] = useState<{ api: boolean; mqtt: boolean } | null>(
    null,
  );
  const [status, setStatus] = useState<{
    total: number;
    online: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [h, devResp, st] = await Promise.all([
          api.getHealth(),
          api.getDevices(),
          api.getStatus(),
        ]);
        setHealth({
          api: h.health_status?.api_connected ?? false,
          mqtt: h.health_status?.ring_mqtt?.connected ?? false,
        });
        setDevices(devResp.devices || []);
        setStatus({
          total: st.status?.total_devices ?? devResp.devices?.length ?? 0,
          online:
            st.status?.online_devices ??
            devResp.devices?.filter((d: RingDevice) => d.online).length ??
            0,
        });
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Tool Inventory
        </h2>
        <div className="flex items-center gap-2 text-slate-400">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading Ring MCP data…
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Tool Inventory
          </h2>
          <p className="text-slate-400">
            {error
              ? "MCP server unreachable"
              : `${devices.length} devices · ${status?.online ?? 0} online`}
          </p>
        </div>
      </div>

      {error && (
        <Card className="border-red-800 bg-red-950/20">
          <CardContent className="p-4 text-sm text-red-400">
            {error}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {toolDefs.map((tool) => {
          const Icon = tool.icon;
          return (
            <Card key={tool.name} className="border-slate-800 bg-slate-950/50">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-200">
                  {tool.name}
                </CardTitle>
                <Icon className={`h-4 w-4 ${tool.iconColor}`} />
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-400">{tool.description}</p>
                <div className="mt-2 flex items-center gap-1 text-xs">
                  {health ? (
                    <>
                      <CheckCircle className="h-3 w-3 text-green-500" />{" "}
                      <span className="text-green-400">API reachable</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-3 w-3 text-red-500" />{" "}
                      <span className="text-red-400">Offline</span>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {devices.length > 0 && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Wrench className="h-4 w-4 text-slate-400" />
              Registered tools ({devices.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {devices.map((d) => (
                <div
                  key={d.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50 border border-slate-800"
                >
                  <div className="flex items-center gap-3">
                    <Activity
                      className={`h-4 w-4 ${d.online ? "text-green-500" : "text-slate-600"}`}
                    />
                    <span className="text-sm font-medium text-slate-200">
                      {d.name}
                    </span>
                    <span className="text-xs text-slate-500">
                      {d.type}
                      {d.family ? ` (${d.family})` : ""}
                    </span>
                  </div>
                  <span
                    className={`text-xs font-mono ${d.online ? "text-green-400" : "text-slate-500"}`}
                  >
                    {d.online ? "online" : "offline"}
                    {d.battery_life != null ? ` · ${d.battery_life}%` : ""}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {!error && devices.length === 0 && (
        <Card className="border-slate-800 bg-slate-950/50 border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-10 text-center">
            <Wrench className="h-10 w-10 text-slate-700 mb-4" />
            <h3 className="text-lg font-medium text-slate-300">
              API connected, no devices
            </h3>
            <p className="text-sm text-slate-500 max-w-sm">
              Ring devices will appear here once discovered by the backend.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
