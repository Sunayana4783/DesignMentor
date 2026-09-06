import uuid
from pydantic import BaseModel, Field
from typing import Literal


# ── Learn mode ───────────────────────────────────────────────────────────

class LearnRequest(BaseModel):
    concept_slug: str
    mode: Literal["learn", "quiz", "design", "interview", "revision", "quick"] = "learn"
    user_message: str = ""
    session_id: str | None = None   # resume existing session


class LearnResponse(BaseModel):
    session_id: str
    agent_message: str
    agent_action: str           # teach | ask_question | quiz | evaluate | reteach | complete
    concept_slug: str
    mode: str
    metadata: dict = {}


# ── Quiz mode ─────────────────────────────────────────────────────────────

class QuizStartRequest(BaseModel):
    concept_slug: str
    num_questions: int = Field(default=5, ge=1, le=10)


class QuestionOut(BaseModel):
    id: uuid.UUID
    question_type: str
    difficulty: str
    content: str
    options: list[str] | None = None    # only for MCQ
    points: int

    model_config = {"from_attributes": True}


class QuizSessionOut(BaseModel):
    attempt_id: uuid.UUID
    concept_slug: str
    questions: list[QuestionOut]


class SubmitAnswerRequest(BaseModel):
    attempt_id: uuid.UUID
    question_id: uuid.UUID
    user_response: str


class AnswerFeedback(BaseModel):
    question_id: uuid.UUID
    is_correct: bool
    score_awarded: float
    ai_evaluation: str
    correct_explanation: str


class QuizResultOut(BaseModel):
    attempt_id: uuid.UUID
    concept_slug: str
    score: float
    max_score: float
    percentage: float
    passed: bool
    mastery_level: str
    ai_feedback: str
    weak_subtopics: list[str]
    next_action: Literal["next_concept", "reteach", "practice_more"]
    next_concept_slug: str | None = None


# ── Design mode ───────────────────────────────────────────────────────────

class DesignSubmitRequest(BaseModel):
    problem_slug: str
    phase: Literal["lld", "hld"]
    difficulty: str
    submission_text: str


class DesignReviewOut(BaseModel):
    submission_id: uuid.UUID
    problem_slug: str
    overall_score: float
    review: dict          # structured review with checklist
    ai_feedback: str


# ── Interview mode ────────────────────────────────────────────────────────

class InterviewStartRequest(BaseModel):
    problem: str
    phase: Literal["lld", "hld"] = "hld"


class InterviewMessageRequest(BaseModel):
    session_id: uuid.UUID
    user_message: str


class InterviewMessageResponse(BaseModel):
    session_id: uuid.UUID
    ai_message: str
    is_completed: bool
    scorecard: dict | None = None


# ── Progress ──────────────────────────────────────────────────────────────

class ConceptProgressOut(BaseModel):
    concept_slug: str
    concept_name: str
    mastery_score: float
    mastery_level: str
    attempts: int
    is_unlocked: bool
    is_completed: bool
    next_review_date: str | None = None
    weak_subtopics: list[str] = []

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    user_id: str
    username: str
    lld_progress: float
    hld_progress: float
    overall_mastery: float
    current_concept: str | None
    weak_areas: list[str]
    concepts_due_for_review: list[str]
    streak_days: int
    total_concepts_mastered: int
    phase_unlocked: Literal["foundation", "lld", "hld"]
