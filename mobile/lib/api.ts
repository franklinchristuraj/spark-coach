/**
 * SPARK Coach API Client
 * Connects to FastAPI backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081';

function getToken(): string {
  if (typeof document === 'undefined') return '';
  const match = document.cookie.match(/(?:^|;\s*)spark_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : '';
}

// Generic fetch wrapper with error handling
async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const token = getToken();

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (response.status === 401) {
    document.cookie = 'spark_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    window.location.href = '/login';
    throw new Error('Not authenticated');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface BriefingResponse {
  status: string;
  briefing: {
    date: string;
    greeting: string;
    reviews_due: Array<{ title: string; path: string; days_overdue: number }>;
    reviews_count: number;
    learning_path_progress: {
      name: string;
      weekly_hours: { target: number; actual: number };
      current_milestone: string;
      overall_progress: number;
    };
    nudges: Array<{ message: string; resource_path: string }>;
    daily_plan: string[];
    stats: {
      active_resources: number;
      at_risk_count: number;
      completion_rate: number;
    };
  };
}

export interface QuizStartResponse {
  status: string;
  session_id: string;
  resource: string;
  resource_path: string;
  total_questions: number;
  current_question: {
    index: number;
    type: string;
    question: string;
    difficulty: string;
  };
}

export interface QuizAnswerResponse {
  status: string;
  correct: boolean;
  score: number;
  feedback: string;
  next_question?: {
    index: number;
    type: string;
    question: string;
    difficulty: string;
  };
  session_progress: {
    answered: number;
    remaining: number;
    correct_so_far: number;
  };
  quiz_complete: boolean;
  final_score?: number;
}

export interface ChatResponse {
  status: string;
  message: string;
  sources?: Array<{ title: string; path: string }>;
  conversation_id?: string;
}

export interface StatsResponse {
  status: string;
  period: string;
  streaks: {
    current_days: number;
    longest_ever: number;
  };
  learning_hours: {
    this_week: number;
    target: number;
    trend: string;
    previous_week: number;
  };
  retention: {
    average_score: number;
    improving: string[];
    declining: string[];
  };
  resources: {
    active: number;
    at_risk: number;
    mastered: number;
    total_in_path: number;
  };
  quizzes: {
    completed_this_week: number;
    average_score: number;
    total_questions_answered?: number;
  };
}

export interface NudgesResponse {
  status: string;
  count: number;
  nudges: Array<{
    id: number;
    resource_path: string;
    nudge_type: string;
    message: string;
    created_at: string;
  }>;
}

export interface VoiceProcessResponse {
  status: string;
  intent: string;
  confidence: number;
  action_taken: string;
  message: string;
  note_path?: string;
  suggested_actions: Array<{ type: string; label: string }>;
}

// ─────────────────────────────────────────────────────────────────────────────
// API Methods
// ─────────────────────────────────────────────────────────────────────────────

export const api = {
  // ─── Health Check ───
  async healthCheck(): Promise<{ status: string; app: string; version: string }> {
    return apiFetch('/health');
  },

  // ─── Briefing ───
  async getBriefing(userName: string): Promise<BriefingResponse> {
    return apiFetch(`/api/v1/briefing?user_name=${encodeURIComponent(userName)}`);
  },

  // ─── Quiz ───
  async startQuiz(
    resourcePath: string,
    numQuestions: number = 3,
    difficulty: string = 'medium'
  ): Promise<QuizStartResponse> {
    return apiFetch('/api/v1/quiz/start', {
      method: 'POST',
      body: JSON.stringify({
        resource_path: resourcePath,
        num_questions: numQuestions,
        difficulty,
      }),
    });
  },

  async submitQuizAnswer(
    sessionId: string,
    questionIndex: number,
    answer: string
  ): Promise<QuizAnswerResponse> {
    return apiFetch('/api/v1/quiz/answer', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        question_index: questionIndex,
        answer,
      }),
    });
  },

  async getQuizSession(sessionId: string): Promise<any> {
    return apiFetch(`/api/v1/quiz/session/${sessionId}`);
  },

  // ─── Chat ───
  async chat(
    message: string,
    conversationHistory: Array<{ role: string; content: string }> = [],
    includeVaultContext: boolean = true
  ): Promise<ChatResponse> {
    return apiFetch('/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_history: conversationHistory,
        include_vault_context: includeVaultContext,
      }),
    });
  },

  async chatHello(): Promise<ChatResponse> {
    return apiFetch('/api/v1/chat/hello');
  },

  // ─── Stats ───
  async getStats(period: string = 'this_week'): Promise<StatsResponse> {
    return apiFetch(`/api/v1/stats/dashboard?period=${period}`);
  },

  async getStreak(): Promise<{ status: string; current_days: number; longest_ever: number }> {
    return apiFetch('/api/v1/stats/streak');
  },

  async getWeeklySummary(): Promise<any> {
    return apiFetch('/api/v1/stats/weekly-summary');
  },

  // ─── Nudges ───
  async getNudges(limit: number = 10): Promise<NudgesResponse> {
    return apiFetch(`/api/v1/nudges?limit=${limit}`);
  },

  async markNudgesDelivered(nudgeIds: number[]): Promise<any> {
    return apiFetch('/api/v1/nudges/mark-delivered', {
      method: 'POST',
      body: JSON.stringify({ nudge_ids: nudgeIds }),
    });
  },

  async runAbandonmentCheck(): Promise<any> {
    return apiFetch('/api/v1/nudges/run-check', {
      method: 'POST',
    });
  },

  // ─── Voice ───
  async processVoice(transcription: string): Promise<VoiceProcessResponse> {
    return apiFetch('/api/v1/voice/process', {
      method: 'POST',
      body: JSON.stringify({ transcription }),
    });
  },

  // ─── MCP (Testing) ───
  async testMCP(): Promise<any> {
    return apiFetch('/api/v1/test-mcp');
  },

  async searchVault(query: string, folder?: string): Promise<any> {
    const params = new URLSearchParams({ query });
    if (folder) params.append('folder', folder);
    return apiFetch(`/api/v1/mcp/search?${params}`);
  },

  async readNote(path: string): Promise<any> {
    return apiFetch(`/api/v1/mcp/read/${encodeURIComponent(path)}`);
  },
};

export default api;
