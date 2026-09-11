import { create } from "zustand";
import { authApi } from "@/lib/api";

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, full_name?: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true });
    const { data } = await authApi.login({ email, password });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const me = await authApi.me();
    set({ user: me.data, isLoading: false });
  },

  register: async (email, username, password, full_name) => {
    set({ isLoading: true });
    await authApi.register({ email, username, password, full_name });
    // Auto-login after register
    const { data } = await authApi.login({ email, password });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const me = await authApi.me();
    set({ user: me.data, isLoading: false });
    // Signal that onboarding is needed
    localStorage.setItem("needs_onboarding", "true");
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null });
  },

  loadUser: async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    try {
      const { data } = await authApi.me();
      set({ user: data });
    } catch {
      set({ user: null });
    }
  },
}));
