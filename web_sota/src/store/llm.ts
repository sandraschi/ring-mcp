import { create } from "zustand";
import { api, type LlmProviderInfo } from "@/lib/api";
import { persistLlm, readStoredLlm } from "@/lib/provider";

export type LlmStatus = "probing" | "ready" | "error";

interface LlmState {
  providers: LlmProviderInfo[];
  providerId: string;
  model: string;
  baseUrl: string;
  status: LlmStatus;
  message: string | null;
  gpuHint: string | null;
  refresh: () => Promise<void>;
  select: (providerId: string, model: string) => void;
}

const stored = readStoredLlm();

export const useLlmStore = create<LlmState>((set, get) => ({
  providers: [],
  providerId: stored.provider,
  model: stored.model,
  baseUrl: "",
  status: "probing",
  message: null,
  gpuHint: null,

  refresh: async () => {
    set({ status: "probing", message: null });
    try {
      const reg = await api.llmProviders();
      const providers = reg.providers ?? [];
      const active =
        providers.find((p) => p.id === get().providerId && p.detected) ??
        providers.find((p) => p.detected) ??
        providers[0];
      const model =
        get().model || active?.default_model || active?.models?.[0] || "";
      set({
        providers,
        providerId: active?.id ?? get().providerId,
        model,
        baseUrl: active?.base_url ?? "",
        status: active?.detected ? "ready" : "error",
        message: active && !active.detected ? active.message : null,
        gpuHint:
          !active?.detected &&
          typeof navigator !== "undefined" &&
          "gpu" in navigator
            ? "This machine exposes WebGPU but no local LLM answered - start Ollama (:11434) to enable Chat."
            : null,
      });
      persistLlm(get().providerId, get().model);
    } catch (e) {
      set({
        status: "error",
        message: e instanceof Error ? e.message : String(e),
      });
    }
  },

  select: (providerId, model) => {
    set({ providerId, model });
    persistLlm(providerId, model);
  },
}));
