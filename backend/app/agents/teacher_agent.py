"""
Teacher Agent — teaches concepts with real-world examples,
cloud-specific content, and a closing question.
"""
import json
from app.agents.state import AgentState
from app.agents.prompts import TEACHER_SYSTEM, TEACHER_HUMAN, RETEACH_HUMAN
from app.agents.llm_client import invoke_llm
from app.core.logging import logger

# Cloud-specific teaching additions
CLOUD_NOTES = {
    "aws":   "Include AWS-specific examples where relevant (EC2, S3, RDS, DynamoDB, Lambda, SQS, CloudFront, ElastiCache, EKS).",
    "gcp":   "Include GCP-specific examples where relevant (GCE, GCS, Cloud SQL, Bigtable, Cloud Run, Pub/Sub, BigQuery).",
    "azure": "Include Azure-specific examples where relevant (VMs, Blob Storage, Cosmos DB, Azure Functions, Service Bus, AKS).",
    "none":  "",
    "other": "",
}


async def teacher_node(state: AgentState) -> dict:
    concept_name = state["concept_name"]
    mastery_score = state.get("mastery_score", 0.0)
    weak_subtopics = state.get("weak_subtopics", [])
    mode = state.get("mode", "learn")
    rag_context = state.get("rag_context", "No additional context available.")
    reteach_count = state.get("reteach_count", 0)
    content = state.get("concept_content", {})
    cloud_provider = state.get("cloud_provider", "none")
    cloud_note = CLOUD_NOTES.get(cloud_provider, "")

    system_prompt = TEACHER_SYSTEM.format(
        concept_name=concept_name,
        mastery_score=mastery_score,
        weak_subtopics=", ".join(weak_subtopics) if weak_subtopics else "None yet",
        mode=mode,
        rag_context=rag_context,
    )

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
            extra = "Revision session — briefly recap key points and tricky edge cases only."
        if cloud_note:
            extra = (extra + "\n\n" + cloud_note).strip()

        human_prompt = TEACHER_HUMAN.format(
            concept_name=concept_name,
            description=content.get("description", ""),
            content_json=json.dumps(content, indent=2)[:2000],
            extra_instruction=extra,
        )

    logger.info("teacher_agent_invoked", concept=concept_name, reteach=reteach_count > 0, cloud=cloud_provider)
    teaching_output = await invoke_llm(system_prompt, human_prompt, temperature=0.5)

    new_message = {"role": "assistant", "content": teaching_output, "agent": "teacher"}
    return {
        "teaching_output": teaching_output,
        "agent_action": "ask_question",
        "messages": [new_message],
        "response_message": teaching_output,
        "response_metadata": {
            "agent": "teacher",
            "concept": concept_name,
            "reteach": reteach_count > 0,
            "cloud": cloud_provider,
        },
    }
