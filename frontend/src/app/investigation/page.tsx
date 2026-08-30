"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { PageShell } from "@/components/Shell";
import { Card } from "@/components/ui";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function InvestigationPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || isLoading) return;

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.chat(question, conversationId);
      setConversationId(response.conversation_id);
      setMessages((prev) => [...prev, { role: "assistant", content: response.reply }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <PageShell title="AI Investigation">
      <Card className="flex h-[60vh] flex-col">
        <div className="flex-1 space-y-3 overflow-y-auto pr-2">
          {messages.length === 0 && (
            <p className="text-sm text-slate-400">
              Ask about a process instance or incident, e.g. &quot;Why is process 6755399441055744 stuck?&quot;
            </p>
          )}
          {messages.map((message, index) => (
            <div
              key={index}
              className={`rounded-md p-3 text-sm ${
                message.role === "user" ? "bg-blue-600/20 text-blue-100" : "bg-slate-800 text-slate-100"
              }`}
            >
              <span className="mb-1 block text-xs uppercase tracking-wide text-slate-400">
                {message.role === "user" ? "You" : "Investigation Agent"}
              </span>
              {message.content}
            </div>
          ))}
          {isLoading && <p className="text-sm text-slate-400">Investigating…</p>}
          {error && <p className="text-sm text-red-400">{error}</p>}
        </div>
        <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the investigation agent..."
            className="flex-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </Card>
      <p className="mt-4 text-xs text-slate-500">
        This chat currently returns a placeholder response. The full LangGraph investigation
        agent with tool use and structured findings (status, root cause, evidence, similar
        incidents, recommended action) is implemented in later phases.
      </p>
    </PageShell>
  );
}
