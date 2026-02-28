# Iteration 1: Morning Briefing — End to End

**Date:** 2026-03-01
**Goal:** Open the app on your phone and see your daily learning briefing.
**Linear milestone:** Iteration 1 (target: 2026-03-07)
**Issues:** FRA-42, FRA-43, FRA-47, FRA-41

---

## What's Already Built

The mobile app is further along than the Linear issues indicate. No UI build work is needed.

| Already done | Files |
|---|---|
| All 5 screens (Home, Chat, Goals, Quiz, Insights) | `mobile/components/rafiki/screens/` |
| JWT login page + middleware auth | `mobile/app/login/page.tsx`, `mobile/middleware.ts` |
| API clients + React hooks | `mobile/services/api.ts`, `mobile/lib/api.ts`, `mobile/hooks/use-api.ts` |
| Home screen fetches + renders briefing | `mobile/components/rafiki/screens/home-screen.tsx` |
| Floating bottom nav | `mobile/components/rafiki/floating-nav.tsx` |
| shadcn/ui component library | `mobile/components/ui/` |
| `@vercel/analytics` pre-installed | `mobile/package.json` |

**Iteration 1 is a deployment and PWA plumbing task, not a build task.**

---

## Deployment Architecture

**Choice: Option B — Frontend on Vercel + API on VPS**

```
Phone (PWA)
    ↓ HTTPS
coach.ziksaka.com  →  Vercel  →  Next.js app
                                      ↓ API calls
coach-api.ziksaka.com  →  Nginx  →  FastAPI (Docker, port 8080)
                                          ↓
                               MCP: mcp.ziksaka.com/mcp
                               LLM: Gemini 1.5 Pro
```

**Why Vercel for frontend:**
- Zero-config HTTPS (required for PWA install)
- Auto-deploys on every `git push` to `main`
- `@vercel/analytics` already installed — zero extra setup

---

## Section 1: PWA Setup

**Files to create:** `mobile/public/manifest.json`, icon PNGs
**Files to update:** `mobile/app/layout.tsx`

### `public/manifest.json`
```json
{
  "name": "Rafiki",
  "short_name": "Rafiki",
  "description": "Your personal AI learning coach",
  "display": "standalone",
  "orientation": "portrait",
  "start_url": "/",
  "background_color": "#FAF8F5",
  "theme_color": "#FAF8F5",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }
  ]
}
```

### Icons
Generate two PNG icons (192×192, 512×512) from SVG — simple "R" lettermark on brand background. Placeholder quality is fine for Iteration 1.

### `layout.tsx` additions
```tsx
// In metadata:
manifest: '/manifest.json',
appleWebApp: {
  capable: true,
  statusBarStyle: 'default',
  title: 'Rafiki',
},
```

---

## Section 2: Backend CORS Update

**File:** `backend/main.py` (or wherever `CORSMiddleware` is configured)

Add `https://coach.ziksaka.com` to the allowed origins list. One-line change.

---

## Section 3: VPS Deployment

### Files to create
- `deploy/nginx-api.conf` — Nginx server block for `coach-api.ziksaka.com`
- `deploy/deploy.sh` — idempotent first-time VPS setup script

### `deploy/nginx-api.conf`
```nginx
server {
    server_name coach-api.ziksaka.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Certbot adds the SSL block after `certbot --nginx`.

### `deploy/deploy.sh` — VPS setup steps
1. Install Docker, Docker Compose, Nginx, Certbot
2. Clone repo to `/opt/spark-coach`
3. Copy `.env` (prompt user — never committed to git)
4. `docker compose up -d` → API running on port 8080
5. Copy `deploy/nginx-api.conf` to `/etc/nginx/sites-available/`
6. Enable site + reload Nginx
7. `certbot --nginx -d coach-api.ziksaka.com`
8. Verify: `curl https://coach-api.ziksaka.com/health`

---

## Section 4: Vercel Setup (Manual Steps)

These are one-time manual steps in the Vercel dashboard — not scripted.

1. Push repo to GitHub (if not already)
2. Import project in Vercel → set **Root Directory** to `mobile/`
3. Add environment variable: `NEXT_PUBLIC_API_URL=https://coach-api.ziksaka.com`
4. Add custom domain: `coach.ziksaka.com`
5. Add DNS CNAME record at DNS provider: `coach` → `cname.vercel-dns.com`
6. Vercel provisions SSL automatically

---

## Section 5: Environment Variables

| Location | Variable | Value |
|---|---|---|
| Vercel dashboard | `NEXT_PUBLIC_API_URL` | `https://coach-api.ziksaka.com` |
| VPS `.env` | `JWT_SECRET` | strong random string |
| VPS `.env` | `GEMINI_API_KEY` | your key |
| VPS `.env` | `MCP_SERVER_URL` | `https://mcp.ziksaka.com/mcp` |
| VPS `.env` | `ANTHROPIC_API_KEY` | optional fallback |

---

## Verification Checklist

**Backend (VPS)**
- [ ] `curl https://coach-api.ziksaka.com/health` returns `{"status": "ok"}`
- [ ] Briefing endpoint returns JSON with auth header

**Frontend (Vercel)**
- [ ] `https://coach.ziksaka.com` redirects unauthenticated users to `/login`
- [ ] Login works, lands on Home screen
- [ ] Home screen shows live greeting + today's focus from API
- [ ] "Add to Home Screen" prompt appears on Chrome/Safari
- [ ] Installed PWA opens fullscreen with no browser chrome

---

## What We're NOT Building in Iteration 1

- New screens (all 5 already exist)
- New API endpoints (briefing API already works)
- Push notifications (Iteration 3)
- Auth changes (JWT already works)
