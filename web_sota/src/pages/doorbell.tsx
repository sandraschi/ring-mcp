import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type RingDevice, api } from "@/lib/api";
import { useRingWebRTC } from "@/lib/useRingWebRTC";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  Bell,
  Loader2,
  Mic,
  MicOff,
  PhoneOff,
  RefreshCw,
  Shield,
  Video,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

function DoorbellSnapshot({ deviceId }: { deviceId: string }) {
  const [ts, setTs] = useState(Date.now());
  const [failed, setFailed] = useState(false);
  const [showLive, setShowLive] = useState(false);
  const {
    videoRef,
    streamState,
    error: webrtcError,
    startStream,
    stopStream,
    toggleTalk,
    talkEnabled,
  } = useRingWebRTC();

  useEffect(() => {
    if (!showLive) stopStream();
  }, [showLive, stopStream]);

  const handleStartLive = async () => {
    setShowLive(true);
    await startStream(deviceId);
  };

  const handleStopLive = () => {
    stopStream();
    setShowLive(false);
  };

  return (
    <div className="space-y-2">
      {showLive ? (
        <div className="space-y-2">
          <div className="relative overflow-hidden rounded-lg border border-slate-700 bg-black">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="aspect-video w-full object-contain"
            />
            {streamState === "connecting" && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                <Loader2 className="h-8 w-8 animate-spin text-white" />
              </div>
            )}
          </div>
          {webrtcError && (
            <p className="text-xs text-red-400">{webrtcError}</p>
          )}
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant={talkEnabled ? "default" : "outline"}
              onClick={toggleTalk}
              disabled={streamState !== "streaming"}
              className="border-slate-700"
            >
              {talkEnabled ? (
                <MicOff className="mr-1 h-3 w-3" />
              ) : (
                <Mic className="mr-1 h-3 w-3" />
              )}
              {talkEnabled ? "Mute" : "Talk"}
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="border-red-800 text-red-400 hover:bg-red-950/30"
              onClick={handleStopLive}
            >
              <PhoneOff className="mr-1 h-3 w-3" />
              Close
            </Button>
          </div>
        </div>
      ) : (
        <>
          <div className="overflow-hidden rounded-lg border border-slate-700 bg-slate-900">
            {failed ? (
              <div className="flex aspect-video items-center justify-center text-sm text-slate-500">
                Snapshot unavailable
              </div>
            ) : (
              <img
                src={`${api.getBaseUrl()}/api/v1/snapshot/${deviceId}?t=${ts}`}
                alt="Doorbell snapshot"
                className="aspect-video w-full object-contain"
                onError={() => setFailed(true)}
              />
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="outline"
              className="border-slate-700 text-slate-300 hover:bg-slate-800"
              onClick={() => { setTs(Date.now()); setFailed(false); }}
            >
              <RefreshCw className="mr-1 h-3 w-3" />
              Refresh
            </Button>
            <Button
              size="sm"
              variant="default"
              onClick={handleStartLive}
            >
              <Video className="mr-1 h-3 w-3" />
              Live view
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

interface RingSummary {
  doorbells?: RingDevice[];
  recent_events?: Array<{
    device_name?: string;
    event_type?: string;
    timestamp?: string;
  }>;
  alarm_mode?: string;
}

export function Doorbell() {
  const { data: devicesData, isLoading } = useQuery({
    queryKey: ["ring-devices"],
    queryFn: () => api.getDevices(false),
  });
  const [ringEvents, setRingEvents] = useState<
    Array<{ device_name?: string; event_type?: string; timestamp?: string }>
  >([]);

  const devices = (devicesData?.devices ?? []).filter((d) => {
    const t = (d.type ?? "").toLowerCase();
    return t === "doorbell" || t.includes("doorbell") || t.includes("doorbot") || t.includes("stickup") || t === "camera";
  });

  const loadEvents = useCallback(async () => {
    try {
      const r = await fetch(`${api.getBaseUrl()}/api/v1/devices/${devices[0]?.id ?? ""}/events?limit=10`);
      if (r.ok) {
        const data = await r.json();
        setRingEvents(data.events ?? []);
      }
    } catch {}
  }, [devices]);

  useEffect(() => {
    if (devices.length > 0) loadEvents();
    const timer = setInterval(loadEvents, 15000);
    return () => clearInterval(timer);
  }, [devices, loadEvents]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-white">Doorbell & Camera</h1>
      </div>

      {isLoading ? (
        <div className="flex items-center gap-2 text-slate-400 py-8">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading devices...
        </div>
      ) : devices.length === 0 ? (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardContent className="pt-6">
            <p className="text-slate-400">No doorbells or cameras found. Configure Ring in Settings.</p>
          </CardContent>
        </Card>
      ) : (
        <>
          {devices.map((d) => (
            <Card key={d.id} className="border-slate-800 bg-slate-950/50">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white flex items-center gap-2">
                    <Bell className="h-5 w-5 text-slate-400" />
                    {d.name ?? d.id}
                  </CardTitle>
                  <span className="text-sm text-slate-400">
                    {d.online === false ? "offline" : "online"}
                    {d.battery_life != null ? ` \u00b7 ${d.battery_life}%` : ""}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <DoorbellSnapshot deviceId={d.id} />
              </CardContent>
            </Card>
          ))}

          {ringEvents.length > 0 && (
            <Card className="border-slate-800 bg-slate-950/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-white">Recent events</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1 text-sm text-slate-400">
                  {ringEvents.slice(0, 10).map((ev, i) => (
                    <li key={`${ev.timestamp}-${i}`}>
                      {ev.device_name ?? "Doorbell"} \u00b7 {ev.event_type ?? "event"}
                      {ev.timestamp ? ` \u00b7 ${new Date(ev.timestamp).toLocaleTimeString()}` : ""}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
