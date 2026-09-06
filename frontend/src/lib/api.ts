import axios, { AxiosInstance } from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 120000, // 2 minutes
});

// Attach token from localStorage on every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${BASE_URL}/api/auth/refresh`, {
            refresh_token: refresh,
          });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          original.headers.Authorization = `Bearer ${data.access_token}`;
          return api(original);
        } catch {
          localStorage.clear();
          window.location.href = "/auth/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post("/api/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/api/auth/login", data),
  me: () => api.get("/api/auth/me"),
};

// ── Curriculum ────────────────────────────────────────────────────────────
export const curriculumApi = {
  topics: () => api.get("/api/curriculum/topics"),
  concept: (slug: string) => api.get(`/api/curriculum/concepts/${slug}`),
};

// ── Learn ─────────────────────────────────────────────────────────────────
export const learnApi = {
  send: (data: {
    concept_slug: string;
    mode: string;
    user_message: string;
    session_id?: string;
  }) => api.post("/api/learn/", data),
  endSession: (sessionId: string) => api.delete(`/api/learn/session/${sessionId}`),
};

// ── Quiz ──────────────────────────────────────────────────────────────────
export const quizApi = {
  start: (data: { concept_slug: string; num_questions: number }) =>
    api.post("/api/quiz/start", data),
  answer: (data: { attempt_id: string; question_id: string; user_response: string }) =>
    api.post("/api/quiz/answer", data),
  complete: (attemptId: string) => api.post(`/api/quiz/complete/${attemptId}`),
};

// ── Progress ──────────────────────────────────────────────────────────────
export const progressApi = {
  dashboard: () => api.get("/api/progress/dashboard"),
  concepts: () => api.get("/api/progress/concepts"),
  rfInsights: (slug: string) => api.get(`/api/progress/rf-insights/${slug}`),
  submitDesign: (data: {
    problem_slug: string;
    phase: string;
    difficulty: string;
    submission_text: string;
  }) => api.post("/api/progress/design/submit", data),
};

// ── Interview ─────────────────────────────────────────────────────────────
export const interviewApi = {
  start: (data: { problem: string; phase: string }) =>
    api.post("/api/interview/start", data),
  message: (data: { session_id: string; user_message: string }) =>
    api.post("/api/interview/message", data),
  sessions: () => api.get("/api/interview/sessions"),
};

export default api;
