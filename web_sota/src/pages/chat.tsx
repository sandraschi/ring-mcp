import { useMutation, useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Send, Bot, User, Loader2, AlertCircle } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

const CHAT_MODEL_STORAGE_KEY = "ring_mcp_chat_model_v1";

type ChatTurn = { role: "user" | "assistant"; content: string };

export function Chat() {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [model, setModel] = useState("");
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);

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
      if (saved) {
        setModel((prev) => prev || saved);
        return;
      }
    } catch {
      /* ignore */
    }
    if (d.default_model) setModel((prev) => prev || d.default_model);
    else if (d.models?.[0]) setModel((prev) => prev || d.models[0]);
  }, [modelsQuery.data]);

  useEffect(() => {
    if (!model) return;
    try {
      localStorage.setItem(CHAT_MODEL_STORAGE_KEY, model);
    } catch {
      /* ignore */
    }
  }, [model]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

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
    setTurns((t) => [...t, userTurn]);
    const history = [...turns, userTurn].map((m) => ({
      role: m.role,
      content: m.content,
    }));
    try {
      const res = await chatMutation.mutateAsync(history);
      const reply = res.reply?.trim() || "(empty reply)";
      setTurns((t) => [...t, { role: "assistant", content: reply }]);
    } catch {
      setTurns((t) => [
        ...t,
        {
          role: "assistant",
          content:
            "Request failed. Is Ollama running on 127.0.0.1:11434? Check Ring HTTP API logs.",
        },
      ]);
    }
  }, [input, turns, model, chatMutation]);

  const base = modelsQuery.data?.base_url ?? "";
  const modelsErr =
    modelsQuery.data?.success === false ? modelsQuery.data?.message : null;

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Local AI chat
          </h2>
          <p className="text-slate-400">
            Browser → this API → Ollama{" "}
            <span className="font-mono text-slate-300">127.0.0.1:11434</span>{" "}
            <span className="font-mono text-slate-300">/v1/chat/completions</span>.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs text-slate-500" htmlFor="llm-model">
            Model
          </label>
          {modelsQuery.isLoading ? (
            <span className="text-sm text-slate-500">Loading models…</span>
          ) : (modelsQuery.data?.models?.length ?? 0) > 0 ? (
            <select
              id="llm-model"
              className="rounded-md border border-slate-800 bg-slate-950 px-2 py-1.5 text-sm text-slate-200"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              {(modelsQuery.data?.models ?? []).map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          ) : (
            <input
              id="llm-model"
              type="text"
              className="min-w-[12rem] rounded-md border border-slate-800 bg-slate-950 px-2 py-1.5 text-sm text-slate-200"
              placeholder="Model id (e.g. llama3.2)"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              aria-label="Model id"
            />
          )}
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
          {base ? (
            <span className="text-slate-400">
              {" "}
              (<span className="font-mono">{base}</span>)
            </span>
          ) : null}
        </div>
      ) : null}

      <Card className="flex flex-1 min-h-0 flex-col border-slate-800 bg-slate-950/50 overflow-hidden">
        <CardContent className="flex flex-1 min-h-0 flex-col overflow-hidden p-0">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {turns.length === 0 ? (
              <p className="text-sm text-slate-500">
                Ask about Ring setup, API routes, or debugging. Messages go to your local
                LLM only (not Ring servers).
              </p>
            ) : null}
            {turns.map((turn, i) => (
              <div key={i} className="flex gap-3">
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${
                    turn.role === "user"
                      ? "border-slate-700 bg-slate-800"
                      : "border-blue-800 bg-blue-900/20"
                  }`}
                >
                  {turn.role === "user" ? (
                    <User className="h-4 w-4 text-slate-400" />
                  ) : (
                    <Bot className="h-4 w-4 text-blue-400" />
                  )}
                </div>
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-sm font-medium ${turn.role === "user" ? "text-slate-200" : "text-blue-400"}`}
                    >
                      {turn.role === "user" ? "You" : "Local model"}
                    </span>
                  </div>
                  <p
                    className={`whitespace-pre-wrap break-words rounded-md border p-3 text-sm ${
                      turn.role === "user"
                        ? "border-slate-800 bg-slate-900/50 text-slate-300"
                        : "border-blue-900/30 bg-blue-950/10 text-slate-300"
                    }`}
                  >
                    {turn.content}
                  </p>
                </div>
              </div>
            ))}
            {chatMutation.isPending ? (
              <div className="flex items-center gap-2 pl-11 text-sm text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Thinking…
              </div>
            ) : null}
            <div ref={bottomRef} />
          </div>
          <div className="border-t border-slate-800 bg-slate-900/30 p-4">
            <div className="flex flex-col gap-2 sm:flex-row">
              <textarea
                className="min-h-[44px] flex-1 resize-y rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Message… (Enter to send on desktop; Shift+Enter for newline)"
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    void send();
                  }
                }}
                disabled={chatMutation.isPending}
              />
              <Button
                type="button"
                className="shrink-0 bg-blue-600 hover:bg-blue-700 sm:self-end"
                onClick={() => void send()}
                disabled={chatMutation.isPending || !input.trim()}
              >
                {chatMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
