"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { progressApi } from "@/lib/api";
import type { Dashboard, ConceptProgress } from "@/types";
import MasteryBar from "@/components/ui/MasteryBar";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from "recharts";
import { BookOpen, Brain, AlertTriangle, Zap, Target, RotateCcw } from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [concepts, setConcepts] = useState<ConceptProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/auth/login");
      return;
    }

    Promise.all([progressApi.dashboard(), progressApi.concepts()])
      .then(([d, c]) => {
        setDash(d.data);
        setConcepts(c.data);
      })
      .catch((err) => {
        if (err?.response?.status === 401 || err?.response?.status === 403) {
          router.push("/auth/login");
        } else {
          setError("Failed to load dashboard. Is the backend running?");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen">
      <Spinner size={8} />
    </div>
  );

  if (error) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="bg-red-900/30 border border-red-800 rounded-xl p-6 text-center max-w-md">
        <p className="text-red-400 font-medium mb-2">Connection Error</p>
        <p className="text-slate-400 text-sm">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm rounded-lg transition-colors"
        >
          Retry
        </button>
      </div>
    </div>
  );

  if (!dash) return null;

  const radarData = [
    { subject: "LLD",     score: dash.lld_progress },
    { subject: "HLD",     score: dash.hld_progress },
    { subject: "Overall", score: dash.overall_mastery },
  ];

  const masteredConcepts   = concepts.filter((c) => c.is_completed);
  const inProgressConcepts = concepts.filter((c) => c.is_unlocked && !c.is_completed);
  const lockedConcepts     = concepts.filter((c) => !c.is_unlocked);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Welcome back, {dash.username} 👋</h1>
          <p className="text-slate-400 text-sm mt-1">
            {dash.total_concepts_mastered} concepts mastered · Phase:{" "}
            <span className="text-brand-400 capitalize font-medium">{dash.phase_unlocked}</span>
          </p>
        </div>
        {dash.current_concept && (
          <Link
            href={`/learn?concept=${dash.current_concept}`}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition-colors"
          >
            <Zap className="w-4 h-4" />
            Continue Learning
          </Link>
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "LLD Progress",  value: `${dash.lld_progress}%`,   icon: BookOpen, color: "text-blue-400" },
          { label: "HLD Progress",  value: `${dash.hld_progress}%`,   icon: Brain,    color: "text-purple-400" },
          { label: "Overall",       value: `${dash.overall_mastery}%`, icon: Target,   color: "text-brand-400" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-surface-card border border-surface-border rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Icon className={`w-4 h-4 ${color}`} />
              <span className="text-sm text-slate-400">{label}</span>
            </div>
            <p className="text-3xl font-bold text-white">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* Radar chart */}
        <div className="bg-surface-card border border-surface-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Mastery Overview</h3>
          <ResponsiveContainer width="100%" height={180}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <Radar dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} strokeWidth={2} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Weak areas */}
        <div className="bg-surface-card border border-surface-border rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-4 h-4 text-yellow-400" />
            <h3 className="text-sm font-semibold text-slate-300">Weak Areas</h3>
          </div>
          {dash.weak_areas.length === 0 ? (
            <p className="text-slate-500 text-sm">No weak areas detected yet.</p>
          ) : (
            <ul className="space-y-2">
              {dash.weak_areas.map((area) => (
                <li key={area} className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 flex-shrink-0" />
                  <span className="text-sm text-slate-300 capitalize">{area}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Review due */}
        <div className="bg-surface-card border border-surface-border rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <RotateCcw className="w-4 h-4 text-green-400" />
            <h3 className="text-sm font-semibold text-slate-300">Due for Review</h3>
          </div>
          {dash.concepts_due_for_review.length === 0 ? (
            <p className="text-slate-500 text-sm">Nothing due today.</p>
          ) : (
            <ul className="space-y-2">
              {dash.concepts_due_for_review.map((slug) => (
                <li key={slug}>
                  <Link
                    href={`/learn?concept=${slug}&mode=revision`}
                    className="text-sm text-brand-400 hover:text-brand-300 hover:underline capitalize"
                  >
                    {slug.replace(/-/g, " ")}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Concept progress list */}
      <div className="bg-surface-card border border-surface-border rounded-xl p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">
          Concept Progress ({masteredConcepts.length}/{concepts.length} mastered)
        </h3>

        {inProgressConcepts.length > 0 && (
          <div className="mb-5">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">In Progress</p>
            <div className="grid grid-cols-2 gap-3">
              {inProgressConcepts.map((c) => (
                <Link
                  key={c.concept_slug}
                  href={`/learn?concept=${c.concept_slug}`}
                  className="bg-surface border border-surface-border rounded-lg p-3 hover:border-brand-600 transition-colors group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium text-white group-hover:text-brand-400 transition-colors truncate">
                      {c.concept_name}
                    </p>
                    <Badge variant="warning">In Progress</Badge>
                  </div>
                  <MasteryBar score={c.mastery_score} level={c.mastery_level} height="h-1.5" />
                </Link>
              ))}
            </div>
          </div>
        )}

        {masteredConcepts.length > 0 && (
          <div className="mb-5">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Mastered</p>
            <div className="flex flex-wrap gap-2">
              {masteredConcepts.map((c) => (
                <Badge key={c.concept_slug} variant="success">✓ {c.concept_name}</Badge>
              ))}
            </div>
          </div>
        )}

        {lockedConcepts.length > 0 && (
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">
              Locked ({lockedConcepts.length})
            </p>
            <div className="flex flex-wrap gap-2">
              {lockedConcepts.slice(0, 8).map((c) => (
                <span key={c.concept_slug} className="text-xs text-slate-600 bg-surface border border-surface-border px-2 py-1 rounded-full">
                  🔒 {c.concept_name}
                </span>
              ))}
              {lockedConcepts.length > 8 && (
                <span className="text-xs text-slate-600">+{lockedConcepts.length - 8} more</span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
