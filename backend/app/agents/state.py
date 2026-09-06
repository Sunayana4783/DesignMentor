"""
Shared LangGraph state schema used by all agents in the pipeline.
TypedDict so LangGraph can merge partial updates from each node.
"""
from typing import TypedDict, Annotated, Literal
import operator


class AgentState(TypedDict):
    # ── Identity ──────────────────────────────────────────────────────────
    user_id: str
    session_id: str
    mode: Literal["learn", "quiz", "design", "interview", "revision", "quick"]

    # ── Current position in the curriculum ───────────────────────────────
    concept_slug: str
    concept_name: str
    concept_content: dict           # full content JSON from DB

    # ── Student memory snapshot (loaded at session start) ─────────────────
    mastery_score: float
    mastery_level: str
    attempts: int
    weak_subtopics: list[str]
    rf_prediction: float            # Random Forest predicted mastery

    # ── Conversation history (append-only via operator.add) ───────────────
    messages: Annotated[list[dict], operator.add]

    # ── Current agent action ──────────────────────────────────────────────
    agent_action: Literal[
        "teach", "ask_question", "quiz", "evaluate",
        "reteach", "complete", "design_review", "interview_question",
        "generate_scorecard", "plan_next"
    ]

    # ── Teaching content produced by TeacherAgent ─────────────────────────
    teaching_output: str

    # ── Quiz state ────────────────────────────────────────────────────────
    current_question: str
    current_question_type: str      # mcq | short_answer | design | scenario
    current_question_options: list[str]
    questions_asked: int
    questions_correct: int
    quiz_complete: bool

    # ── User's latest input ───────────────────────────────────────────────
    user_input: str

    # ── Evaluation output ─────────────────────────────────────────────────
    evaluation_score: float         # 0-100
    evaluation_feedback: str
    evaluation_weak_topics: list[str]
    evaluation_next_action: Literal["next_concept", "reteach", "practice_more"]
    reteach_count: int              # how many times we've re-taught this concept

    # ── Planning output ───────────────────────────────────────────────────
    next_concept_slug: str | None
    plan_reasoning: str

    # ── Design / Interview mode ───────────────────────────────────────────
    design_checklist: dict          # populated by DesignReviewerAgent
    interview_turn: int
    interview_scorecard: dict

    # ── RAG context ───────────────────────────────────────────────────────
    rag_context: str                # retrieved knowledge chunks

    # ── Final response to the API layer ──────────────────────────────────
    response_message: str
    response_metadata: dict
