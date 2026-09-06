"use client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { clsx } from "clsx";

interface Props {
  role: "user" | "assistant";
  content: string;
  agent?: string;
}

const AGENT_LABELS: Record<string, string> = {
  teacher:        "📚 Teacher",
  quiz:           "❓ Quiz",
  evaluator:      "📊 Evaluator",
  mentor:         "🧑‍🏫 Mentor",
  planner:        "🗺 Planner",
  design_reviewer:"🏗 Design Reviewer",
  interview:      "🎤 Interviewer",
};

export default function ChatBubble({ role, content, agent }: Props) {
  const isUser = role === "user";

  return (
    <div className={clsx("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div
        className={clsx(
          "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-brand-600 text-white rounded-br-sm"
            : "bg-surface-card text-slate-200 rounded-bl-sm border border-surface-border"
        )}
      >
        {!isUser && agent && (
          <p className="text-xs text-brand-500 font-semibold mb-2">
            {AGENT_LABELS[agent] ?? agent}
          </p>
        )}
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ node, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || "");
              const inline = !match;
              return inline ? (
                <code className="bg-surface-border px-1 py-0.5 rounded text-xs font-mono" {...props}>
                  {children}
                </code>
              ) : (
                <SyntaxHighlighter
                  style={vscDarkPlus as Record<string, React.CSSProperties>}
                  language={match[1]}
                  PreTag="div"
                  className="rounded-lg text-xs my-2"
                >
                  {String(children).replace(/\n$/, "")}
                </SyntaxHighlighter>
              );
            },
            table: ({ children }) => (
              <div className="overflow-x-auto my-2">
                <table className="min-w-full text-xs border-collapse border border-surface-border">
                  {children}
                </table>
              </div>
            ),
            th: ({ children }) => (
              <th className="border border-surface-border px-2 py-1 bg-surface-border text-left">{children}</th>
            ),
            td: ({ children }) => (
              <td className="border border-surface-border px-2 py-1">{children}</td>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
