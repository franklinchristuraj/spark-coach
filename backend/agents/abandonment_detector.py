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
        Main entry point - scan all resources and detect abandonment

        Returns:
            Dictionary with detected resources and generated nudges
        """
        logger.info("🔍 Running abandonment detection...")

        try:
            # Get all active and paused resources
            at_risk_resources = await self.get_at_risk_resources()

            if not at_risk_resources:
                logger.info("✓ No at-risk resources found")
                return {
                    "status": "success",
                    "at_risk_count": 0,
                    "nudges_created": 0,
                    "resources": []
                }

            logger.info(f"Found {len(at_risk_resources)} at-risk resources")

            # Process each at-risk resource
            nudges_created = 0
            processed_resources = []

            for resource in at_risk_resources:
                path = resource["path"]
                risk_level = resource["risk_level"]
                days_inactive = resource["days_inactive"]

                # Update abandonment_risk in vault
                await self.update_resource_metadata(path, {
                    "abandonment_risk": risk_level
                })

                # Generate nudge for high-risk resources
                if risk_level == "high":
                    nudge = await self._generate_nudge(resource)
                    if nudge:
                        await self._store_nudge(path, nudge)
                        nudges_created += 1

                processed_resources.append({
                    "path": path,
                    "title": resource["title"],
                    "risk_level": risk_level,
                    "days_inactive": days_inactive,
                    "nudge_sent": risk_level == "high"
                })

            logger.info(f"✓ Processed {len(processed_resources)} resources, created {nudges_created} nudges")

            return {
                "status": "success",
                "at_risk_count": len(at_risk_resources),
                "nudges_created": nudges_created,
                "resources": processed_resources
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
