import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  Battery,
  Bell,
  Loader2,
  RefreshCw,
  Shield,
  Wifi,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type RingDevice } from "@/lib/api";

function useStatus() {
  return useQuery({
    queryKey: ["ring-status"],
    queryFn: () => api.getStatus(),
    refetchInterval: 30_000,
  });
}

function useDevices() {
  return useQuery({
    queryKey: ["ring-devices"],
    queryFn: () => api.getDevices(false),
    refetchInterval: 30_000,
  });
}

export function Status() {
  const queryClient = useQueryClient();
  const statusQuery = useStatus();
  const devicesQuery = useDevices();

  const setArmMutation = useMutation({
    mutationFn: ({ deviceId, status }: { deviceId: string; status: boolean }) =>
      api.setArmStatus(deviceId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ring-status"] });
      queryClient.invalidateQueries({ queryKey: ["ring-devices"] });
    },
  });

  const chimeMutation = useMutation({
    mutationFn: (deviceId: string) => api.triggerChime(deviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ring-devices"] });
    },
  });

  const refetch = () => {
    statusQuery.refetch();
    devicesQuery.refetch();
  };

  const status = statusQuery.data?.status;
  const devices = devicesQuery.data?.devices ?? [];
  const isLoading = statusQuery.isLoading || devicesQuery.isLoading;
  const statusError = statusQuery.error;
  const devicesError = devicesQuery.error;
  const noAuth =
    (statusQuery.data && statusQuery.data.success === false) ||
    (devicesQuery.data && devicesQuery.data.success === false);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Security Status
          </h2>
          <p className="text-slate-400">
            Ring devices and system status from API
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="border-slate-800 text-slate-300 hover:bg-slate-800"
          onClick={refetch}
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

      {(statusError || devicesError) && (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="pt-4">
            <p className="text-red-400 text-sm">
              {statusError instanceof Error
                ? statusError.message
                : devicesError instanceof Error
                  ? devicesError.message
                  : "Failed to load. Configure Ring credentials in Settings and ensure the backend is running (web_sota\\start.ps1)."}
            </p>
          </CardContent>
        </Card>
      )}

      {noAuth && !statusQuery.data?.success && !devicesQuery.data?.success && (
        <Card className="border-amber-900/50 bg-amber-950/20">
          <CardContent className="pt-4">
            <p className="text-amber-400 text-sm">
              Not authenticated. Add your Ring email and password in Settings,
              then click &quot;Save Ring credentials&quot;.
            </p>
          </CardContent>
        </Card>
      )}

      {status && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                Total devices
              </CardTitle>
              <Shield className="h-4 w-4 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {status.total_devices}
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                Online
              </CardTitle>
              <Wifi className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {status.online_devices}
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                Doorbells
              </CardTitle>
              <Bell className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {status.doorbells}
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                Cameras
              </CardTitle>
              <Activity className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {status.cameras}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Devices</CardTitle>
          {devices.length === 0 && !isLoading && (
            <p className="text-slate-400 text-sm">
              No devices. Configure Ring in Settings and refresh.
            </p>
          )}
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="flex items-center gap-2 text-slate-400">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading devices…
            </div>
          )}
          {!isLoading && devices.length > 0 && (
            <div className="space-y-4">
              {devices.map((d) => (
                <DeviceRow
                  key={d.id}
                  device={d}
                  onArm={(status) =>
                    setArmMutation.mutate({ deviceId: d.id, status })
                  }
                  onChime={() => chimeMutation.mutate(d.id)}
                  armLoading={setArmMutation.isPending}
                  chimeLoading={chimeMutation.isPending}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DeviceRow({
  device,
  onArm,
  onChime,
  armLoading,
  chimeLoading,
}: {
  device: RingDevice;
  onArm: (status: boolean) => void;
  onChime: () => void;
  armLoading: boolean;
  chimeLoading: boolean;
}) {
  const online = device.online ?? false;
  const type = (device.type ?? "").toLowerCase();
  const isAlarm = type === "alarm" || type.includes("alarm");
  const isDoorbell = type === "doorbell" || type.includes("doorbell");

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3 last:border-0 last:pb-0">
      <div className="flex items-center gap-3">
        <span className="font-medium text-white">{device.name}</span>
        <span
          className={
            online ? "text-emerald-500 text-sm" : "text-slate-500 text-sm"
          }
        >
          {online ? "ONLINE" : "OFFLINE"}
        </span>
        {device.battery_life != null && (
          <span className="flex items-center gap-1 text-slate-400 text-sm">
            <Battery className="h-3 w-3" />
            {device.battery_life}%
          </span>
        )}
      </div>
      <div className="flex items-center gap-2">
        {isAlarm && (
          <Button
            variant="outline"
            size="sm"
            className="border-slate-800 text-slate-300 hover:bg-slate-800"
            onClick={() => onArm(true)}
            disabled={armLoading}
          >
            Arm
          </Button>
        )}
        {isAlarm && (
          <Button
            variant="outline"
            size="sm"
            className="border-slate-800 text-slate-300 hover:bg-slate-800"
            onClick={() => onArm(false)}
            disabled={armLoading}
          >
            Disarm
          </Button>
        )}
        {isDoorbell && (
          <Button
            variant="outline"
            size="sm"
            className="border-slate-800 text-slate-300 hover:bg-slate-800"
            onClick={onChime}
            disabled={chimeLoading}
          >
            Chime
          </Button>
        )}
      </div>
    </div>
  );
}
