import { useCallback, useEffect, useState } from "react";

const LEVELS = [0.5, 0.6, 0.7, 0.8, 1.0, 1.25, 1.5, 2.0, 3.0];
const STORAGE_KEY = "tauri-zoom";

function nearestLevel(value: number): number {
  let best = LEVELS[0];
  for (const l of LEVELS) {
    if (Math.abs(l - value) < Math.abs(best - value)) best = l;
  }
  return best;
}

function readSaved(): number {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const v = raw === null ? Number.NaN : Number(raw);
    if (Number.isFinite(v)) return nearestLevel(v);
  } catch {
    /* private mode */
  }
  return 1.0;
}

/**
 * Fleet zoom: Ctrl+wheel steps through LEVELS, Ctrl+0 resets to 1.0.
 * Applies via CSS `zoom` (dev browser + WebView) and persists to localStorage.
 */
export function useZoom(): { zoom: number; resetZoom: () => void } {
  const [zoom, setZoom] = useState<number>(readSaved);

  useEffect(() => {
    document.documentElement.style.setProperty("zoom", String(zoom));
    try {
      localStorage.setItem(STORAGE_KEY, String(zoom));
    } catch {
      /* private mode */
    }
  }, [zoom]);

  const resetZoom = useCallback(() => setZoom(1.0), []);

  useEffect(() => {
    const onWheel = (e: WheelEvent) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      setZoom((z) => {
        const i = LEVELS.indexOf(nearestLevel(z));
        const next =
          e.deltaY < 0
            ? Math.min(LEVELS.length - 1, i + 1)
            : Math.max(0, i - 1);
        return LEVELS[next];
      });
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey && (e.key === "0" || e.key === "Digit0")) {
        e.preventDefault();
        setZoom(1.0);
      }
    };
    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  return { zoom, resetZoom };
}
