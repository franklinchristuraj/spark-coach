# SPARK Coach — Technical Specification v1.0

> AI Learning & Accountability System  
> February 2026 | Franklin | Guinea Pig Learning Path: LLMOps & AI Observability

---

## 1. System Overview

SPARK Coach is an AI-powered learning and accountability system that transforms a passive Obsidian knowledge vault into an active coaching partner. The system connects to the existing SPARK PKM methodology via MCP server, uses LLM APIs for reasoning and coaching, and delivers learning experiences through a React Native mobile app.

### 1.1 Core Problem Statement

Knowledge is captured but not retained. Resources are started but not completed. Insights are stored but not applied. The system lacks active feedback loops that surface the right knowledge at the right time and hold the learner accountable to finishing what they start.

### 1.2 Architecture Overview

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| Layer 1 | SPARK Learning Schema | Extended YAML metadata in Obsidian vault for tracking learning state |
| Layer 2 | Agent Orchestrator (Python) | AI reasoning, coaching logic, scheduled jobs, REST API |
| Layer 3 | React Native App | Mobile UI for voice input, quizzes, dashboards, audio digests |

### 1.3 Data Flow

```
Voice/text input → React Native app → REST API → Agent Orchestrator → MCP Server → Obsidian Vault
```

Responses flow back through the same chain. Scheduled agents (cron) independently scan the vault and push notifications to the app.

### 1.4 Design Principle

> Every interaction must either teach something, reinforce something, or surface a connection. The app never opens to a blank screen — it always has something to say.

---

## 2. Layer 1: SPARK Learning Schema

The learning system extends the existing SPARK YAML templates without breaking current functionality. New fields are added to the Resources template and a new Learning Path construct is introduced.

### 2.1 Extended Resources YAML

Add the following fields to `04_resources/` notes:

```yaml
# ── New Learning Fields (add to existing Resources template) ──
learning_status: active       # active | paused | abandoned | mastered
learning_path: ""             # groups resources into journeys
last_reviewed: ""             # YYYY-MM-DD, updated by agent
next_review: ""               # YYYY-MM-DD, spaced repetition
review_count: 0               # incremented per review session
retention_score: 0            # 0-100, updated by quiz performance
abandonment_risk: low         # low | medium | high (calculated by agent)
estimated_hours: 0            # total estimated learning time
hours_invested: 0             # tracked time spent
key_questions: []             # agent-generated quiz questions
mastery_criteria: ""          # what does "done" look like
```

> **Abandonment Risk Calculation:** Risk = f(days_since_last_review, completion_status, hours_invested vs estimated_hours). If a resource is `in_progress` with no review in 7+ days and < 50% complete, risk = high. The agent nudges accordingly.

### 2.2 Learning Path Note (New Type)

A new note type in `02_projects/` that groups resources into a structured learning journey:

```yaml
---
folder: 02_projects
type: learning_path
created: 2026-02-16
status: active
path_name: "LLMOps & AI Observability"
goal: "Deep expertise in evaluation, observability, guardrails, and governance for AI agents"
target_date: 2026-06-01
resources: []                  # ordered list of resource note links
milestones:
  - name: "Fundamentals"
    resources: []
    status: not_started
  - name: "Evaluation Frameworks"
    resources: []
    status: not_started
  - name: "Production Observability"
    resources: []
    status: not_started
  - name: "Guardrails & Governance"
    resources: []
    status: not_started
current_milestone: "Fundamentals"
overall_progress: 0            # percentage
weekly_target_hours: 5
tags:
  - learning-path
  - project
---
```

### 2.3 Spaced Repetition Schedule

The agent calculates `next_review` dates using a modified SM-2 algorithm based on `retention_score`:

| Retention Score | Interval | Review Type | Difficulty |
|----------------|----------|-------------|------------|
| 0-30 (Low) | 1 day | Full quiz + re-read | Hard |
| 31-60 (Medium) | 3 days | Quick quiz | Medium |
| 61-85 (Good) | 7 days | Connection prompt | Easy |
| 86-100 (Mastered) | 30 days | Application challenge | Maintenance |

---

## 3. Layer 2: Agent Orchestrator

A Python FastAPI service running in Docker on the VPS. It orchestrates all AI reasoning, connects to the Obsidian MCP server, manages scheduled tasks, and exposes a REST API for the mobile app.

### 3.1 Tech Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | FastAPI (async, type-safe) |
| LLM Integration | Anthropic Claude API (primary) + Google Gemini (fallback) |
| MCP Client | HTTP client calling Obsidian MCP server endpoints |
| Task Scheduler | APScheduler (cron-like jobs within FastAPI) |
| Database | SQLite (user state, quiz history, session logs) |
| TTS Engine | Google Cloud TTS or ElevenLabs API (weekly digests) |
| Push Notifications | Firebase Cloud Messaging (FCM) |
| Auth (MVP) | API key in header (migrate to JWT in week 2) |
| Container | Docker + docker-compose on Ubuntu VPS |

### 3.2 Agent Definitions

Each agent is a self-contained module with a single responsibility. Agents are invoked either by scheduled cron jobs or by API requests from the app.

---

#### Agent 1: Morning Briefing Agent

- **Trigger:** Daily cron at 07:00 + on app open
- **MCP Tools:** `search_notes`, `read_note`, `list_notes`
- **LLM Role:** Synthesize vault state into a personalized daily plan

**Logic:**
1. Scan all resources where `learning_status = active` and `next_review <= today`
2. Check learning_path progress against `weekly_target_hours`
3. Pull recent daily notes for mood/energy context
4. Generate a prioritized learning plan for the day via LLM
5. Push notification with summary if app not opened by 08:00

---

#### Agent 2: Abandonment Detector

- **Trigger:** Daily cron at 20:00
- **MCP Tools:** `search_notes`, `read_note`, `update_note`
- **LLM Role:** Classify risk and generate personalized nudge

**Logic:**
1. Query resources where `learning_status = active` or `paused`
2. Calculate days since `last_reviewed` for each
3. Flag resources with no activity > 5 days as medium risk, > 10 days as high risk
4. Update `abandonment_risk` field in vault
5. For high-risk items: LLM generates a motivational nudge referencing WHY the user started this resource (from `key_insights` or learning_path goal)
6. Push notification with nudge

---

#### Agent 3: Quiz Generator

- **Trigger:** On-demand via API + scheduled review sessions
- **MCP Tools:** `read_note`, `update_note`
- **LLM Role:** Generate contextual questions from note content

**Logic:**
1. Read the resource note content and `key_insights`
2. LLM generates 3-5 questions of varying difficulty (recall, application, connection)
3. Store questions in `key_questions` field for reuse
4. After quiz: update `retention_score` based on performance
5. Recalculate `next_review` date using spaced repetition table
6. If `retention_score` drops below 30, escalate to Morning Briefing

---

#### Agent 4: Connection Finder

- **Trigger:** Weekly cron (Sunday evening) + on new resource creation
- **MCP Tools:** `search_notes`, `read_note`, `list_notes`, `append_note`
- **LLM Role:** Discover non-obvious cross-domain connections

**Logic:**
1. Scan all knowledge notes (`05_knowledge/`) and active resources
2. Use LLM to identify thematic overlaps between resources in different learning paths
3. Generate "connection prompts" — short challenges that ask the user to synthesize two ideas
4. Append connection suggestions to relevant knowledge notes
5. Surface top 2-3 connections in the weekly digest

---

#### Agent 5: Weekly Digest Agent

- **Trigger:** Weekly cron (Sunday 18:00)
- **MCP Tools:** `search_notes`, `read_note`, `list_notes`
- **LLM Role:** Compile and narrate weekly learning summary

**Logic:**
1. Aggregate: resources reviewed, quizzes taken, retention scores, hours invested
2. Compare against `weekly_target_hours` from learning path
3. Identify wins (mastered topics, streak maintained) and gaps (abandoned items, low retention)
4. LLM generates a narrative summary in coaching tone
5. Convert to audio via TTS API
6. Store audio file and make available in app

---

#### Agent 6: Voice Input Router

- **Trigger:** On-demand via API (voice transcription from app)
- **MCP Tools:** `create_note`, `append_note`, `search_notes`
- **LLM Role:** Classify intent and route to correct SPARK folder

**Logic:**
1. Receive transcribed text from app (speech-to-text handled client-side)
2. LLM classifies intent: new seed, question about existing note, learning reflection, quiz answer
3. Route to appropriate action: create seed, query vault, update daily note, score quiz
4. Return structured response to app

---

## 4. MCP Integration Map

Mapping of which MCP tools each agent uses:

| MCP Tool | Morning Brief | Abandonment | Quiz Gen | Connection | Digest | Voice Router |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|
| `search_notes` | ✓ | ✓ | — | ✓ | ✓ | ✓ |
| `read_note` | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `list_notes` | ✓ | — | — | ✓ | ✓ | — |
| `update_note` | — | ✓ | ✓ | — | — | — |
| `append_note` | — | — | — | ✓ | — | ✓ |
| `create_note` | — | — | — | — | — | ✓ |

> **MCP Communication:** The Agent Orchestrator communicates with the Obsidian MCP server via HTTP. Each agent constructs MCP tool calls as JSON-RPC requests, sends them to the MCP server URL on the VPS, and parses the responses. No direct Obsidian plugin API access is needed.

---

## 5. REST API Endpoints

All endpoints require `X-API-Key` header (MVP). Responses are JSON.

### 5.1 Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/briefing` | Get today's learning briefing (calls Morning Agent) |
| GET | `/api/v1/learning-paths` | List all learning paths with progress |
| GET | `/api/v1/learning-paths/:id/resources` | Get resources in a learning path with status |
| POST | `/api/v1/quiz/start` | Start quiz for a specific resource |
| POST | `/api/v1/quiz/answer` | Submit quiz answer, get score + next question |
| POST | `/api/v1/voice/process` | Process voice transcription (calls Router Agent) |
| GET | `/api/v1/digest/latest` | Get latest weekly digest (text + audio URL) |
| GET | `/api/v1/nudges` | Get pending nudges/notifications |
| POST | `/api/v1/chat` | Free-form coaching chat (LLM with vault context) |
| GET | `/api/v1/stats/dashboard` | Aggregated stats: streaks, retention, hours, progress |

### 5.2 Request/Response Examples

#### GET /api/v1/briefing

```json
{
  "date": "2026-02-16",
  "greeting": "Morning Franklin. You have 2 reviews due and you're 2.5 hours behind your weekly target.",
  "reviews_due": [
    {
      "resource": "langfuse-observability",
      "retention": 45,
      "type": "quick_quiz",
      "estimated_minutes": 5
    }
  ],
  "learning_path_progress": {
    "name": "LLMOps & AI Observability",
    "weekly_hours": { "target": 5, "actual": 2.5 },
    "current_milestone": "Fundamentals"
  },
  "nudges": [
    {
      "type": "abandonment",
      "resource": "prompt-engineering-guide",
      "days_inactive": 8,
      "message": "You were 60% through this and your notes on chain-of-thought evaluation were solid. Worth finishing?"
    }
  ]
}
```

#### POST /api/v1/quiz/start

```json
// Request
{
  "resource_path": "04_resources/langfuse-observability.md"
}

// Response
{
  "session_id": "quiz_20260216_001",
  "resource": "langfuse-observability",
  "total_questions": 4,
  "current_question": {
    "index": 1,
    "type": "recall",
    "question": "What are the three core data types Langfuse uses to model LLM execution traces?",
    "difficulty": "medium"
  }
}
```

#### POST /api/v1/quiz/answer

```json
// Request
{
  "session_id": "quiz_20260216_001",
  "question_index": 1,
  "answer": "Traces, observations, and scores"
}

// Response
{
  "correct": true,
  "score": 85,
  "feedback": "Correct. Langfuse models execution as traces containing observations (spans, generations, events) with scores for evaluation.",
  "next_question": {
    "index": 2,
    "type": "application",
    "question": "How would you use Langfuse to detect hallucination in your SPARK Coach quiz generator agent?",
    "difficulty": "hard"
  },
  "session_progress": {
    "answered": 1,
    "remaining": 3,
    "running_score": 85
  }
}
```

#### POST /api/v1/voice/process

```json
// Request
{
  "transcription": "I just read about LLM-as-judge evaluation patterns and I think it connects to the guardrails work"
}

// Response
{
  "intent": "new_seed",
  "action_taken": "created_note",
  "note_path": "01_seeds/llm-as-judge-guardrails-connection.md",
  "message": "Captured as a seed. I also found a connection to your existing note on 'evaluation-frameworks'. Want me to link them?",
  "suggested_actions": [
    { "type": "link_notes", "label": "Link to evaluation-frameworks" },
    { "type": "promote", "label": "Promote to knowledge note" }
  ]
}
```

#### GET /api/v1/stats/dashboard

```json
{
  "period": "2026-W07",
  "streaks": {
    "current_days": 5,
    "longest_ever": 12
  },
  "learning_hours": {
    "this_week": 3.5,
    "target": 5,
    "trend": "up"
  },
  "retention": {
    "average_score": 62,
    "improving": ["langfuse-observability", "prompt-evaluation"],
    "declining": ["mlops-fundamentals"]
  },
  "resources": {
    "active": 5,
    "at_risk": 1,
    "mastered": 2,
    "total_in_path": 12
  },
  "quizzes": {
    "completed_this_week": 4,
    "average_score": 72
  }
}
```

---

## 6. Docker Service Layout

### 6.1 docker-compose.yml

```yaml
version: "3.8"

services:
  spark-coach-api:
    build: ./api
    ports:
      - "8080:8080"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - MCP_SERVER_URL=${MCP_SERVER_URL}
      - FCM_CREDENTIALS_PATH=/secrets/fcm.json
      - TTS_API_KEY=${TTS_API_KEY}
      - API_KEY=${SPARK_COACH_API_KEY}
      - DATABASE_URL=sqlite:///data/spark_coach.db
    volumes:
      - ./data:/app/data
      - ./audio:/app/audio
      - ./secrets:/secrets:ro
    depends_on:
      - obsidian-mcp
    restart: unless-stopped

  obsidian-mcp:
    # Your existing MCP server container
    # Reference your current container/config here
    ports:
      - "3000:3000"
```

### 6.2 Directory Structure

```
/opt/spark-coach/
├── docker-compose.yml
├── .env                        # API keys (never commit)
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Settings & env vars
│   ├── auth.py                 # API key middleware (JWT in week 2)
│   ├── mcp_client.py           # MCP server communication
│   ├── llm_client.py           # Claude/Gemini abstraction layer
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py       # Abstract base class for agents
│   │   ├── morning_briefing.py
│   │   ├── abandonment_detector.py
│   │   ├── quiz_generator.py
│   │   ├── connection_finder.py
│   │   ├── weekly_digest.py
│   │   └── voice_router.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── briefing.py
│   │   ├── learning_paths.py
│   │   ├── quiz.py
│   │   ├── voice.py
│   │   ├── digest.py
│   │   ├── chat.py
│   │   └── stats.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLite models (quiz sessions, logs)
│   │   └── schemas.py          # Pydantic request/response schemas
│   └── scheduler.py            # APScheduler cron config
├── data/                       # SQLite DB (persisted volume)
├── audio/                      # Generated digest audio files
└── secrets/                    # FCM credentials
```

### 6.3 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 6.4 requirements.txt

```
fastapi==0.115.*
uvicorn[standard]==0.34.*
anthropic==0.49.*
google-generativeai==0.8.*
httpx==0.28.*
apscheduler==3.11.*
sqlalchemy==2.0.*
aiosqlite==0.20.*
pydantic==2.10.*
python-dotenv==1.0.*
firebase-admin==6.6.*
```

---

## 7. Key Implementation Details

### 7.1 MCP Client (mcp_client.py)

The MCP client wraps HTTP calls to your existing Obsidian MCP server:

```python
import httpx
from config import settings

class MCPClient:
    def __init__(self):
        self.base_url = settings.MCP_SERVER_URL

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call an MCP tool on the Obsidian server."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/call-tool",
                json={
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            response.raise_for_status()
            return response.json()

    async def search_notes(self, query: str, folder: str = None) -> list:
        args = {"query": query}
        if folder:
            args["folder"] = folder
        return await self.call_tool("search_notes", args)

    async def read_note(self, path: str) -> dict:
        return await self.call_tool("read_note", {"path": path})

    async def update_note(self, path: str, content: str) -> dict:
        return await self.call_tool("update_note", {"path": path, "content": content})

    async def create_note(self, path: str, content: str) -> dict:
        return await self.call_tool("create_note", {"path": path, "content": content})

    async def append_note(self, path: str, content: str) -> dict:
        return await self.call_tool("append_note", {"path": path, "content": content})

    async def list_notes(self, folder: str = None) -> list:
        args = {}
        if folder:
            args["folder"] = folder
        return await self.call_tool("list_notes", args)
```

> **Note:** Adapt the HTTP endpoint paths to match your actual MCP server's API surface. If your MCP server uses JSON-RPC or SSE transport, adjust accordingly.

### 7.2 LLM Client (llm_client.py)

Abstraction layer to switch between Claude and Gemini:

```python
import anthropic
from config import settings

class LLMClient:
    def __init__(self):
        self.anthropic = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.default_model = "claude-sonnet-4-5-20250929"

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: str = None,
        max_tokens: int = 1024
    ) -> str:
        """Get a completion from Claude."""
        response = await self.anthropic.messages.create(
            model=model or self.default_model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text

    async def complete_json(
        self,
        system_prompt: str,
        user_message: str,
        model: str = None
    ) -> dict:
        """Get a JSON-structured completion."""
        response = await self.complete(
            system_prompt=system_prompt + "\n\nRespond ONLY with valid JSON. No markdown, no preamble.",
            user_message=user_message,
            model=model
        )
        import json
        return json.loads(response.strip().strip("```json").strip("```"))
```

### 7.3 Base Agent Pattern

```python
from abc import ABC, abstractmethod
from mcp_client import MCPClient
from llm_client import LLMClient

class BaseAgent(ABC):
    def __init__(self):
        self.mcp = MCPClient()
        self.llm = LLMClient()

    @abstractmethod
    async def run(self, **kwargs) -> dict:
        """Execute the agent's main logic."""
        pass

    async def get_active_resources(self) -> list:
        """Shared helper: get all active learning resources."""
        results = await self.mcp.search_notes("learning_status: active", folder="04_resources")
        return results

    async def get_learning_path(self, path_name: str) -> dict:
        """Shared helper: get a learning path by name."""
        results = await self.mcp.search_notes(path_name, folder="02_projects")
        for r in results:
            content = await self.mcp.read_note(r["path"])
            if "type: learning_path" in content:
                return content
        return None
```

### 7.4 SQLite Models (database.py)

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class QuizSession(Base):
    __tablename__ = "quiz_sessions"
    id = Column(String, primary_key=True)
    resource_path = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_questions = Column(Integer)
    correct_answers = Column(Integer, default=0)
    score = Column(Float, default=0.0)

class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False)
    question_index = Column(Integer)
    question_text = Column(Text)
    user_answer = Column(Text)
    is_correct = Column(Boolean)
    score = Column(Float)
    answered_at = Column(DateTime, default=datetime.utcnow)

class LearningLog(Base):
    __tablename__ = "learning_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_path = Column(String)
    action = Column(String)  # quiz, review, voice_capture, chat
    duration_minutes = Column(Float, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(Text)  # JSON string for flexible data

class NudgeHistory(Base):
    __tablename__ = "nudge_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_path = Column(String)
    nudge_type = Column(String)  # abandonment, review_due, milestone
    message = Column(Text)
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 7.5 Auth Middleware (auth.py)

```python
from fastapi import Request, HTTPException
from config import settings

async def verify_api_key(request: Request):
    """MVP auth: simple API key check."""
    api_key = request.headers.get("X-API-Key")
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

---

## 8. Week 1 Implementation Plan

**Goal:** A working backend that can coach you on the LLMOps learning path, accessible via API. No mobile app yet — test everything via curl or Postman.

> **Anti-Abandonment Design:** Each day produces a testable, usable increment. If you stop after day 3, you still have a working quiz system. Every day ships value.

### Day 1: Foundation

- [ ] Set up `/opt/spark-coach/` directory structure on VPS
- [ ] Create `Dockerfile` + `docker-compose.yml` + `.env`
- [ ] Implement `main.py` with FastAPI skeleton + health check endpoint
- [ ] Implement `mcp_client.py` — test calling `search_notes` and `read_note` on your live vault
- [ ] Implement `auth.py` — simple API key check middleware

**Deliverable:** `GET /health` returns 200, `GET /api/v1/test-mcp` returns a note from your vault

### Day 2: Learning Schema + First Agent

- [ ] Create the LLMOps learning path note in Obsidian with the new YAML schema
- [ ] Add learning metadata to 2-3 existing LLMOps resources in your vault
- [ ] Implement `llm_client.py` — Claude API wrapper with system prompts
- [ ] Build `morning_briefing.py` agent — reads vault, generates daily plan

**Deliverable:** `GET /api/v1/briefing` returns a personalized daily learning plan

### Day 3: Quiz System

- [ ] Implement `quiz_generator.py` — reads note content, generates questions via LLM
- [ ] Create SQLite models for quiz sessions and answers
- [ ] Build `POST /api/v1/quiz/start` and `POST /api/v1/quiz/answer` endpoints
- [ ] Implement retention score calculation and `next_review` update

**Deliverable:** Can quiz yourself on any resource via API and see retention scores update in Obsidian

### Day 4: Abandonment + Nudges

- [ ] Implement `abandonment_detector.py` agent
- [ ] Set up APScheduler with morning briefing (07:00) and abandonment check (20:00)
- [ ] Build `GET /api/v1/nudges` endpoint
- [ ] Test full daily cycle: briefing → quiz → abandonment check

**Deliverable:** System proactively detects stale resources and generates nudges

### Day 5: Voice Router + Chat

- [ ] Implement `voice_router.py` — classifies transcribed text and routes to action
- [ ] Build `POST /api/v1/voice/process` endpoint
- [ ] Implement `POST /api/v1/chat` for free-form coaching conversations
- [ ] Build `GET /api/v1/stats/dashboard` for aggregated metrics

**Deliverable:** Full API surface ready for mobile app integration

### Weekend: Integration Test

- [ ] Test complete flow: briefing → study → quiz → nudge → chat
- [ ] Seed vault with 5-8 LLMOps resources across milestones
- [ ] Document API with example curl commands
- [ ] Fix bugs and edge cases

**Deliverable:** Battle-tested API ready for React Native app (Week 2)

---

## 9. Beyond Week 1: Roadmap

### Week 2: React Native App + JWT Auth

- [ ] Scaffold React Native project with Expo
- [ ] Implement JWT authentication flow
- [ ] Build Home/Dashboard screen consuming `/api/v1/briefing`
- [ ] Add voice input using Expo Speech-to-Text
- [ ] Build Quiz Mode screen

### Week 3: Learning Experience Polish

- [ ] Build Learning Paths screen with visual progress
- [ ] Implement Connection Finder agent
- [ ] Add push notifications via FCM
- [ ] Build Weekly Digest screen + TTS audio generation

### Week 4: Coaching Intelligence

- [ ] Implement adaptive difficulty in quizzes based on retention patterns
- [ ] Add pattern recognition across learning paths
- [ ] Build coaching chat with full vault context
- [ ] Add visual guides / study cards generated from notes

### Month 2+: Advanced Features

- [ ] Multi-learning-path management
- [ ] Integration with external content (YouTube, articles) via web scraping
- [ ] Social accountability features (optional)
- [ ] Self-observability dashboard — apply your LLMOps learning to the system itself

---

## 10. Key Design Decisions & Rationale

### Why SQLite alongside Obsidian?

Obsidian is the knowledge store — it holds what you know. SQLite holds operational state: quiz history, session logs, retention score timeseries, notification delivery status. Mixing operational data into Obsidian notes would pollute the SPARK system. Think of it as: Obsidian = long-term memory, SQLite = working memory.

### Why FastAPI over a Node.js backend?

Python has the strongest LLM ecosystem (anthropic SDK, litellm, langchain). FastAPI gives async performance with type safety. Since the MCP server is already Node-based, having the orchestrator in Python gives separation of concerns and exposes you to the Python AI tooling ecosystem — directly relevant to the LLMOps learning goal.

### Why not use LangChain or LangGraph?

For a single-user system with well-defined agent loops, a framework adds complexity without proportional value. Building agents from scratch teaches more about LLM orchestration — which is the point. You can always add LangSmith for observability later as part of the LLMOps learning path.

### Why React Native with Expo?

Expo removes 80% of native Android configuration pain. Hot reload, speech-to-text APIs, push notification support, and over-the-air updates out of the box. For vibe-coding a first mobile app, the DX difference is massive. If Expo limitations appear later, you can eject.

### Why spaced repetition over simple reminders?

Simple reminders are noise — the brain learns to ignore them. Spaced repetition is evidence-based: it targets the exact moment you're about to forget something. The retention score creates a feedback loop that makes the system smarter over time, not louder.

---

## 11. Meta-Learning Loop

As you build this system, you're learning LLMOps by doing LLMOps. The guinea pig learning path (AI Observability) should eventually be used to add observability to SPARK Coach itself. The system teaches you how to improve the system.

**Concrete example:** By Week 4, you should be able to add Langfuse tracing to every agent's LLM call, track token usage, evaluate quiz question quality, and build a dashboard showing your own system's AI performance — all knowledge gained from the learning path the system is coaching you on.

---

*End of Technical Specification v1.0*
