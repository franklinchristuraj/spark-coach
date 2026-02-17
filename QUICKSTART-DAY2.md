# SPARK Coach - Day 2 Quick Start

Get your morning briefing working in 10 minutes!

## Prerequisites

- ✅ Day 1 completed (API running, MCP server connected)
- ✅ Anthropic API key in `.env`
- ✅ Obsidian vault with SPARK structure

## Option 1: Quick Test (No Vault Setup)

Test the Day 2 implementation without configuring your vault:

```bash
# 1. Ensure you have Anthropic API key in .env
cat .env | grep ANTHROPIC_API_KEY

# 2. Install new dependencies
cd api
pip install -r requirements.txt
cd ..

# 3. Run the API
make run

# 4. In another terminal, test quick briefing (no LLM)
curl -H "X-API-Key: dev_test_key_12345" \
     http://localhost:8080/api/v1/briefing/quick

# Expected: Returns stats (likely all zeros if vault not configured)
```

## Option 2: Full Setup (With Vault)

Get personalized briefings with your actual learning path:

### Step 1: Create Learning Path (5 min)

1. Open your vault: `~/Documents/franklin-vault/` (or your vault path)

2. Create file: `02_projects/llmops-learning-path.md`

3. Copy this template:

```yaml
---
folder: 02_projects
type: learning_path
created: 2026-02-16
status: active
path_name: "LLMOps & AI Observability"
goal: "Deep expertise in evaluation, observability, guardrails"
target_date: 2026-06-01
resources: []
milestones:
  - name: "Fundamentals"
    resources: []
    status: in_progress
current_milestone: "Fundamentals"
overall_progress: 10
weekly_target_hours: 5
tags:
  - learning-path
  - llmops
---

# LLMOps & AI Observability Learning Path

My learning journey for mastering LLM operations and observability.
```

4. Save and close

### Step 2: Add Learning Metadata to Resources (3 min)

1. Open an existing resource in `04_resources/` (or create one)

2. Add these fields to the frontmatter:

```yaml
# Add to existing resource frontmatter:
learning_status: active
learning_path: "LLMOps & AI Observability"
last_reviewed: "2026-02-16"
next_review: "2026-02-16"
review_count: 0
retention_score: 50
abandonment_risk: low
estimated_hours: 8
hours_invested: 0
key_questions: []
mastery_criteria: "Can explain key concepts and apply them"
```

3. Repeat for 2-3 resources

4. Important: Make sure `learning_path` value matches exactly!

### Step 3: Run and Test (2 min)

```bash
# 1. Start the API
make run

# 2. Get your morning briefing!
curl -H "X-API-Key: dev_test_key_12345" \
     http://localhost:8080/api/v1/briefing | jq

# 3. Or run the full test suite
make test-day2
```

## Expected Output

### Quick Briefing (No LLM)

```json
{
  "status": "success",
  "quick_briefing": {
    "date": "Monday, February 16, 2026",
    "reviews_due_count": 3,
    "at_risk_count": 0,
    "learning_path": "LLMOps & AI Observability",
    "current_milestone": "Fundamentals"
  }
}
```

### Full Briefing (With LLM)

```json
{
  "status": "success",
  "briefing": {
    "date": "Monday, February 16, 2026",
    "greeting": "Morning Franklin. You have 3 reviews due today. Let's build momentum on your LLMOps journey.",
    "reviews_due": [
      {
        "resource": "langfuse-observability",
        "retention": 50,
        "type": "quick_quiz",
        "estimated_minutes": 5
      }
    ],
    "learning_path_progress": {
      "name": "LLMOps & AI Observability",
      "weekly_hours": {"target": 5, "actual": 0},
      "current_milestone": "Fundamentals",
      "overall_progress": 10
    },
    "nudges": [],
    "daily_plan": [
      "Start with the langfuse-observability review",
      "Continue progress on fundamentals",
      "Spend 1 hour on active resources"
    ]
  }
}
```

## Troubleshooting

### "No learning path found"

**Problem:** API returns empty briefing or errors

**Solution:**
1. Check file is in `02_projects/` folder
2. Verify frontmatter has `type: learning_path`
3. Ensure `status: active`
4. Check YAML syntax (use online YAML validator)

### "No reviews due"

**Problem:** Briefing shows 0 reviews

**Solution:**
1. Set `next_review` to today's date or earlier
2. Ensure resources have `learning_status: active`
3. Verify `learning_path` matches exactly (case-sensitive!)

### "MCP server not reachable"

**Problem:** 503 errors from API

**Solution:**
1. Check MCP server is running
2. Verify `MCP_SERVER_URL` in `.env`
3. Test with: `curl http://localhost:3000/health`

### "LLM errors / 500 status"

**Problem:** Full briefing fails with 500 error

**Solution:**
1. Check `ANTHROPIC_API_KEY` in `.env` is valid
2. Verify API key has credits: https://console.anthropic.com/
3. Try quick briefing first (no LLM): `/api/v1/briefing/quick`
4. Check API logs for details

## Next Steps

Once your briefing is working:

1. **Daily Routine:**
   - Morning: `curl -H "X-API-Key: key" http://localhost:8080/api/v1/briefing`
   - Review the resources listed
   - (Day 3+: Take quizzes)

2. **Add More Resources:**
   - Add learning metadata to more notes
   - Update your learning path milestones
   - Set realistic `estimated_hours`

3. **Wait for Day 3:**
   - Quiz system will be implemented
   - Retention scores will update automatically
   - Next review dates calculated via spaced repetition

## Useful Commands

```bash
# Quick stats (fast, no LLM)
curl -H "X-API-Key: dev_test_key_12345" \
     http://localhost:8080/api/v1/briefing/quick | jq

# Full briefing (personalized, uses LLM)
curl -H "X-API-Key: dev_test_key_12345" \
     http://localhost:8080/api/v1/briefing | jq

# Test MCP connectivity
curl -H "X-API-Key: dev_test_key_12345" \
     http://localhost:8080/api/v1/test-mcp | jq

# Search for learning paths
curl -H "X-API-Key: dev_test_key_12345" \
     "http://localhost:8080/api/v1/mcp/search?query=type:+learning_path&folder=02_projects" | jq

# Search for active resources
curl -H "X-API-Key: dev_test_key_12345" \
     "http://localhost:8080/api/v1/mcp/search?query=learning_status:+active&folder=04_resources" | jq

# Run full test suite
make test-day2
```

## Help & Resources

- **Full Setup Guide:** `templates/VAULT-SETUP-GUIDE.md`
- **Learning Path Template:** `templates/obsidian/learning-path-template.md`
- **Resource Template:** `templates/obsidian/resource-with-learning-metadata.md`
- **Implementation Details:** `DAY2-SUMMARY.md`
- **API Docs:** http://localhost:8080/docs (when server running)

---

**You're ready!** Your AI learning coach is now active. 🚀

*Last Updated: 2026-02-16*
