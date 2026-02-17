"""
Briefing API Routes
Endpoints for morning briefing and daily learning plans
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from auth import verify_api_key
from agents.morning_briefing import morning_briefing_agent

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["briefing"],
    dependencies=[Depends(verify_api_key)]
)


@router.get("/briefing")
async def get_morning_briefing() -> Dict[str, Any]:
    """
    Get today's morning briefing with personalized learning plan

    Returns:
        Briefing with:
        - Greeting message
        - Reviews due today
        - Learning path progress
        - Abandonment nudges
        - Recommended daily plan
    """
    try:
        logger.info("Generating morning briefing")

        # Run the morning briefing agent
        briefing = await morning_briefing_agent.run()

        return {
            "status": "success",
            "briefing": briefing
        }

    except Exception as e:
        logger.error(f"Failed to generate briefing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate briefing: {str(e)}"
        )


@router.get("/briefing/quick")
async def get_quick_briefing() -> Dict[str, Any]:
    """
    Get a quick briefing summary (no LLM generation, just stats)

    Returns:
        Quick summary of learning status
    """
    try:
        logger.info("Generating quick briefing")

        # Use morning briefing agent's helper methods without LLM
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        reviews_due = await morning_briefing_agent.get_resources_due_for_review(today)
        at_risk = await morning_briefing_agent.get_at_risk_resources("medium")
        learning_path = await morning_briefing_agent.get_learning_path()

        return {
            "status": "success",
            "quick_briefing": {
                "date": datetime.now().strftime("%A, %B %d, %Y"),
                "reviews_due_count": len(reviews_due),
                "at_risk_count": len(at_risk),
                "learning_path": learning_path.get("frontmatter", {}).get("path_name") if learning_path else None,
                "current_milestone": learning_path.get("frontmatter", {}).get("current_milestone") if learning_path else None
            }
        }

    except Exception as e:
        logger.error(f"Failed to generate quick briefing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quick briefing: {str(e)}"
        )
