"""
/api/interview — stateful interview mode sessions.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import CurrentUser, DBSession
from app.models.progress import InterviewSession
from app.schemas.learning import (
    InterviewStartRequest,
    InterviewMessageRequest,
    InterviewMessageResponse,
)
from app.agents.orchestrator import run_agent
from app.core.logging import logger

router = APIRouter()


@router.post("/start", response_model=InterviewMessageResponse)
async def start_interview(
    req: InterviewStartRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Start a new interview session. AI opens with the first question."""
    session = InterviewSession(
        id=uuid.uuid4(),
        user_id=current_user.id,
        problem=req.problem,
        phase=req.phase,
        conversation_history=[],
        scorecard={},
    )
    db.add(session)
    await db.flush()

    # Run one turn with empty user message so AI opens
    initial_state = {
        "user_id":        str(current_user.id),
        "session_id":     str(session.id),
        "mode":           "interview",
        "concept_slug":   req.problem.lower().replace(" ", "-"),
        "concept_name":   req.problem,
        "user_input":     "",
        "interview_turn": 0,
        "messages":       [],
    }

    final_state = await run_agent(initial_state, db)

    session.conversation_history = final_state.get("messages", [])
    await db.commit()

    return InterviewMessageResponse(
        session_id=session.id,
        ai_message=final_state.get("response_message", ""),
        is_completed=False,
    )


@router.post("/message", response_model=InterviewMessageResponse)
async def interview_message(
    req: InterviewMessageRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Send a message in an ongoing interview session."""
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == req.session_id,
            InterviewSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    if session.is_completed:
        raise HTTPException(status_code=400, detail="Interview already completed")

    turn = len([m for m in session.conversation_history if m.get("role") == "user"])

    initial_state = {
        "user_id":        str(current_user.id),
        "session_id":     str(session.id),
        "mode":           "interview",
        "concept_slug":   session.problem.lower().replace(" ", "-")[:50],
        "concept_name":   session.problem,
        "user_input":     req.user_message,
        "interview_turn": turn,
        "messages":       session.conversation_history,
    }

    final_state = await run_agent(initial_state, db)

    is_completed = final_state.get("agent_action") == "generate_scorecard"
    scorecard = final_state.get("interview_scorecard", {})

    session.conversation_history = final_state.get("messages", [])
    if is_completed:
        session.is_completed = True
        session.scorecard = scorecard
        session.overall_score = float(scorecard.get("overall_score", 0)) * 10
        session.ended_at = datetime.now(timezone.utc)

    await db.commit()

    return InterviewMessageResponse(
        session_id=session.id,
        ai_message=final_state.get("response_message", ""),
        is_completed=is_completed,
        scorecard=scorecard if is_completed else None,
    )


@router.get("/sessions", response_model=list[dict])
async def list_interview_sessions(current_user: CurrentUser, db: DBSession):
    """List all interview sessions for the current user."""
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.user_id == current_user.id)
        .order_by(InterviewSession.started_at.desc())
        .limit(20)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "problem": s.problem,
            "phase": s.phase,
            "is_completed": s.is_completed,
            "overall_score": s.overall_score,
            "started_at": s.started_at.isoformat(),
        }
        for s in sessions
    ]
