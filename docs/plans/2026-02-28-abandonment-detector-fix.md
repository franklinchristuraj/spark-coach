# Abandonment Detector Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix `abandonment_detector.run()` so it calculates risk from live frontmatter data instead of reading a stale field it is supposed to be setting.

**Architecture:** Single-file fix in `backend/agents/abandonment_detector.py`. Replace the circular `get_at_risk_resources()` call with `get_active_resources()`, compute `days_inactive` and `risk_level` inline using the existing `calculate_abandonment_risk()` helper, and pass a correctly-shaped dict to `_generate_nudge()`.

**Tech Stack:** Python 3.13, pytest + pytest-asyncio, unittest.mock (stdlib), FastAPI backend in `backend/`

---

## Context

All commands run from `backend/` directory. The venv is at the repo root:

```bash
cd /Users/a.christuraj/Projects/spark-coach
source venv/bin/activate
cd backend
```

Tests use `pytest`. The existing tests in `backend/tests/` set env vars at the top of each file before importing anything — follow that pattern.

---

## Task 1: Write the failing tests

**Files:**
- Create: `backend/tests/test_abandonment_detector.py`

**Step 1: Create the test file**

```python
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
os.environ.setdefault("GEMINI_API_KEY", "")


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
```

**Step 2: Run tests to verify they fail**

```bash
cd /Users/a.christuraj/Projects/spark-coach
source venv/bin/activate
cd backend
python -m pytest tests/test_abandonment_detector.py -v
```

Expected: All 5 tests FAIL — most will error with `KeyError: 'risk_level'` or `KeyError: 'days_inactive'` because the bug is present.

**Step 3: Commit the failing tests**

```bash
git add backend/tests/test_abandonment_detector.py
git commit -m "test: add failing tests for abandonment detector (FRA-39)"
```

---

## Task 2: Fix `abandonment_detector.run()`

**Files:**
- Modify: `backend/agents/abandonment_detector.py` — replace `run()` only

**Step 1: Replace the `run()` method**

Open `backend/agents/abandonment_detector.py`. Replace the entire `run()` method (lines 26–90) with:

```python
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
```

**Step 2: Run the tests**

```bash
cd /Users/a.christuraj/Projects/spark-coach
source venv/bin/activate
cd backend
python -m pytest tests/test_abandonment_detector.py -v
```

Expected output:
```
PASSED tests/test_abandonment_detector.py::test_no_resources_returns_empty
PASSED tests/test_abandonment_detector.py::test_low_risk_resources_are_skipped
PASSED tests/test_abandonment_detector.py::test_medium_risk_updates_vault_no_nudge
PASSED tests/test_abandonment_detector.py::test_high_risk_creates_nudge
PASSED tests/test_abandonment_detector.py::test_missing_last_reviewed_is_low_risk
5 passed
```

If any test fails, check the error carefully — it will pinpoint what's still wrong.

**Step 3: Run the full existing test suite to check for regressions**

```bash
python -m pytest tests/ -v
```

All previously passing tests should still pass.

**Step 4: Commit the fix**

```bash
git add backend/agents/abandonment_detector.py
git commit -m "fix(abandonment): calculate risk from frontmatter data, not stale field (FRA-39)"
```

---

## Task 3: Manual smoke test via API

This verifies the end-to-end flow: scheduler → nudges endpoint.

**Step 1: Start the backend**

```bash
cd /Users/a.christuraj/Projects/spark-coach
source venv/bin/activate
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

**Step 2: Login to get a JWT token**

```bash
TOKEN=$(curl -s -X POST http://localhost:8081/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"franklin","password":"YOUR_PASSWORD"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: $TOKEN"
```

**Step 3: Manually trigger abandonment check**

```bash
curl -s -X POST http://localhost:8081/api/v1/nudges/run-check \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: JSON with `at_risk_count`, `nudges_created`, and a `resources` list. No 500 errors.

**Step 4: Fetch any pending nudges**

```bash
curl -s http://localhost:8081/api/v1/nudges \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: `{"status": "success", "count": N, "nudges": [...]}` — no KeyError crashes.

**Step 5: Commit smoke test notes (optional)**

If you hit any issues during smoke testing, fix them and commit with:

```bash
git commit -m "fix(abandonment): <describe what was wrong>"
```

---

## Task 4: Update Linear

Mark FRA-38 (Day 3 Quiz System) as Done and FRA-39 (Day 4) as In Progress via Linear.

No code changes — just bookkeeping.

---

## Done

After all 4 tasks, the abandonment detector:
- Calculates risk fresh from vault frontmatter every time it runs
- Updates `abandonment_risk` in vault for medium/high-risk resources
- Generates and stores nudges only for high-risk resources
- Returns a well-shaped response the nudges API can serve
- Has 5 passing unit tests
