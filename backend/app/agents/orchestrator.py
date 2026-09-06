"""
LangGraph Orchestrator — the central agent router.

Graph topology:
                    START
                      │
               ┌──────▼──────┐
               │  load_state │  (load student memory + RAG context)
               └──────┬──────┘
                      │
               ┌──────▼──────┐
               │   router    │  (decide which agent node to invoke)
               └──────┬──────┘
          ┌───────────┼───────────┬────────────┬───────────┐
          ▼           ▼           ▼            ▼           ▼
       teacher     mentor      quiz        evaluator   planner
          │           │           │            │           │
          └───────────┴───────────┴────────────┴───────────┘
                              │
                       ┌──────▼──────┐
                       │   design_   │
                       │  reviewer   │  (only in design mode)
                       └──────┬──────┘
                              │
                       ┌──────▼──────┐
                       │  interview  │  (only in interview mode)
                       └──────┬──────┘
                              │
                            END
"""
import uuid
import json
from functools import partial

from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState
from app.agents.teacher_agent import teacher_node
from app.agents.quiz_agent import quiz_node
from app.agents.evaluation_agent import evaluation_node
from app.agents.mentor_agent import mentor_node
from app.agents.planning_agent import planning_node
from app.agents.design_reviewer_agent import design_reviewer_node
from app.agents.interview_agent import interview_node
from app.core.logging import logger


# ── Router logic ─────────────────────────────────────────────────────────────

def router(state: AgentState) -> str:
    mode = state.get("mode", "learn")
    agent_action = state.get("agent_action", "teach")
    user_input = state.get("user_input", "").strip()
    evaluation_next = state.get("evaluation_next_action", "")
    mastery_score = state.get("mastery_score", 0.0)

    # ── Interview mode ────────────────────────────────────────────────────
    if mode == "interview":
        return "interview"

    # ── Design mode ───────────────────────────────────────────────────────
    if mode == "design":
        return "design_reviewer"

    # ── After evaluation ──────────────────────────────────────────────────
    if agent_action == "evaluate":
        if evaluation_next == "reteach":
            return "teacher"
        return "planner"

    # ── After planning → always end ───────────────────────────────────────
    if agent_action == "plan_next":
        return END

    # ── After mentor, teacher, quiz → always end (wait for user) ─────────
    if agent_action in ("ask_question", "quiz", "teach"):
        return END

    # ── No user input yet → teach ─────────────────────────────────────────
    if not user_input:
        if agent_action == "teach" or mastery_score == 0:
            return "teacher"
        return END

    # ── After teacher ran (ask_question means teacher just finished) ───────
    if agent_action == "ask_question":
        return END

    # ── User has input → decide based on mode ────────────────────────────
    if mode in ("quiz", "quick", "revision"):
        return "quiz"

    # Default: mentor handles the user message
    return "mentor"


# ── State loader node ─────────────────────────────────────────────────────────

async def load_state_node(state: AgentState, db: AsyncSession) -> dict:
    """
    Loads student memory from DB and fetches RAG context.
    Runs first in every graph execution.
    """
    from sqlalchemy import select
    from app.models.progress import UserProgress
    from app.models.curriculum import Concept
    from app.rag.retriever import retrieve_context

    user_id = uuid.UUID(state["user_id"])
    concept_slug = state.get("concept_slug", "")

    # Load concept from DB
    concept_result = await db.execute(
        select(Concept).where(Concept.slug == concept_slug)
    )
    concept = concept_result.scalar_one_or_none()
    if not concept:
        return {
            "concept_name": concept_slug,
            "concept_content": {},
            "rag_context": "",
        }

    # Load student progress for this concept
    progress_result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == user_id,
            UserProgress.concept_id == concept.id,
        )
    )
    progress = progress_result.scalar_one_or_none()

    mastery_score = progress.mastery_score if progress else 0.0
    mastery_level = progress.mastery_level.value if progress and progress.mastery_level else "not_started"
    attempts = progress.attempts if progress else 0
    weak_subtopics = progress.weak_subtopics if progress else []

    # Get RF prediction
    from app.ml.rf_model import MasteryPredictor
    rf_features = progress.rf_features if progress else {}
    rf_prediction = MasteryPredictor.predict(rf_features) if rf_features else 0.0

    # Retrieve RAG context
    try:
        rag_context = await retrieve_context(
            query=f"{concept.name} {concept.description}",
            concept_slug=concept_slug,
            top_k=3,
        )
    except Exception as e:
        logger.warning("rag_retrieval_failed", error=str(e))
        rag_context = ""

    return {
        "concept_name": concept.name,
        "concept_content": concept.content,
        "mastery_score": mastery_score,
        "mastery_level": mastery_level,
        "attempts": attempts,
        "weak_subtopics": weak_subtopics,
        "rf_prediction": rf_prediction,
        "rag_context": rag_context,
        "agent_action": "teach" if not state.get("user_input", "").strip() else "ask_question",
    }


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_graph(db: AsyncSession) -> StateGraph:
    """
    Builds and compiles the LangGraph StateGraph.
    db is injected so agent nodes can query student progress.
    """
    graph = StateGraph(AgentState)

    # ── Nodes ─────────────────────────────────────────────────────────────
    graph.add_node("load_state",     partial(load_state_node,     db=db))
    graph.add_node("teacher",        teacher_node)
    graph.add_node("quiz",           quiz_node)
    graph.add_node("evaluator",      evaluation_node)
    graph.add_node("mentor",         mentor_node)
    graph.add_node("planner",        partial(planning_node,       db=db))
    graph.add_node("design_reviewer", design_reviewer_node)
    graph.add_node("interview",      interview_node)

    # ── Entry point ───────────────────────────────────────────────────────
    graph.set_entry_point("load_state")

    # ── load_state always routes to the router ────────────────────────────
    graph.add_conditional_edges(
        "load_state",
        router,
        {
            "teacher":          "teacher",
            "quiz":             "quiz",
            "evaluator":        "evaluator",
            "mentor":           "mentor",
            "planner":          "planner",
            "design_reviewer":  "design_reviewer",
            "interview":        "interview",
            END:                END,
        }
    )

    # ── Each agent routes back through the router or ends ─────────────────
    for node_name in ["teacher", "quiz", "mentor"]:
        graph.add_conditional_edges(
            node_name,
            router,
            {
                "teacher":          "teacher",
                "quiz":             "quiz",
                "evaluator":        "evaluator",
                "mentor":           "mentor",
                "planner":          "planner",
                "design_reviewer":  "design_reviewer",
                "interview":        "interview",
                END:                END,
            }
        )

    graph.add_conditional_edges(
        "evaluator",
        router,
        {
            "teacher":  "teacher",
            "planner":  "planner",
            END:        END,
        }
    )

    # Planner, design_reviewer, interview always end (API handles the response)
    graph.add_edge("planner",          END)
    graph.add_edge("design_reviewer",  END)
    graph.add_edge("interview",        END)

    return graph.compile()


# ── Public entry-point ────────────────────────────────────────────────────────

async def run_agent(
    initial_state: dict,
    db: AsyncSession,
) -> AgentState:
    """
    Compile the graph for this request and invoke it.
    Returns the final state after graph execution.
    """
    graph = build_graph(db)

    # Defaults for required fields that might not be set
    defaults: dict = {
        "messages": [],
        "weak_subtopics": [],
        "questions_asked": 0,
        "questions_correct": 0,
        "quiz_complete": False,
        "reteach_count": 0,
        "mastery_score": 0.0,
        "rf_prediction": 0.0,
        "interview_turn": 0,
        "interview_scorecard": {},
        "design_checklist": {},
        "evaluation_score": 0.0,
        "evaluation_feedback": "",
        "evaluation_weak_topics": [],
        "evaluation_next_action": "",
        "next_concept_slug": None,
        "plan_reasoning": "",
        "agent_action": "teach",
        "teaching_output": "",
        "current_question": "",
        "current_question_type": "short_answer",
        "current_question_options": [],
        "rag_context": "",
        "response_message": "",
        "response_metadata": {},
    }

    state = {**defaults, **initial_state}

    logger.info(
        "agent_graph_start",
        user_id=state.get("user_id"),
        concept=state.get("concept_slug"),
        mode=state.get("mode"),
    )

    final_state = await graph.ainvoke(state, {"recursion_limit": 5})

    logger.info(
        "agent_graph_complete",
        user_id=state.get("user_id"),
        action=final_state.get("agent_action"),
    )

    return final_state
