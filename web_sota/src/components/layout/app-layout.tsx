import { useEffect, useState } from "react";
import { useZoom } from "@/lib/useZoom";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

// import { Toaster } from '@/components/ui/toaster';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const { zoom, resetZoom } = useZoom();
  const [tauriBackend, setTauriBackend] = useState<string | null>(null);

  // Persist sidebar state
  useEffect(() => {
    const stored = localStorage.getItem("sidebar-collapsed");
    if (stored !== null) setCollapsed(stored === "true");
  }, []);

  // Tauri backend-status events (desktop shell); browsers keep HTTP polling.
  useEffect(() => {
    let unlisten: (() => void) | undefined;
    let cancelled = false;
    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        if (cancelled) return;
        unlisten = await listen<string>("backend-status", (event) => {
          setTauriBackend(event.payload);
        });
      } catch {
        /* not under Tauri - HTTP polling covers status */
      }
    })();
    return () => {
      cancelled = true;
      unlisten?.();
    };
  }, []);

  const handleToggle = () => {
    const newState = !collapsed;
    setCollapsed(newState);
    localStorage.setItem("sidebar-collapsed", String(newState));
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-50 font-sans selection:bg-emerald-500/30">
      <div className="flex flex-1 overflow-hidden">
        <Sidebar collapsed={collapsed} onToggle={handleToggle} />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Topbar />
          {tauriBackend !== null ? (
            <div
              data-testid="tauri-backend-status"
              className="border-b border-slate-800 bg-slate-900/60 px-6 py-1 text-xs text-slate-400"
            >
              Tauri backend: {tauriBackend}
            </div>
          ) : null}
          <main className="flex-1 overflow-y-auto p-6 scroll-smooth">
            <div className="mx-auto max-w-7xl animate-in fade-in duration-500">
              {children}
            </div>
          </main>
          <footer className="flex items-center justify-end gap-2 border-t border-slate-800 px-6 py-1 text-xs text-slate-500">
            <button
              type="button"
              data-testid="zoom-indicator"
              title="UI zoom (Ctrl+scroll, Ctrl+0 resets)"
              onClick={() => resetZoom()}
              className="hover:text-slate-300"
            >
              {Math.round(zoom * 100)}%
            </button>
          </footer>
        </div>
      </div>
      {/* <Toaster /> */}
    </div>
  );
}
