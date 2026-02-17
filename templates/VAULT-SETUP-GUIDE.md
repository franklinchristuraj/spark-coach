# SPARK Coach Vault Setup Guide

This guide helps you configure your Obsidian vault to work with SPARK Coach's learning system.

## Prerequisites

- Existing SPARK PKM vault in Obsidian
- Folders: `01_seeds/`, `02_projects/`, `03_daily/`, `04_resources/`, `05_knowledge/`
- Basic familiarity with YAML frontmatter

## Step 1: Create Your Learning Path

1. **Create a new note in `02_projects/`:**
   - Filename: `llmops-ai-observability-learning-path.md` (or your preferred name)
   - Copy the template from `templates/obsidian/learning-path-template.md`

2. **Customize the frontmatter:**
   ```yaml
   path_name: "Your Learning Path Name"
   goal: "Your specific learning goal"
   target_date: YYYY-MM-DD
   weekly_target_hours: X
   ```

3. **Define your milestones:**
   - Break your learning journey into 3-5 major milestones
   - List resources for each milestone
   - Set status: `not_started`, `in_progress`, `completed`

4. **Set current milestone:**
   ```yaml
   current_milestone: "Fundamentals"
   ```

## Step 2: Add Learning Metadata to Resources

For each resource you're actively learning from:

1. **Open the resource note in `04_resources/`**

2. **Add learning fields to frontmatter:**
   ```yaml
   # ── New Learning Fields ──
   learning_status: active
   learning_path: "LLMOps & AI Observability"
   last_reviewed: "2026-02-16"
   next_review: "2026-02-19"
   review_count: 0
   retention_score: 50
   abandonment_risk: low
   estimated_hours: 8
   hours_invested: 0
   key_questions: []
   mastery_criteria: "Define what 'done' looks like"
   ```

3. **Set initial values:**
   - `learning_status`: `active` (if currently studying)
   - `learning_path`: Name of your learning path (must match exactly)
   - `last_reviewed`: Today's date (YYYY-MM-DD)
   - `next_review`: 3 days from now (initial review)
   - `retention_score`: Start at 50 (neutral)
   - `estimated_hours`: How long you think this resource will take
   - `mastery_criteria`: What does "mastering" this resource mean?

4. **Repeat for 2-3 resources** to start with

## Step 3: Link Resources to Learning Path

Update your learning path note to reference your resources:

```yaml
resources:
  - "[[resource-1-name]]"
  - "[[resource-2-name]]"
  - "[[resource-3-name]]"
```

And in each milestone:

```yaml
milestones:
  - name: "Fundamentals"
    resources:
      - "[[resource-1-name]]"
      - "[[resource-2-name]]"
    status: in_progress
```

## Step 4: Configure SPARK Coach API

1. **Set vault path in `.env`:**
   ```bash
   # In spark-coach/.env
   MCP_SERVER_URL=http://localhost:3000
   ```

2. **Ensure your MCP server is running** and pointing to your vault

3. **Test connectivity:**
   ```bash
   curl -H "X-API-Key: your_api_key" \
        http://localhost:8080/api/v1/test-mcp
   ```

## Step 5: Test the Morning Briefing

Run the API server and request your first briefing:

```bash
cd spark-coach
make run

# In another terminal:
curl -H "X-API-Key: your_api_key" \
     http://localhost:8080/api/v1/briefing
```

You should receive:
- Personalized greeting
- List of reviews due
- Learning path progress
- Any abandonment nudges
- Daily plan

## Field Definitions

### Learning Status
- `active`: Currently studying this resource
- `paused`: Temporarily stopped (with intent to resume)
- `abandoned`: Stopped with no plan to resume
- `mastered`: Completed and retained well

### Retention Score (0-100)
- **0-30**: Low retention - needs immediate review
- **31-60**: Medium retention - review soon
- **61-85**: Good retention - review in a week
- **86-100**: Mastered - review in a month

Updated by quiz performance and agent scoring.

### Abandonment Risk
- **low**: Active, recently reviewed
- **medium**: 5+ days without review
- **high**: 7+ days without review and < 50% complete

Calculated automatically by the agent based on:
- Days since last review
- Completion percentage
- Completion status

### Next Review Date
Calculated by agent using spaced repetition:
- Low retention (0-30): Review in 1 day
- Medium retention (31-60): Review in 3 days
- Good retention (61-85): Review in 7 days
- Mastered (86-100): Review in 30 days

## Example Workflow

### Day 1: Setup
1. Create learning path note
2. Add metadata to 3 resources
3. Set all `next_review` to today or tomorrow
4. Test API with `/api/v1/briefing`

### Day 2: First Briefing
1. Morning: Get briefing
2. See 3 resources due for review
3. Study one resource
4. (Day 3+: Take quiz to update retention)

### Day 3+: Routine
1. Morning briefing shows what's due
2. Complete reviews (quizzes)
3. Agent updates `retention_score` and `next_review`
4. Continue with active resources
5. Get nudges for at-risk resources

## Troubleshooting

### "No learning path found"
- Check that `type: learning_path` is in frontmatter
- Ensure note is in `02_projects/` folder
- Verify `status: active`

### "No reviews due"
- Check `next_review` dates are not in the future
- Verify `learning_status: active` on resources
- Ensure resources have `learning_path` matching your path name

### "MCP server not reachable"
- Verify MCP server is running
- Check `MCP_SERVER_URL` in `.env`
- Test with `/api/v1/test-mcp` endpoint

### Resources not found
- Ensure resources are in `04_resources/` folder
- Check `learning_path` name matches exactly (case-sensitive)
- Verify frontmatter YAML is valid (no syntax errors)

## Tips

1. **Start small:** Begin with one learning path and 3-5 resources
2. **Be specific:** Write clear, measurable mastery criteria
3. **Update regularly:** Let the agent update metadata, but review manually weekly
4. **Honest estimates:** Set realistic `estimated_hours` and `weekly_target_hours`
5. **Rich notes:** The better your resource notes, the better the quiz questions

## Next Steps

Once your vault is configured:
1. ✅ Get daily briefings working
2. Wait for Day 3: Quiz system implementation
3. Wait for Day 4: Abandonment detection with scheduled jobs
4. Wait for Day 5: Voice input for quick captures

---

*Last Updated: 2026-02-16*
*SPARK Coach: Day 2 Implementation*
