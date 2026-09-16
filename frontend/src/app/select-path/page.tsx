"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import Spinner from "@/components/ui/Spinner";
import { Zap, CheckCircle } from "lucide-react";
import { clsx } from "clsx";

type PathType = "lld_only" | "hld_only" | "personalized" | "full";

const PATHS = [
  { value: "lld_only" as PathType,    icon: "🧱", label: "LLD Only",           desc: "OOP, SOLID, Design Patterns, LLD Problems", color: "border-blue-500 bg-blue-500/10" },
  { value: "hld_only" as PathType,    icon: "🌐", label: "HLD Only",           desc: "Architecture, Networking, Databases, Caching", color: "border-purple-500 bg-purple-500/10" },
  { value: "personalized" as PathType,icon: "✨", label: "Personalized",       desc: "AI chooses your path based on your profile", color: "border-brand-500 bg-brand-500/10" },
  { value: "full" as PathType,        icon: "🏆", label: "Full System Design", desc: "Complete LLD + HLD from basics to advanced", color: "border-green-500 bg-green-500/10" },
];

export default function SelectPathPage() {
  const router = useRouter();
  const [selected, setSelected] = useState<PathType>("personalized");
  const [loading, setLoading] = useState(false);

  const handleContinue = async () => {
    setLoading(true);
    try {
      // Update only path_type, keep existing experience/cloud preferences
      await api.post("/api/onboarding/update-path", { path_type: selected });
    } catch {
      // If endpoint fails, still navigate
    } finally {
      setLoading(false);
      router.push("/dashboard");
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4">
      <div className="w-full max-w-xl">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-2">
            <Zap className="w-7 h-7 text-brand-500" />
            <span className="text-2xl font-bold text-white">DesignMentor AI</span>
          </div>
          <h2 className="text-lg font-semibold text-white mt-3">What do you want to focus on today?</h2>
          <p className="text-slate-400 text-sm mt-1">This updates your learning path</p>
        </div>

        {/* Path cards */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {PATHS.map(p => (
            <button key={p.value} onClick={() => setSelected(p.value)}
              className={clsx(
                "text-left p-5 rounded-2xl border-2 transition-all duration-200",
                selected === p.value
                  ? p.color + " scale-[1.02]"
                  : "border-surface-border hover:border-slate-500 bg-surface-card"
              )}>
              <div className="flex items-start justify-between mb-3">
                <span className="text-3xl">{p.icon}</span>
                {selected === p.value && <CheckCircle className="w-5 h-5 text-brand-400" />}
              </div>
              <p className="font-semibold text-white text-sm mb-1">{p.label}</p>
              <p className="text-slate-400 text-xs leading-relaxed">{p.desc}</p>
            </button>
          ))}
        </div>

        <button onClick={handleContinue} disabled={loading}
          className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-bold py-3.5 rounded-xl transition-colors text-base flex items-center justify-center gap-2">
          {loading ? <Spinner size={5} /> : <><Zap className="w-5 h-5" /> Start Learning</>}
        </button>

        <p className="text-center text-xs text-slate-600 mt-4">
          <button onClick={() => router.push("/dashboard")} className="hover:text-slate-400 transition-colors">
            Skip — go to dashboard
          </button>
        </p>
      </div>
    </div>
  );
}
