---
folder: 04_resources
type: resource
created: 2026-02-16
status: in_progress
title: "Langfuse - LLM Observability Platform"
url: "https://langfuse.com/docs"
source_type: documentation
completion_status: in_progress

# ── Existing SPARK Fields ──
key_insights:
  - "Langfuse models LLM execution as traces containing observations (spans, generations, events)"
  - "Supports scoring and evaluation with custom metrics"
  - "Can integrate with OpenAI SDK via drop-in wrapper"
tags:
  - llmops
  - observability
  - evaluation

# ── New Learning Fields ──
learning_status: active
learning_path: "LLMOps & AI Observability"
last_reviewed: "2026-02-16"
next_review: "2026-02-19"
review_count: 2
retention_score: 65
abandonment_risk: low
estimated_hours: 8
hours_invested: 3
key_questions:
  - "What are the three core data types Langfuse uses to model LLM execution traces?"
  - "How would you use Langfuse to detect hallucination in your SPARK Coach quiz generator agent?"
  - "What's the difference between a span and a generation in Langfuse?"
mastery_criteria: "Can instrument a multi-agent LLM application with Langfuse, set up custom scoring, and build an observability dashboard"
---

# Langfuse - LLM Observability Platform

## Overview

Langfuse is an open-source observability platform designed specifically for LLM applications. It provides tracing, evaluation, and analytics for understanding and improving LLM-powered systems.

## Core Concepts

### Traces and Observations

Langfuse models LLM execution hierarchically:

```
Trace (root execution)
  └─ Observations
      ├─ Spans (operations with duration)
      ├─ Generations (LLM calls)
      └─ Events (point-in-time occurrences)
```

**Trace:** Top-level container representing a full execution (e.g., one user request)
**Span:** An operation with a start and end time (e.g., "retrieve context from vector DB")
**Generation:** A specific LLM call with prompt, completion, and metadata
**Event:** A point-in-time occurrence (e.g., "user feedback received")

### Scoring and Evaluation

Langfuse supports multiple evaluation patterns:

1. **Manual Scoring:** Human annotators review and score outputs
2. **Model-Based Scoring:** LLM-as-judge patterns for automated evaluation
3. **Rule-Based Scoring:** Deterministic checks (length, format, keywords)
4. **Custom Metrics:** User-defined scoring functions

Scores are attached to traces or generations and can be:
- Numeric (0-1, 0-100)
- Categorical (pass/fail, quality levels)
- Boolean (correct/incorrect)

## Integration Patterns

### OpenAI SDK Integration

```python
from langfuse.openai import OpenAI

# Drop-in replacement for OpenAI client
client = OpenAI(api_key="...")

# Automatic trace creation
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Custom Instrumentation

```python
from langfuse import Langfuse

langfuse = Langfuse()

# Create trace
trace = langfuse.trace(name="user_query")

# Add generation
generation = trace.generation(
    name="llm_call",
    model="claude-sonnet-4-5",
    input="What is LLMOps?",
    output="LLMOps is..."
)

# Add score
trace.score(name="quality", value=0.85)
```

## Use Cases for SPARK Coach

### 1. Agent Observability

Instrument each SPARK Coach agent:
- Morning Briefing Agent: Track greeting generation quality
- Quiz Generator: Monitor question generation and scoring accuracy
- Connection Finder: Measure connection relevance

### 2. Cost Tracking

Monitor token usage and costs across:
- Daily briefings
- Quiz generation
- Coaching messages
- Connection finding

### 3. Quality Evaluation

Implement LLM-as-judge for:
- Coaching message tone and relevance
- Quiz question clarity and difficulty
- Connection insight quality

### 4. Performance Monitoring

Track latencies:
- End-to-end API response times
- Individual agent execution times
- MCP server call durations

## Key Insights

1. **Hierarchical Modeling:** The trace → observation hierarchy mirrors how LLM applications actually work (request → operations → LLM calls)

2. **Evaluation First-Class:** Unlike generic observability tools, Langfuse treats evaluation/scoring as a core primitive

3. **SDK Integration:** Drop-in wrappers for popular SDKs reduce instrumentation effort

4. **Open Source:** Self-hostable for data sovereignty and privacy

## Open Questions

- How does Langfuse handle distributed tracing across multiple services?
- Can you retroactively add scores to traces (e.g., based on user feedback)?
- What's the performance overhead of instrumentation?
- How does it compare to alternatives like LangSmith or Phoenix?

## Next Steps

1. ✅ Read Langfuse documentation overview
2. 🔲 Set up local Langfuse instance
3. 🔲 Instrument one SPARK Coach agent as proof-of-concept
4. 🔲 Build a simple dashboard for agent performance
5. 🔲 Implement LLM-as-judge evaluation for quiz questions

## Connections

- **Related to:** [[llm-evaluation-frameworks]], [[opentelemetry-llm]], [[llm-as-judge-patterns]]
- **Supports:** Building observability into SPARK Coach (meta-learning!)
- **Contrasts with:** Generic APM tools (New Relic, Datadog) - LLM-specific vs. generic

---

*Source:* https://langfuse.com/docs
*Last Reviewed:* 2026-02-16
*Next Review:* 2026-02-19 (3 days - medium retention)
*Retention Score:* 65/100
*Hours Invested:* 3 / 8 estimated
