export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
}

export interface ConceptProgress {
  concept_slug: string;
  concept_name: string;
  mastery_score: number;
  mastery_level: string;
  attempts: number;
  is_unlocked: boolean;
  is_completed: boolean;
  next_review_date?: string;
  weak_subtopics: string[];
}

export interface Dashboard {
  user_id: string;
  username: string;
  lld_progress: number;
  hld_progress: number;
  overall_mastery: number;
  current_concept: string | null;
  weak_areas: string[];
  concepts_due_for_review: string[];
  streak_days: number;
  total_concepts_mastered: number;
  phase_unlocked: "foundation" | "lld" | "hld";
}

export interface QuizQuestion {
  id: string;
  question_type: string;
  difficulty: string;
  content: string;
  options?: string[];
  points: number;
}

export interface QuizSession {
  attempt_id: string;
  concept_slug: string;
  questions: QuizQuestion[];
}

export interface QuizResult {
  attempt_id: string;
  concept_slug: string;
  score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  mastery_level: string;
  ai_feedback: string;
  weak_subtopics: string[];
  next_action: "next_concept" | "reteach" | "practice_more";
  next_concept_slug?: string;
}

export interface LearnResponse {
  session_id: string;
  agent_message: string;
  agent_action: string;
  concept_slug: string;
  mode: string;
  metadata: Record<string, unknown>;
}

export type Mode = "learn" | "quiz" | "design" | "interview" | "revision" | "quick";

export const MASTERY_COLORS: Record<string, string> = {
  not_started: "#475569",
  beginner:    "#ef4444",
  learning:    "#f97316",
  developing:  "#eab308",
  good:        "#22c55e",
  mastered:    "#6366f1",
};

export const MASTERY_LABELS: Record<string, string> = {
  not_started: "Not Started",
  beginner:    "Beginner",
  learning:    "Learning",
  developing:  "Developing",
  good:        "Good",
  mastered:    "Mastered ✓",
};
