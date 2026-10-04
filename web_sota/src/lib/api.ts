/**
 * Ring MCP REST API client.
 * Backend: ring_mcp.http_server (uvicorn on port 10729 by default).
 */

const defaultBase = "http://127.0.0.1:10729";
export const API_URL_STORAGE_KEY = "ring-mcp-api-url";
const STORAGE_KEY = API_URL_STORAGE_KEY;

function baseUrl(): string {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored?.trim()) return stored.trim().replace(/\/$/, "");
  } catch {
    /* ignore */
  }
  if (
    typeof import.meta !== "undefined" &&
    (import.meta as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL
  ) {
    const u = (import.meta as unknown as { env: { VITE_API_URL: string } }).env
      .VITE_API_URL;
    return u.trim().replace(/\/$/, "");
  }
  return defaultBase;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${baseUrl()}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg =
      (data as { message?: string; detail?: string })?.message ??
      (data as { detail?: string })?.detail ??
      res.statusText;
    throw new Error(String(msg));
  }
  return data as T;
}

export interface HealthResponse {
  success: boolean;
  message?: string;
  health_status?: {
    api_connected: boolean;
    devices_accessible: number;
    authentication_valid: boolean;
    /** ISO UTC from server when this health payload was built */
    last_check?: string;
    ring_mqtt?: {
      enabled: boolean;
      connected: boolean;
      alarm_panels_seen: number;
      last_error?: string | null;
    };
  };
}

export interface DevicesResponse {
  success: boolean;
  devices: RingDevice[];
  count: number;
}

export interface RingDevice {
  id: string;
  name: string;
  type: string;
  /** Raw ring_doorbell device family (e.g. doorbots, stickup_cams) when provided */
  family?: string;
  model?: string;
  online?: boolean;
  battery_life?: number;
  firmware?: string;
  address?: string;
  timezone?: string;
  has_subscription?: boolean;
  last_update?: string;
  /** ring-mqtt bridge alarm panel */
  source?: string;
  mqtt_state?: string;
}

export interface StatusResponse {
  success: boolean;
  status?: {
    total_devices: number;
    online_devices: number;
    doorbells: number;
    cameras: number;
    alarms: number;
    last_updated?: string;
  };
}

export interface LogEntry {
  ts: string;
  level: string;
  message: string;
  extra?: Record<string, unknown>;
}

export interface LogsResponse {
  success: boolean;
  logs: LogEntry[];
  count: number;
}

export interface LlmModelsResponse {
  success: boolean;
  models: string[];
  message?: string | null;
  default_model?: string | null;
  base_url?: string;
}

export interface LlmChatResponse {
  success: boolean;
  reply?: string;
}

export const api = {
  getBaseUrl: baseUrl,

  async configureAuth(credentials: {
    username: string;
    password: string;
  }): Promise<{ success: boolean; message?: string; user?: string }> {
    return request("/api/v1/auth/configure", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
  },

  async getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>("/api/v1/health");
  },

  async getDevices(forceRefresh = false): Promise<DevicesResponse> {
    const q = forceRefresh ? "?force_refresh=true" : "";
    return request<DevicesResponse>(`/api/v1/devices${q}`);
  },

  async getDevice(
    deviceId: string,
  ): Promise<{ success: boolean; device: RingDevice }> {
    return request(`/api/v1/devices/${encodeURIComponent(deviceId)}`);
  },

  async getStatus(): Promise<StatusResponse> {
    return request<StatusResponse>("/api/v1/status");
  },

  async getLogs(limit = 200): Promise<LogsResponse> {
    const lim = Math.min(500, Math.max(1, limit));
    return request<LogsResponse>(
      `/api/v1/logs?limit=${encodeURIComponent(String(lim))}`,
    );
  },

  async setArmStatus(
    deviceId: string,
    status: boolean,
  ): Promise<{ success: boolean; message?: string }> {
    return request(`/api/v1/devices/${encodeURIComponent(deviceId)}/arm`, {
      method: "POST",
      body: JSON.stringify({ status }),
    });
  },

  /** ring-mqtt alarm panel: disarm | arm_home | arm_away */
  async setArmMode(
    deviceId: string,
    mode: "disarm" | "arm_home" | "arm_away",
  ): Promise<{ success: boolean; message?: string }> {
    return request(`/api/v1/devices/${encodeURIComponent(deviceId)}/arm`, {
      method: "POST",
      body: JSON.stringify({ mode }),
    });
  },

  async triggerChime(
    deviceId: string,
  ): Promise<{ success: boolean; message?: string }> {
    return request(`/api/v1/devices/${encodeURIComponent(deviceId)}/chime`, {
      method: "POST",
    });
  },

  async getStreamUrl(
    deviceId: string,
  ): Promise<{ success: boolean; url?: string }> {
    return request(`/api/v1/devices/${encodeURIComponent(deviceId)}/stream`);
  },

  /** WebSocket URL for WebRTC signaling (offer/answer/ICE). */
  getWebRtcWsUrl(deviceId: string): string {
    const base = baseUrl();
    const wsBase = base
      .replace(/^http:\/\//i, "ws://")
      .replace(/^https:\/\//i, "wss://");
    return `${wsBase}/api/v1/devices/${encodeURIComponent(deviceId)}/stream/webrtc`;
  },

  async intercomStart(
    deviceId: string,
  ): Promise<{ success: boolean; message?: string }> {
    return request(
      `/api/v1/devices/${encodeURIComponent(deviceId)}/intercom/start`,
      {
        method: "POST",
      },
    );
  },

  async intercomStop(
    deviceId: string,
  ): Promise<{ success: boolean; message?: string }> {
    return request(
      `/api/v1/devices/${encodeURIComponent(deviceId)}/intercom/stop`,
      {
        method: "POST",
      },
    );
  },

  async llmModels(): Promise<LlmModelsResponse> {
    return request<LlmModelsResponse>("/api/v1/llm/models");
  },

  async llmChat(body: {
    messages: { role: string; content: string }[];
    model?: string;
  }): Promise<LlmChatResponse> {
    return request<LlmChatResponse>("/api/v1/llm/chat", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
};
