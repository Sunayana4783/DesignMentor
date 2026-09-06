"""
Quiz Agent — generates contextual, difficulty-weighted questions.
"""
import json
from app.agents.state import AgentState
from app.agents.prompts import QUIZ_SYSTEM, QUIZ_HUMAN
from app.agents.llm_client import invoke_llm_json
from app.core.logging import logger


async def quiz_node(state: AgentState) -> dict:
    """LangGraph node: generates quiz questions for the current concept."""
    concept_name = state["concept_name"]
    weak_subtopics = state.get("weak_subtopics", [])
    mastery_score = state.get("mastery_score", 0.0)
    mode = state.get("mode", "quiz")

    # Calibrate question count and difficulty mix
    if mode == "quick":
        num_questions = 3
        easy, medium, hard = 1, 1, 1
    elif mastery_score < 40:
        num_questions = 4
        easy, medium, hard = 2, 2, 0
    elif mastery_score < 70:
        num_questions = 5
        easy, medium, hard = 1, 3, 1
    else:
        num_questions = 5
        easy, medium, hard = 0, 3, 2

    # Extract previous questions from message history to avoid repeats
    previous_questions = [
        msg["content"][:100]
        for msg in state.get("messages", [])
        if msg.get("agent") == "quiz"
    ]

    human_prompt = QUIZ_HUMAN.format(
        concept_name=concept_name,
        num_questions=num_questions,
        easy_count=easy,
        medium_count=medium,
        hard_count=hard,
        weak_subtopics=", ".join(weak_subtopics) if weak_subtopics else "None — cover all sub-topics evenly",
        previous_questions=json.dumps(previous_questions[:5]) if previous_questions else "[]",
    )

    logger.info("quiz_agent_invoked", concept=concept_name, num_questions=num_questions)

    questions_data = await invoke_llm_json(QUIZ_SYSTEM, human_prompt, temperature=0.6)

    # Normalise to list
    if isinstance(questions_data, dict):
        questions_data = questions_data.get("questions", [questions_data])

    # Pick first question to present
    first_q = questions_data[0] if questions_data else {}

    new_message = {
        "role": "assistant",
        "content": first_q.get("content", ""),
        "agent": "quiz",
        "question_type": first_q.get("question_type", "short_answer"),
        "options": first_q.get("options", []),
    }

    return {
        "agent_action": "quiz",
        "current_question": first_q.get("content", ""),
        "current_question_type": first_q.get("question_type", "short_answer"),
        "current_question_options": first_q.get("options", []),
        "messages": [new_message],
        "response_message": _format_question(first_q),
        "response_metadata": {
            "agent": "quiz",
            "all_questions": questions_data,
            "total_questions": len(questions_data),
            "question_index": 0,
        },
    }


def _format_question(q: dict) -> str:
    """Format a question dict into a human-readable string."""
    content = q.get("content", "")
    options = q.get("options", [])
    if options:
        options_text = "\n".join(options)
        return f"{content}\n\n{options_text}"
    return content
