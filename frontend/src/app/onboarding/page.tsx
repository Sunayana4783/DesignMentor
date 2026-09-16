"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import Spinner from "@/components/ui/Spinner";
import { Zap, ArrowRight, ArrowLeft, CheckCircle } from "lucide-react";
import { clsx } from "clsx";

type PathType = "lld_only" | "hld_only" | "personalized" | "full";
type Experience = "fresher" | "1yr" | "2yr" | "3yr" | "4yr" | "5yr+";
type Cloud = "aws" | "gcp" | "azure" | "none" | "other";

const PATHS = [
  { value: "lld_only" as PathType,    icon: "🧱", label: "LLD Only",           desc: "OOP, SOLID, Design Patterns, LLD Problems" },
  { value: "hld_only" as PathType,    icon: "🌐", label: "HLD Only",           desc: "Architecture, Networking, Databases, Caching" },
  { value: "personalized" as PathType,icon: "✨", label: "Personalized",       desc: "AI builds your custom path based on your profile" },
  { value: "full" as PathType,        icon: "🏆", label: "Full System Design", desc: "Complete LLD + HLD from basics to advanced" },
];

const EXPERIENCES = [
  { value: "fresher" as Experience, label: "Fresher",  desc: "Just starting out" },
  { value: "1yr"    as Experience, label: "1 Year",   desc: "Junior developer" },
  { value: "2yr"    as Experience, label: "2 Years",  desc: "Starting interviews" },
  { value: "3yr"    as Experience, label: "3 Years",  desc: "Mid-level engineer" },
  { value: "4yr"    as Experience, label: "4 Years",  desc: "Senior engineer" },
  { value: "5yr+"   as Experience, label: "5+ Years", desc: "Staff / Architect" },
];

const CLOUDS = [
  { value: "aws"   as Cloud, icon: "☁️",  label: "Amazon AWS",      detail: "EC2, S3, RDS, DynamoDB, Lambda, SQS..." },
  { value: "gcp"   as Cloud, icon: "🔵",  label: "Google Cloud",    detail: "GCE, GCS, Cloud SQL, Bigtable, Pub/Sub..." },
  { value: "azure" as Cloud, icon: "🟦",  label: "Microsoft Azure", detail: "VMs, Blob Storage, Cosmos DB, Service Bus..." },
  { value: "none"  as Cloud, icon: "⚡",  label: "No Preference",   detail: "Cloud-agnostic examples only" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    path_type: "personalized" as PathType,
    experience: "fresher" as Experience,
    lld_knowledge_pct: 0,
    hld_knowledge_pct: 0,
    cloud_provider: "none" as Cloud,
  });

  const submit = async () => {
    setLoading(true);
    try {
      await api.post("/api/onboarding/", form);
      router.push("/dashboard");
    } catch {
      router.push("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-2xl">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-2">
            <Zap className="w-7 h-7 text-brand-500" />
            <span className="text-2xl font-bold text-white">DesignMentor AI</span>
          </div>
          <p className="text-slate-400 text-sm">Let's personalise your learning journey</p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-6">
          {[1,2,3,4].map(i => (
            <div key={i} className="flex-1">
              <div className={clsx("h-1.5 rounded-full transition-all", i <= step ? "bg-brand-500" : "bg-surface-border")} />
            </div>
          ))}
        </div>

        <div className="bg-surface-card border border-surface-border rounded-2xl p-6 animate-fade-in">

          {/* ── Step 1: Path ── */}
          {step === 1 && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-1">What do you want to learn?</h2>
              <p className="text-slate-400 text-sm mb-5">Choose your learning path</p>
              <div className="grid grid-cols-2 gap-3">
                {PATHS.map(p => (
                  <button key={p.value} onClick={() => setForm(f => ({...f, path_type: p.value}))}
                    className={clsx("text-left p-4 rounded-xl border-2 transition-all",
                      form.path_type === p.value ? "border-brand-500 bg-brand-600/15" : "border-surface-border hover:border-slate-500")}>
                    <span className="text-2xl block mb-2">{p.icon}</span>
                    <p className="font-semibold text-white text-sm">{p.label}</p>
                    <p className="text-slate-400 text-xs mt-1">{p.desc}</p>
                    {form.path_type === p.value && <CheckCircle className="w-4 h-4 text-brand-400 mt-2" />}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* ── Step 2: Experience ── */}
          {step === 2 && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-1">Your experience level</h2>
              <p className="text-slate-400 text-sm mb-5">Helps us prioritise what matters for your career stage</p>
              <div className="grid grid-cols-3 gap-3">
                {EXPERIENCES.map(e => (
                  <button key={e.value} onClick={() => setForm(f => ({...f, experience: e.value}))}
                    className={clsx("text-left p-3 rounded-xl border-2 transition-all",
                      form.experience === e.value ? "border-brand-500 bg-brand-600/15" : "border-surface-border hover:border-slate-500")}>
                    <p className="font-semibold text-white text-sm">{e.label}</p>
                    <p className="text-slate-500 text-xs mt-0.5">{e.desc}</p>
                  </button>
                ))}
              </div>
              {(form.experience === "1yr" || form.experience === "2yr") && (
                <div className="mt-4 bg-brand-900/20 border border-brand-800 rounded-lg p-3 text-xs text-brand-300">
                  💡 At 1-2 years, HLD is critical for interviews. Your plan will go deep on Architecture, Databases, and Caching.
                </div>
              )}
              {form.experience === "5yr+" && (
                <div className="mt-4 bg-purple-900/20 border border-purple-800 rounded-lg p-3 text-xs text-purple-300">
                  🚀 Expert path — focused on advanced distributed systems, consensus, and real-world case studies.
                </div>
              )}
            </div>
          )}

          {/* ── Step 3: Self-assessment ── */}
          {step === 3 && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-1">How much do you already know?</h2>
              <p className="text-slate-400 text-sm mb-5">We'll skip concepts you already know well</p>
              <div className="space-y-6">
                {/* LLD slider */}
                {form.path_type !== "hld_only" && (
                  <div>
                    <div className="flex justify-between mb-2">
                      <label className="text-sm font-medium text-slate-300">🧱 Low-Level Design (LLD)</label>
                      <span className="text-brand-400 font-bold">{form.lld_knowledge_pct}%</span>
                    </div>
                    <input type="range" min={0} max={100} step={10}
                      value={form.lld_knowledge_pct}
                      onChange={e => setForm(f => ({...f, lld_knowledge_pct: Number(e.target.value)}))}
                      className="w-full accent-brand-500 cursor-pointer" />
                    <div className="flex justify-between text-xs text-slate-600 mt-1">
                      <span>Know nothing</span><span>Know it well</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      {form.lld_knowledge_pct === 0 && "Full LLD curriculum from scratch"}
                      {form.lld_knowledge_pct >= 10 && form.lld_knowledge_pct < 60 && "Some basics known — full LLD covered"}
                      {form.lld_knowledge_pct >= 60 && form.lld_knowledge_pct < 80 && "Good base — skipping OOP basics, starting from SOLID"}
                      {form.lld_knowledge_pct >= 80 && "Strong LLD — jumping straight to Design Patterns"}
                    </p>
                  </div>
                )}
                {/* HLD slider */}
                {form.path_type !== "lld_only" && (
                  <div>
                    <div className="flex justify-between mb-2">
                      <label className="text-sm font-medium text-slate-300">🌐 High-Level Design (HLD)</label>
                      <span className="text-brand-400 font-bold">{form.hld_knowledge_pct}%</span>
                    </div>
                    <input type="range" min={0} max={100} step={10}
                      value={form.hld_knowledge_pct}
                      onChange={e => setForm(f => ({...f, hld_knowledge_pct: Number(e.target.value)}))}
                      className="w-full accent-brand-500 cursor-pointer" />
                    <div className="flex justify-between text-xs text-slate-600 mt-1">
                      <span>Know nothing</span><span>Know it well</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      {form.hld_knowledge_pct === 0 && "Full HLD curriculum from scratch"}
                      {form.hld_knowledge_pct >= 10 && form.hld_knowledge_pct < 60 && "Some basics known — full HLD covered"}
                      {form.hld_knowledge_pct >= 60 && form.hld_knowledge_pct < 80 && "Good base — skipping fundamentals, starting from Databases"}
                      {form.hld_knowledge_pct >= 80 && "Strong HLD — jumping to Distributed Systems"}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Step 4: Cloud ── */}
          {step === 4 && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-1">Which cloud platform do you use?</h2>
              <p className="text-slate-400 text-sm mb-5">When teaching scaling and databases we'll include platform-specific examples</p>
              <div className="grid grid-cols-2 gap-3">
                {CLOUDS.map(c => (
                  <button key={c.value} onClick={() => setForm(f => ({...f, cloud_provider: c.value}))}
                    className={clsx("flex items-center gap-3 p-4 rounded-xl border-2 transition-all text-left",
                      form.cloud_provider === c.value ? "border-brand-500 bg-brand-600/15" : "border-surface-border hover:border-slate-500")}>
                    <span className="text-2xl">{c.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-white text-sm">{c.label}</p>
                      <p className="text-xs text-slate-400 mt-0.5 truncate">{c.detail}</p>
                    </div>
                    {form.cloud_provider === c.value && <CheckCircle className="w-4 h-4 text-brand-400 flex-shrink-0" />}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8">
            <button onClick={() => setStep(s => s - 1)} disabled={step === 1}
              className="flex items-center gap-1 text-slate-400 hover:text-white disabled:opacity-30 text-sm transition-colors">
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
            <span className="text-xs text-slate-500">Step {step} of 4</span>
            {step < 4 ? (
              <button onClick={() => setStep(s => s + 1)}
                className="flex items-center gap-1 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-colors">
                Next <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button onClick={submit} disabled={loading}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-colors">
                {loading ? <Spinner size={4} /> : <><CheckCircle className="w-4 h-4" /> Start Learning</>}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
