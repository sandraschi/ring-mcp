import { Eye, EyeOff } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_URL_STORAGE_KEY, api } from "@/lib/api";
import { useLlmStore } from "@/store/llm";

function getStoredApiUrl(): string {
  try {
    const u = localStorage.getItem(API_URL_STORAGE_KEY);
    if (u?.trim()) return u.trim();
  } catch {
    /* ignore */
  }
  return api.getBaseUrl();
}

/** Persists Ring account fields across refresh and failed save (local browser only). */
const RING_ACCOUNT_FORM_STORAGE_KEY = "ring_mcp_ring_account_form_v1";

function LLMSettings() {
  const {
    providers,
    providerId,
    model,
    baseUrl,
    status,
    message,
    gpuHint,
    refresh,
    select,
  } = useLlmStore();
  useEffect(() => {
    refresh();
  }, [refresh]);
  const active = providers.find((p) => p.id === providerId) ?? providers[0];
  const models = active?.models ?? [];
  return (
    <Card className="border-slate-800 bg-slate-950/50">
      <CardHeader>
        <CardTitle className="text-white">Local LLM</CardTitle>
        <CardDescription
          className="text-slate-400"
          data-testid="llm-provider-card-local"
        >
          Provider and model selection
          {baseUrl ? ` · ${baseUrl}` : ""}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          className="flex items-center gap-2 text-sm"
          data-testid="llm-status"
        >
          <span
            className={`inline-block h-2 w-2 rounded-full ${status === "ready" ? "bg-emerald-500" : status === "probing" ? "bg-amber-400 animate-pulse" : "bg-red-500"}`}
          />
          <span className="text-slate-300">
            {status === "ready"
              ? `Ready${model ? ` · ${model}` : ""}`
              : status === "probing"
                ? "Probing local providers…"
                : (message ?? "No local LLM detected")}
          </span>
          <Button
            type="button"
            variant="outline"
            size="sm"
            data-testid="llm-refresh"
            className="ml-auto border-slate-700 text-slate-200"
            onClick={() => refresh()}
          >
            Refresh
          </Button>
        </div>
        {gpuHint ? <p className="text-sm text-amber-300">{gpuHint}</p> : null}
        <div className="grid gap-2">
          <Label className="text-slate-300" htmlFor="llm-provider">
            Provider
          </Label>
          <select
            id="llm-provider"
            data-testid="llm-provider-select"
            className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
            value={providerId}
            onChange={(e) => {
              const next = providers.find((p) => p.id === e.target.value);
              select(
                e.target.value,
                next?.default_model || next?.models?.[0] || "",
              );
            }}
          >
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
                {p.detected ? "" : " (not detected)"}
              </option>
            ))}
          </select>
        </div>
        <div className="grid gap-2">
          <Label className="text-slate-300" htmlFor="llm-model">
            Model
          </Label>
          <select
            id="llm-model"
            data-testid="llm-model-select"
            className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
            value={model}
            onChange={(e) => {
              select(providerId, e.target.value);
            }}
          >
            {models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
      </CardContent>
    </Card>
  );
}

export function Settings() {
  const [apiUrl, setApiUrl] = useState(getStoredApiUrl);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [securityCode, setSecurityCode] = useState("");
  const [formHydrated, setFormHydrated] = useState(false);
  const [needsTwoFactor, setNeedsTwoFactor] = useState(false);
  const [testMessage, setTestMessage] = useState<{
    ok: boolean;
    text: string;
  } | null>(null);
  const [authMessage, setAuthMessage] = useState<{
    ok: boolean;
    text: string;
  } | null>(null);
  const [testLoading, setTestLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(RING_ACCOUNT_FORM_STORAGE_KEY);
      if (!raw) {
        setFormHydrated(true);
        return;
      }
      const parsed = JSON.parse(raw) as {
        username?: string;
        password?: string;
        securityCode?: string;
      };
      if (typeof parsed.username === "string") setUsername(parsed.username);
      if (typeof parsed.password === "string") setPassword(parsed.password);
      if (typeof parsed.securityCode === "string")
        setSecurityCode(parsed.securityCode);
    } catch {
      /* ignore */
    }
    setFormHydrated(true);
  }, []);

  useEffect(() => {
    if (!formHydrated) return;
    try {
      localStorage.setItem(
        RING_ACCOUNT_FORM_STORAGE_KEY,
        JSON.stringify({ username, password, securityCode }),
      );
    } catch {
      /* ignore */
    }
  }, [formHydrated, username, password, securityCode]);

  const saveApiUrl = useCallback(() => {
    try {
      localStorage.setItem(API_URL_STORAGE_KEY, apiUrl);
      setTestMessage({
        ok: true,
        text: "API URL saved. Test connection to verify.",
      });
    } catch {
      setTestMessage({ ok: false, text: "Failed to save API URL." });
    }
  }, [apiUrl]);

  const testConnection = useCallback(async () => {
    setTestLoading(true);
    setTestMessage(null);
    try {
      const base = apiUrl.trim() || api.getBaseUrl();
      const res = await fetch(`${base.replace(/\/$/, "")}/api/v1/health`);
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.success !== false) {
        const devices = data.health_status?.devices_accessible ?? 0;
        setTestMessage({
          ok: true,
          text: `Backend reachable. ${devices} device(s) accessible.`,
        });
      } else {
        setTestMessage({
          ok: false,
          text: data.message || data.detail || `HTTP ${res.status}`,
        });
      }
    } catch (e) {
      setTestMessage({
        ok: false,
        text: e instanceof Error ? e.message : "Connection failed",
      });
    } finally {
      setTestLoading(false);
    }
  }, [apiUrl]);

  const configureAuth = useCallback(async () => {
    if (!username.trim() || !password) {
      setAuthMessage({
        ok: false,
        text: "Username and password are required.",
      });
      return;
    }
    setAuthLoading(true);
    setAuthMessage(null);
    try {
      const base = apiUrl.trim() || api.getBaseUrl();
      const body: Record<string, string> = {
        username: username.trim(),
        password,
      };
      const otp = securityCode.trim();
      if (otp) {
        body.two_factor_code = otp;
      }
      const res = await fetch(
        `${base.replace(/\/$/, "")}/api/v1/auth/configure`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
      );
      const data = (await res.json().catch(() => ({}))) as {
        success?: boolean;
        requires_two_factor?: boolean;
        message?: string;
        detail?: string | { msg?: string }[];
      };
      if (res.ok && data.success) {
        setNeedsTwoFactor(false);
        setSecurityCode("");
        setAuthMessage({
          ok: true,
          text: "Ring credentials configured successfully.",
        });
        return;
      }
      if (res.ok && data.requires_two_factor) {
        setNeedsTwoFactor(true);
        setAuthMessage({
          ok: false,
          text:
            data.message ||
            "Ring sent a verification code. Enter it under Security code and save again.",
        });
        return;
      }
      setNeedsTwoFactor(false);
      const detail = data.detail;
      const detailStr =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail
                .map((d) =>
                  typeof d === "object" && d && "msg" in d
                    ? String(d.msg)
                    : JSON.stringify(d),
                )
                .join("; ")
            : "";
      setAuthMessage({
        ok: false,
        text: data.message || detailStr || `HTTP ${res.status}`,
      });
    } catch (e) {
      setAuthMessage({
        ok: false,
        text: e instanceof Error ? e.message : "Request failed",
      });
    } finally {
      setAuthLoading(false);
    }
  }, [apiUrl, username, password, securityCode]);

  return (
    <div className="space-y-6" data-testid="settings-page">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Configuration
        </h2>
        <p className="text-slate-400">Ring credentials and API connection</p>
      </div>

      <div className="grid gap-6">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Ring Account</CardTitle>
            <CardDescription className="text-slate-400">
              Email and password for your Ring account. Used to list and control
              devices.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label className="text-slate-300">Email</Label>
              <Input
                type="email"
                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-400"
                placeholder="you@example.com"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label className="text-slate-300">Password</Label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  className="bg-slate-900 border-slate-800 pr-10 text-slate-100 placeholder:text-slate-400"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-200"
                  onClick={() => setShowPassword((v) => !v)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" aria-hidden />
                  ) : (
                    <Eye className="h-4 w-4" aria-hidden />
                  )}
                </button>
              </div>
            </div>
            <div className="grid gap-2">
              <Label className="text-slate-300">
                Security code (if Ring sent one)
              </Label>
              <Input
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                className={
                  needsTwoFactor
                    ? "bg-amber-950/40 border-amber-600 text-slate-100 placeholder:text-slate-400"
                    : "bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-400"
                }
                placeholder="6-digit code from SMS or email"
                value={securityCode}
                onChange={(e) => {
                  setSecurityCode(e.target.value);
                  if (e.target.value.trim()) {
                    setNeedsTwoFactor(false);
                  }
                }}
              />
              <p className="text-xs text-slate-500">
                If Ring asks for verification, paste the code here and click
                Save again (same email and password).
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                className="border-slate-800 text-slate-300 hover:bg-slate-800"
                onClick={configureAuth}
                disabled={authLoading}
              >
                {authLoading ? "Saving…" : "Save Ring credentials"}
              </Button>
              {authMessage && (
                <span
                  className={
                    authMessage.ok
                      ? "text-emerald-400 text-sm"
                      : needsTwoFactor
                        ? "text-amber-400 text-sm max-w-md"
                        : "text-red-400 text-sm"
                  }
                >
                  {authMessage.text}
                </span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">API Bridge</CardTitle>
            <CardDescription className="text-slate-400">
              Backend URL (default: http://127.0.0.1:10729). Run
              web_sota\\start.ps1 to start backend.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label className="text-slate-300">API URL</Label>
              <Input
                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-400"
                placeholder="http://127.0.0.1:10729"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                data-testid="settings-save-url"
                className="border-slate-800 text-slate-300 hover:bg-slate-800"
                onClick={saveApiUrl}
              >
                Save URL
              </Button>
              <Button
                variant="outline"
                data-testid="settings-test-connection"
                className="border-slate-800 text-slate-300 hover:bg-slate-800"
                onClick={testConnection}
                disabled={testLoading}
              >
                {testLoading ? "Testing…" : "Test connection"}
              </Button>
              {testMessage && (
                <span
                  className={
                    testMessage.ok
                      ? "text-emerald-400 text-sm"
                      : "text-red-400 text-sm"
                  }
                >
                  {testMessage.text}
                </span>
              )}
            </div>
          </CardContent>
        </Card>

        <LLMSettings />
      </div>
    </div>
  );
}
