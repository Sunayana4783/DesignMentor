"""
Design Reviewer Agent — evaluates LLD/HLD design submissions.
Checks against a structured checklist for each problem type.
"""
import json
from app.agents.state import AgentState
from app.agents.prompts import DESIGN_REVIEWER_SYSTEM, DESIGN_REVIEWER_HUMAN
from app.agents.llm_client import invoke_llm_json
from app.core.logging import logger

# Checklists per problem type
DESIGN_CHECKLISTS: dict[str, dict] = {
    "lld-parking-lot": {
        "Entities identified": "Did the student identify ParkingLot, ParkingSpot, Vehicle, Ticket?",
        "Inheritance hierarchy": "Is there a Vehicle hierarchy (Car, Bike, Truck)?",
        "Spot types handled": "Are compact, large, handicapped spots addressed?",
        "Design pattern used": "Is Factory, Strategy, or Singleton used appropriately?",
        "SOLID compliance": "Does the design follow SRP and OCP?",
        "Ticket/pricing": "Is a Ticket class and pricing strategy present?",
    },
    "lld-elevator": {
        "State machine": "Is elevator state (IDLE, MOVING_UP, etc.) modelled?",
        "Scheduling algorithm": "Is a scheduling strategy (FCFS, SCAN) present?",
        "Request handling": "Are both floor requests and cabin requests handled?",
        "Multiple elevators": "Does the design support multiple elevators?",
        "Observer pattern": "Is there event notification between components?",
    },
    "hld-url-shortener": {
        "Short code generation": "Is a base62 encoding or similar approach described?",
        "Database choice": "Is there a justified DB choice?",
        "Caching": "Is Redis or similar cache proposed for redirects?",
        "Load balancing": "Is a load balancer included?",
        "Scalability": "Is horizontal scaling addressed?",
        "Analytics (bonus)": "Is click tracking mentioned?",
    },
    "hld-instagram": {
        "Upload flow": "Is the photo upload flow described (S3 + CDN)?",
        "Feed generation": "Is push vs pull model discussed?",
        "Database design": "Is a DB chosen and schema sketched?",
        "Caching strategy": "Is feed/profile caching addressed?",
        "CDN": "Is a CDN used for media delivery?",
        "Notification service": "Is notification/event handling present?",
        "Scalability": "Are bottlenecks and scaling solutions addressed?",
    },
    "hld-rate-limiter": {
        "Algorithm choice": "Is a rate limiting algorithm described?",
        "Distributed operation": "Is the distributed nature addressed?",
        "Redis usage": "Is Redis used for counter storage?",
        "Race conditions": "Are race conditions and atomic operations addressed?",
        "Per-user vs global": "Is per-user rate limiting distinguished from global?",
    },
    "default": {
        "Requirements addressed": "Are functional requirements covered?",
        "Architecture diagram": "Is the high-level architecture described?",
        "Database": "Is data storage addressed?",
        "Scalability": "Is scaling mentioned?",
        "Failure modes": "Are single points of failure addressed?",
    },
}


async def design_reviewer_node(state: AgentState) -> dict:
    """LangGraph node: reviews a design submission and returns structured feedback."""
    # Design submissions are passed via the user_input field
    # with metadata in response_metadata from the route
    submission = state.get("user_input", "")
    concept_slug = state.get("concept_slug", "")
    mode = state.get("mode", "design")
    phase = "lld" if "lld" in concept_slug else "hld"

    # Determine checklist
    checklist = DESIGN_CHECKLISTS.get(concept_slug, DESIGN_CHECKLISTS["default"])

    human_prompt = DESIGN_REVIEWER_HUMAN.format(
        problem_name=state.get("concept_name", concept_slug),
        phase=phase.upper(),
        difficulty=state.get("response_metadata", {}).get("difficulty", "intermediate"),
        submission=submission[:3000],
        checklist=json.dumps(checklist, indent=2),
    )

    logger.info("design_reviewer_invoked", problem=concept_slug, phase=phase)
    review = await invoke_llm_json(DESIGN_REVIEWER_SYSTEM, human_prompt, temperature=0.3)

    score = float(review.get("score", 50))
    follow_up = review.get("follow_up_question", "What would you change if we needed 10x the scale?")
    overall_feedback = review.get("overall_feedback", "")

    # Compose response message
    strengths = review.get("strengths", [])
    improvements = review.get("improvements", [])

    parts = [overall_feedback, ""]
    if strengths:
        parts.append("**Strengths:**")
        parts.extend(f"✓ {s}" for s in strengths)
    if improvements:
        parts.append("\n**Areas to improve:**")
        parts.extend(f"• {i}" for i in improvements)
    parts.append(f"\n**Follow-up question:** _{follow_up}_")

    response_message = "\n".join(parts)

    assistant_message = {
        "role": "assistant",
        "content": response_message,
        "agent": "design_reviewer",
    }

    return {
        "agent_action": "design_review",
        "design_checklist": review.get("checklist_results", {}),
        "evaluation_score": score,
        "evaluation_feedback": overall_feedback,
        "messages": [assistant_message],
        "response_message": response_message,
        "response_metadata": {
            "agent": "design_reviewer",
            "score": score,
            "checklist_results": review.get("checklist_results", {}),
            "strengths": strengths,
            "improvements": improvements,
            "follow_up_question": follow_up,
        },
    }
