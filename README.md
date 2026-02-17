# SPARK Coach

AI Learning & Accountability System for SPARK PKM

## Overview

SPARK Coach is an AI-powered learning and accountability system that transforms a passive Obsidian knowledge vault into an active coaching partner. It uses LLM APIs for reasoning and coaching, connecting to your SPARK PKM system via MCP server.

## Project Structure

```
spark-coach/
├── backend/              # Python FastAPI backend
│   ├── agents/          # AI agents (briefing, quiz, voice, etc.)
│   ├── routes/          # API endpoints
│   ├── models/          # Database models & schemas
│   ├── main.py          # FastAPI app entry point
│   └── requirements.txt
├── mobile/              # React Native app (Rafiki)
│   └── (your React Native code here)
├── data/                # SQLite database (persisted)
├── .env                 # Environment variables (not in git)
├── docker-compose.yml   # Container orchestration
└── venv/               # Python virtual environment
```

## Architecture

- **Layer 1:** SPARK Learning Schema (Extended YAML metadata in Obsidian)
- **Layer 2:** Agent Orchestrator (Python FastAPI - `/backend`)
- **Layer 3:** React Native Mobile App (Rafiki - `/mobile`)

## Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (for production deployment)
- A running Obsidian MCP server
- Anthropic API key

### Local Development Setup

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/spark-coach
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

   Required environment variables:
   - `ANTHROPIC_API_KEY`: Your Anthropic API key
   - `MCP_SERVER_URL`: URL of your Obsidian MCP server (default: http://localhost:3000)
   - `SPARK_COACH_API_KEY`: API key for client authentication (set to any secure value)

3. **Install backend dependencies:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Run the backend server:**
   ```bash
   python main.py
   ```

   Or with uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8080
   ```

5. **Test the API:**
   ```bash
   # Health check (no auth required)
   curl http://localhost:8080/health

   # Test MCP connection (requires API key)
   curl -H "X-API-Key: dev_test_key_12345" http://localhost:8080/api/v1/test-mcp
   ```

### Docker Deployment

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f spark-coach-api
   ```

3. **Stop services:**
   ```bash
   docker-compose down
   ```

## API Endpoints

### Public Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)

### Authenticated Endpoints

All authenticated endpoints require the `X-API-Key` header.

**Day 1 - MCP Test Endpoints:**
- `GET /api/v1/test-mcp` - Test MCP server connectivity
- `GET /api/v1/mcp/search?query={query}&folder={folder}` - Search notes in vault
- `GET /api/v1/mcp/read/{path}` - Read a specific note

**Day 2 - Learning & Briefing:**
- `GET /api/v1/briefing` - Get personalized morning briefing with daily plan
- `GET /api/v1/briefing/quick` - Get quick stats without LLM processing

**Coming Soon (Day 3+):**
- `GET /api/v1/learning-paths` - List all learning paths
- `POST /api/v1/quiz/start` - Start a quiz session
- `POST /api/v1/quiz/answer` - Submit quiz answer
- `POST /api/v1/voice/process` - Process voice input
- `GET /api/v1/stats/dashboard` - Get learning statistics

## Development Progress

### ✅ Day 1: Foundation (Completed)
- [x] Set up directory structure
- [x] Create Dockerfile + docker-compose.yml + .env
- [x] Implement main.py with FastAPI skeleton + health check
- [x] Implement mcp_client.py with MCP server communication
- [x] Implement auth.py with API key middleware

**Deliverable:** `GET /health` returns 200, `GET /api/v1/test-mcp` returns a note from vault

### ✅ Day 2: Learning Schema + First Agent (Completed)
- [x] Create LLMOps learning path template with new YAML schema
- [x] Create resource template with learning metadata fields
- [x] Implement llm_client.py with Claude API and coaching methods
- [x] Implement base_agent.py with shared helper methods
- [x] Build morning_briefing.py agent with personalized daily plans
- [x] Create briefing API routes

**Deliverable:** `GET /api/v1/briefing` returns personalized daily learning plan

### 🔄 Day 3: Quiz System (Next)
- [ ] Implement quiz_generator.py agent
- [ ] Create SQLite models for quiz sessions
- [ ] Build quiz API endpoints (start, answer)
- [ ] Implement retention score calculation
- [ ] Update next_review dates automatically

### 📋 Day 4-5: Abandonment, Voice, Stats
- [ ] Abandonment detector with scheduled jobs
- [ ] Voice input router
- [ ] Stats dashboard

## Project Structure

```
spark-coach/
├── api/
│   ├── agents/           # AI agent modules
│   ├── routes/           # API route handlers
│   ├── models/           # Database models
│   ├── main.py           # FastAPI entry point
│   ├── config.py         # Configuration management
│   ├── auth.py           # Authentication middleware
│   ├── mcp_client.py     # MCP server client
│   ├── llm_client.py     # LLM API client
│   ├── Dockerfile
│   └── requirements.txt
├── data/                 # SQLite database (persisted)
├── audio/                # Generated audio digests
├── secrets/              # FCM credentials
├── docker-compose.yml
├── .env                  # Environment variables (gitignored)
└── .env.example          # Environment template
```

## Configuration

All configuration is managed through environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | Required |
| `MCP_SERVER_URL` | Obsidian MCP server URL | `http://localhost:3000` |
| `SPARK_COACH_API_KEY` | API key for authentication | Required |
| `DATABASE_URL` | SQLite database path | `sqlite:///data/spark_coach.db` |
| `DEBUG` | Enable debug mode | `false` |

## Testing

### Manual Testing

Use the interactive API docs at `http://localhost:8080/docs` or test with curl:

```bash
# Set your API key
export API_KEY="dev_test_key_12345"

# Test health check
curl http://localhost:8080/health

# Test MCP connection
curl -H "X-API-Key: $API_KEY" http://localhost:8080/api/v1/test-mcp

# Search notes
curl -H "X-API-Key: $API_KEY" "http://localhost:8080/api/v1/mcp/search?query=learning&folder=01_seeds"

# Read a note
curl -H "X-API-Key: $API_KEY" http://localhost:8080/api/v1/mcp/read/01_seeds/example-seed.md

# Get morning briefing (Day 2)
curl -H "X-API-Key: $API_KEY" http://localhost:8080/api/v1/briefing

# Get quick briefing stats
curl -H "X-API-Key: $API_KEY" http://localhost:8080/api/v1/briefing/quick
```

## Troubleshooting

### MCP Server Not Reachable

If you see "MCP server is not reachable" errors:

1. Verify your MCP server is running
2. Check the `MCP_SERVER_URL` in `.env`
3. Ensure the MCP server is accessible from the API container (use `host.docker.internal` on macOS/Windows)

### Authentication Errors

If you get 401 errors:

1. Verify you're including the `X-API-Key` header
2. Check the API key matches `SPARK_COACH_API_KEY` in `.env`

### Import Errors

If you see Python import errors:

1. Ensure you're in the `api/` directory when running `python main.py`
2. Or add the api directory to PYTHONPATH: `export PYTHONPATH=/path/to/spark-coach/api:$PYTHONPATH`

## License

MIT License - See LICENSE file for details

## Contributing

This is a personal learning project following the SPARK-COACH-SPEC.md specification. Feel free to fork and adapt for your own use.
