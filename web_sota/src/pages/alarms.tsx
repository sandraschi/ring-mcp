import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Shield, ShieldOff, Loader2, RefreshCw } from "lucide-react";
import { api, type RingDevice } from "@/lib/api";

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
    mutationFn: ({ deviceId, status }: { deviceId: string; status: boolean }) =>
      api.setArmStatus(deviceId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ring-devices"] });
    },
  });

  const devices = (devicesData?.devices ?? []).filter(isAlarm);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Ring Alarm</h2>
          <p className="text-slate-400">Arm and disarm your Ring security systems</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="border-slate-800 text-slate-300 hover:bg-slate-800"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          <span className="ml-2">Refresh</span>
        </Button>
      </div>

      {error && (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="pt-4">
            <p className="text-red-400 text-sm">
              {error instanceof Error ? error.message : "Failed to load devices. Configure Ring in Settings."}
            </p>
          </CardContent>
        </Card>
      )}

      {!error && devices.length === 0 && !isLoading && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardContent className="pt-6">
            <p className="text-slate-400">No Ring alarm devices found. Add a Ring Alarm base station and sensors in the Ring app.</p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {devices.map((device) => (
          <Card key={device.id} className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-white text-base">{device.name}</CardTitle>
              {device.online ? (
                <span className="text-emerald-500 text-xs">Online</span>
              ) : (
                <span className="text-slate-500 text-xs">Offline</span>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              {device.model && (
                <p className="text-slate-400 text-sm">{device.model}</p>
              )}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1 border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-emerald-400"
                  onClick={() => setArmMutation.mutate({ deviceId: device.id, status: true })}
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
                  onClick={() => setArmMutation.mutate({ deviceId: device.id, status: false })}
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
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
