import { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, API_URL_STORAGE_KEY } from "@/lib/api";

function getStoredApiUrl(): string {
  try {
    const u = localStorage.getItem(API_URL_STORAGE_KEY);
    if (u && u.trim()) return u.trim();
  } catch {
    /* ignore */
  }
  return api.getBaseUrl();
}

export function Settings() {
  const [apiUrl, setApiUrl] = useState(getStoredApiUrl);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [testMessage, setTestMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [authMessage, setAuthMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [testLoading, setTestLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);

  const saveApiUrl = useCallback(() => {
    try {
      localStorage.setItem(API_URL_STORAGE_KEY, apiUrl);
      setTestMessage({ ok: true, text: "API URL saved. Test connection to verify." });
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
      setAuthMessage({ ok: false, text: "Username and password are required." });
      return;
    }
    setAuthLoading(true);
    setAuthMessage(null);
    try {
      const base = apiUrl.trim() || api.getBaseUrl();
      const res = await fetch(`${base.replace(/\/$/, "")}/api/v1/auth/configure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.success) {
        setAuthMessage({ ok: true, text: "Ring credentials configured successfully." });
      } else {
        setAuthMessage({
          ok: false,
          text: data.message || data.detail || `HTTP ${res.status}`,
        });
      }
    } catch (e) {
      setAuthMessage({
        ok: false,
        text: e instanceof Error ? e.message : "Request failed",
      });
    } finally {
      setAuthLoading(false);
    }
  }, [apiUrl, username, password]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Configuration</h2>
        <p className="text-slate-400">Ring credentials and API connection</p>
      </div>

      <div className="grid gap-6">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Ring Account</CardTitle>
            <CardDescription className="text-slate-400">
              Email and password for your Ring account. Used to list and control devices.
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
              <Input
                type="password"
                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-400"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
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
                <span className={authMessage.ok ? "text-emerald-400 text-sm" : "text-red-400 text-sm"}>
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
              Backend URL (default: http://127.0.0.1:10729). Run web_sota\\start.ps1 to start backend.
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
                className="border-slate-800 text-slate-300 hover:bg-slate-800"
                onClick={saveApiUrl}
              >
                Save URL
              </Button>
              <Button
                variant="outline"
                className="border-slate-800 text-slate-300 hover:bg-slate-800"
                onClick={testConnection}
                disabled={testLoading}
              >
                {testLoading ? "Testing…" : "Test connection"}
              </Button>
              {testMessage && (
                <span className={testMessage.ok ? "text-emerald-400 text-sm" : "text-red-400 text-sm"}>
                  {testMessage.text}
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
