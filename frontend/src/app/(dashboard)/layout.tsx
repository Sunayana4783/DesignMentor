"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import { useAuthStore } from "@/store/useAuthStore";
import api from "@/lib/api";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, loadUser } = useAuthStore();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/auth/login");
      return;
    }
    loadUser()
      .then(async () => {
        try {
          const { data } = await api.get("/api/onboarding/");
          if (!data || !data.is_complete) {
            router.push("/onboarding");
            return;
          }
        } catch {
          // onboarding check failed — continue to dashboard
        }
        setChecked(true);
      })
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        router.push("/auth/login");
      });
  }, []);

  if (!checked || !user) return null;

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar />
      <main className="flex-1 ml-60 overflow-y-auto min-h-screen">
        {children}
      </main>
    </div>
  );
}
