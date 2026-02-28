"""
Abandonment Detector Agent
Identifies stale resources and generates personalized nudges
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging
import json

from agents.base_agent import BaseAgent
from models.database import NudgeHistory, LearningLog, get_db_sync

logger = logging.getLogger(__name__)


class AbandonmentDetectorAgent(BaseAgent):
    """
    Detects abandoned resources and generates motivational nudges

    Risk Levels:
    - LOW: Reviewed within last 5 days
    - MEDIUM: No activity 5-10 days
    - HIGH: No activity > 10 days
    """

    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Scan all active resources, calculate abandonment risk from scratch,
        update vault metadata, and generate nudges for high-risk resources.
        """
        logger.info("🔍 Running abandonment detection...")

        try:
            resources = await self.get_active_resources()

            if not resources:
                logger.info("✓ No active resources found")
                return {
                    "status": "success",
                    "at_risk_count": 0,
                    "nudges_created": 0,
                    "resources": [],
                }

            nudges_created = 0
            processed_resources = []

            for resource in resources:
                path = resource["path"]
                frontmatter = resource.get("frontmatter", {})
                title = frontmatter.get("title", path.split("/")[-1].replace(".md", ""))
                last_reviewed = frontmatter.get("last_reviewed")

                # Calculate days inactive
                if last_reviewed:
                    try:
                        last_date = datetime.strptime(last_reviewed, "%Y-%m-%d")
                        days_inactive = (datetime.now() - last_date).days
                    except Exception:
                        days_inactive = 0
                else:
                    days_inactive = 0

                # Calculate risk using the base agent helper
                risk_level = self.calculate_abandonment_risk(
                    last_reviewed=last_reviewed,
                    completion_status=frontmatter.get("completion_status", "in_progress"),
                    hours_invested=float(frontmatter.get("hours_invested", 0)),
                    estimated_hours=float(frontmatter.get("estimated_hours", 1)),
                )

                if risk_level == "low":
                    continue

                # Update vault with calculated risk level
                await self.update_resource_metadata(path, {"abandonment_risk": risk_level})

                # Generate and store nudge for high-risk resources only
                nudge_sent = False
                if risk_level == "high":
                    enriched = {
                        "path": path,
                        "title": title,
                        "days_inactive": days_inactive,
                        "key_insights": frontmatter.get("key_insights", []),
                        "learning_path": frontmatter.get("learning_path", ""),
                    }
                    nudge = await self._generate_nudge(enriched)
                    if nudge:
                        await self._store_nudge(path, nudge)
                        nudges_created += 1
                        nudge_sent = True

                processed_resources.append({
                    "path": path,
                    "title": title,
                    "risk_level": risk_level,
                    "days_inactive": days_inactive,
                    "nudge_sent": nudge_sent,
                })

            logger.info(
                f"✓ Processed {len(processed_resources)} at-risk resources, "
                f"created {nudges_created} nudges"
            )

            return {
                "status": "success",
                "at_risk_count": len(processed_resources),
                "nudges_created": nudges_created,
                "resources": processed_resources,
            }

        except Exception as e:
            logger.error(f"Abandonment detection failed: {str(e)}")
            raise

    async def _generate_nudge(self, resource: Dict[str, Any]) -> str:
        """
        Generate a personalized motivational nudge using LLM

        Args:
            resource: Resource info with path, title, insights, learning_path

        Returns:
            Nudge message text
        """
        try:
            title = resource["title"]
            days_inactive = resource["days_inactive"]
            key_insights = resource.get("key_insights", [])
            learning_path = resource.get("learning_path", "")

            # Build context about WHY the user started this resource
            motivation_context = ""
            if key_insights:
                motivation_context = f"Original insights that interested them: {', '.join(key_insights[:2])}"
            elif learning_path:
                motivation_context = f"Part of their {learning_path} learning journey"

            system_prompt = """You are a supportive learning coach for the SPARK system.
Generate a brief, personal nudge message to re-engage someone with an abandoned resource.

Guidelines:
- Reference WHY they started this (their original motivation/insights)
- Be warm but direct - acknowledge the gap without guilt
- Include a clear micro-action to restart (e.g., "review your notes for 5 minutes")
- Keep it to 2-3 sentences max
- Make it feel personal, not automated"""

            user_message = f"""Generate a nudge for this abandoned resource:

Resource: "{title}"
Days inactive: {days_inactive}
{motivation_context}

Create a motivational message to help them restart."""

            nudge = await self.llm.complete(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=256,
                temperature=0.9  # Higher temperature for more personal feel
            )

            logger.info(f"Generated nudge for {title}")
            return nudge.strip()

        except Exception as e:
            logger.error(f"Failed to generate nudge: {str(e)}")
            # Fallback to template message
            return f"It's been {days_inactive} days since you last reviewed \"{title}\". Ready to pick up where you left off? Just 5 minutes to refresh your memory."

    async def _store_nudge(self, resource_path: str, message: str) -> bool:
        """
        Store nudge in database

        Args:
            resource_path: Path to resource
            message: Nudge message

        Returns:
            True if stored successfully
        """
        try:
            db = get_db_sync()
            try:
                nudge = NudgeHistory(
                    resource_path=resource_path,
                    nudge_type="abandonment",
                    message=message,
                    delivered=False  # Will be marked True when sent via push notification
                )
                db.add(nudge)
                db.commit()

                logger.info(f"Stored nudge for {resource_path}")
                return True

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to store nudge: {str(e)}")
            return False

    async def get_pending_nudges(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get pending nudges that haven't been delivered

        Args:
            limit: Maximum number of nudges to return

        Returns:
            List of nudge dictionaries
        """
        try:
            db = get_db_sync()
            try:
                nudges = db.query(NudgeHistory)\
                    .filter_by(delivered=False)\
                    .order_by(NudgeHistory.created_at.desc())\
                    .limit(limit)\
                    .all()

                result = []
                for nudge in nudges:
                    result.append({
                        "id": nudge.id,
                        "resource_path": nudge.resource_path,
                        "nudge_type": nudge.nudge_type,
                        "message": nudge.message,
                        "created_at": nudge.created_at.isoformat()
                    })

                return result

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to get pending nudges: {str(e)}")
            return []

    async def mark_nudges_delivered(self, nudge_ids: List[int]) -> bool:
        """
        Mark nudges as delivered

        Args:
            nudge_ids: List of nudge IDs to mark

        Returns:
            True if successful
        """
        try:
            db = get_db_sync()
            try:
                for nudge_id in nudge_ids:
                    nudge = db.query(NudgeHistory).filter_by(id=nudge_id).first()
                    if nudge:
                        nudge.delivered = True
                        nudge.delivered_at = datetime.utcnow()

                db.commit()
                logger.info(f"Marked {len(nudge_ids)} nudges as delivered")
                return True

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to mark nudges delivered: {str(e)}")
            return False


# Global agent instance
abandonment_detector_agent = AbandonmentDetectorAgent()
