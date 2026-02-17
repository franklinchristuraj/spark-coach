"""
Morning Briefing Agent
Generates personalized daily learning plan by analyzing vault state
"""
from typing import Dict, Any, List
from datetime import datetime
import logging

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class MorningBriefingAgent(BaseAgent):
    """
    Generates morning briefing with:
    - Reviews due today
    - Learning path progress
    - Abandonment nudges
    - Personalized daily plan
    """

    async def run(self, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate morning briefing

        Args:
            user_context: Optional context (timezone, preferences, etc.)

        Returns:
            Briefing data with greeting, reviews, progress, nudges, and plan
        """
        logger.info(f"Running {self.agent_name}")

        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        today_formatted = datetime.now().strftime("%A, %B %d, %Y")

        # Gather data from vault
        reviews_due = await self.get_resources_due_for_review(today)
        learning_path = await self.get_learning_path()
        at_risk = await self.get_at_risk_resources(risk_level="medium")

        # Get recent daily notes for mood/energy context
        recent_notes = await self.get_recent_daily_notes(days=3)

        # Calculate learning path progress
        path_progress = await self._calculate_path_progress(learning_path)

        # Generate personalized greeting and plan
        briefing_data = await self._generate_briefing(
            date=today_formatted,
            reviews_due=reviews_due,
            learning_path=learning_path,
            path_progress=path_progress,
            at_risk=at_risk,
            recent_notes=recent_notes
        )

        logger.info(f"Briefing generated: {len(reviews_due)} reviews, {len(at_risk)} at-risk")

        return briefing_data

    async def _calculate_path_progress(
        self,
        learning_path: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate learning path progress metrics"""
        if not learning_path:
            return {
                "weekly_hours": {"target": 0, "actual": 0},
                "behind_by": 0,
                "current_milestone": None,
                "overall_progress": 0
            }

        frontmatter = learning_path.get("frontmatter", {})

        # Get target hours
        weekly_target = frontmatter.get("weekly_target_hours", 5)

        # Calculate actual hours this week (would need to sum from logs)
        # For now, use placeholder - will integrate with database in Day 3
        actual_hours = 0  # TODO: Calculate from learning_logs in database

        # Get current milestone and overall progress
        current_milestone = frontmatter.get("current_milestone", "Unknown")
        overall_progress = frontmatter.get("overall_progress", 0)

        return {
            "weekly_hours": {
                "target": weekly_target,
                "actual": actual_hours
            },
            "behind_by": max(0, weekly_target - actual_hours),
            "current_milestone": current_milestone,
            "overall_progress": overall_progress
        }

    async def _generate_briefing(
        self,
        date: str,
        reviews_due: List[Dict[str, Any]],
        learning_path: Dict[str, Any],
        path_progress: Dict[str, Any],
        at_risk: List[Dict[str, Any]],
        recent_notes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate personalized briefing using LLM"""

        # Build context for LLM
        context = self._build_context(
            reviews_due=reviews_due,
            learning_path=learning_path,
            path_progress=path_progress,
            at_risk=at_risk,
            recent_notes=recent_notes
        )

        # Generate greeting and daily plan
        greeting = await self._generate_greeting(context, path_progress)

        # Format reviews due
        formatted_reviews = self._format_reviews(reviews_due)

        # Generate nudges for at-risk resources
        nudges = await self._generate_nudges(at_risk)

        # Generate recommended daily plan
        daily_plan = await self._generate_daily_plan(context)

        # Compile briefing
        briefing = {
            "date": date,
            "greeting": greeting,
            "reviews_due": formatted_reviews,
            "reviews_count": len(reviews_due),
            "learning_path_progress": {
                "name": learning_path.get("frontmatter", {}).get("path_name") if learning_path else None,
                "weekly_hours": path_progress.get("weekly_hours"),
                "current_milestone": path_progress.get("current_milestone"),
                "overall_progress": path_progress.get("overall_progress", 0)
            },
            "nudges": nudges,
            "daily_plan": daily_plan,
            "stats": {
                "active_resources": len(reviews_due) + len(at_risk),
                "at_risk_count": len(at_risk),
                "completion_rate": path_progress.get("overall_progress", 0)
            }
        }

        return briefing

    def _build_context(
        self,
        reviews_due: List[Dict[str, Any]],
        learning_path: Dict[str, Any],
        path_progress: Dict[str, Any],
        at_risk: List[Dict[str, Any]],
        recent_notes: List[Dict[str, Any]]
    ) -> str:
        """Build context string for LLM"""

        context_parts = []

        # Learning path info
        if learning_path:
            fm = learning_path.get("frontmatter", {})
            context_parts.append(f"Learning Path: {fm.get('path_name', 'Unknown')}")
            context_parts.append(f"Goal: {fm.get('goal', 'Not specified')}")
            context_parts.append(f"Current Milestone: {path_progress.get('current_milestone')}")
            context_parts.append(f"Progress: {path_progress.get('overall_progress', 0)}%")

        # Weekly progress
        weekly = path_progress.get("weekly_hours", {})
        context_parts.append(f"\nWeekly Target: {weekly.get('target', 0)} hours")
        context_parts.append(f"Actual This Week: {weekly.get('actual', 0)} hours")
        context_parts.append(f"Behind By: {path_progress.get('behind_by', 0)} hours")

        # Reviews due
        if reviews_due:
            context_parts.append(f"\nReviews Due Today: {len(reviews_due)}")
            for r in reviews_due[:3]:  # Show first 3
                title = r.get("title", "Untitled")
                retention = r.get("frontmatter", {}).get("retention_score", 0)
                context_parts.append(f"  - {title} (retention: {retention}%)")

        # At-risk resources
        if at_risk:
            context_parts.append(f"\nAt-Risk Resources: {len(at_risk)}")
            for r in at_risk[:2]:  # Show first 2
                title = r.get("title", "Untitled")
                risk = r.get("frontmatter", {}).get("abandonment_risk", "unknown")
                last_review = r.get("frontmatter", {}).get("last_reviewed", "never")
                context_parts.append(f"  - {title} (risk: {risk}, last: {last_review})")

        # Recent activity hints from daily notes
        if recent_notes:
            context_parts.append(f"\nRecent Activity: {len(recent_notes)} daily notes")

        return "\n".join(context_parts)

    async def _generate_greeting(self, context: str, path_progress: Dict[str, Any]) -> str:
        """Generate personalized greeting"""

        behind_by = path_progress.get("behind_by", 0)

        # Build coaching query
        query = f"""Generate a brief morning greeting (1-2 sentences) for a learner.

Status:
- Behind weekly target by {behind_by} hours
- Focus on {path_progress.get('current_milestone')}

Be {('encouraging' if behind_by < 3 else 'urgent')}, specific, and action-oriented."""

        try:
            greeting = await self.llm.coach_message(
                context=context,
                query=query,
                tone="encouraging" if behind_by < 3 else "urgent",
                max_tokens=256
            )
            return greeting.strip()
        except Exception as e:
            logger.error(f"Failed to generate greeting: {str(e)}")
            # Fallback greeting
            name = "Franklin"  # TODO: Get from user profile
            return f"Morning {name}. You have reviews due and learning to do. Let's make progress today."

    def _format_reviews(self, reviews_due: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format reviews due for response"""
        formatted = []

        for review in reviews_due:
            fm = review.get("frontmatter", {})
            retention = fm.get("retention_score", 50)

            # Determine review type based on retention score
            if retention <= 30:
                review_type = "full_quiz"
                estimated_minutes = 10
            elif retention <= 60:
                review_type = "quick_quiz"
                estimated_minutes = 5
            elif retention <= 85:
                review_type = "connection_prompt"
                estimated_minutes = 3
            else:
                review_type = "application_challenge"
                estimated_minutes = 5

            formatted.append({
                "resource": review.get("title", "Untitled"),
                "path": review.get("path"),
                "retention": retention,
                "type": review_type,
                "estimated_minutes": estimated_minutes,
                "last_reviewed": fm.get("last_reviewed", "never")
            })

        # Sort by priority (lowest retention first)
        formatted.sort(key=lambda x: x["retention"])

        return formatted

    async def _generate_nudges(self, at_risk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate nudges for at-risk resources"""
        nudges = []

        for resource in at_risk:
            fm = resource.get("frontmatter", {})
            title = resource.get("title", "Untitled")
            risk = fm.get("abandonment_risk", "medium")
            last_reviewed = fm.get("last_reviewed", "")
            completion_status = fm.get("completion_status", "in_progress")

            # Calculate days inactive
            days_inactive = 0
            if last_reviewed:
                try:
                    from datetime import datetime
                    last_date = datetime.strptime(last_reviewed, "%Y-%m-%d")
                    days_inactive = (datetime.now() - last_date).days
                except Exception:
                    pass

            # Generate personalized nudge message
            context = f"""Resource: {title}
Status: {completion_status}
Last reviewed: {self.format_time_ago(last_reviewed) if last_reviewed else 'never'}
Risk level: {risk}
Days inactive: {days_inactive}"""

            query = "Generate a brief nudge (1 sentence) to re-engage with this resource. Reference why they started it if possible."

            try:
                message = await self.llm.coach_message(
                    context=context,
                    query=query,
                    tone="encouraging",
                    max_tokens=256
                )
            except Exception as e:
                logger.error(f"Failed to generate nudge: {str(e)}")
                message = f"You were making progress on {title}. Ready to pick it back up?"

            nudges.append({
                "type": "abandonment",
                "resource": title,
                "path": resource.get("path"),
                "days_inactive": days_inactive,
                "risk_level": risk,
                "message": message.strip()
            })

        return nudges

    async def _generate_daily_plan(self, context: str) -> List[str]:
        """Generate recommended daily plan"""

        query = """Generate a prioritized daily learning plan (3-4 action items).
Each item should be specific and achievable today.
Focus on: 1) Reviews due, 2) Active resource progress, 3) At-risk items.

Return as a simple bullet list."""

        try:
            plan_text = await self.llm.coach_message(
                context=context,
                query=query,
                tone="reflective",
                max_tokens=512
            )

            # Parse bullet points
            lines = plan_text.strip().split("\n")
            plan_items = []
            for line in lines:
                line = line.strip()
                if line.startswith("-") or line.startswith("•") or line.startswith("*"):
                    plan_items.append(line[1:].strip())
                elif line and len(plan_items) < 4:
                    plan_items.append(line)

            return plan_items[:4]  # Max 4 items

        except Exception as e:
            logger.error(f"Failed to generate daily plan: {str(e)}")
            # Fallback plan
            return [
                "Complete reviews that are due today",
                "Continue progress on active resources",
                "Review at-risk items to prevent abandonment"
            ]


# Global agent instance
morning_briefing_agent = MorningBriefingAgent()
