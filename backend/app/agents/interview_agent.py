"""
Interview Agent — simulates a real system design interview.
Asks probing questions, evaluates breadth of coverage, generates final scorecard.
"""
import json
from app.agents.state import AgentState
from app.agents.prompts import (
    INTERVIEW_SYSTEM,
    INTERVIEW_HUMAN,
    INTERVIEW_SCORECARD_INSTRUCTION,
)
from app.agents.llm_client import invoke_llm, invoke_llm_json
from app.core.logging import logger

INTERVIEW_MAX_TURNS = 15


def _format_history(messages: list[dict]) -> str:
    lines = []
    for msg in messages[-20:]:
        role = "Candidate" if msg.get("role") == "user" else "Interviewer"
        lines.append(f"{role}: {msg.get('content', '')[:400]}")
    return "\n".join(lines)


async def interview_node(state: AgentState) -> dict:
    """LangGraph node: handles one turn of the interview."""
    problem = state.get("concept_name", "Design a system")
    user_input = state.get("user_input", "")
    turn = state.get("interview_turn", 0) + 1
    messages = state.get("messages", [])

    conversation_history = _format_history(messages)
    generate_scorecard = turn >= INTERVIEW_MAX_TURNS

    scorecard_instruction = INTERVIEW_SCORECARD_INSTRUCTION if generate_scorecard else ""

    human_prompt = INTERVIEW_HUMAN.format(
        problem=problem,
        turn=turn,
        conversation_history=conversation_history,
        user_input=user_input,
        scorecard_instruction=scorecard_instruction,
    )

    logger.info("interview_agent_invoked", problem=problem, turn=turn)

    user_message = {"role": "user", "content": user_input, "agent": "user"}

    if generate_scorecard:
        # Parse out scorecard JSON from the response
        raw = await invoke_llm(INTERVIEW_SYSTEM, human_prompt, temperature=0.3)
        try:
            from app.agents.llm_client import parse_json_response
            scorecard = parse_json_response(raw)
        except Exception:
            scorecard = {"overall_score": 7.0, "summary": raw[:500]}

        overall_score = float(scorecard.get("overall_score", 7.0))
        scorecard_text = _format_scorecard(scorecard)
        response_message = scorecard_text

        assistant_message = {
            "role": "assistant",
            "content": scorecard_text,
            "agent": "interview",
        }

        return {
            "agent_action": "generate_scorecard",
            "interview_turn": turn,
            "interview_scorecard": scorecard,
            "evaluation_score": overall_score * 10,
            "messages": [user_message, assistant_message],
            "response_message": response_message,
            "response_metadata": {
                "agent": "interview",
                "turn": turn,
                "is_completed": True,
                "scorecard": scorecard,
            },
        }
    else:
        # Normal interview turn
        response = await invoke_llm(INTERVIEW_SYSTEM, human_prompt, temperature=0.5)
        assistant_message = {
            "role": "assistant",
            "content": response,
            "agent": "interview",
        }

        return {
            "agent_action": "interview_question",
            "interview_turn": turn,
            "messages": [user_message, assistant_message],
            "response_message": response,
            "response_metadata": {
                "agent": "interview",
                "turn": turn,
                "turns_remaining": INTERVIEW_MAX_TURNS - turn,
                "is_completed": False,
            },
        }


def _format_scorecard(scorecard: dict) -> str:
    """Format scorecard into a readable string."""
    dimensions = [
        ("requirements_clarification", "Requirements"),
        ("architecture", "Architecture"),
        ("database_design", "Database Design"),
        ("scalability", "Scalability"),
        ("failure_handling", "Failure Handling"),
        ("communication", "Communication"),
    ]

    lines = ["# Interview Scorecard\n"]
    lines.append(f"**Problem:** {scorecard.get('problem', 'System Design')}\n")
    lines.append("| Dimension | Score | Comment |")
    lines.append("|---|---|---|")

    for key, label in dimensions:
        dim = scorecard.get(key, {})
        score = dim.get("score", "N/A") if isinstance(dim, dict) else "N/A"
        comment = dim.get("comment", "") if isinstance(dim, dict) else ""
        lines.append(f"| {label} | {score}/10 | {comment[:80]} |")

    overall = scorecard.get("overall_score", "N/A")
    lines.append(f"\n**Overall: {overall}/10**\n")

    summary = scorecard.get("summary", "")
    if summary:
        lines.append(f"\n{summary}")

    strengths = scorecard.get("strengths", [])
    if strengths:
        lines.append("\n**Strengths:**")
        lines.extend(f"✓ {s}" for s in strengths)

    improvements = scorecard.get("areas_to_improve", [])
    if improvements:
        lines.append("\n**Areas to Improve:**")
        lines.extend(f"• {i}" for i in improvements)

    return "\n".join(lines)
