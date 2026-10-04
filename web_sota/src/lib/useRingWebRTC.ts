import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";

export type StreamState = "idle" | "connecting" | "streaming" | "error";

const ICE_SERVERS = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };
const KEEPALIVE_INTERVAL = 25000;

function apiUrl(path: string): string {
  return `${api.getBaseUrl()}${path}`;
}

export function useRingWebRTC() {
  const [streamState, setStreamState] = useState<StreamState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [talkEnabled, setTalkEnabled] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const keepaliveRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const deviceIdRef = useRef<string | null>(null);

  const stopStream = useCallback(async () => {
    if (keepaliveRef.current) {
      clearInterval(keepaliveRef.current);
      keepaliveRef.current = null;
    }
    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((t) => {
        t.stop();
      });
      localStreamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setTalkEnabled(false);
    if (deviceIdRef.current) {
      fetch(apiUrl(`/api/v1/webrtc/close/${deviceIdRef.current}`), {
        method: "POST",
      }).catch(() => {});
    }
    deviceIdRef.current = null;
    setStreamState("idle");
  }, []);

  const startStream = useCallback(
    async (deviceId: string) => {
      await stopStream();
      setError(null);
      setStreamState("connecting");
      deviceIdRef.current = deviceId;

      try {
        const pc = new RTCPeerConnection(ICE_SERVERS);
        pcRef.current = pc;

        pc.ontrack = (event) => {
          if (videoRef.current && event.streams[0]) {
            videoRef.current.srcObject = event.streams[0];
            setStreamState("streaming");
          }
        };

        pc.onicecandidate = async (event) => {
          if (event.candidate) {
            try {
              await fetch(apiUrl("/api/v1/webrtc/candidate"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  device_id: deviceId,
                  candidate: JSON.stringify(event.candidate),
                }),
              });
            } catch {
              /* best-effort */
            }
          }
        };

        pc.onconnectionstatechange = () => {
          if (
            pc.connectionState === "failed" ||
            pc.connectionState === "disconnected"
          ) {
            setError("WebRTC connection lost");
            setStreamState("error");
            stopStream();
          }
        };

        pc.addTransceiver("video", { direction: "recvonly" });
        pc.addTransceiver("audio", { direction: "recvonly" });

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        const res = await fetch(apiUrl("/api/v1/webrtc/offer"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            device_id: deviceId,
            sdp_offer: offer.sdp,
          }),
        });
        if (!res.ok) {
          const errBody = await res.json().catch(() => ({}));
          throw new Error(
            (errBody as { detail?: string }).detail ?? `HTTP ${res.status}`,
          );
        }
        const data = await res.json();
        await pc.setRemoteDescription(
          new RTCSessionDescription({
            type: "answer",
            sdp: data.sdp_answer,
          }),
        );

        keepaliveRef.current = setInterval(() => {
          fetch(apiUrl(`/api/v1/webrtc/keepalive/${deviceId}`), {
            method: "POST",
          }).catch(() => {});
        }, KEEPALIVE_INTERVAL);
      } catch (e) {
        setError(String(e));
        setStreamState("error");
        stopStream();
      }
    },
    [stopStream],
  );

  const toggleTalk = useCallback(async () => {
    if (talkEnabled) {
      if (pcRef.current) {
        const sender = pcRef.current
          .getSenders()
          .find((s) => s.track?.kind === "audio");
        if (sender) {
          pcRef.current.removeTrack(sender);
        }
      }
      if (localStreamRef.current) {
        localStreamRef.current.getAudioTracks().forEach((t) => {
          t.stop();
        });
        localStreamRef.current = null;
      }
      setTalkEnabled(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        localStreamRef.current = stream;
        if (pcRef.current) {
          stream.getAudioTracks().forEach((track) => {
            pcRef.current?.addTrack(track, stream);
          });
          const transceiver = pcRef.current
            .getTransceivers()
            .find((t) => t.receiver.track.kind === "audio");
          if (transceiver) {
            transceiver.direction = "sendrecv";
          }
        }
        setTalkEnabled(true);
      } catch (e) {
        setError(
          `Microphone access denied: ${e instanceof Error ? e.message : e}`,
        );
      }
    }
  }, [talkEnabled]);

  useEffect(() => {
    return () => {
      stopStream();
    };
  }, [stopStream]);

  return {
    videoRef,
    streamState,
    error,
    startStream,
    stopStream,
    toggleTalk,
    talkEnabled,
  };
}
