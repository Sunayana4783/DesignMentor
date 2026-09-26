"use client";

export default function GlobalError({ error }: { error: Error }) {
  return (
    <div style={{ padding: 32, fontFamily: "monospace", background: "#0f172a", color: "#f1f5f9", minHeight: "100vh" }}>
      <h2 style={{ color: "#f87171" }}>Runtime Error</h2>
      <pre style={{ whiteSpace: "pre-wrap", color: "#fbbf24" }}>{error.message}</pre>
      <pre style={{ whiteSpace: "pre-wrap", color: "#94a3b8", fontSize: 12 }}>{error.stack}</pre>
    </div>
  );
}
