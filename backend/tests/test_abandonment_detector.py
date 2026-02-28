# backend/tests/test_abandonment_detector.py
import pytest
import os
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

# Must set env vars before any project imports
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256")
os.environ.setdefault("SPARK_COACH_PASSWORD_HASH", "")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("MCP_SERVER_URL", "http://localhost:3000")
os.environ.setdefault("MCP_API_KEY", "")
os.environ.setdefault("GEMINI_API_KEY", "fake-gemini-key-for-tests")


def _resource(path, last_reviewed, completion_status="in_progress",
              hours_invested=0, estimated_hours=10,
              key_insights=None, learning_path=""):
    """Helper: build a resource dict shaped like get_active_resources() returns."""
    title = path.split("/")[-1].replace(".md", "")
    return {
        "path": path,
        "title": title,
        "frontmatter": {
            "title": title,
            "last_reviewed": last_reviewed,
            "completion_status": completion_status,
            "hours_invested": hours_invested,
            "estimated_hours": estimated_hours,
            "key_insights": key_insights or [],
            "learning_path": learning_path,
        },
        "content": "Some content",
    }


@pytest.mark.asyncio
async def test_no_resources_returns_empty():
    """When vault has no active resources, run() returns cleanly with zero counts."""
    with patch(
        "agents.abandonment_detector.AbandonmentDetectorAgent.get_active_resources",
        new=AsyncMock(return_value=[]),
    ):
        from agents.abandonment_detector import AbandonmentDetectorAgent
        agent = AbandonmentDetectorAgent()
        result = await agent.run()

    assert result["status"] == "success"
    assert result["at_risk_count"] == 0
    assert result["nudges_created"] == 0
    assert result["resources"] == []


@pytest.mark.asyncio
async def test_low_risk_resources_are_skipped():
    """Resources reviewed today are low-risk and must not be processed."""
    today = datetime.now().strftime("%Y-%m-%d")
    resource = _resource("04_resources/recent.md", last_reviewed=today)

    with patch(
        "agents.abandonment_detector.AbandonmentDetectorAgent.get_active_resources",
        new=AsyncMock(return_value=[resource]),
    ):
        with patch(
            "agents.abandonment_detector.AbandonmentDetectorAgent.update_resource_metadata",
            new=AsyncMock(),
        ) as mock_update:
            from agents.abandonment_detector import AbandonmentDetectorAgent
            agent = AbandonmentDetectorAgent()
            result = await agent.run()

    assert result["at_risk_count"] == 0
    assert result["nudges_created"] == 0
    mock_update.assert_not_called()


@pytest.mark.asyncio
async def test_medium_risk_updates_vault_no_nudge():
    """Resource inactive for 6 days: vault gets abandonment_risk=medium, no nudge."""
    six_days_ago = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
    resource = _resource("04_resources/stale.md", last_reviewed=six_days_ago)

    with patch(
        "agents.abandonment_detector.AbandonmentDetectorAgent.get_active_resources",
        new=AsyncMock(return_value=[resource]),
    ):
        with patch(
            "agents.abandonment_detector.AbandonmentDetectorAgent.update_resource_metadata",
            new=AsyncMock(),
        ) as mock_update:
            from agents.abandonment_detector import AbandonmentDetectorAgent
            agent = AbandonmentDetectorAgent()
            result = await agent.run()

    assert result["at_risk_count"] == 1
    assert result["nudges_created"] == 0
    assert result["resources"][0]["risk_level"] == "medium"
    assert result["resources"][0]["days_inactive"] == 6
    mock_update.assert_called_once_with(
        "04_resources/stale.md", {"abandonment_risk": "medium"}
    )


@pytest.mark.asyncio
async def test_high_risk_creates_nudge():
    """Resource inactive for 11 days: nudge is generated and stored."""
    eleven_days_ago = (datetime.now() - timedelta(days=11)).strftime("%Y-%m-%d")
    resource = _resource(
        "04_resources/abandoned.md",
        last_reviewed=eleven_days_ago,
        key_insights=["LLM observability is key"],
        learning_path="LLMOps",
    )
    fake_nudge = "It's been 11 days — ready to pick up where you left off?"

    with patch(
        "agents.abandonment_detector.AbandonmentDetectorAgent.get_active_resources",
        new=AsyncMock(return_value=[resource]),
    ):
        with patch(
            "agents.abandonment_detector.AbandonmentDetectorAgent.update_resource_metadata",
            new=AsyncMock(),
        ):
            with patch(
                "agents.abandonment_detector.AbandonmentDetectorAgent._generate_nudge",
                new=AsyncMock(return_value=fake_nudge),
            ):
                with patch(
                    "agents.abandonment_detector.AbandonmentDetectorAgent._store_nudge",
                    new=AsyncMock(),
                ) as mock_store:
                    from agents.abandonment_detector import AbandonmentDetectorAgent
                    agent = AbandonmentDetectorAgent()
                    result = await agent.run()

    assert result["at_risk_count"] == 1
    assert result["nudges_created"] == 1
    assert result["resources"][0]["risk_level"] == "high"
    assert result["resources"][0]["days_inactive"] == 11
    assert result["resources"][0]["nudge_sent"] is True
    mock_store.assert_called_once_with("04_resources/abandoned.md", fake_nudge)


@pytest.mark.asyncio
async def test_missing_last_reviewed_is_low_risk():
    """Resources with no last_reviewed date are treated as 0 days inactive (low risk)."""
    resource = _resource("04_resources/new.md", last_reviewed=None)

    with patch(
        "agents.abandonment_detector.AbandonmentDetectorAgent.get_active_resources",
        new=AsyncMock(return_value=[resource]),
    ):
        with patch(
            "agents.abandonment_detector.AbandonmentDetectorAgent.update_resource_metadata",
            new=AsyncMock(),
        ) as mock_update:
            from agents.abandonment_detector import AbandonmentDetectorAgent
            agent = AbandonmentDetectorAgent()
            result = await agent.run()

    assert result["at_risk_count"] == 0
    mock_update.assert_not_called()
