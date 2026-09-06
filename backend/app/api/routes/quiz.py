"""
/api/quiz — structured quiz flow separate from the freeform learn endpoint.
"""
import uuid
from fastapi import APIRouter
from app.core.deps import CurrentUser, DBSession
from app.schemas.learning import (
    QuizStartRequest, QuizSessionOut,
    SubmitAnswerRequest, AnswerFeedback,
    QuizResultOut,
)
from app.services.quiz_service import QuizService

router = APIRouter()


@router.post("/start", response_model=QuizSessionOut)
async def start_quiz(
    req: QuizStartRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Start a quiz for a concept. Returns all questions upfront."""
    return await QuizService.start_quiz(current_user.id, req, db)


@router.post("/answer", response_model=AnswerFeedback)
async def submit_answer(
    req: SubmitAnswerRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Submit an answer to a single quiz question. Returns immediate AI feedback."""
    return await QuizService.submit_answer(current_user.id, req, db)


@router.post("/complete/{attempt_id}", response_model=QuizResultOut)
async def complete_quiz(
    attempt_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Close the quiz attempt, compute final score, update mastery,
    run RF prediction, detect weak topics, and return the full result.
    """
    return await QuizService.complete_quiz(current_user.id, attempt_id, db)
