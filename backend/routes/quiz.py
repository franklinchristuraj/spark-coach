"""
Quiz API Routes
Endpoints for quiz sessions and answer submission
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from auth import verify_token
from agents.quiz_generator import quiz_generator_agent
from models.schemas import (
    QuizStartRequest,
    QuizStartResponse,
    QuizAnswerRequest,
    QuizAnswerResponse,
    Question
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["quiz"],
    dependencies=[Depends(verify_token)]
)


@router.post("/quiz/start", response_model=QuizStartResponse)
async def start_quiz(request: QuizStartRequest) -> Dict[str, Any]:
    """
    Start a new quiz session for a resource

    Args:
        request: Quiz start request with resource_path, num_questions, difficulty

    Returns:
        Quiz session with first question
    """
    try:
        logger.info(f"Starting quiz for {request.resource_path}")

        result = await quiz_generator_agent.start_quiz(
            resource_path=request.resource_path,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )

        return {
            "status": "success",
            **result
        }

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start quiz: {str(e)}")


@router.post("/quiz/answer", response_model=QuizAnswerResponse)
async def submit_answer(request: QuizAnswerRequest) -> Dict[str, Any]:
    """
    Submit an answer to a quiz question

    Args:
        request: Answer request with session_id, question_index, answer

    Returns:
        Score, feedback, and next question or final results
    """
    try:
        logger.info(f"Submitting answer for session {request.session_id}, Q{request.question_index}")

        result = await quiz_generator_agent.score_answer(
            session_id=request.session_id,
            question_index=request.question_index,
            user_answer=request.answer
        )

        return {
            "status": "success",
            **result
        }

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit answer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@router.get("/quiz/session/{session_id}")
async def get_quiz_session(session_id: str) -> Dict[str, Any]:
    """
    Get the status of a quiz session

    Args:
        session_id: Quiz session ID

    Returns:
        Session details and progress
    """
    try:
        from models.database import QuizSession, QuizAnswer, get_db_sync

        db = get_db_sync()
        try:
            session = db.query(QuizSession).filter_by(id=session_id).first()

            if not session:
                raise HTTPException(status_code=404, detail="Quiz session not found")

            # Get answers
            answers = db.query(QuizAnswer).filter_by(session_id=session_id).all()

            return {
                "status": "success",
                "session": {
                    "id": session.id,
                    "resource_path": session.resource_path,
                    "started_at": session.started_at.isoformat(),
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                    "total_questions": session.total_questions,
                    "correct_answers": session.correct_answers,
                    "score": session.score,
                    "status": session.status,
                    "answers_count": len(answers)
                }
            }

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")
