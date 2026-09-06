"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { progressApi } from "@/lib/api";
import type { ConceptProgress } from "@/types";
import { MASTERY_COLORS, MASTERY_LABELS } from "@/types";
import MasteryBar from "@/components/ui/MasteryBar";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from "recharts";
import { BookOpen, Lock, CheckCircle } from "lucide-react";
import { clsx } from "clsx";

export default function ProgressPage() {
  const [concepts, setConcepts] = useState<ConceptProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "unlocked" | "completed" | "weak">("all");

  useEffect(() => {
    progressApi.concepts()
      .then(({ data }) => setConcepts(data))
      .finally(() => setLoading(false));
  }, []);

  const filtered = concepts.filter((c) => {
    if (filter === "unlocked") return c.is_unlocked && !c.is_completed;
    if (filter === "completed") return c.is_completed;
    if (filter === "weak") return c.weak_subtopics.length > 0;
    return true;
  });

  const chartData = concepts
    .filter((c) => c.attempts > 0)
    .slice(0, 12)
    .map((c) => ({
      name: c.concept_name.length > 14 ? c.concept_name.slice(0, 14) + "…" : c.concept_name,
      mastery: Math.round(c.mastery_score),
      level: c.mastery_level,
    }));

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen">
      <Spinner size={8} />
    </div>
  );

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Progress</h1>
        <p className="text-slate-400 text-sm mt-1">
          {concepts.filter((c) => c.is_completed).length} / {concepts.length} concepts mastered
        </p>
      </div>

      {/* Bar chart */}
      {chartData.length > 0 && (
        <div className="bg-surface-card border border-surface-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Mastery by Concept</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} angle={-30} textAnchor="end" />
              <YAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                formatter={(val: number) => [`${val}%`, "Mastery"]}
              />
              <Bar dataKey="mastery" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={MASTERY_COLORS[entry.level] ?? "#6366f1"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-2">
        {(["all", "unlocked", "completed", "weak"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={clsx(
              "px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors",
              filter === f ? "bg-brand-600 text-white" : "text-slate-400 bg-surface-card border border-surface-border hover:text-white"
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Concept grid */}
      <div className="grid grid-cols-1 gap-3">
        {filtered.map((c) => (
          <div key={c.concept_slug} className="bg-surface-card border border-surface-border rounded-xl p-4">
            <div className="flex items-center gap-3">
              {/* Status icon */}
              {c.is_completed ? (
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              ) : c.is_unlocked ? (
                <BookOpen className="w-5 h-5 text-brand-400 flex-shrink-0" />
              ) : (
                <Lock className="w-5 h-5 text-slate-600 flex-shrink-0" />
              )}

              {/* Name + mastery */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <p className={clsx("text-sm font-medium truncate", c.is_unlocked ? "text-white" : "text-slate-500")}>
                    {c.concept_name}
                  </p>
                  <span className="text-xs text-slate-400 flex-shrink-0">
                    {c.mastery_score.toFixed(0)}%
                  </span>
                </div>
                <MasteryBar score={c.mastery_score} level={c.mastery_level} showLabel={false} height="h-1.5" />
              </div>

              {/* Attempts badge */}
              <div className="text-right flex-shrink-0 pl-4">
                <p className="text-xs text-slate-500">{c.attempts} attempts</p>
                <Badge
                  variant={c.is_completed ? "success" : c.is_unlocked ? "brand" : "default"}
                  className="mt-1"
                >
                  {MASTERY_LABELS[c.mastery_level] ?? c.mastery_level}
                </Badge>
              </div>

              {/* Action */}
              {c.is_unlocked && (
                <Link
                  href={`/learn?concept=${c.concept_slug}`}
                  className="flex-shrink-0 ml-3 text-xs bg-brand-600/20 hover:bg-brand-600/40 text-brand-400 px-3 py-1.5 rounded-lg transition-colors"
                >
                  {c.is_completed ? "Review" : "Study"}
                </Link>
              )}
            </div>

            {/* Weak subtopics */}
            {c.weak_subtopics.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5 ml-8">
                {c.weak_subtopics.map((t) => (
                  <Badge key={t} variant="warning">{t}</Badge>
                ))}
              </div>
            )}

            {/* Next review */}
            {c.next_review_date && (
              <p className="text-xs text-slate-600 ml-8 mt-1.5">
                Next review: {new Date(c.next_review_date).toLocaleDateString()}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
