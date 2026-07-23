import { useMutation, useQuery } from "@tanstack/react-query";
import { Bot, Download, Eraser, Loader2, Send, User, AlertCircle } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

const CHAT_MODEL_STORAGE_KEY = "ring_mcp_chat_model_v1";
const HISTORY_KEY = "ring-chat-history";
const PERSONALITY_KEY = "ring-chat-personality";
const MAX_HISTORY = 100;

const PERSONALITIES: Record<string, string> = {
  "Security Expert": "You are a home security expert specializing in Ring devices. Provide guidance on camera placement, motion detection settings, security best practices, and incident response.",
  "Camera Manager": "You are a camera management specialist. Focus on live view, recording schedules, motion zones, and device configuration for Ring cameras and doorbells.",
  "Quick Summarizer": "Keep responses to 2-3 sentences. Focus on key facts.",
  "Custom": "Custom prompt \u2014 editable below.",
};

const EXAMPLE_PROMPTS = [
  { group: "Cameras", prompts: ["List all cameras", "Show camera status", "Get live view from front door"] },
  { group: "Events", prompts: ["Show recent motion events", "Find events from last night", "Check doorbell rings today"] },
  { group: "Security", prompts: ["Enable motion alerts", "Set privacy zone", "Check battery levels"] },
];

type ChatTurn = { role: "user" | "assistant"; content: string };

export function Chat() {
  const [personality, setPersonality] = useState(() => localStorage.getItem(PERSONALITY_KEY) || "Security Expert");
  const [turns, setTurns] = useState<ChatTurn[]>(() => {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); } catch { return []; }
  });
  const [input, setInput] = useState("");
  const [model, setModel] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const modelsQuery = useQuery({
    queryKey: ["ring-llm-models"],
    queryFn: () => api.llmModels(),
    staleTime: 60_000,
  });

  useEffect(() => {
    const d = modelsQuery.data;
    if (!d) return;
    try {
      const saved = localStorage.getItem(CHAT_MODEL_STORAGE_KEY);
      if (saved) { setModel((prev) => prev || saved); return; }
    } catch { /* ignore */ }
    if (d.default_model) setModel((prev) => prev || d.default_model);
    else if (d.models?.[0]) setModel((prev) => prev || d.models[0]);
  }, [modelsQuery.data]);

  useEffect(() => {
    if (!model) return;
    try { localStorage.setItem(CHAT_MODEL_STORAGE_KEY, model); } catch { /* ignore */ }
  }, [model]);

  useEffect(() => { localStorage.setItem(HISTORY_KEY, JSON.stringify(turns)); }, [turns]);
  useEffect(() => { localStorage.setItem(PERSONALITY_KEY, personality); }, [personality]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [turns]);

  const chatMutation = useMutation({
    mutationFn: async (messages: { role: string; content: string }[]) => {
      return api.llmChat({ messages, model: model || undefined });
    },
  });

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || chatMutation.isPending) return;
    setInput("");
    const userTurn: ChatTurn = { role: "user", content: text };
    const updatedTurns = [...turns, userTurn];
    setTurns(updatedTurns);
    const history = updatedTurns.map((m) => ({ role: m.role, content: m.content }));
    try {
      const res = await chatMutation.mutateAsync(history);
      const reply = res.reply?.trim() || "(empty reply)";
      setTurns((t) => [...t, { role: "assistant", content: reply }]);
    } catch {
      setTurns((t) => [...t, { role: "assistant", content: "Request failed. Is Ollama running on 127.0.0.1:11434? Check Ring HTTP API logs." }]);
    }
  }, [input, turns, model, chatMutation]);

  const base = modelsQuery.data?.base_url ?? "";
  const modelsErr = modelsQuery.data?.success === false ? modelsQuery.data?.message : null;

  const exportChat = () => {
    const text = turns.map((m) => `[${m.role.toUpperCase()}] ${m.content}`).join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "ring-chat.txt"; a.click();
    URL.revokeObjectURL(url);
  };

  const clearChat = () => { setTurns([]); };

  return (
    <div data-testid="chat-page" className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div data-testid="chat-controls" className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Local AI chat</h2>
          <p className="text-slate-400">
            Browser \u2192 this API \u2192 Ollama{" "}
            <span className="font-mono text-slate-300">127.0.0.1:11434</span>{" "}
            <span className="font-mono text-slate-300">/v1/chat/completions</span>.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">skill:ring-expert</span>
          <select data-testid="personality-select" className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200" value={personality} onChange={(e) => setPersonality(e.target.value)}>
            {Object.keys(PERSONALITIES).map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <button data-testid="chat-export" onClick={exportChat} disabled={turns.length === 0} className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30" title="Export"><Download className="h-4 w-4" /></button>
          <button data-testid="chat-clear" onClick={clearChat} disabled={turns.length === 0} className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30" title="Clear"><Eraser className="h-4 w-4" /></button>
        </div>
      </div>

      {modelsQuery.isError ? (
        <div className="flex items-center gap-2 rounded-md border border-red-900/50 bg-red-950/20 px-3 py-2 text-sm text-red-300">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Could not load models. Is the Ring API running at {api.getBaseUrl()}?
        </div>
      ) : null}

      {modelsErr ? (
        <div className="flex items-center gap-2 rounded-md border border-amber-900/40 bg-amber-950/20 px-3 py-2 text-sm text-amber-200/90">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {modelsErr}
          {base ? <span className="text-slate-400"> (<span className="font-mono">{base}</span>)</span> : null}
        </div>
      ) : null}

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-500" htmlFor="llm-model">Model</label>
          {modelsQuery.isLoading ? (
            <span className="text-sm text-slate-500">Loading models\u2026</span>
          ) : (modelsQuery.data?.models?.length ?? 0) > 0 ? (
            <select id="llm-model" className="rounded-md border border-slate-800 bg-slate-950 px-2 py-1.5 text-sm text-slate-200" value={model} onChange={(e) => setModel(e.target.value)}>
              {(modelsQuery.data?.models ?? []).map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          ) : (
            <input id="llm-model" type="text" className="min-w-[12rem] rounded-md border border-slate-800 bg-slate-950 px-2 py-1.5 text-sm text-slate-200" placeholder="Model id (e.g. llama3.2)" value={model} onChange={(e) => setModel(e.target.value)} aria-label="Model id" />
          )}
        </div>
      </div>

      <div className="flex flex-1 min-h-0 flex-col border border-slate-800 bg-slate-950/50 rounded-lg overflow-hidden">
        <div className="flex flex-1 min-h-0 flex-col overflow-hidden p-0">
          <div data-testid="chat-messages" className="flex-1 overflow-y-auto p-4 space-y-4">
            {turns.length === 0 ? (
              <p className="text-sm text-slate-500">Ask about Ring setup, API routes, or debugging. Messages go to your local LLM only (not Ring servers).</p>
            ) : null}
            {turns.map((turn, i) => (
              <div key={i} className="flex gap-3">
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${turn.role === "user" ? "border-slate-700 bg-slate-800" : "border-blue-800 bg-blue-900/20"}`}>
                  {turn.role === "user" ? <User className="h-4 w-4 text-slate-400" /> : <Bot className="h-4 w-4 text-blue-400" />}
                </div>
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${turn.role === "user" ? "text-slate-200" : "text-blue-400"}`}>
                      {turn.role === "user" ? "You" : "Local model"}
                    </span>
                  </div>
                  <p className={`whitespace-pre-wrap break-words rounded-md border p-3 text-sm ${turn.role === "user" ? "border-slate-800 bg-slate-900/50 text-slate-300" : "border-blue-900/30 bg-blue-950/10 text-slate-300"}`}>
                    {turn.content}
                  </p>
                </div>
              </div>
            ))}
            {chatMutation.isPending ? (
              <div className="flex items-center gap-2 pl-11 text-sm text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Thinking\u2026
              </div>
            ) : null}
            <div ref={bottomRef} />
          </div>

          <div data-testid="example-prompts" className="px-4 py-2 border-t border-slate-800 flex flex-wrap gap-2">
            {EXAMPLE_PROMPTS.map((group) => (
              <div key={group.group} className="flex flex-wrap items-center gap-1">
                <span className="text-xs text-slate-500 mr-1">{group.group}:</span>
                {group.prompts.map((p) => (
                  <button key={p} onClick={() => setInput(p)} className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded">{p}</button>
                ))}
              </div>
            ))}
          </div>

          <div className="border-t border-slate-800 bg-slate-900/30 p-4">
            <div className="flex flex-col gap-2 sm:flex-row">
              <textarea data-testid="chat-input" className="min-h-[44px] flex-1 resize-y rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Message\u2026 (Enter to send on desktop; Shift+Enter for newline)" rows={2} value={input}
                onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                disabled={chatMutation.isPending} />
              <button data-testid="chat-send" onClick={() => send()} disabled={chatMutation.isPending || !input.trim()}
                className="shrink-0 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-md sm:self-end">
                {chatMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
