"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Zap } from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading } = useAuthStore();
  const [form, setForm] = useState({ email: "", username: "", password: "", full_name: "" });
  const [error, setError] = useState("");

  const update = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await register(form.email, form.username, form.password, form.full_name || undefined);
      router.push("/onboarding");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Registration failed.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <Zap className="w-8 h-8 text-brand-500" />
            <span className="text-2xl font-bold text-white">DesignMentor AI</span>
          </div>
          <p className="text-slate-400 text-sm">Start your system design journey</p>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-2xl p-8">
          <h1 className="text-xl font-semibold text-white mb-6">Create account</h1>

          {error && (
            <div className="bg-red-900/30 border border-red-800 rounded-lg p-3 mb-4 text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {[
              { key: "full_name", label: "Full name (optional)", type: "text", placeholder: "Alice Smith" },
              { key: "username",  label: "Username",             type: "text", placeholder: "alice" },
              { key: "email",     label: "Email",                type: "email",placeholder: "alice@example.com" },
              { key: "password",  label: "Password",             type: "password", placeholder: "min 8 characters" },
            ].map(({ key, label, type, placeholder }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">{label}</label>
                <input
                  type={type}
                  required={key !== "full_name"}
                  value={form[key as keyof typeof form]}
                  onChange={update(key)}
                  placeholder={placeholder}
                  className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                />
              </div>
            ))}

            <button
              type="submit" disabled={isLoading}
              className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-semibold py-2.5 rounded-lg transition-colors text-sm"
            >
              {isLoading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="text-center text-sm text-slate-400 mt-6">
            Already have an account?{" "}
            <Link href="/auth/login" className="text-brand-400 hover:text-brand-300 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
