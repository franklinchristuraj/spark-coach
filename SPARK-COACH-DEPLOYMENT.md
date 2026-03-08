# SPARK Coach — VPS Deployment Guide

> Deploy the FastAPI backend + Next.js frontend behind your existing Nginx reverse proxy with SSL.

---

## Architecture on VPS

```
Phone Browser (HTTPS)
        │
        ▼
   Nginx Reverse Proxy (SSL termination)
        │
        ├── coach.yourdomain.com      → Next.js frontend (port 3001)
        ├── coach-api.yourdomain.com   → FastAPI backend  (port 8080)
        └── (your existing services)
                                            │
                                    FastAPI ──→ Obsidian MCP Server (port 3000)
```

> **Alternative:** You can use a single subdomain with path-based routing (`coach.yourdomain.com` for frontend, `coach.yourdomain.com/api/` proxied to backend). Choose whichever matches your existing Nginx pattern.

---

## Step 1: Prepare Your Local Project for Deployment

### 1.1 Backend — Add Dockerfile if missing

Create `api/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 1.2 Frontend — Add Dockerfile for Next.js

Create `mobile/Dockerfile`:

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# Set the API URL at build time
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public

EXPOSE 3001

CMD ["npm", "start", "--", "-p", "3001"]
```

> **Important:** If your Next.js app fetches the API URL from an environment variable, make sure it uses `NEXT_PUBLIC_API_URL` (or whatever your app uses). This gets baked in at build time.

### 1.3 Create docker-compose.yml at project root

Create `docker-compose.yml` in your `spark-coach/` root:

```yaml
version: "3.8"

services:
  spark-coach-api:
    build: ./api
    container_name: spark-coach-api
    ports:
      - "8080:8080"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./audio:/app/audio
    networks:
      - spark-network
    restart: unless-stopped

  spark-coach-web:
    build:
      context: ./mobile
      args:
        NEXT_PUBLIC_API_URL: https://coach-api.yourdomain.com
    container_name: spark-coach-web
    ports:
      - "3001:3001"
    networks:
      - spark-network
    restart: unless-stopped

networks:
  spark-network:
    driver: bridge
```

### 1.4 Create .env file

```bash
# .env (never commit this)
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
MCP_SERVER_URL=http://host.docker.internal:3000  # or your MCP server's internal URL
SPARK_COACH_API_KEY=your-secret-api-key-here
DATABASE_URL=sqlite:///data/spark_coach.db
TTS_API_KEY=...
```

> **MCP_SERVER_URL:** If your MCP server runs in Docker on the same VPS, use the container name or Docker network. If it's on the host, use `http://host.docker.internal:3000` or the host IP. Check how your MCP server is networked.

---

## Step 2: Transfer Files to VPS

### Option A: Git (recommended)

```bash
# On local machine — push to a private repo
cd ~/projects/spark-coach
git init
echo ".env" >> .gitignore
echo "node_modules" >> .gitignore
echo "__pycache__" >> .gitignore
echo "data/" >> .gitignore
echo ".next" >> .gitignore
git add .
git commit -m "Initial SPARK Coach"
git remote add origin git@github.com:yourusername/spark-coach.git
git push -u origin main

# On VPS
cd /opt
git clone git@github.com:yourusername/spark-coach.git
cd spark-coach
```

### Option B: SCP (quick and dirty)

```bash
# From local machine
scp -r ~/projects/spark-coach user@your-vps-ip:/opt/spark-coach
```

> **Exclude unnecessary files:** Don't transfer `node_modules/`, `.next/`, `__pycache__/`, or `data/`. Docker will build fresh.

---

## Step 3: Configure Nginx

### 3.1 Create DNS Records

In your domain registrar, add two A records:

```
coach.yourdomain.com      → your VPS IP
coach-api.yourdomain.com  → your VPS IP
```

> Wait for DNS propagation (usually 5-15 minutes).

### 3.2 Add Nginx Server Blocks

SSH into your VPS and create the config files:

**Backend API:**

```bash
sudo nano /etc/nginx/sites-available/coach-api
```

```nginx
server {
    listen 80;
    server_name coach-api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Important for streaming/SSE if you add it later
        proxy_buffering off;
        proxy_read_timeout 300s;
    }
}
```

**Frontend:**

```bash
sudo nano /etc/nginx/sites-available/coach-web
```

```nginx
server {
    listen 80;
    server_name coach.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (Next.js hot reload in dev, useful for future features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3.3 Enable Sites + SSL

```bash
# Enable the sites
sudo ln -s /etc/nginx/sites-available/coach-api /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/coach-web /etc/nginx/sites-enabled/

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Generate SSL certs with Let's Encrypt (same as your existing services)
sudo certbot --nginx -d coach.yourdomain.com -d coach-api.yourdomain.com
```

> Certbot will automatically modify your Nginx configs to add SSL. It will also set up auto-renewal.

---

## Step 4: Build and Launch

```bash
# SSH into VPS
cd /opt/spark-coach

# Create the .env file
nano .env
# (paste your environment variables)

# Create data directories
mkdir -p data audio

# Build and start
docker compose up -d --build

# Check logs
docker compose logs -f spark-coach-api
docker compose logs -f spark-coach-web
```

### Verify Everything Works

```bash
# Test API health
curl https://coach-api.yourdomain.com/health

# Test API with auth
curl -H "X-API-Key: your-secret-api-key" https://coach-api.yourdomain.com/api/v1/briefing

# Test frontend
curl -I https://coach.yourdomain.com
```

---

## Step 5: Access from Your Phone

1. Open Chrome/Firefox on your Android phone
2. Navigate to `https://coach.yourdomain.com`
3. **Add to Home Screen** (makes it feel like a native app):
   - Tap the three-dot menu in Chrome
   - Tap "Add to Home screen"
   - Name it "SPARK Coach" (or whatever you named it)
   - It now launches like a native app with no browser chrome

> **Pro tip:** If your Next.js app has a `manifest.json` (PWA manifest), the "Add to Home Screen" experience will be even better — custom icon, splash screen, standalone window. You can add this later.

---

## Step 6: MCP Server Networking

The most common issue: the FastAPI container can't reach your MCP server. Here's how to fix it depending on your setup:

### If MCP server is a Docker container on the same VPS:

```yaml
# In docker-compose.yml, connect to the MCP server's network
services:
  spark-coach-api:
    # ... existing config ...
    networks:
      - spark-network
      - mcp-network  # join the MCP server's network

networks:
  spark-network:
    driver: bridge
  mcp-network:
    external: true  # reference the existing network
```

Then set `MCP_SERVER_URL=http://your-mcp-container-name:3000` in `.env`.

### If MCP server runs on host (not in Docker):

```yaml
services:
  spark-coach-api:
    # ... existing config ...
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

Then set `MCP_SERVER_URL=http://host.docker.internal:3000` in `.env`.

### Quick test from inside the container:

```bash
docker exec -it spark-coach-api curl http://your-mcp-url:3000/health
```

---

## Troubleshooting Checklist

| Problem | Fix |
|---------|-----|
| `502 Bad Gateway` | Container not running. Check `docker compose ps` and `docker compose logs` |
| `Connection refused` on API | Port 8080 not exposed or Nginx proxy_pass wrong |
| Frontend can't reach API | Check `NEXT_PUBLIC_API_URL` — must be the public HTTPS URL, not localhost |
| MCP connection fails | Network issue — see Step 6 above |
| SSL cert error | Run `sudo certbot --nginx` again, check DNS propagation |
| App slow on phone | Next.js not built in production mode — ensure `NODE_ENV=production` |
| CORS errors | Add CORS middleware to FastAPI: `app.add_middleware(CORSMiddleware, allow_origins=["https://coach.yourdomain.com"])` |

---

## Updating After Changes

```bash
# On VPS
cd /opt/spark-coach

# Pull latest code (if using git)
git pull

# Rebuild and restart
docker compose up -d --build

# Or rebuild just one service
docker compose up -d --build spark-coach-api
docker compose up -d --build spark-coach-web
```

---

## Optional: Add PWA Support for Native App Feel

Add this to your Next.js app for a better mobile experience:

### Create `public/manifest.json`:

```json
{
  "name": "SPARK Coach",
  "short_name": "Coach",
  "description": "AI Learning & Accountability Partner",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1A1A2E",
  "theme_color": "#1A1A2E",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### Add to your `<Head>` in layout:

```html
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#1A1A2E" />
<meta name="mobile-web-app-capable" content="yes" />
```

This makes "Add to Home Screen" launch as a standalone app — no browser URL bar, feels native.

---

*End of Deployment Guide*
