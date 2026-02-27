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
