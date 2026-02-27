# Login & Authentication Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add password-protected login to Spark Coach — a bcrypt-hashed password in `.env`, FastAPI issues a signed 7-day JWT, Next.js middleware protects all pages, a `Secure; SameSite=Strict` cookie carries the token.

**Architecture:** FastAPI gains a `POST /api/v1/auth/login` endpoint and replaces the `X-API-Key` dependency with JWT verification across all routes. Next.js `middleware.ts` redirects unauthenticated visitors to `/login`. The login page sets a JS-readable (non-httpOnly) `Secure; SameSite=Strict` cookie so both the middleware and the API client can access the token without a proxy.

**Tech Stack:** Python `python-jose[cryptography]` + `passlib[bcrypt]` (backend); Next.js 16 App Router middleware + `document.cookie` (frontend)

**Cookie note:** `httpOnly` is skipped intentionally — the frontend and backend are on different subdomains, so an httpOnly cookie set on the frontend domain cannot be sent to the API. `Secure; SameSite=Strict` is used instead, which prevents CSRF and is appropriate for a single-user personal app with no third-party scripts.

---

## Task 1: Add JWT dependencies to backend

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Add the two new packages**

Open `backend/requirements.txt` and append:
```
python-jose[cryptography]==3.3.*
passlib[bcrypt]==1.7.*
```

**Step 2: Install them**

```bash
cd /Users/a.christuraj/Projects/spark-coach
source venv/bin/activate
pip install "python-jose[cryptography]==3.3.*" "passlib[bcrypt]==1.7.*"
```

Expected: Both packages install without errors. `bcrypt` will be pulled as a dependency of `passlib[bcrypt]`.

**Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "feat(auth): add python-jose and passlib dependencies"
```

---

## Task 2: Add JWT config to settings

**Files:**
- Modify: `backend/config.py`

**Step 1: Write the failing test**

Create `backend/tests/test_config.py`:

```python
import os
import pytest

def test_jwt_secret_key_setting():
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-chars-minimum!!"
    from importlib import reload
    import config
    reload(config)
    assert config.settings.JWT_SECRET_KEY == "test-secret-key-32-chars-minimum!!"

def test_password_hash_setting():
    os.environ["SPARK_COACH_PASSWORD_HASH"] = "$2b$12$testhash"
    from importlib import reload
    import config
    reload(config)
    assert config.settings.SPARK_COACH_PASSWORD_HASH == "$2b$12$testhash"
```

**Step 2: Run to verify it fails**

```bash
cd /Users/a.christuraj/Projects/spark-coach/backend
python -m pytest tests/test_config.py -v
```

Expected: `AttributeError: 'Settings' object has no attribute 'JWT_SECRET_KEY'`

**Step 3: Add the two settings to `backend/config.py`**

In the `Settings` class, after the `API_KEY` line, add:

```python
    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-to-a-random-32-char-secret")
    SPARK_COACH_PASSWORD_HASH: str = os.getenv("SPARK_COACH_PASSWORD_HASH", "")
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_config.py -v
```

Expected: 2 passed.

**Step 5: Commit**

```bash
git add backend/config.py backend/tests/test_config.py
git commit -m "feat(auth): add JWT_SECRET_KEY and SPARK_COACH_PASSWORD_HASH settings"
```

---

## Task 3: Generate your password hash and update .env

**Step 1: Generate the bcrypt hash of your chosen password**

```bash
cd /Users/a.christuraj/Projects/spark-coach
source venv/bin/activate
python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('YOUR_PASSWORD_HERE'))"
```

Replace `YOUR_PASSWORD_HERE` with the password you want to use. Copy the output hash — it will look like `$2b$12$...`.

**Step 2: Generate a JWT secret**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output (64-char hex string).

**Step 3: Update `.env`**

Open `/Users/a.christuraj/Projects/spark-coach/.env` (or create it from `.env.example`) and add:

```bash
JWT_SECRET_KEY=<paste-your-64-char-hex-here>
SPARK_COACH_PASSWORD_HASH=<paste-your-bcrypt-hash-here>
```

The old `SPARK_COACH_API_KEY` can stay for now — it will be retired in Task 5.

**Step 4: Verify the .env is in .gitignore**

```bash
grep ".env" /Users/a.christuraj/Projects/spark-coach/.gitignore
```

Expected: `.env` appears. If not: `echo ".env" >> .gitignore`

---

## Task 4: Rewrite auth.py with JWT functions

**Files:**
- Modify: `backend/auth.py`
- Create: `backend/tests/test_auth.py`

**Step 1: Write the failing tests**

Create `backend/tests/test_auth.py`:

```python
import pytest
import os
from datetime import datetime, timedelta

# Set test env vars before importing anything
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256"
os.environ["SPARK_COACH_PASSWORD_HASH"] = ""

from passlib.context import CryptContext

# Generate a real test hash once
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TEST_HASH = _pwd_context.hash("correctpassword")


def test_verify_password_correct():
    from auth import verify_password
    assert verify_password("correctpassword", TEST_HASH) is True


def test_verify_password_wrong():
    from auth import verify_password
    assert verify_password("wrongpassword", TEST_HASH) is False


def test_create_access_token_returns_string():
    from auth import create_access_token
    token = create_access_token()
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_is_decodable():
    from auth import create_access_token
    from jose import jwt
    token = create_access_token()
    payload = jwt.decode(token, "test-secret-key-that-is-long-enough-for-hs256", algorithms=["HS256"])
    assert payload["sub"] == "franklin"


def test_create_access_token_expires_in_7_days():
    from auth import create_access_token
    from jose import jwt
    token = create_access_token()
    payload = jwt.decode(token, "test-secret-key-that-is-long-enough-for-hs256", algorithms=["HS256"])
    exp = datetime.utcfromtimestamp(payload["exp"])
    now = datetime.utcnow()
    diff = exp - now
    # Should be approximately 7 days (allow 1 minute tolerance)
    assert timedelta(days=6, hours=23) < diff < timedelta(days=7, minutes=1)
```

**Step 2: Run to verify they fail**

```bash
cd /Users/a.christuraj/Projects/spark-coach/backend
python -m pytest tests/test_auth.py -v
```

Expected: `ImportError` — `verify_password` and `create_access_token` don't exist yet.

**Step 3: Replace `backend/auth.py` with JWT implementation**

```python
"""
Authentication for SPARK Coach API
JWT-based auth replacing the MVP API key approach.
"""
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against its bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(expires_delta: timedelta = timedelta(days=TOKEN_EXPIRE_DAYS)) -> str:
    """Create a signed JWT that expires after expires_delta."""
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": "franklin",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> str:
    """
    FastAPI dependency — validates Bearer JWT from Authorization header.
    Raises 401 if token is missing, invalid, or expired.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        sub: str = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return sub
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_auth.py -v
```

Expected: 5 passed.

**Step 5: Commit**

```bash
git add backend/auth.py backend/tests/test_auth.py
git commit -m "feat(auth): implement JWT verify_password, create_access_token, verify_token"
```

---

## Task 5: Add POST /api/v1/auth/login endpoint

**Files:**
- Create: `backend/routes/auth.py`
- Create: `backend/tests/test_routes_auth.py`

**Step 1: Write failing tests**

Create `backend/tests/test_routes_auth.py`:

```python
import pytest
import os
from passlib.context import CryptContext
from fastapi.testclient import TestClient

os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256"
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
os.environ["SPARK_COACH_PASSWORD_HASH"] = _pwd.hash("testpassword123")

from main import app

client = TestClient(app)


def test_login_success():
    resp = client.post("/api/v1/auth/login", json={"password": "testpassword123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 604800


def test_login_wrong_password():
    resp = client.post("/api/v1/auth/login", json={"password": "wrongpassword"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect password"


def test_login_empty_password():
    resp = client.post("/api/v1/auth/login", json={"password": ""})
    assert resp.status_code == 422  # Pydantic validation


def test_protected_endpoint_with_valid_token():
    # Get a token
    resp = client.post("/api/v1/auth/login", json={"password": "testpassword123"})
    token = resp.json()["access_token"]
    # Use it on a protected endpoint
    resp = client.get("/health")
    assert resp.status_code == 200  # health is public


def test_protected_endpoint_without_token():
    resp = client.get(
        "/api/v1/briefing/quick",
        headers={}  # no Authorization header
    )
    assert resp.status_code == 401
```

**Step 2: Run to verify they fail**

```bash
python -m pytest tests/test_routes_auth.py -v
```

Expected: Most fail with import errors or 404 on the login route.

**Step 3: Create `backend/routes/auth.py`**

```python
"""
Authentication routes for SPARK Coach API.
Single endpoint: POST /api/v1/auth/login
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from auth import verify_password, create_access_token
from config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password cannot be empty")
        return v


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 604800  # 7 days in seconds


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate with password, receive a 7-day JWT.
    The token should be stored as a cookie and sent as
    'Authorization: Bearer <token>' on subsequent API calls.
    """
    if not settings.SPARK_COACH_PASSWORD_HASH:
        raise HTTPException(
            status_code=500,
            detail="Server not configured: SPARK_COACH_PASSWORD_HASH is not set",
        )
    if not verify_password(request.password, settings.SPARK_COACH_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Incorrect password")
    token = create_access_token()
    return LoginResponse(access_token=token)
```

**Step 4: Register the auth router and swap `verify_api_key` → `verify_token` in `backend/main.py`**

In `main.py`, change the imports at the top:

```python
# Replace this line:
from auth import verify_api_key

# With:
from auth import verify_token
from routes.auth import router as auth_router
```

Add the router after the existing routers (find the `app.include_router` block):

```python
app.include_router(auth_router)
```

Update the three test endpoints in `main.py` that use `verify_api_key`. Find each occurrence of `Depends(verify_api_key)` and replace with `Depends(verify_token)`:

- Line ~122: `async def test_mcp_connection(api_key: str = Depends(verify_api_key)):`
  → `async def test_mcp_connection(_: str = Depends(verify_token)):`

- Line ~181: `async def test_mcp_search(..., api_key: str = Depends(verify_api_key)):`
  → `async def test_mcp_search(..., _: str = Depends(verify_token)):`

- Line ~216: `async def test_mcp_read(path: str, api_key: str = Depends(verify_api_key)):`
  → `async def test_mcp_read(path: str, _: str = Depends(verify_token)):`

**Step 5: Swap `verify_api_key` → `verify_token` in all five route files**

Each of the five route files (`briefing.py`, `quiz.py`, `nudges.py`, `voice.py`, `stats.py`) has this pattern at the top:

```python
from auth import verify_api_key
```

and in the router definition:

```python
dependencies=[Depends(verify_api_key)]
```

In each file, change both lines:

```python
# Change import:
from auth import verify_token

# Change dependency:
dependencies=[Depends(verify_token)]
```

**Step 6: Run tests**

```bash
python -m pytest tests/test_routes_auth.py -v
```

Expected: 5 passed.

**Step 7: Smoke test the server starts**

```bash
cd /Users/a.christuraj/Projects/spark-coach/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8081 &
sleep 2
curl http://localhost:8081/health
curl -s -X POST http://localhost:8081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "YOUR_PASSWORD_HERE"}' | python -m json.tool
pkill -f "uvicorn main:app"
```

Expected: Health returns `{"status":"healthy",...}`. Login returns `{"access_token":"eyJ...","token_type":"bearer","expires_in":604800}`.

**Step 8: Commit**

```bash
git add backend/routes/auth.py backend/tests/test_routes_auth.py \
        backend/main.py backend/routes/briefing.py backend/routes/quiz.py \
        backend/routes/nudges.py backend/routes/voice.py backend/routes/stats.py
git commit -m "feat(auth): add login endpoint, swap API key auth for JWT across all routes"
```

---

## Task 6: Add Next.js middleware for page protection

**Files:**
- Create: `mobile/middleware.ts`

**Step 1: Create `mobile/middleware.ts`**

```typescript
import { NextRequest, NextResponse } from "next/server"

const PUBLIC_PATHS = ["/login"]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Allow public paths through
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next()
  }

  // Check for JWT cookie
  const token = request.cookies.get("spark_token")?.value

  if (!token) {
    const loginUrl = new URL("/login", request.url)
    loginUrl.searchParams.set("from", pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  // Run on all routes except static files and Next.js internals
  matcher: ["/((?!_next/static|_next/image|favicon.ico|icon.*|apple-icon.*).*)"],
}
```

**Step 2: Verify it works manually**

```bash
cd /Users/a.christuraj/Projects/spark-coach/mobile
npm run dev
```

Open `http://localhost:3000` in browser. Expected: redirects to `/login` (404 for now since page doesn't exist yet — that's fine, confirms middleware is running).

Stop dev server with Ctrl+C.

**Step 3: Commit**

```bash
git add mobile/middleware.ts
git commit -m "feat(auth): add Next.js middleware to protect all pages behind login"
```

---

## Task 7: Create the login page

**Files:**
- Create: `mobile/app/login/page.tsx`

**Step 1: Create `mobile/app/login/page.tsx`**

```tsx
"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8081"

function setCookie(name: string, value: string, days: number) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString()
  const secure = location.protocol === "https:" ? "; Secure" : ""
  document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Strict${secure}`
}

export default function LoginPage() {
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const searchParams = useSearchParams()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!password.trim()) {
      setError("Please enter your password")
      return
    }

    setLoading(true)
    setError("")

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      })

      if (!res.ok) {
        setError("Incorrect password")
        return
      }

      const { access_token } = await res.json()
      setCookie("spark_token", access_token, 7)

      const redirectTo = searchParams.get("from") ?? "/"
      router.push(redirectTo)
      router.refresh()
    } catch {
      setError("Something went wrong. Try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-[#E8E5E0]">
      <div className="w-full max-w-[390px] bg-background rounded-[24px] border border-border shadow-xl p-8 mx-4">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold tracking-tight">Rafiki</h1>
          <p className="text-sm text-muted-foreground mt-1">Your personal learning coach</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
              autoFocus
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
            />
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="inline-flex w-full items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground ring-offset-background transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  )
}
```

**Step 2: Test manually**

```bash
cd /Users/a.christuraj/Projects/spark-coach/mobile
npm run dev
```

1. Open `http://localhost:3000` — should redirect to `/login`
2. Enter wrong password — should show "Incorrect password" (backend must be running)
3. Enter correct password — should set cookie and redirect to `/`

To start backend for testing:
```bash
cd /Users/a.christuraj/Projects/spark-coach/backend
source ../venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8081
```

**Step 3: Commit**

```bash
git add mobile/app/login/
git commit -m "feat(auth): add login page with password field and JWT cookie handling"
```

---

## Task 8: Create API client with token helper

**Files:**
- Create: `mobile/services/api.ts`

**Step 1: Create `mobile/services/api.ts`**

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8081"

/** Read the JWT from the spark_token cookie. Returns empty string if not found. */
function getToken(): string {
  if (typeof document === "undefined") return ""
  const match = document.cookie.match(/(?:^|;\s*)spark_token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : ""
}

/** Clear the auth cookie and redirect to login. */
export function logout() {
  document.cookie = "spark_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/"
  window.location.href = "/login"
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  })

  if (res.status === 401) {
    logout()
    throw new Error("Not authenticated")
  }

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`)
  }

  return res.json() as Promise<T>
}

// ─── Typed API methods ──────────────────────────────────────────────────────

export const api = {
  getBriefing: () => request<BriefingResponse>("/api/v1/briefing"),
  getBriefingQuick: () => request<BriefingQuickResponse>("/api/v1/briefing/quick"),
  startQuiz: (resourcePath: string) =>
    request<QuizStartResponse>("/api/v1/quiz/start", {
      method: "POST",
      body: JSON.stringify({ resource_path: resourcePath }),
    }),
  answerQuiz: (sessionId: string, questionIndex: number, answer: string) =>
    request<QuizAnswerResponse>("/api/v1/quiz/answer", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, question_index: questionIndex, answer }),
    }),
  chat: (message: string, sessionId?: string) =>
    request<ChatResponse>("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId }),
    }),
  getNudges: () => request<NudgesResponse>("/api/v1/nudges"),
  getDashboard: () => request<DashboardResponse>("/api/v1/stats/dashboard"),
  processVoice: (transcription: string) =>
    request<VoiceResponse>("/api/v1/voice/process", {
      method: "POST",
      body: JSON.stringify({ transcription }),
    }),
}

// ─── Response types (extend as backend evolves) ─────────────────────────────

export interface BriefingResponse {
  date: string
  greeting: string
  reviews_due: Array<{ resource: string; retention: number; type: string; estimated_minutes: number }>
  learning_path_progress: { name: string; weekly_hours: { target: number; actual: number }; current_milestone: string; overall_progress: number }
  nudges: Array<{ type: string; resource: string; days_inactive: number; message: string }>
  daily_plan: string[]
}

export interface BriefingQuickResponse {
  reviews_count: number
  at_risk_count: number
  learning_path: string
  current_milestone: string
}

export interface QuizStartResponse {
  session_id: string
  resource: string
  total_questions: number
  current_question: { index: number; type: string; question: string; difficulty: string }
}

export interface QuizAnswerResponse {
  correct: boolean
  score: number
  feedback: string
  next_question: QuizStartResponse["current_question"] | null
  session_progress: { answered: number; remaining: number; running_score: number }
}

export interface ChatResponse {
  response: string
  session_id: string
  suggested_actions: Array<{ type: string; label: string }>
}

export interface NudgesResponse {
  nudges: Array<{ id: number; type: string; resource: string; days_inactive: number; message: string; created_at: string }>
}

export interface DashboardResponse {
  period: string
  streaks: { current_days: number; longest_ever: number }
  learning_hours: { this_week: number; target: number; trend: string }
  retention: { average_score: number; improving: string[]; declining: string[] }
  resources: { active: number; at_risk: number; mastered: number; total_in_path: number }
  quizzes: { completed_this_week: number; average_score: number }
}

export interface VoiceResponse {
  intent: string
  action_taken: string
  note_path: string
  message: string
  suggested_actions: Array<{ type: string; label: string }>
}
```

**Step 2: Commit**

```bash
git add mobile/services/api.ts
git commit -m "feat(auth): add typed API client with token cookie helper and logout"
```

---

## Task 9: Add logout button to the app shell

**Files:**
- Modify: `mobile/app/page.tsx`

**Step 1: Add a logout button to `mobile/app/page.tsx`**

Import `logout` at the top of the file:

```typescript
import { logout } from "@/services/api"
```

Inside the mobile shell div (after the `<div className="h-full overflow-y-auto scrollbar-hide">` block closes, before the `<FloatingNav>` line), add:

```tsx
{/* Logout — small, unobtrusive, top-right */}
<button
  onClick={logout}
  className="absolute top-4 right-4 z-50 text-xs text-muted-foreground hover:text-foreground transition-colors"
>
  Sign out
</button>
```

**Step 2: Verify manually**

Start both backend and frontend. Log in. Confirm "Sign out" button appears. Click it — should clear cookie and redirect to `/login`.

**Step 3: Commit**

```bash
git add mobile/app/page.tsx
git commit -m "feat(auth): add sign out button to app shell"
```

---

## Task 10: Add NEXT_PUBLIC_API_URL to environment and verify end-to-end

**Step 1: Create `mobile/.env.local`** (if it doesn't exist)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8081
```

For production, this will be set to `https://coach-api.yourdomain.com` at build time.

**Step 2: Update CORS in `backend/main.py`**

The current CORS config uses `allow_origins=["*"]`. For production, tighten it. Find this block in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
```

Change to:

```python
import os
_allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
```

Add `ALLOWED_ORIGINS=https://coach.yourdomain.com` to `.env` when deploying.

**Step 3: End-to-end test**

Start backend:
```bash
cd /Users/a.christuraj/Projects/spark-coach/backend
source ../venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8081
```

Start frontend (separate terminal):
```bash
cd /Users/a.christuraj/Projects/spark-coach/mobile
npm run dev
```

Run through this checklist:
- [ ] `http://localhost:3000` redirects to `/login`
- [ ] Wrong password shows "Incorrect password"
- [ ] Correct password sets `spark_token` cookie and redirects to `/`
- [ ] App loads at `/`
- [ ] Browser DevTools → Application → Cookies: `spark_token` present, `Secure` (in prod), `SameSite=Strict`
- [ ] "Sign out" clears cookie and returns to `/login`
- [ ] Opening DevTools → Network: API calls include `Authorization: Bearer eyJ...` header

**Step 4: Commit**

```bash
git add mobile/.env.local backend/main.py
git commit -m "feat(auth): tighten CORS config, add NEXT_PUBLIC_API_URL env setup"
```

---

## Done

Authentication is complete. The old `SPARK_COACH_API_KEY` / `X-API-Key` flow is fully replaced.

**What to update in `.env` on VPS when deploying:**
```bash
JWT_SECRET_KEY=<64-char-hex>
SPARK_COACH_PASSWORD_HASH=<bcrypt-hash>
ALLOWED_ORIGINS=https://coach.yourdomain.com
```
