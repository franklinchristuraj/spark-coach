/**
 * React hooks for SPARK Coach API
 */

import { useState, useEffect, useCallback } from 'react';
import { api, BriefingResponse, StatsResponse, ChatResponse, QuizStartResponse, QuizAnswerResponse } from '@/lib/api';

// ─────────────────────────────────────────────────────────────────────────────
// Generic Hook Creator
// ─────────────────────────────────────────────────────────────────────────────

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

function useApi<T>(
  fetcher: () => Promise<T>,
  dependencies: any[] = []
): UseApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await fetcher();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
      console.error('API Error:', err);
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ─────────────────────────────────────────────────────────────────────────────
// Specific Hooks
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Get daily briefing
 */
export function useBriefing(userName: string = 'Franklin') {
  return useApi<BriefingResponse>(
    () => api.getBriefing(userName),
    [userName]
  );
}

/**
 * Get learning stats
 */
export function useStats(period: string = 'this_week') {
  return useApi<StatsResponse>(
    () => api.getStats(period),
    [period]
  );
}

/**
 * Get current streak
 */
export function useStreak() {
  return useApi<{ status: string; current_days: number; longest_ever: number }>(
    () => api.getStreak(),
    []
  );
}

/**
 * Get weekly summary
 */
export function useWeeklySummary() {
  return useApi(
    () => api.getWeeklySummary(),
    []
  );
}

/**
 * Get pending nudges
 */
export function useNudges(limit: number = 10) {
  return useApi(
    () => api.getNudges(limit),
    [limit]
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Chat Hook (with state management)
// ─────────────────────────────────────────────────────────────────────────────

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{ title: string; path: string }>;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const sendMessage = useCallback(async (message: string) => {
    // Add user message
    const userMessage: ChatMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);

    try {
      setLoading(true);
      setError(null);

      // Send to API
      const response = await api.chat(message, messages);

      // Add assistant message
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.message,
        sources: response.sources,
      };
      setMessages(prev => [...prev, assistantMessage]);

    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to send message'));
      console.error('Chat error:', err);
      // Remove failed user message
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  }, [messages]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, sendMessage, clearChat };
}

// ─────────────────────────────────────────────────────────────────────────────
// Quiz Hook (with state management)
// ─────────────────────────────────────────────────────────────────────────────

interface QuizState {
  sessionId: string | null;
  resource: string | null;
  currentQuestion: {
    index: number;
    type: string;
    question: string;
    difficulty: string;
  } | null;
  totalQuestions: number;
  progress: {
    answered: number;
    remaining: number;
    correct: number;
  };
  lastFeedback: {
    correct: boolean;
    score: number;
    feedback: string;
  } | null;
  finalScore: number | null;
  isComplete: boolean;
}

export function useQuiz() {
  const [quizState, setQuizState] = useState<QuizState>({
    sessionId: null,
    resource: null,
    currentQuestion: null,
    totalQuestions: 0,
    progress: { answered: 0, remaining: 0, correct: 0 },
    lastFeedback: null,
    finalScore: null,
    isComplete: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const startQuiz = useCallback(async (resourcePath: string, numQuestions: number = 3) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.startQuiz(resourcePath, numQuestions);

      setQuizState({
        sessionId: response.session_id,
        resource: response.resource,
        currentQuestion: response.current_question,
        totalQuestions: response.total_questions,
        progress: { answered: 0, remaining: response.total_questions, correct: 0 },
        lastFeedback: null,
        finalScore: null,
        isComplete: false,
      });
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to start quiz'));
      console.error('Quiz start error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const submitAnswer = useCallback(async (answer: string) => {
    if (!quizState.sessionId || !quizState.currentQuestion) {
      setError(new Error('No active quiz session'));
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await api.submitQuizAnswer(
        quizState.sessionId,
        quizState.currentQuestion.index,
        answer
      );

      setQuizState(prev => ({
        ...prev,
        currentQuestion: response.next_question || null,
        progress: {
          answered: response.session_progress.answered,
          remaining: response.session_progress.remaining,
          correct: response.session_progress.correct_so_far,
        },
        lastFeedback: {
          correct: response.correct,
          score: response.score,
          feedback: response.feedback,
        },
        finalScore: response.final_score || null,
        isComplete: response.quiz_complete,
      }));

      return response;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to submit answer'));
      console.error('Quiz answer error:', err);
    } finally {
      setLoading(false);
    }
  }, [quizState.sessionId, quizState.currentQuestion]);

  const resetQuiz = useCallback(() => {
    setQuizState({
      sessionId: null,
      resource: null,
      currentQuestion: null,
      totalQuestions: 0,
      progress: { answered: 0, remaining: 0, correct: 0 },
      lastFeedback: null,
      finalScore: null,
      isComplete: false,
    });
    setError(null);
  }, []);

  return { quizState, loading, error, startQuiz, submitAnswer, resetQuiz };
}

export default {
  useBriefing,
  useStats,
  useStreak,
  useChat,
  useQuiz,
  useNudges,
};
