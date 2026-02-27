# Login & Authentication Design

**Date:** 2026-02-27
**Status:** Approved
**Scope:** Add password-protected login to Spark Coach (frontend + backend)

---

## Context

Spark Coach is a personal-use app. The MVP used a hardcoded `X-API-Key` header for backend auth with no frontend protection — anyone with the URL could access it. This design adds a proper login page and replaces the API key with JWT auth on both layers.

**Constraints:**
- Single user (personal use only)
- 7-day session (re-login once a week)
- Next.js frontend + FastAPI backend
- Deployed on VPS behind Nginx + SSL

---

## Architecture & Data Flow

```
User visits any page
  → Next.js middleware checks for JWT cookie
  → missing/expired → redirect to /login
  → valid → page renders normally

/login page
  → user enters password → POST /api/v1/auth/login
  → FastAPI checks password against bcrypt hash in .env
  → success → returns signed JWT
  → Next.js API route (/api/auth/set-cookie) stores JWT
    as httpOnly cookie (7-day maxAge, Secure, SameSite=Lax)
  → redirect to /

All subsequent API calls
  → cookie sent automatically by browser
  → Next.js reads cookie, passes JWT in Authorization: Bearer header
  → FastAPI verifies JWT signature on every request
```

---

## Environment Variables

Two new vars replace `SPARK_COACH_API_KEY`:

| Variable | Description |
|---|---|
| `SPARK_COACH_PASSWORD_HASH` | bcrypt hash of your chosen password |
| `JWT_SECRET_KEY` | Random 32+ char string for signing tokens |

**One-time setup to generate password hash:**
```bash
python -c "from passlib.context import CryptContext; \
  print(CryptContext(schemes=['bcrypt']).hash('your-password'))"
```

---

## Backend Components (`api/`)

### `auth.py` (replace existing API key logic)
- `verify_password(plain, hashed)` — bcrypt verification
- `verify_token(token)` — decode + validate JWT, raise HTTP 401 if invalid or expired
- `create_access_token()` — sign JWT with 7-day expiry, `sub: "franklin"`

### `routes/auth.py` (new file)
- `POST /api/v1/auth/login`
  - Request: `{ password: string }`
  - Success: `{ access_token: string, token_type: "bearer", expires_in: 604800 }`
  - Failure: `401 Incorrect password`

### `main.py`
- Include auth router
- Swap `verify_api_key` dependency → `verify_token` across all existing routes

### New dependencies
```
python-jose[cryptography]
passlib[bcrypt]
```

---

## Frontend Components (`mobile/`)

### `app/login/page.tsx`
- Single password field + "Sign In" button
- No username field (personal use)
- Calls `POST /api/v1/auth/login`
- On success: calls `/api/auth/set-cookie`, then redirects to `/`
- On failure: shows "Incorrect password"
- On empty submit: client-side validation (no API call)

### `app/api/auth/set-cookie/route.ts`
- Next.js API route (bridge for setting `httpOnly` cookie from client-side JS)
- Receives JWT, sets cookie: `httpOnly`, `Secure` (prod), `SameSite=Lax`, `maxAge=604800`

### `app/api/auth/logout/route.ts`
- Clears the JWT cookie
- Redirects to `/login`

### `middleware.ts`
- Runs on every request (except `/login` and `/api/auth/*`)
- Reads JWT cookie
- Redirects to `/login` if absent or expired

### `services/api.ts`
- Updated to read JWT from cookie and attach as `Authorization: Bearer <token>` on all backend calls

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Wrong password | `401` from API → "Incorrect password" on login page |
| Empty password field | Client-side block, no API call |
| Network error | "Something went wrong, try again" |
| JWT expired (after 7 days) | Next request → `401` → middleware clears cookie → redirect `/login` |
| Invalid/tampered JWT | `401` → same redirect flow |

No rate limiting for MVP (personal use).

---

## Security

- `httpOnly` cookie — JS cannot read or steal the token
- `Secure` flag — HTTPS only in production; relaxed for local dev
- `SameSite=Lax` — CSRF protection
- Password stored as bcrypt hash, never plaintext
- JWT secret stored in `.env`, never committed

---

## What This Replaces

- `SPARK_COACH_API_KEY` env var → retired
- `X-API-Key` header on all requests → retired
- `verify_api_key` FastAPI dependency → replaced by `verify_token`
