import { useState, useCallback, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Video, Mic, MicOff, Loader2, ExternalLink } from "lucide-react";
import { api, type RingDevice } from "@/lib/api";

function useDevices() {
  return useQuery({
    queryKey: ["ring-devices"],
    queryFn: () => api.getDevices(false),
  });
}

function isDoorbellOrCamera(d: RingDevice): boolean {
  const t = (d.type ?? "").toLowerCase();
  return t === "doorbell" || t === "camera" || t.includes("doorbell") || t.includes("camera");
}

export function Doorbell() {
  const { data: devicesData, isLoading, error } = useDevices();
  const [selectedId, setSelectedId] = useState<string>("");
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [streamLoading, setStreamLoading] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [intercomActive, setIntercomActive] = useState(false);
  const [intercomError, setIntercomError] = useState<string | null>(null);
  const [webrtcConnecting, setWebrtcConnecting] = useState(false);
  const [webrtcError, setWebrtcError] = useState<string | null>(null);
  const [webrtcActive, setWebrtcActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);

  const devices = (devicesData?.devices ?? []).filter(isDoorbellOrCamera);
  const selected = devices.find((d) => d.id === selectedId);

  const stopWebRtc = useCallback(() => {
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {
        /* ignore */
      }
      wsRef.current = null;
    }
    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }
    setWebrtcActive(false);
    setWebrtcConnecting(false);
  }, []);

  useEffect(() => {
    return () => {
      stopWebRtc();
    };
  }, [stopWebRtc]);

  const startWebRtc = useCallback(async () => {
    if (!selectedId) return;
    stopWebRtc();
    setWebrtcError(null);
    setWebrtcConnecting(true);
    const wsUrl = api.getWebRtcWsUrl(selectedId);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    });
    pcRef.current = pc;

    pc.ontrack = (ev) => {
      const v = videoRef.current;
      if (v && ev.streams?.[0]) {
        v.srcObject = ev.streams[0];
        setWebrtcActive(true);
        setWebrtcConnecting(false);
      }
    };
    pc.onicecandidate = (ev) => {
      if (ev.candidate) {
        ws.send(JSON.stringify({ type: "ice", candidate: ev.candidate.candidate, mlineindex: ev.candidate.sdpMLineIndex }));
      }
    };
    pc.onconnectionstatechange = () => {
      if (pc.connectionState === "failed" || pc.connectionState === "disconnected" || pc.connectionState === "closed") {
        setWebrtcError(`Connection ${pc.connectionState}`);
        setWebrtcActive(false);
        setWebrtcConnecting(false);
      }
    };

    ws.onerror = () => {
      setWebrtcError("WebSocket error");
      setWebrtcConnecting(false);
    };
    ws.onclose = () => {
      setWebrtcActive(false);
      setWebrtcConnecting(false);
    };

    ws.onopen = async () => {
      try {
        pc.addTransceiver("video", { direction: "recvonly" });
        pc.addTransceiver("audio", { direction: "recvonly" });
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        ws.send(JSON.stringify({ type: "offer", sdp: offer.sdp }));
      } catch (e) {
        setWebrtcError(e instanceof Error ? e.message : "Create offer failed");
        setWebrtcConnecting(false);
      }
    };

    ws.onmessage = async (event) => {
      try {
        const msg = JSON.parse(event.data as string) as { type: string; sdp?: string; candidate?: string; mlineindex?: number; message?: string };
        if (msg.type === "error") {
          setWebrtcError(msg.message ?? "Stream error");
          setWebrtcConnecting(false);
          return;
        }
        if (msg.type === "answer" && msg.sdp) {
          await pc.setRemoteDescription(new RTCSessionDescription({ type: "answer", sdp: msg.sdp }));
          return;
        }
        if (msg.type === "ice" && msg.candidate != null) {
          await pc.addIceCandidate(new RTCIceCandidate({ candidate: msg.candidate, sdpMLineIndex: msg.mlineindex ?? 0 }));
        }
      } catch (e) {
        setWebrtcError(e instanceof Error ? e.message : "Signaling error");
        setWebrtcConnecting(false);
      }
    };
  }, [selectedId, stopWebRtc]);

  const loadStream = useCallback(async () => {
    if (!selectedId) return;
    setStreamLoading(true);
    setStreamError(null);
    setStreamUrl(null);
    try {
      const res = await api.getStreamUrl(selectedId);
      if (res.success && res.url) setStreamUrl(res.url);
      else setStreamError("No stream URL returned");
    } catch (e) {
      setStreamError(e instanceof Error ? e.message : "Failed to load stream");
    } finally {
      setStreamLoading(false);
    }
  }, [selectedId]);

  const startIntercom = useCallback(async () => {
    if (!selectedId) return;
    setIntercomError(null);
    setIntercomActive(true);
    try {
      await api.intercomStart(selectedId);
    } catch (e) {
      setIntercomError(e instanceof Error ? e.message : "Intercom start failed");
      setIntercomActive(false);
    }
  }, [selectedId]);

  const stopIntercom = useCallback(async () => {
    if (!selectedId) return;
    setIntercomActive(false);
    try {
      await api.intercomStop(selectedId);
    } catch {
      /* ignore */
    }
  }, [selectedId]);

  const isRtsp = streamUrl?.toLowerCase().startsWith("rtsp:");
  const isHttp = streamUrl?.toLowerCase().startsWith("http");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Doorbell & Camera</h2>
        <p className="text-slate-400">Live stream and two-way audio (e.g. tell delivery to leave package with neighbour)</p>
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

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Select device</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center gap-2 text-slate-400">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading devices…
            </div>
          ) : devices.length === 0 ? (
            <p className="text-slate-400">No doorbells or cameras. Configure Ring in Settings.</p>
          ) : (
            <select
              className="w-full max-w-md rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
              value={selectedId}
              onChange={(e) => {
                setSelectedId(e.target.value);
                setStreamUrl(null);
                setStreamError(null);
                setWebrtcError(null);
                stopWebRtc();
              }}
            >
              <option value="">Choose a doorbell or camera</option>
              {devices.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.type})
                </option>
              ))}
            </select>
          )}
        </CardContent>
      </Card>

      {selectedId && selected && (
        <>
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-white flex items-center gap-2">
                  <Video className="h-5 w-5" />
                  Live video (WebRTC)
                </CardTitle>
                <p className="text-slate-400 text-sm mt-1">
                  Start live view to connect via WebRTC; video appears below.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="border-slate-800 text-slate-300 hover:bg-slate-800"
                  onClick={startWebRtc}
                  disabled={webrtcConnecting || webrtcActive}
                >
                  {webrtcConnecting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Connecting…
                    </>
                  ) : webrtcActive ? (
                    "Live"
                  ) : (
                    "Start live view"
                  )}
                </Button>
                {(webrtcActive || webrtcConnecting) && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-slate-400 hover:text-white"
                    onClick={stopWebRtc}
                  >
                    Stop
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {webrtcError && (
                <p className="text-red-400 text-sm mb-2">{webrtcError}</p>
              )}
              <div className="rounded overflow-hidden bg-black max-h-[480px] flex items-center justify-center min-h-[240px] relative">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-contain"
                />
                {!webrtcActive && !webrtcConnecting && (
                  <p className="absolute text-slate-500 text-sm text-center p-4 pointer-events-none">
                    Click &quot;Start live view&quot; to see the camera.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-white">Raw stream URL</CardTitle>
              <Button
                variant="outline"
                size="sm"
                className="border-slate-800 text-slate-300 hover:bg-slate-800"
                onClick={loadStream}
                disabled={streamLoading}
              >
                {streamLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Get URL (e.g. for VLC)"}
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {streamError && <p className="text-red-400 text-sm">{streamError}</p>}
              {streamUrl && (
                <>
                  {isRtsp && (
                    <div className="space-y-2">
                      <a
                        href={streamUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 rounded-md bg-slate-800 px-3 py-2 text-sm text-emerald-400 hover:bg-slate-700"
                      >
                        <ExternalLink className="h-4 w-4" />
                        Open in VLC
                      </a>
                      <p className="text-slate-500 text-xs break-all">{streamUrl}</p>
                    </div>
                  )}
                  {isHttp && <p className="text-slate-500 text-xs break-all">{streamUrl}</p>}
                  {!isRtsp && !isHttp && <p className="text-slate-400 text-sm break-all">{streamUrl}</p>}
                </>
              )}
              {!streamUrl && !streamLoading && !streamError && (
                <p className="text-slate-500 text-sm">Click to get the raw stream URL for VLC or other players.</p>
              )}
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Mic className="h-5 w-5" />
                Two-way audio
              </CardTitle>
              <p className="text-slate-400 text-sm">
                Hold the button to talk to the visitor (e.g. tell delivery to leave package with neighbour). Release to stop.
              </p>
            </CardHeader>
            <CardContent className="space-y-3">
              {intercomError && <p className="text-red-400 text-sm">{intercomError}</p>}
              <div className="flex items-center gap-4">
                <Button
                  variant={intercomActive ? "default" : "outline"}
                  size="lg"
                  className={
                    intercomActive
                      ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                      : "border-slate-800 text-slate-300 hover:bg-slate-800"
                  }
                  onMouseDown={startIntercom}
                  onMouseUp={stopIntercom}
                  onMouseLeave={stopIntercom}
                  onTouchStart={(e) => {
                    e.preventDefault();
                    startIntercom();
                  }}
                  onTouchEnd={(e) => {
                    e.preventDefault();
                    stopIntercom();
                  }}
                >
                  {intercomActive ? (
                    <>
                      <Mic className="h-5 w-5 mr-2" />
                      Talking…
                    </>
                  ) : (
                    <>
                      <MicOff className="h-5 w-5 mr-2" />
                      Hold to talk
                    </>
                  )}
                </Button>
                <span className="text-slate-500 text-sm">
                  Two-way audio may require backend support (Ring app works for sure).
                </span>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
