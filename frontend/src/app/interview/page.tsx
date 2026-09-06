"use client";
import { useState, useRef, useEffect } from "react";
import { interviewApi } from "@/lib/api";
import ChatBubble from "@/components/ui/ChatBubble";
import Spinner from "@/components/ui/Spinner";
import Badge from "@/components/ui/Badge";
import { Send, Mic, Trophy } from "lucide-react";

const PROBLEMS = [
  { label: "Design YouTube",         value: "Design YouTube",          phase: "hld" },
  { label: "Design URL Shortener",   value: "Design URL Shortener",    phase: "hld" },
  { label: "Design WhatsApp",        value: "Design WhatsApp",         phase: "hld" },
  { label: "Design Instagram",       value: "Design Instagram",        phase: "hld" },
  { label: "Design Uber",            value: "Design Uber",             phase: "hld" },
  { label: "Design Parking Lot",     value: "Design Parking Lot",      phase: "lld" },
  { label: "Design Elevator System", value: "Design Elevator System",  phase: "lld" },
  { label: "Design Splitwise",       value: "Design Splitwise",        phase: "lld" },
];

interface Message { role: "user" | "assistant"; content: string; }

export default function InterviewPage() {
  const [phase, setPhase] = useState<"setup" | "interview" | "result">("setup");
  const [selectedProblem, setSelectedProblem] = useState(PROBLEMS[0]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [scorecard, setScorecard] = useState<Record<string, unknown> | null>(null);
  const [turnsLeft, setTurnsLeft] = useState(15);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startInterview = async () => {
    setLoading(true);
    try {
      const { data } = await interviewApi.start({
        problem: selectedProblem.value,
        phase: selectedProblem.phase,
      });
      setSessionId(data.session_id);
      setMessages([{ role: "assistant", content: data.ai_message }]);
      setPhase("interview");
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !sessionId || loading) return;
    const msg = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: msg }]);
    setLoading(true);
    try {
      const { data } = await interviewApi.message({ session_id: sessionId, user_message: msg });
      setMessages((m) => [...m, { role: "assistant", content: data.ai_message }]);
      setTurnsLeft((t) => t - 1);
      if (data.is_completed) {
        setScorecard(data.scorecard);
        setPhase("result");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  // ── Setup screen ──────────────────────────────────────────────────────
  if (phase === "setup") return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-2">
        <Mic className="w-6 h-6 text-brand-500" />
        <h1 className="text-2xl font-bold text-white">Interview Mode</h1>
      </div>
      <p className="text-slate-400 text-sm mb-8">
        The AI acts as a senior engineer interviewer. Drive the design — it will probe deeper.
      </p>

      <div className="bg-surface-card border border-surface-border rounded-xl p-6 space-y-5">
        <div>
          <p className="text-sm font-medium text-slate-300 mb-3">Select a problem:</p>
          <div className="grid grid-cols-2 gap-2">
            {PROBLEMS.map((p) => (
              <button
                key={p.value}
                onClick={() => setSelectedProblem(p)}
                className={`text-left text-sm px-3 py-3 rounded-lg border transition-colors ${
                  selectedProblem.value === p.value
                    ? "border-brand-500 bg-brand-600/20 text-white"
                    : "border-surface-border text-slate-400 hover:border-slate-400 hover:text-white"
                }`}
              >
                <span className="block font-medium">{p.label}</span>
                <Badge variant={p.phase === "hld" ? "brand" : "default"} className="mt-1">
                  {p.phase.toUpperCase()}
                </Badge>
              </button>
            ))}
          </div>
        </div>

        <div className="bg-surface rounded-lg p-3 text-xs text-slate-400 space-y-1">
          <p>• Up to 15 turns · AI never volunteers answers</p>
          <p>• Final scorecard across 6 dimensions</p>
          <p>• Tip: clarify requirements first</p>
        </div>

        <button
          onClick={startInterview} disabled={loading}
          className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition-colors text-sm flex items-center justify-center gap-2"
        >
          {loading ? <Spinner size={4} /> : <><Mic className="w-4 h-4" /> Start Interview</>}
        </button>
      </div>
    </div>
  );

  // ── Result screen ─────────────────────────────────────────────────────
  if (phase === "result" && scorecard) {
    const dims = [
      { key: "requirements_clarification", label: "Requirements" },
      { key: "architecture",               label: "Architecture" },
      { key: "database_design",            label: "Database" },
      { key: "scalability",                label: "Scalability" },
      { key: "failure_handling",           label: "Failure Handling" },
      { key: "communication",              label: "Communication" },
    ];
    const overall = scorecard.overall_score as number ?? 0;

    return (
      <div className="p-6 max-w-2xl mx-auto animate-fade-in">
        <div className="bg-surface-card border border-surface-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <Trophy className="w-8 h-8 text-yellow-400" />
            <div>
              <h2 className="text-xl font-bold text-white">Interview Complete</h2>
              <p className="text-slate-400 text-sm">{selectedProblem.label}</p>
            </div>
            <div className="ml-auto text-center">
              <p className="text-4xl font-bold text-brand-400">{overall}<span className="text-xl text-slate-400">/10</span></p>
              <p className="text-xs text-slate-500">Overall</p>
            </div>
          </div>

          <div className="space-y-3 mb-6">
            {dims.map(({ key, label }) => {
              const dim = scorecard[key] as { score?: number; comment?: string } | undefined;
              const score = dim?.score ?? 0;
              return (
                <div key={key}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-300">{label}</span>
                    <span className="text-slate-400">{score}/10</span>
                  </div>
                  <div className="w-full bg-surface-border rounded-full h-1.5">
                    <div
                      className="h-1.5 rounded-full bg-brand-500 transition-all"
                      style={{ width: `${(score / 10) * 100}%` }}
                    />
                  </div>
                  {dim?.comment && <p className="text-xs text-slate-500 mt-0.5">{dim.comment}</p>}
                </div>
              );
            })}
          </div>

          {scorecard.summary && <p className="text-slate-300 text-sm mb-4">{scorecard.summary as string}</p>}

          <button
            onClick={() => { setPhase("setup"); setMessages([]); setScorecard(null); setTurnsLeft(15); }}
            className="text-sm text-slate-400 hover:text-white px-4 py-2 border border-surface-border rounded-lg transition-colors"
          >
            Try another problem
          </button>
        </div>
      </div>
    );
  }

  // ── Interview chat ────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-screen">
      <div className="flex-shrink-0 px-6 py-4 border-b border-surface-border bg-surface-card flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-white">{selectedProblem.label}</h2>
          <p className="text-xs text-slate-500 mt-0.5">System Design Interview</p>
        </div>
        <Badge variant={turnsLeft <= 3 ? "danger" : "brand"}>
          {turnsLeft} turns left
        </Badge>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((m, i) => (
          <ChatBubble key={i} role={m.role} content={m.content} agent={m.role === "assistant" ? "interview" : undefined} />
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-surface-card border border-surface-border rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-2 text-slate-400 text-sm">
              <Spinner size={4} /> <span>Interviewer is thinking…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex-shrink-0 px-6 py-4 border-t border-surface-border bg-surface-card">
        <div className="flex items-end gap-3 max-w-4xl mx-auto">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Describe your approach, ask clarifying questions, or explain your design…"
            rows={2}
            className="flex-1 bg-surface border border-surface-border rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
          />
          <button
            onClick={sendMessage} disabled={!input.trim() || loading}
            className="w-11 h-11 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 rounded-xl flex items-center justify-center transition-colors"
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}
