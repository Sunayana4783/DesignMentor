"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import Spinner from "@/components/ui/Spinner";
import { Zap, BookOpen, Brain, Cloud, Star, ArrowRight, ArrowLeft, CheckCircle } from "lucide-react";
import { clsx } from "clsx";

// ── Types ─────────────────────────────────────────────────────────────────
type PathType = "lld_only" | "hld_only" | "personalized" | "full";
type Experience = "fresher" | "1yr" | "2yr" | "3yr" | "4yr" | "5yr+";
type CloudProvider = "aws" | "gcp" | "azure" | "none" | "other";

interface FormData {
  path_type: PathType;
  experience: Experience;
  lld_knowledge_pct: number;
  hld_knowledge_pct: number;
  cloud_provider: CloudProvider;
}

// ── Step configs ──────────────────────────────────────────────────────────
const PATH_OPTIONS: { value: PathType; label: string; desc: string; icon: string }[] = [
  { value: "lld_only",     label: "Low-Level Design",      desc: "OOP, SOLID, Design Patterns, LLD problems",             icon: "🧱" },
  { value: "hld_only",     label: "High-Level Design",     desc: "Architecture, Databases, Distributed Systems, HLD problems", icon: "🌐" },
  { value: "personalized", label: "Personalized Path",     desc: "AI decides based on your experience and knowledge",      icon: "✨" },
  { value: "full",         label: "Full System Design",    desc: "Complete LLD + HLD from basics to advanced",            icon: "🏆" },
];

const EXPERIENCE_OPTIONS: { value: Experience; label: string; desc: string }[] = [
  { value: "fresher", label: "Fresher",     desc: "0 years — just starting out" },
  { value: "1yr",     label: "1 Year",      desc: "1 year of experience" },
  { value: "2yr",     label: "2 Years",     desc: "2 years — starting to get interviews" },
  { value: "3yr",     label: "3 Years",     desc: "3 years — targeting senior roles" },
  { value: "4yr",     label: "4 Years",     desc: "4 years — senior engineer" },
  { value: "5yr+",    label: "5+ Years",    desc: "5+ years — staff / architect level" },
];

const CLOUD_OPTIONS: { value: CloudProvider; label: string; icon: string; color: string }[] = [
  { value: "aws",   label: "Amazon AWS",      icon: "☁️",  color: "border-orange-500 bg-orange-500/10" },
  { value: "gcp",   label: "Google Cloud",    icon: "🔵",  color: "border-blue-500 bg-blue-500/10" },
  { value: "azure", label: "Microsoft Azure", icon: "🟦",  color: "border-blue-400 bg-blue-400/10" },
  { value: "none",  label: "No preference",   icon: "⚡",  color: "border-slate-500 bg-slate-500/10" },
  { value: "other", label: "Other",            icon: "🌩️", color: "border-purple-500 bg-purple-500/10" },
];

// ── Main component ────────────────────────────────────────────────────────
export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState<FormData>({
    path_type: "personalized",
    experience: "fresher",
    lld_knowledge_pct: 0,
    hld_knowledge_pct: 0,
    cloud_provider: "none",
  });

  const totalSteps = 4;

  const next = () => setStep((s) => Math.min(s + 1, totalSteps));
  const back = () => setStep((s) => Math.max(s - 1, 1));

  const submit = async () => {
    setLoading(true);
    try {
      await api.post("/api/onboarding/", form);
      router.push("/dashboard");
    } catch {
      alert("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <Zap className="w-7 h-7 text-brand-500" />
            <span className="text-2xl font-bold text-white">DesignMentor AI</span>
          </div>
          <p className="text-slate-400 text-sm">Let's personalise your learning journey</p>
        </div>

        {/* Progress bar */}
        <div className="flex items-center gap-2 mb-8">
          {Array.from({ length: totalSteps }, (_, i) => (
            <div key={i} className="flex-1">
              <div className={clsx(
                "h-1.5 rounded-full transition-all duration-500",
                i + 1 <= step ? "bg-brand-500" : "bg-surface-border"
              )} />
            </div>
          ))}
        </div>

        {/* Step card */}
        <div className="bg-surface-card border border-surface-border rounded-2xl p-6 animate-fade-in">

          {/* ── Step 1: Path Type ── */}
          {step === 1 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <BookOpen className="w-5 h-5 text-brand-400" />
                <h2 className="text-lg font-semibold text-white">What do you want to learn?</h2>
              </div>
              <p className="text-slate-400 text-sm mb-6">Choose your learning path</p>
              <div className="grid grid-cols-2 gap-3">
                {PATH_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setForm((f) => ({ ...f, path_type: opt.value }))}
                    className={clsx(
                      "text-left p-4 rounded-xl border transition-all",
                      form.path_type === opt.value
                        ? "border-brand-500 bg-brand-600/15"
                        : "border-surface-border hover:border-slate-400"
                    )}
                  >
                    <span className="text-2xl mb-2 block">{opt.icon}</span>
                    <p className="font-semibold text-white text-sm">{opt.label}</p>
                    <p className="text-slate-400 text-xs mt-1">{opt.desc}</p>
                    {form.path_type === opt.value && (
                      <CheckCircle className="w-4 h-4 text-brand-400 mt-2" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* ── Step 2: Experience ── */}
          {step === 2 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Star className="w-5 h-5 text-brand-400" />
                <h2 className="text-lg font-semibold text-white">Your experience level</h2>
              </div>
              <p className="text-slate-400 text-sm mb-6">This helps us prioritise what matters most for your career stage</p>
              <div className="grid grid-cols-3 gap-3">
                {EXPERIENCE_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setForm((f) => ({ ...f, experience: opt.value }))}
                    className={clsx(
                      "text-left p-3 rounded-xl border transition-all",
                      form.experience === opt.value
                        ? "border-brand-500 bg-brand-600/15"
                        : "border-surface-border hover:border-slate-400"
                    )}
                  >
                    <p className="font-semibold text-white text-sm">{opt.label}</p>
                    <p className="text-slate-500 text-xs mt-1">{opt.desc}</p>
                  </button>
                ))}
              </div>

              {/* Experience-based HLD note */}
              {(form.experience === "1yr" || form.experience === "2yr") && (
                <div className="mt-4 bg-brand-900/20 border border-brand-800 rounded-lg p-3 text-sm text-brand-300">
                  💡 At 1-2 years, HLD is very important for interviews. Your plan will prioritise HLD with extra depth.
                </div>
              )}
              {form.experience === "5yr+" && (
                <div className="mt-4 bg-purple-900/20 border border-purple-800 rounded-lg p-3 text-sm text-purple-300">
                  🚀 Expert path — focused on advanced distributed systems, consensus algorithms, and real-world case studies.
                </div>
              )}
            </div>
          )}

          {/* ── Step 3: Self-assessment ── */}
          {step === 3 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-5 h-5 text-brand-400" />
                <h2 className="text-lg font-semibold text-white">How much do you already know?</h2>
              </div>
              <p className="text-slate-400 text-sm mb-6">Be honest — this skips concepts you already know well</p>

              <div className="space-y-6">
                {/* LLD slider */}
                <div>
                  <div className="flex justify-between mb-2">
                    <label className="text-sm font-medium text-slate-300">
                      🧱 Low-Level Design (LLD)
                    </label>
                    <span className="text-brand-400 font-bold">{form.lld_knowledge_pct}%</span>
                  </div>
                  <input
                    type="range" min={0} max={100} step={10}
                    value={form.lld_knowledge_pct}
                    onChange={(e) => setForm((f) => ({ ...f, lld_knowledge_pct: Number(e.target.value) }))}
                    className="w-full accent-brand-500 cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-slate-600 mt-1">
                    <span>I know nothing</span>
                    <span>I know it well</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    {form.lld_knowledge_pct === 0 && "Starting from scratch — full LLD curriculum"}
                    {form.lld_knowledge_pct >= 10 && form.lld_knowledge_pct < 60 && "Some basics known — we'll cover everything"}
                    {form.lld_knowledge_pct >= 60 && form.lld_knowledge_pct < 80 && "Good base — skipping OOP basics, starting from SOLID"}
                    {form.lld_knowledge_pct >= 80 && "Strong LLD — jumping straight to Design Patterns"}
                  </p>
                </div>

                {/* HLD slider */}
                {form.path_type !== "lld_only" && (
                  <div>
                    <div className="flex justify-between mb-2">
                      <label className="text-sm font-medium text-slate-300">
                        🌐 High-Level Design (HLD)
                      </label>
                      <span className="text-brand-400 font-bold">{form.hld_knowledge_pct}%</span>
                    </div>
                    <input
                      type="range" min={0} max={100} step={10}
                      value={form.hld_knowledge_pct}
                      onChange={(e) => setForm((f) => ({ ...f, hld_knowledge_pct: Number(e.target.value) }))}
                      className="w-full accent-brand-500 cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-slate-600 mt-1">
                      <span>I know nothing</span>
                      <span>I know it well</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      {form.hld_knowledge_pct === 0 && "Starting from scratch — full HLD curriculum"}
                      {form.hld_knowledge_pct >= 10 && form.hld_knowledge_pct < 60 && "Some basics known — full HLD covered"}
                      {form.hld_knowledge_pct >= 60 && form.hld_knowledge_pct < 80 && "Good base — skipping fundamentals, starting from databases"}
                      {form.hld_knowledge_pct >= 80 && "Strong HLD — jumping to distributed systems"}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Step 4: Cloud Provider ── */}
          {step === 4 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Cloud className="w-5 h-5 text-brand-400" />
                <h2 className="text-lg font-semibold text-white">Which cloud platform do you use?</h2>
              </div>
              <p className="text-slate-400 text-sm mb-6">
                When teaching scaling, databases, and storage — we'll include {form.cloud_provider === "none" ? "cloud-agnostic" : "platform-specific"} examples
              </p>
              <div className="grid grid-cols-1 gap-3">
                {CLOUD_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setForm((f) => ({ ...f, cloud_provider: opt.value }))}
                    className={clsx(
                      "flex items-center gap-3 p-4 rounded-xl border transition-all text-left",
                      form.cloud_provider === opt.value
                        ? opt.color + " border-opacity-100"
                        : "border-surface-border hover:border-slate-400"
                    )}
                  >
                    <span className="text-xl">{opt.icon}</span>
                    <div className="flex-1">
                      <p className="font-semibold text-white text-sm">{opt.label}</p>
                      {opt.value === "aws" && <p className="text-xs text-slate-400 mt-0.5">EC2, S3, RDS, DynamoDB, Lambda, SQS, EKS...</p>}
                      {opt.value === "gcp" && <p className="text-xs text-slate-400 mt-0.5">GCE, GCS, Cloud SQL, Bigtable, Cloud Run, Pub/Sub...</p>}
                      {opt.value === "azure" && <p className="text-xs text-slate-400 mt-0.5">VMs, Blob Storage, Cosmos DB, Azure Functions, Service Bus...</p>}
                      {opt.value === "none" && <p className="text-xs text-slate-400 mt-0.5">Cloud-agnostic concepts only</p>}
                    </div>
                    {form.cloud_provider === opt.value && (
                      <CheckCircle className="w-5 h-5 text-brand-400 flex-shrink-0" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8">
            <button
              onClick={back}
              disabled={step === 1}
              className="flex items-center gap-2 text-slate-400 hover:text-white disabled:opacity-30 transition-colors text-sm"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>

            <span className="text-xs text-slate-500">Step {step} of {totalSteps}</span>

            {step < totalSteps ? (
              <button
                onClick={next}
                className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-colors"
              >
                Next <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={submit}
                disabled={loading}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-colors"
              >
                {loading ? <Spinner size={4} /> : <><CheckCircle className="w-4 h-4" /> Start Learning</>}
              </button>
            )}
          </div>
        </div>

        {/* Skip */}
        <p className="text-center text-xs text-slate-600 mt-4">
          <button
            onClick={() => router.push("/dashboard")}
            className="hover:text-slate-400 transition-colors"
          >
            Skip for now and use default settings
          </button>
        </p>
      </div>
    </div>
  );
}
