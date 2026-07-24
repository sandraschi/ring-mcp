import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type RingDevice, api } from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, RefreshCw, Shield, ShieldOff } from "lucide-react";

function useDevices() {
  return useQuery({
    queryKey: ["ring-devices"],
    queryFn: () => api.getDevices(false),
    refetchInterval: 30_000,
  });
}

function isAlarm(d: RingDevice): boolean {
  const t = (d.type ?? "").toLowerCase();
  return t === "alarm" || t.includes("alarm") || t === "security_system";
}

export function Alarms() {
  const queryClient = useQueryClient();
  const { data: devicesData, isLoading, error, refetch } = useDevices();
  const setArmMutation = useMutation({
    mutationFn: ({
      deviceId,
      status,
      mode,
    }: {
      deviceId: string;
      status?: boolean;
      mode?: "disarm" | "arm_home" | "arm_away";
    }) => {
      if (mode) return api.setArmMode(deviceId, mode);
      if (typeof status === "boolean")
        return api.setArmStatus(deviceId, status);
      return Promise.reject(new Error("Missing arm command"));
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ring-devices"] });
    },
  });

  const devices = (devicesData?.devices ?? []).filter(isAlarm);

  return (
    <div className="space-y-6" data-testid="alarms-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Ring Alarm
          </h2>
          <p className="text-slate-400">
            Base station / burglar alarm via{" "}
            <span className="text-slate-300">ring-mqtt</span> (MQTT) or legacy
            Ring API when available
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="border-slate-800 text-slate-300 hover:bg-slate-800"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          <span className="ml-2">Refresh</span>
        </Button>
      </div>

      {error && (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="pt-4">
            <p className="text-red-400 text-sm">
              {error instanceof Error
                ? error.message
                : "Failed to load devices. Configure Ring in Settings."}
            </p>
          </CardContent>
        </Card>
      )}

      {!error && devices.length === 0 && !isLoading && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardContent className="pt-6 space-y-3">
            <p className="text-slate-400">
              To control the Ring Alarm{" "}
              <span className="text-slate-300">base station</span> here, run{" "}
              <a
                className="text-sky-400 hover:underline"
                href="https://github.com/tsightler/ring-mqtt/wiki"
                target="_blank"
                rel="noreferrer"
              >
                ring-mqtt
              </a>{" "}
              (Docker or Home Assistant add-on) against an MQTT broker, then set
              on the Ring MCP server:{" "}
              <span className="font-mono text-slate-300">
                RING_MQTT_ENABLED=1
              </span>
              , <span className="font-mono text-slate-300">RING_MQTT_URL</span>{" "}
              (e.g. mqtt://127.0.0.1:1883), optional username/password, and{" "}
              <span className="font-mono text-slate-300">
                RING_MQTT_TOPIC_PREFIX
              </span>{" "}
              if you changed the default{" "}
              <span className="font-mono text-slate-300">ring</span> prefix.
              Restart Ring MCP; alarm panels appear after ring-mqtt publishes
              state topics. Doorbells and cameras still use Ring credentials on
              the other pages.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {devices.map((device) => (
          <Card key={device.id} className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-white text-base">
                {device.name}
              </CardTitle>
              {device.online ? (
                <span className="text-emerald-500 text-xs" data-testid="alarm-status">Online</span>
              ) : (
                <span className="text-slate-500 text-xs" data-testid="alarm-status">Offline</span>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              {device.model && (
                <p className="text-slate-400 text-sm">{device.model}</p>
              )}
              {device.mqtt_state && (
                <p className="text-slate-500 text-xs font-mono">
                  State: {device.mqtt_state}
                </p>
              )}
              {device.source === "ring_mqtt" ? (
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-emerald-400"
                    onClick={() =>
                      setArmMutation.mutate({
                        deviceId: device.id,
                        mode: "arm_away",
                      })
                    }
                    disabled={setArmMutation.isPending || !device.online}
                  >
                    {setArmMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <Shield className="h-4 w-4 mr-1" />
                        Away
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-teal-400"
                    onClick={() =>
                      setArmMutation.mutate({
                        deviceId: device.id,
                        mode: "arm_home",
                      })
                    }
                    disabled={setArmMutation.isPending || !device.online}
                  >
                    {setArmMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <Shield className="h-4 w-4 mr-1" />
                        Home
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-amber-400"
                    onClick={() =>
                      setArmMutation.mutate({
                        deviceId: device.id,
                        mode: "disarm",
                      })
                    }
                    disabled={setArmMutation.isPending || !device.online}
                  >
                    {setArmMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <ShieldOff className="h-4 w-4 mr-1" />
                        Disarm
                      </>
                    )}
                  </Button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-emerald-400"
                    onClick={() =>
                      setArmMutation.mutate({
                        deviceId: device.id,
                        status: true,
                      })
                    }
                    disabled={setArmMutation.isPending || !device.online}
                  >
                    {setArmMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <Shield className="h-4 w-4 mr-1" />
                        Arm
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-amber-400"
                    onClick={() =>
                      setArmMutation.mutate({
                        deviceId: device.id,
                        status: false,
                      })
                    }
                    disabled={setArmMutation.isPending || !device.online}
                  >
                    {setArmMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <ShieldOff className="h-4 w-4 mr-1" />
                        Disarm
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
