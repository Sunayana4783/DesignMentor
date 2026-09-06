"use client";
import { useEffect, useRef, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { learnApi } from "@/lib/api";
import ChatBubble from "@/components/ui/ChatBubble";
import Spinner from "@/components/ui/Spinner";
import { Send, BookOpen, Brain, Zap, RotateCcw, Pen } from "lucide-react";
import { clsx } from "clsx";
import type { Mode } from "@/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  agent?: string;
}

const MODES: { key: Mode; label: string; icon: React.ElementType }[] = [
  { key: "learn",    label: "Learn",      icon: BookOpen },
  { key: "quiz",     label: "Quick Quiz", icon: Brain },
  { key: "revision", label: "Revision",   icon: RotateCcw },
  { key: "design",   label: "Design",     icon: Pen },
  { key: "quick",    label: "Quick",      icon: Zap },
];

function LearnContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const conceptSlug = searchParams.get("concept") ?? "classes-and-objects";
  const initialMode = (searchParams.get("mode") ?? "learn") as Mode;

  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>(initialMode);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [agentAction, setAgentAction] = useState("teach");
  const bottomRef = useRef<HTMLDivElement>(null);
  const hasStarted = useRef(false);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;
    startSession();
  }, []);

  const startSession = async () => {
    setIsLoading(true);
    setMessages([]);
    try {
      const { data } = await learnApi.send({
        concept_slug: conceptSlug,
        mode: mode,
        user_message: "",
      });
      setSessionId(data.session_id);
      setAgentAction(data.agent_action);
      setMessages([{
        role: "assistant",
        content: data.agent_message,
        agent: data.metadata?.agent as string,
      }]);
    } catch (e) {
      setMessages([{
        role: "assistant",
        content: "⚠️ Could not connect to the AI tutor. Make sure the backend is running.",
        agent: "system",
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    const userMsg = input.trim();
    setInput("");

    const userMessage: Message = { role: "user", content: userMsg };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const { data } = await learnApi.send({
        concept_slug: conceptSlug,
        mode,
        user_message: userMsg,
        session_id: sessionId ?? undefined,
      });
      setSessionId(data.session_id);
      setAgentAction(data.agent_action);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.agent_message,
        agent: data.metadata?.agent as string,
      }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Something went wrong. Please try again.",
        agent: "system",
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-surface-border bg-surface-card">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-semibold text-white capitalize">
              {conceptSlug.replace(/-/g, " ")}
            </h1>
            <p className="text-xs text-slate-500 capitalize mt-0.5">
              {agentAction.replace(/_/g, " ")}
            </p>
          </div>
          {/* Mode tabs */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push(`/quiz?concept=${conceptSlug}`)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-green-700 hover:bg-green-600 text-white transition-colors"
            >
              <Brain className="w-3 h-3" />
              Take Quiz
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex items-center justify-center h-full">
            <p className="text-slate-500 text-sm">Starting lesson…</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatBubble key={i} role={msg.role} content={msg.content} agent={msg.agent} />
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-surface-card border border-surface-border rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex items-center gap-2 text-slate-400 text-sm">
                <Spinner size={4} />
                <span>Thinking…</span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 px-6 py-4 border-t border-surface-border bg-surface-card">
        <div className="flex items-end gap-3 max-w-4xl mx-auto">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question or reply…"
            rows={1}
            className="flex-1 bg-surface border border-surface-border rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none min-h-[44px] max-h-36"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="flex-shrink-0 w-11 h-11 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 rounded-xl flex items-center justify-center transition-colors"
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
        <p className="text-xs text-slate-600 text-center mt-2">Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  );
}

export default function LearnPage() {
  return (
    <Suspense>
      <LearnContent />
    </Suspense>
  );
}
