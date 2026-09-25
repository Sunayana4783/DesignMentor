"""
/api/learn — main learning session endpoint.
Calls agents directly without LangGraph to avoid state merge issues.
"""
import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.core.deps import CurrentUser, DBSession
from app.schemas.learning import LearnRequest, LearnResponse
from app.models.progress import LearningSession
from app.models.curriculum import Concept
from app.models.progress import UserProgress
from app.core.logging import logger

router = APIRouter()


@router.post("/", response_model=LearnResponse)
async def learn(req: LearnRequest, current_user: CurrentUser, db: DBSession):
    # ── Load or create session ────────────────────────────────────────────
    session_id = req.session_id
    conversation_history = []

    if session_id:
        result = await db.execute(
            select(LearningSession).where(
                LearningSession.id == uuid.UUID(session_id),
                LearningSession.user_id == current_user.id,
                LearningSession.is_active == True,
            )
        )
        session = result.scalar_one_or_none()
        if session:
            conversation_history = session.conversation_history or []
    else:
        session = None

    if not session:
        session = LearningSession(
            id=uuid.uuid4(),
            user_id=current_user.id,
            mode=req.mode,
            conversation_history=[],
            agent_state={},
        )
        db.add(session)
        await db.flush()
        session_id = str(session.id)

    # ── Load concept ──────────────────────────────────────────────────────
    concept_result = await db.execute(
        select(Concept).where(Concept.slug == req.concept_slug)
    )
    concept = concept_result.scalar_one_or_none()
    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept '{req.concept_slug}' not found")

    # ── Load student progress ─────────────────────────────────────────────
    progress_result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.concept_id == concept.id,
        )
    )
    progress = progress_result.scalar_one_or_none()
    mastery_score = progress.mastery_score if progress else 0.0
    weak_subtopics = progress.weak_subtopics if progress else []

    # ── Load onboarding preferences (cloud provider) ──────────────────────
    from app.models.onboarding import UserOnboarding
    onboarding_result = await db.execute(
        select(UserOnboarding).where(UserOnboarding.user_id == current_user.id)
    )
    onboarding = onboarding_result.scalar_one_or_none()
    cloud_provider = onboarding.cloud_provider.value if onboarding else "none"

    # ── RAG context (best-effort) ─────────────────────────────────────────
    rag_context = ""
    try:
        from app.rag.retriever import retrieve_context
        rag_context = await retrieve_context(
            query=f"{concept.name} {concept.description}",
            concept_slug=req.concept_slug,
            top_k=2,
            db=db,
        )
    except Exception:
        pass

    # ── Build agent state ─────────────────────────────────────────────────
    state = {
        "user_id":        str(current_user.id),
        "session_id":     session_id,
        "mode":           req.mode,
        "concept_slug":   req.concept_slug,
        "concept_name":   concept.name,
        "concept_content": concept.content,
        "mastery_score":  mastery_score,
        "weak_subtopics": weak_subtopics,
        "user_input":     req.user_message,
        "messages":       conversation_history,
        "rag_context":    rag_context,
        "reteach_count":  0,
        "agent_action":   "teach",
        "cloud_provider": cloud_provider,
    }

    # ── Route to correct agent ────────────────────────────────────────────
    user_input = req.user_message.strip()
    mode = req.mode

    try:
        if mode == "interview":
            from app.agents.interview_agent import interview_node
            result_state = await interview_node(state)

        elif mode == "design":
            from app.agents.design_reviewer_agent import design_reviewer_node
            result_state = await design_reviewer_node(state)

        elif not user_input:
            # No input → teach the concept
            from app.agents.teacher_agent import teacher_node
            result_state = await teacher_node(state)

        elif mode in ("quiz", "quick", "revision"):
            # User answered a quiz question → evaluate
            from app.agents.quiz_agent import quiz_node
            result_state = await quiz_node(state)

        else:
            # User sent a message → mentor responds
            from app.agents.mentor_agent import mentor_node
            result_state = await mentor_node(state)

    except Exception as exc:
        logger.error("agent_error", error=str(exc), concept=req.concept_slug)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(exc)}")

    # ── Extract response ──────────────────────────────────────────────────
    response_message = result_state.get("response_message", "")
    if not response_message:
        # Fallback: get last assistant message
        new_msgs = result_state.get("messages", [])
        for msg in reversed(new_msgs):
            if msg.get("role") == "assistant" and msg.get("content"):
                response_message = msg["content"]
                break

    agent_action = result_state.get("agent_action", "teach")
    response_metadata = result_state.get("response_metadata", {})

    # ── Persist session ───────────────────────────────────────────────────
    new_messages = result_state.get("messages", [])
    if user_input:
        user_msg = {"role": "user", "content": user_input, "agent": "user"}
        conversation_history = conversation_history + [user_msg] + new_messages
    else:
        conversation_history = conversation_history + new_messages

    session.conversation_history = conversation_history[-20:]  # keep last 20 messages
    await db.commit()

    logger.info(
        "learn_response",
        concept=req.concept_slug,
        agent_action=agent_action,
        message_len=len(response_message),
    )

    return LearnResponse(
        session_id=session_id,
        agent_message=response_message,
        agent_action=agent_action,
        concept_slug=req.concept_slug,
        mode=mode,
        metadata=response_metadata,
    )


@router.delete("/session/{session_id}")
async def end_session(session_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == uuid.UUID(session_id),
            LearningSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if session:
        session.is_active = False
        session.ended_at = datetime.now(timezone.utc)
        await db.commit()
    return {"status": "ended"}


@router.post("/stream")
async def learn_stream(req: LearnRequest, current_user: CurrentUser, db: DBSession):
    """
    Streaming version of the learn endpoint.
    Returns Server-Sent Events (SSE) — tokens arrive word by word.
    Only used for teacher and mentor agents (not quiz/design/interview).
    """
    # ── Load or create session ────────────────────────────────────────────
    session_id = req.session_id
    conversation_history = []

    if session_id:
        result = await db.execute(
            select(LearningSession).where(
                LearningSession.id == uuid.UUID(session_id),
                LearningSession.user_id == current_user.id,
                LearningSession.is_active == True,
            )
        )
        session = result.scalar_one_or_none()
        if session:
            conversation_history = session.conversation_history or []
    else:
        session = None

    if not session:
        session = LearningSession(
            id=uuid.uuid4(),
            user_id=current_user.id,
            mode=req.mode,
            conversation_history=[],
            agent_state={},
        )
        db.add(session)
        await db.flush()
        session_id = str(session.id)

    # ── Load concept ──────────────────────────────────────────────────────
    concept_result = await db.execute(
        select(Concept).where(Concept.slug == req.concept_slug)
    )
    concept = concept_result.scalar_one_or_none()
    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept '{req.concept_slug}' not found")

    # ── Load student progress ─────────────────────────────────────────────
    progress_result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.concept_id == concept.id,
        )
    )
    progress = progress_result.scalar_one_or_none()
    mastery_score = progress.mastery_score if progress else 0.0
    weak_subtopics = progress.weak_subtopics if progress else []

    # ── Load onboarding preferences ───────────────────────────────────────
    from app.models.onboarding import UserOnboarding
    onboarding_result = await db.execute(
        select(UserOnboarding).where(UserOnboarding.user_id == current_user.id)
    )
    onboarding = onboarding_result.scalar_one_or_none()
    cloud_provider = onboarding.cloud_provider.value if onboarding else "none"

    # ── RAG context (best-effort) ─────────────────────────────────────────
    rag_context = ""
    try:
        from app.rag.retriever import retrieve_context
        rag_context = await retrieve_context(
            query=f"{concept.name} {concept.description}",
            concept_slug=req.concept_slug,
            top_k=2,
            db=db,
        )
    except Exception:
        pass

    user_input = req.user_message.strip()
    mode = req.mode

    # ── Non-streamable modes → fall back to regular endpoint ─────────────
    if mode in ("quiz", "design", "interview"):
        raise HTTPException(
            status_code=400,
            detail="Use /api/learn/ for quiz, design, and interview modes."
        )

    # ── Build prompts based on agent type ────────────────────────────────
    from app.agents.prompts import (
        TEACHER_SYSTEM, TEACHER_HUMAN,
        MENTOR_SYSTEM, MENTOR_HUMAN,
    )
    import json as _json

    if not user_input:
        extra = f"Cloud provider preference: {cloud_provider}. Use {cloud_provider}-specific examples where relevant." if cloud_provider != "none" else ""
        system_prompt = TEACHER_SYSTEM.format(
            concept_name=concept.name,
            mastery_score=mastery_score,
            weak_subtopics=", ".join(weak_subtopics) if weak_subtopics else "none",
            mode=mode,
            rag_context=rag_context or "No additional context available.",
        )
        human_prompt = TEACHER_HUMAN.format(
            concept_name=concept.name,
            description=concept.description,
            content_json=_json.dumps(concept.content, indent=2)[:1500],
            extra_instruction=extra,
        )
        agent_action = "ask_question"
    else:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content'][:200]}"
            for m in conversation_history[-10:]
        )
        system_prompt = MENTOR_SYSTEM
        human_prompt = MENTOR_HUMAN.format(
            concept_name=concept.name,
            conversation_history=history_text,
            user_input=user_input,
        )
        agent_action = "teach"

    # ── Stream generator ──────────────────────────────────────────────────
    from app.agents.llm_client import stream_llm

    async def event_generator():
        full_response = ""

        meta = _json.dumps({
            "type": "meta",
            "session_id": session_id,
            "agent_action": agent_action,
            "concept_slug": req.concept_slug,
            "mode": mode,
        })
        yield f"data: {meta}\n\n"

        try:
            async for token in stream_llm(system_prompt, human_prompt):
                full_response += token
                payload = _json.dumps({"type": "token", "content": token})
                yield f"data: {payload}\n\n"
        except Exception as exc:
            logger.error("stream_error", error=str(exc))
            err = _json.dumps({"type": "error", "content": "Stream interrupted."})
            yield f"data: {err}\n\n"
            return

        done = _json.dumps({"type": "done", "content": full_response})
        yield f"data: {done}\n\n"

        try:
            new_msg = {
                "role": "assistant",
                "content": full_response,
                "agent": "teacher" if not user_input else "mentor",
            }
            if user_input:
                user_msg = {"role": "user", "content": user_input, "agent": "user"}
                updated_history = conversation_history + [user_msg, new_msg]
            else:
                updated_history = conversation_history + [new_msg]

            session.conversation_history = updated_history[-20:]
            await db.commit()
        except Exception as exc:
            logger.warning("stream_session_persist_failed", error=str(exc))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
