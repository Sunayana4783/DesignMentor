"""
Teacher Agent — Node in the LangGraph pipeline.
Generates concept explanations with examples and ends with a question.
"""
import json
from app.agents.state import AgentState
from app.agents.prompts import TEACHER_SYSTEM, TEACHER_HUMAN, RETEACH_HUMAN
from app.agents.llm_client import invoke_llm
from app.core.logging import logger


async def teacher_node(state: AgentState) -> dict:
    """
    LangGraph node: teaches or re-teaches a concept.
    Reads state, calls LLM, returns partial state update.
    """
    concept_name = state["concept_name"]
    mastery_score = state.get("mastery_score", 0.0)
    weak_subtopics = state.get("weak_subtopics", [])
    mode = state.get("mode", "learn")
    rag_context = state.get("rag_context", "No additional context available.")
    reteach_count = state.get("reteach_count", 0)
    content = state.get("concept_content", {})

    system_prompt = TEACHER_SYSTEM.format(
        concept_name=concept_name,
        mastery_score=mastery_score,
        weak_subtopics=", ".join(weak_subtopics) if weak_subtopics else "None yet",
        mode=mode,
        rag_context=rag_context,
    )

    # Choose human prompt based on whether this is a reteach
    if reteach_count > 0 and weak_subtopics:
        human_prompt = RETEACH_HUMAN.format(
            weak_subtopics=", ".join(weak_subtopics),
            concept_name=concept_name,
        )
    else:
        extra = ""
        if mode == "quick":
            extra = "Keep this very concise — 3-4 key points maximum, one code example."
        elif mode == "revision":
            extra = "This is a revision session. Be brief — highlight key points and tricky edge cases only."

        human_prompt = TEACHER_HUMAN.format(
            concept_name=concept_name,
            description=content.get("description", ""),
            content_json=json.dumps(content, indent=2)[:2000],
            extra_instruction=extra,
        )

    logger.info("teacher_agent_invoked", concept=concept_name, reteach=reteach_count > 0)
    teaching_output = await invoke_llm(system_prompt, human_prompt, temperature=0.5)

    new_message = {
        "role": "assistant",
        "content": teaching_output,
        "agent": "teacher",
    }

    return {
        "teaching_output": teaching_output,
        "agent_action": "ask_question",
        "messages": [new_message],
        "response_message": teaching_output,
        "response_metadata": {
            "agent": "teacher",
            "concept": concept_name,
            "reteach": reteach_count > 0,
        },
    }
