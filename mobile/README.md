# Rafiki - SPARK Coach Mobile App

React Native mobile app for SPARK Coach.

## Setup

Place your React Native app code here.

### Typical React Native Structure:
```
mobile/
├── app/                 # App screens (if using Expo Router)
├── components/          # Reusable components
├── services/            # API client for backend
├── assets/              # Images, fonts, etc.
├── app.json            # Expo/React Native config
├── package.json        # Dependencies
└── tsconfig.json       # TypeScript config (if using TS)
```

## Backend Integration

Backend API runs at: `http://localhost:8080`

### Authentication
All endpoints (except `/health`) require API key header:
```
X-API-Key: your_api_key_here
```

### Key Endpoints

See backend API documentation at: `http://localhost:8080/docs`

**Main endpoints:**
- `GET /api/v1/briefing` - Daily briefing
- `POST /api/v1/quiz/start` - Start quiz
- `POST /api/v1/quiz/answer` - Submit answer
- `POST /api/v1/chat` - Chat with Rafiki
- `POST /api/v1/voice/process` - Process voice input
- `GET /api/v1/stats/dashboard` - Learning stats
- `GET /api/v1/nudges` - Get nudges

## Development

1. Start backend first:
   ```bash
   cd ../backend
   source venv/bin/activate
   python main.py
   ```

2. Start mobile app:
   ```bash
   cd mobile
   npm start
   # or
   expo start
   ```

## Environment Variables

Create `.env` in this directory:
```
BACKEND_URL=http://localhost:8080
API_KEY=your_api_key_here
```
