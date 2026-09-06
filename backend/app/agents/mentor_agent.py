"""
Mentor Agent — handles freeform student messages during a session.
Acts as a Socratic tutor: asks questions, guides, never just gives answers.
"""
from app.agents.state import AgentState
from app.agents.prompts import MENTOR_SYSTEM, MENTOR_HUMAN
from app.agents.llm_client import invoke_llm
from app.core.logging import logger


def _format_conversation_history(messages: list[dict], limit: int = 10) -> str:
    """Format recent messages into a readable conversation string."""
    recent = messages[-limit:] if len(messages) > limit else messages
    lines = []
    for msg in recent:
        role = "Student" if msg.get("role") == "user" else "Mentor"
        content = msg.get("content", "")[:300]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


async def mentor_node(state: AgentState) -> dict:
    """LangGraph node: handles conversational student messages as a mentor."""
    concept_name = state["concept_name"]
    user_input = state.get("user_input", "")
    messages = state.get("messages", [])

    conversation_history = _format_conversation_history(messages)

    human_prompt = MENTOR_HUMAN.format(
        concept_name=concept_name,
        conversation_history=conversation_history,
        user_input=user_input,
    )

    logger.info("mentor_agent_invoked", concept=concept_name, input_len=len(user_input))
    response = await invoke_llm(MENTOR_SYSTEM, human_prompt, temperature=0.6)

    user_message = {"role": "user", "content": user_input, "agent": "user"}
    assistant_message = {"role": "assistant", "content": response, "agent": "mentor"}

    return {
        "agent_action": "ask_question",
        "messages": [user_message, assistant_message],
        "response_message": response,
        "response_metadata": {"agent": "mentor"},
    }
