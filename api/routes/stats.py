"""
Stats & Dashboard API Routes
Endpoints for learning analytics and progress tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from auth import verify_api_key
from models.database import QuizSession, QuizAnswer, LearningLog, get_db_sync

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["stats"],
    dependencies=[Depends(verify_api_key)]
)


@router.get("/stats/dashboard")
async def get_dashboard_stats(period: str = "this_week") -> Dict[str, Any]:
    """
    Get aggregated learning statistics for dashboard

    Metrics included:
    - Streak tracking (current and longest)
    - Learning hours (weekly target vs actual)
    - Retention scores (average and trends)
    - Resource status (active, at-risk, mastered)
    - Quiz completion stats

    Args:
        period: Time period for stats (default: "this_week")

    Returns:
        Dashboard statistics dictionary
    """
    try:
        logger.info(f"Fetching dashboard stats for period: {period}")

        db = get_db_sync()
        try:
            # Calculate date ranges
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)

            # Get this week's data
            week_start_dt = datetime.combine(week_start, datetime.min.time())
            week_end_dt = datetime.combine(week_end, datetime.max.time())

            # ─── STREAKS ───
            streaks = await _calculate_streaks(db)

            # ─── LEARNING HOURS ───
            learning_hours = await _calculate_learning_hours(db, week_start_dt, week_end_dt)

            # ─── RETENTION SCORES ───
            retention = await _calculate_retention(db, week_start_dt)

            # ─── RESOURCE STATUS ───
            resources = await _calculate_resource_status()

            # ─── QUIZ STATS ───
            quizzes = await _calculate_quiz_stats(db, week_start_dt, week_end_dt)

            return {
                "status": "success",
                "period": f"{week_start.isocalendar()[0]}-W{week_start.isocalendar()[1]:02d}",
                "streaks": streaks,
                "learning_hours": learning_hours,
                "retention": retention,
                "resources": resources,
                "quizzes": quizzes,
                "generated_at": datetime.now().isoformat()
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to generate dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate stats: {str(e)}"
        )


async def _calculate_streaks(db) -> Dict[str, int]:
    """Calculate current and longest learning streaks"""
    try:
        # Get all learning logs ordered by date
        logs = db.query(LearningLog)\
            .order_by(LearningLog.timestamp.desc())\
            .limit(90)\
            .all()

        if not logs:
            return {"current_days": 0, "longest_ever": 0}

        # Group by date
        active_dates = set()
        for log in logs:
            active_dates.add(log.timestamp.date())

        # Calculate current streak
        current_streak = 0
        check_date = datetime.now().date()

        while check_date in active_dates:
            current_streak += 1
            check_date -= timedelta(days=1)

        # Calculate longest streak
        sorted_dates = sorted(active_dates, reverse=True)
        longest_streak = 1
        current_run = 1

        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i-1] - sorted_dates[i]).days == 1:
                current_run += 1
                longest_streak = max(longest_streak, current_run)
            else:
                current_run = 1

        return {
            "current_days": current_streak,
            "longest_ever": max(longest_streak, current_streak)
        }

    except Exception as e:
        logger.error(f"Streak calculation failed: {str(e)}")
        return {"current_days": 0, "longest_ever": 0}


async def _calculate_learning_hours(db, week_start: datetime, week_end: datetime) -> Dict[str, Any]:
    """Calculate learning hours for the week"""
    try:
        logs = db.query(LearningLog)\
            .filter(LearningLog.timestamp >= week_start)\
            .filter(LearningLog.timestamp <= week_end)\
            .all()

        total_minutes = sum(log.duration_minutes for log in logs if log.duration_minutes)
        total_hours = round(total_minutes / 60, 1)

        # Get previous week for trend
        prev_week_start = week_start - timedelta(days=7)
        prev_logs = db.query(LearningLog)\
            .filter(LearningLog.timestamp >= prev_week_start)\
            .filter(LearningLog.timestamp < week_start)\
            .all()

        prev_hours = round(sum(log.duration_minutes for log in prev_logs if log.duration_minutes) / 60, 1)

        trend = "up" if total_hours > prev_hours else "down" if total_hours < prev_hours else "flat"

        return {
            "this_week": total_hours,
            "target": 5.0,  # Default target, could be from learning path
            "trend": trend,
            "previous_week": prev_hours
        }

    except Exception as e:
        logger.error(f"Learning hours calculation failed: {str(e)}")
        return {"this_week": 0, "target": 5.0, "trend": "flat"}


async def _calculate_retention(db, week_start: datetime) -> Dict[str, Any]:
    """Calculate retention scores and trends"""
    try:
        # Get recent quiz sessions
        sessions = db.query(QuizSession)\
            .filter(QuizSession.started_at >= week_start - timedelta(days=30))\
            .filter(QuizSession.status == "completed")\
            .all()

        if not sessions:
            return {
                "average_score": 0,
                "improving": [],
                "declining": []
            }

        # Calculate average
        avg_score = int(sum(s.score for s in sessions) / len(sessions))

        # Group by resource to find trends
        resource_scores = {}
        for session in sessions:
            path = session.resource_path
            if path not in resource_scores:
                resource_scores[path] = []
            resource_scores[path].append({
                "score": session.score,
                "date": session.started_at
            })

        # Find improving and declining
        improving = []
        declining = []

        for path, scores in resource_scores.items():
            if len(scores) >= 2:
                # Sort by date
                sorted_scores = sorted(scores, key=lambda x: x["date"])
                recent = sorted_scores[-1]["score"]
                previous = sorted_scores[-2]["score"]

                resource_name = path.split("/")[-1].replace(".md", "").replace("-", " ")

                if recent > previous + 10:
                    improving.append(resource_name)
                elif recent < previous - 10:
                    declining.append(resource_name)

        return {
            "average_score": avg_score,
            "improving": improving[:3],
            "declining": declining[:3]
        }

    except Exception as e:
        logger.error(f"Retention calculation failed: {str(e)}")
        return {"average_score": 0, "improving": [], "declining": []}


async def _calculate_resource_status() -> Dict[str, int]:
    """Calculate resource status counts"""
    try:
        from mcp_client import mcp_client
        from agents.base_agent import BaseAgent

        agent = BaseAgent()

        # Get active resources
        active = await agent.get_active_resources()
        at_risk = await agent.get_at_risk_resources()

        # Count mastered (resources with retention_score > 85)
        mastered = 0
        for resource in active:
            retention = resource.get("retention_score", 0)
            if retention > 85:
                mastered += 1

        return {
            "active": len(active),
            "at_risk": len(at_risk),
            "mastered": mastered,
            "total_in_path": len(active) + mastered  # Simplified
        }

    except Exception as e:
        logger.error(f"Resource status calculation failed: {str(e)}")
        return {"active": 0, "at_risk": 0, "mastered": 0, "total_in_path": 0}


async def _calculate_quiz_stats(db, week_start: datetime, week_end: datetime) -> Dict[str, Any]:
    """Calculate quiz completion statistics"""
    try:
        sessions = db.query(QuizSession)\
            .filter(QuizSession.started_at >= week_start)\
            .filter(QuizSession.started_at <= week_end)\
            .filter(QuizSession.status == "completed")\
            .all()

        if not sessions:
            return {
                "completed_this_week": 0,
                "average_score": 0
            }

        avg_score = int(sum(s.score for s in sessions) / len(sessions))

        return {
            "completed_this_week": len(sessions),
            "average_score": avg_score,
            "total_questions_answered": sum(s.total_questions for s in sessions)
        }

    except Exception as e:
        logger.error(f"Quiz stats calculation failed: {str(e)}")
        return {"completed_this_week": 0, "average_score": 0}


@router.get("/stats/streak")
async def get_streak() -> Dict[str, Any]:
    """
    Get current learning streak

    Returns:
        Current streak count and longest streak
    """
    try:
        db = get_db_sync()
        try:
            streaks = await _calculate_streaks(db)
            return {
                "status": "success",
                **streaks
            }
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to get streak: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get streak: {str(e)}"
        )


@router.get("/stats/weekly-summary")
async def get_weekly_summary() -> Dict[str, Any]:
    """
    Get condensed weekly learning summary

    Returns:
        Key weekly metrics in summary format
    """
    try:
        db = get_db_sync()
        try:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            week_start_dt = datetime.combine(week_start, datetime.min.time())
            week_end_dt = datetime.combine(week_end, datetime.max.time())

            quizzes = await _calculate_quiz_stats(db, week_start_dt, week_end_dt)
            hours = await _calculate_learning_hours(db, week_start_dt, week_end_dt)
            streaks = await _calculate_streaks(db)

            return {
                "status": "success",
                "week": f"Week of {week_start.strftime('%b %d')}",
                "quizzes_completed": quizzes["completed_this_week"],
                "average_score": quizzes["average_score"],
                "hours_invested": hours["this_week"],
                "current_streak": streaks["current_days"],
                "on_track": hours["this_week"] >= hours["target"] * 0.7  # 70% of target
            }
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to get weekly summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get summary: {str(e)}"
        )
