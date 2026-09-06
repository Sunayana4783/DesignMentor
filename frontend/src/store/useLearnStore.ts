import { create } from "zustand";

interface Message {
  role: "user" | "assistant";
  content: string;
  agent?: string;
}

interface LearnState {
  sessionId: string | null;
  conceptSlug: string;
  mode: string;
  messages: Message[];
  isLoading: boolean;
  agentAction: string;
  metadata: Record<string, unknown>;
  setSession: (id: string) => void;
  addMessage: (msg: Message) => void;
  setLoading: (v: boolean) => void;
  setAgentAction: (a: string) => void;
  setMetadata: (m: Record<string, unknown>) => void;
  reset: (conceptSlug: string, mode: string) => void;
}

export const useLearnStore = create<LearnState>((set) => ({
  sessionId: null,
  conceptSlug: "",
  mode: "learn",
  messages: [],
  isLoading: false,
  agentAction: "teach",
  metadata: {},

  setSession: (id) => set({ sessionId: id }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setLoading: (v) => set({ isLoading: v }),
  setAgentAction: (a) => set({ agentAction: a }),
  setMetadata: (m) => set({ metadata: m }),
  reset: (conceptSlug, mode) =>
    set({ sessionId: null, conceptSlug, mode, messages: [], agentAction: "teach", metadata: {} }),
}));
