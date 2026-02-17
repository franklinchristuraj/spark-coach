"""
Base Agent for SPARK Coach
Abstract base class that all agents inherit from
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from mcp_client import mcp_client
from llm_client import llm_client

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all SPARK Coach agents"""

    def __init__(self):
        """Initialize agent with MCP and LLM clients"""
        self.mcp = mcp_client
        self.llm = llm_client
        self.agent_name = self.__class__.__name__

    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the agent's main logic

        Returns:
            Dictionary containing agent results
        """
        pass

    # ─────────────────────────────────────────────────────────────────────────
    # Shared Helper Methods
    # ─────────────────────────────────────────────────────────────────────────

    async def get_active_resources(self, learning_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all active learning resources

        Args:
            learning_path: Optional filter by learning path name

        Returns:
            List of active resource dictionaries with metadata
        """
        try:
            # Search for notes with learning_status: active in resources folder
            results = await self.mcp.search_notes(
                query="learning_status",  # Simpler keyword
                folder="04_resources"
            )

            resources = []
            for result in results:
                try:
                    # Read full note to get metadata
                    note = await self.mcp.read_note(result.get("path"))
                    frontmatter = note.get("frontmatter", {})

                    # Filter by learning path if specified
                    if learning_path and frontmatter.get("learning_path") != learning_path:
                        continue

                    resources.append({
                        "path": result.get("path"),
                        "title": result.get("title", "Untitled"),
                        "frontmatter": frontmatter,
                        "content": note.get("content", "")
                    })
                except Exception as e:
                    logger.warning(f"Failed to read resource {result.get('path')}: {str(e)}")
                    continue

            logger.info(f"Found {len(resources)} active resources")
            return resources

        except Exception as e:
            logger.error(f"Failed to get active resources: {str(e)}")
            return []

    async def get_learning_path(self, path_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get a learning path by name or get the first active learning path

        Args:
            path_name: Optional specific learning path name

        Returns:
            Learning path dictionary or None
        """
        try:
            # Search in projects folder for learning_path type
            results = await self.mcp.search_notes(
                query="learning_path",  # Simpler keyword for keyword search
                folder="02_projects"
            )

            for result in results:
                try:
                    note = await self.mcp.read_note(result.get("path"))
                    frontmatter = note.get("frontmatter", {})

                    # Check if type is learning_path
                    if frontmatter.get("type") != "learning_path":
                        continue

                    # If specific path requested, check name match
                    if path_name and frontmatter.get("path_name") != path_name:
                        continue

                    # Return first match
                    return {
                        "path": result.get("path"),
                        "title": result.get("title", "Untitled"),
                        "frontmatter": frontmatter,
                        "content": note.get("content", "")
                    }

                except Exception as e:
                    logger.warning(f"Failed to read learning path {result.get('path')}: {str(e)}")
                    continue

            logger.warning(f"No learning path found for: {path_name or 'any'}")
            return None

        except Exception as e:
            logger.error(f"Failed to get learning path: {str(e)}")
            return None

    async def get_resources_due_for_review(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get resources that are due for review

        Args:
            date: Date to check (YYYY-MM-DD), defaults to today

        Returns:
            List of resources due for review
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            resources = await self.get_active_resources()

            due_resources = []
            for resource in resources:
                frontmatter = resource.get("frontmatter", {})
                next_review = frontmatter.get("next_review", "")

                # Check if review is due (next_review <= today)
                if next_review and next_review <= date:
                    due_resources.append(resource)

            logger.info(f"Found {len(due_resources)} resources due for review on {date}")
            return due_resources

        except Exception as e:
            logger.error(f"Failed to get resources due for review: {str(e)}")
            return []

    async def get_at_risk_resources(self, risk_level: str = "medium") -> List[Dict[str, Any]]:
        """
        Get resources at risk of abandonment

        Args:
            risk_level: Minimum risk level (low, medium, high)

        Returns:
            List of at-risk resources
        """
        risk_levels = {"low": 0, "medium": 1, "high": 2}
        min_risk = risk_levels.get(risk_level, 1)

        try:
            resources = await self.get_active_resources()

            at_risk = []
            for resource in resources:
                frontmatter = resource.get("frontmatter", {})
                resource_risk = frontmatter.get("abandonment_risk", "low")
                resource_risk_value = risk_levels.get(resource_risk, 0)

                if resource_risk_value >= min_risk:
                    at_risk.append(resource)

            logger.info(f"Found {len(at_risk)} resources at {risk_level}+ risk")
            return at_risk

        except Exception as e:
            logger.error(f"Failed to get at-risk resources: {str(e)}")
            return []

    async def update_resource_metadata(
        self,
        path: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a resource's frontmatter metadata

        Args:
            path: Resource path
            updates: Dictionary of frontmatter fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read current note
            note = await self.mcp.read_note(path)
            current_frontmatter = note.get("frontmatter", {})

            # Merge updates
            updated_frontmatter = {**current_frontmatter, **updates}

            # Update note
            await self.mcp.update_note(
                path=path,
                frontmatter=updated_frontmatter
            )

            logger.info(f"Updated metadata for {path}: {list(updates.keys())}")
            return True

        except Exception as e:
            logger.error(f"Failed to update resource metadata for {path}: {str(e)}")
            return False

    async def get_recent_daily_notes(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get recent daily notes for context

        Args:
            days: Number of recent days to fetch

        Returns:
            List of recent daily notes
        """
        try:
            # List notes in daily notes folder (assuming 03_daily or similar)
            notes = await self.mcp.list_notes(folder="03_daily", recursive=False)

            # Sort by date (assuming filename or frontmatter has date)
            # Take the most recent 'days' notes
            recent_notes = sorted(
                notes,
                key=lambda x: x.get("modified", ""),
                reverse=True
            )[:days]

            # Read full content for each
            daily_notes = []
            for note_meta in recent_notes:
                try:
                    note = await self.mcp.read_note(note_meta.get("path"))
                    daily_notes.append(note)
                except Exception as e:
                    logger.warning(f"Failed to read daily note {note_meta.get('path')}: {str(e)}")
                    continue

            logger.info(f"Retrieved {len(daily_notes)} recent daily notes")
            return daily_notes

        except Exception as e:
            logger.warning(f"Failed to get recent daily notes: {str(e)}")
            return []

    def calculate_abandonment_risk(
        self,
        last_reviewed: Optional[str],
        completion_status: str,
        hours_invested: float,
        estimated_hours: float
    ) -> str:
        """
        Calculate abandonment risk based on activity patterns

        Args:
            last_reviewed: Last review date (YYYY-MM-DD)
            completion_status: Resource completion status
            hours_invested: Hours spent on resource
            estimated_hours: Estimated total hours

        Returns:
            Risk level: low, medium, or high
        """
        if not last_reviewed:
            return "medium"

        # Calculate days since last review
        try:
            last_date = datetime.strptime(last_reviewed, "%Y-%m-%d")
            days_since = (datetime.now() - last_date).days
        except Exception:
            days_since = 0

        # Calculate completion percentage
        completion_pct = (hours_invested / estimated_hours * 100) if estimated_hours > 0 else 0

        # Risk logic from spec:
        # High risk: in_progress + no review in 7+ days + < 50% complete
        # Medium risk: no review in 5+ days
        # Low risk: everything else

        if completion_status == "in_progress":
            if days_since >= 10:
                return "high"
            elif days_since >= 7 and completion_pct < 50:
                return "high"
            elif days_since >= 5:
                return "medium"

        if days_since >= 5:
            return "medium"

        return "low"

    def calculate_next_review_date(
        self,
        retention_score: int,
        last_reviewed: Optional[str] = None
    ) -> str:
        """
        Calculate next review date using spaced repetition

        Args:
            retention_score: Score 0-100
            last_reviewed: Last review date (defaults to today)

        Returns:
            Next review date (YYYY-MM-DD)
        """
        from datetime import timedelta

        if last_reviewed:
            try:
                base_date = datetime.strptime(last_reviewed, "%Y-%m-%d")
            except Exception:
                base_date = datetime.now()
        else:
            base_date = datetime.now()

        # Spaced repetition intervals from spec
        if retention_score <= 30:
            interval_days = 1
        elif retention_score <= 60:
            interval_days = 3
        elif retention_score <= 85:
            interval_days = 7
        else:  # 86-100
            interval_days = 30

        next_date = base_date + timedelta(days=interval_days)
        return next_date.strftime("%Y-%m-%d")

    def format_time_ago(self, date_str: str) -> str:
        """
        Format a date as relative time (e.g., '3 days ago')

        Args:
            date_str: Date string (YYYY-MM-DD)

        Returns:
            Relative time string
        """
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            delta = datetime.now() - date
            days = delta.days

            if days == 0:
                return "today"
            elif days == 1:
                return "yesterday"
            elif days < 7:
                return f"{days} days ago"
            elif days < 30:
                weeks = days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                months = days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
        except Exception:
            return "unknown"
