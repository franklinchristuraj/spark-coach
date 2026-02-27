"""
Nudges API Routes
Endpoints for retrieving and managing learning nudges
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List
import logging

from auth import verify_token
from agents.abandonment_detector import abandonment_detector_agent

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["nudges"],
    dependencies=[Depends(verify_token)]
)


@router.get("/nudges")
async def get_nudges(limit: int = 10) -> Dict[str, Any]:
    """
    Get pending nudges that haven't been delivered

    Args:
        limit: Maximum number of nudges to return (default 10)

    Returns:
        List of pending nudges with messages
    """
    try:
        logger.info(f"Fetching pending nudges (limit: {limit})")

        nudges = await abandonment_detector_agent.get_pending_nudges(limit=limit)

        return {
            "status": "success",
            "count": len(nudges),
            "nudges": nudges
        }

    except Exception as e:
        logger.error(f"Failed to get nudges: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve nudges: {str(e)}"
        )


@router.post("/nudges/mark-delivered")
async def mark_nudges_delivered(
    nudge_ids: List[int] = Body(..., embed=True)
) -> Dict[str, Any]:
    """
    Mark nudges as delivered (typically called after push notification sent)

    Args:
        nudge_ids: List of nudge IDs to mark as delivered

    Returns:
        Success status
    """
    try:
        logger.info(f"Marking {len(nudge_ids)} nudges as delivered")

        success = await abandonment_detector_agent.mark_nudges_delivered(nudge_ids)

        if success:
            return {
                "status": "success",
                "marked": len(nudge_ids),
                "message": f"Marked {len(nudge_ids)} nudges as delivered"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to mark nudges as delivered"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark nudges delivered: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark nudges delivered: {str(e)}"
        )


@router.post("/nudges/run-check")
async def run_abandonment_check() -> Dict[str, Any]:
    """
    Manually trigger abandonment detection
    (Normally runs automatically at 20:00 daily)

    Returns:
        Detection results with at-risk resources and nudges created
    """
    try:
        logger.info("Manual abandonment check triggered")

        result = await abandonment_detector_agent.run()

        return result

    except Exception as e:
        logger.error(f"Manual abandonment check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Abandonment check failed: {str(e)}"
        )
