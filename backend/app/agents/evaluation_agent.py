"""
Evaluation Agent — scores student answers and detects weak sub-topics.
Uses the RF model prediction as a signal alongside LLM evaluation.
"""
import json
from app.agents.state import AgentState
from app.agents.prompts import EVALUATOR_SYSTEM, EVALUATOR_HUMAN
from app.agents.llm_client import invoke_llm_json
from app.core.config import settings
from app.core.logging import logger


async def evaluation_node(state: AgentState) -> dict:
    """LangGraph node: evaluates the student's answer and decides next step."""
    concept_name = state["concept_name"]
    question = state.get("current_question", "")
    question_type = state.get("current_question_type", "short_answer")
    user_answer = state.get("user_input", "")
    current_mastery = state.get("mastery_score", 0.0)
    weak_subtopics = state.get("weak_subtopics", [])
    reteach_count = state.get("reteach_count", 0)
    rf_prediction = state.get("rf_prediction", 0.0)
    concept_content = state.get("concept_content", {})

    # Extract expected answer points from the latest quiz message metadata
    expected_points = []
    for msg in reversed(state.get("messages", [])):
        if msg.get("agent") == "quiz":
            # The agent stored expected_answer_points in the all_questions metadata
            break

    # Use the concept's key_points as fallback
    expected_points = (
        concept_content.get("key_points", [])
        or concept_content.get("key_concepts", {})
    )

    mastery_threshold = concept_content.get("mastery_threshold", settings.MASTERY_THRESHOLD)

    human_prompt = EVALUATOR_HUMAN.format(
        concept_name=concept_name,
        threshold=mastery_threshold,
        question=question,
        question_type=question_type,
        user_answer=user_answer,
        expected_points=json.dumps(expected_points, indent=2)[:1000],
        current_mastery=current_mastery,
        weak_subtopics=", ".join(weak_subtopics) if weak_subtopics else "None",
        reteach_count=reteach_count,
    )

    logger.info("evaluation_agent_invoked", concept=concept_name, answer_len=len(user_answer))

    eval_result = await invoke_llm_json(EVALUATOR_SYSTEM, human_prompt, temperature=0.2)

    llm_score = float(eval_result.get("score", 0))
    is_correct = eval_result.get("is_correct", False)
    feedback = eval_result.get("feedback", "")
    encouragement = eval_result.get("encouragement", "Keep going — you're making progress!")
    new_weak_topics = eval_result.get("weak_subtopics", [])
    llm_next_action = eval_result.get("next_action", "reteach")

    # Blend LLM score with RF prediction (RF gives longer-term context)
    if rf_prediction > 0:
        blended_score = 0.7 * llm_score + 0.3 * rf_prediction
    else:
        blended_score = llm_score

    # Override next_action if we've retaught too many times — move on regardless
    if reteach_count >= settings.MAX_RETEACH_ATTEMPTS:
        next_action = "next_concept"
    else:
        next_action = llm_next_action

    # Build feedback message
    response_parts = [feedback]
    if eval_result.get("missing_points"):
        missing = "\n".join(f"• {p}" for p in eval_result["missing_points"])
        response_parts.append(f"\n\n**What to review:**\n{missing}")
    response_parts.append(f"\n\n_{encouragement}_")
    response_message = "\n".join(response_parts)

    assistant_message = {
        "role": "assistant",
        "content": response_message,
        "agent": "evaluator",
        "score": llm_score,
    }

    return {
        "evaluation_score": blended_score,
        "evaluation_feedback": feedback,
        "evaluation_weak_topics": new_weak_topics,
        "evaluation_next_action": next_action,
        "agent_action": "evaluate",
        "weak_subtopics": list(set(weak_subtopics + new_weak_topics)),
        "messages": [assistant_message],
        "response_message": response_message,
        "response_metadata": {
            "agent": "evaluator",
            "score": llm_score,
            "blended_score": blended_score,
            "is_correct": is_correct,
            "next_action": next_action,
            "correct_points": eval_result.get("correct_points", []),
            "missing_points": eval_result.get("missing_points", []),
        },
    }
