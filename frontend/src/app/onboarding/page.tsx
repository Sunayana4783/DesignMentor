"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import Spinner from "@/components/ui/Spinner";
import { Zap, BookOpen, Brain, Globe, CheckCircle } from "lucide-react";
import { clsx } from "clsx";

type PathType = "lld_only" | "hld_only" | "personalized" | "full";

const PATH_OPTIONS: { value: PathType; label: string; desc: string; icon: string; color: string }[] = [
  {
    value: "lld_only",
    label: "Low-Level Design",
    desc: "OOP, SOLID, Design Patterns, LLD problems like Parking Lot, Elevator, Cache",
    icon: "🧱",
    color: "border-blue-500 bg-blue-500/10",
  },
  {
    value: "hld_only",
    label: "High-Level Design",
    desc: "Architecture, Networking, Databases, Caching, Distributed Systems",
    icon: "🌐",
    color: "border-purple-500 bg-purple-500/10",
  },
  {
    value: "personalized",
    label: "Personalized Path",
    desc: "AI builds a custom curriculum — starts with your gaps, focuses on what matters",
    icon: "✨",
    color: "border-brand-500 bg-brand-500/10",
  },
  {
    value: "full",
    label: "Full System Design",
    desc: "Complete journey — LLD foundation first, then full HLD from basics to advanced",
    icon: "🏆",
    color: "border-green-500 bg-green-500/10",
  },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [selected, setSelected] = useState<PathType>("personalized");
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    setLoading(true);
    try {
      await api.post("/api/onboarding/", {
        path_type: selected,
        experience: "fresher",
        lld_knowledge_pct: 0,
        hld_knowledge_pct: 0,
        cloud_provider: "none",
      });
      router.push("/dashboard");
    } catch {
      // If onboarding already exists, just go to dashboard
      router.push("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-2xl">

        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 mb-4">
            <Zap className="w-8 h-8 text-brand-500" />
            <span className="text-3xl font-bold text-white">DesignMentor AI</span>
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">What do you want to learn?</h2>
          <p className="text-slate-400 text-sm">Choose your learning path — you can change this later</p>
        </div>

        {/* Options */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          {PATH_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setSelected(opt.value)}
              className={clsx(
                "text-left p-5 rounded-2xl border-2 transition-all duration-200",
                selected === opt.value
                  ? opt.color + " scale-[1.02]"
                  : "border-surface-border hover:border-slate-500 bg-surface-card"
              )}
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-3xl">{opt.icon}</span>
                {selected === opt.value && (
                  <CheckCircle className="w-5 h-5 text-brand-400 flex-shrink-0" />
                )}
              </div>
              <p className="font-semibold text-white text-sm mb-1.5">{opt.label}</p>
              <p className="text-slate-400 text-xs leading-relaxed">{opt.desc}</p>
            </button>
          ))}
        </div>

        {/* What's included preview */}
        <div className="bg-surface-card border border-surface-border rounded-xl p-4 mb-6 text-xs text-slate-400">
          {selected === "lld_only" && (
            <div className="space-y-1">
              <p className="text-white font-medium mb-2">📚 LLD path includes:</p>
              <p>• OOP (Classes, Encapsulation, Inheritance, Polymorphism)</p>
              <p>• SOLID Principles (SRP, OCP, LSP, ISP, DIP)</p>
              <p>• Design Patterns (Singleton, Factory, Strategy, Observer...)</p>
              <p>• LLD Problems (Parking Lot, Elevator, Splitwise, Cache, Rate Limiter)</p>
            </div>
          )}
          {selected === "hld_only" && (
            <div className="space-y-1">
              <p className="text-white font-medium mb-2">🌐 HLD path includes:</p>
              <p>• Architecture (Monolith, Microservices, Event-Driven, Serverless)</p>
              <p>• Networking & APIs (HTTP, REST, gRPC, WebSockets, CDN)</p>
              <p>• Databases (SQL, NoSQL, Indexing, Sharding, CAP Theorem)</p>
              <p>• Caching (Redis, Strategies, Invalidation, Distributed Cache)</p>
            </div>
          )}
          {selected === "personalized" && (
            <div className="space-y-1">
              <p className="text-white font-medium mb-2">✨ Personalized path:</p>
              <p>• Starts with LLD foundation (OOP + SOLID)</p>
              <p>• Moves to HLD after LLD mastery ≥ 75%</p>
              <p>• AI reteaches weak concepts automatically</p>
              <p>• Spaced repetition schedules reviews</p>
            </div>
          )}
          {selected === "full" && (
            <div className="space-y-1">
              <p className="text-white font-medium mb-2">🏆 Full path includes:</p>
              <p>• Complete LLD (20 concepts) + Complete HLD (36 concepts)</p>
              <p>• 56 total concepts with real-world examples</p>
              <p>• Interview mode with system design problems</p>
              <p>• Adaptive ML model tracks your true mastery</p>
            </div>
          )}
        </div>

        {/* Start button */}
        <button
          onClick={handleStart}
          disabled={loading}
          className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-bold py-3.5 rounded-xl transition-colors text-base flex items-center justify-center gap-2"
        >
          {loading ? (
            <Spinner size={5} />
          ) : (
            <>
              <Zap className="w-5 h-5" />
              Start Learning {selected === "lld_only" ? "LLD" : selected === "hld_only" ? "HLD" : selected === "full" ? "Full Path" : "My Path"}
            </>
          )}
        </button>

      </div>
    </div>
  );
}
