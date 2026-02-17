---
folder: 02_projects
type: learning_path
created: 2026-02-16
status: active
path_name: "LLMOps & AI Observability"
goal: "Deep expertise in evaluation, observability, guardrails, and governance for AI agents"
target_date: 2026-06-01
resources:
  - "[[langfuse-observability]]"
  - "[[prompt-engineering-guide]]"
  - "[[llm-evaluation-frameworks]]"
milestones:
  - name: "Fundamentals"
    resources:
      - "[[llm-basics]]"
      - "[[prompt-engineering-guide]]"
    status: in_progress
  - name: "Evaluation Frameworks"
    resources:
      - "[[llm-evaluation-frameworks]]"
      - "[[llm-as-judge-patterns]]"
    status: not_started
  - name: "Production Observability"
    resources:
      - "[[langfuse-observability]]"
      - "[[opentelemetry-llm]]"
    status: not_started
  - name: "Guardrails & Governance"
    resources:
      - "[[llm-guardrails]]"
      - "[[ai-safety-patterns]]"
    status: not_started
current_milestone: "Fundamentals"
overall_progress: 15
weekly_target_hours: 5
tags:
  - learning-path
  - project
  - llmops
---

# LLMOps & AI Observability Learning Path

## Vision

Become proficient in the full lifecycle of LLM-powered applications: from evaluation and observability to guardrails and governance. This learning path supports building production-ready AI systems with proper monitoring, safety, and accountability.

## Milestones

### 1. Fundamentals (In Progress)
**Goal:** Understand core LLM concepts and prompt engineering patterns
**Estimated:** 2 weeks
**Status:** 15% complete

Resources:
- [[llm-basics]] - Foundation concepts
- [[prompt-engineering-guide]] - Practical patterns

**Success Criteria:**
- Can explain key LLM architecture concepts
- Comfortable with prompt engineering patterns
- Understand token limits and context windows

### 2. Evaluation Frameworks
**Goal:** Master techniques for evaluating LLM outputs
**Estimated:** 3 weeks
**Status:** Not started

Resources:
- [[llm-evaluation-frameworks]] - Overview of evaluation approaches
- [[llm-as-judge-patterns]] - Using LLMs to evaluate LLMs

**Success Criteria:**
- Can design evaluation criteria for use cases
- Understand LLM-as-judge patterns
- Know when to use human vs automated eval

### 3. Production Observability
**Goal:** Implement comprehensive observability for LLM applications
**Estimated:** 4 weeks
**Status:** Not started

Resources:
- [[langfuse-observability]] - Langfuse platform deep dive
- [[opentelemetry-llm]] - Distributed tracing for LLMs

**Success Criteria:**
- Can instrument LLM applications with tracing
- Understand key metrics (latency, cost, quality)
- Can build observability dashboards

### 4. Guardrails & Governance
**Goal:** Implement safety and governance for production LLMs
**Estimated:** 3 weeks
**Status:** Not started

Resources:
- [[llm-guardrails]] - Input/output validation patterns
- [[ai-safety-patterns]] - Safety and alignment approaches

**Success Criteria:**
- Can implement input/output guardrails
- Understand prompt injection defenses
- Know governance best practices

## Weekly Commitment

- **Target:** 5 hours per week
- **Schedule:**
  - Weekday mornings: 45 min before work (3 days)
  - Weekend deep dive: 2 hours (Saturday)
- **Review cycle:** Daily review of active resources, weekly progress check

## Reflection Questions

- What patterns am I noticing across different observability tools?
- How do evaluation approaches differ for different LLM use cases?
- What trade-offs exist between safety guardrails and user experience?

## Connections to Other Paths

This learning path directly supports:
- Building SPARK Coach itself (meta-learning!)
- Applying observability to production AI systems
- Understanding AI safety in the real world

---

*Created: 2026-02-16*
*Last Updated: 2026-02-16*
