"use client"

import { useState, useEffect } from "react"
import { ArrowLeft, BookOpen, Zap, Loader2, CheckCircle2, XCircle } from "lucide-react"
import { useQuiz, useStreak } from "@/hooks/use-api"

interface QuizScreenProps {
  onBack: () => void
}

export function QuizScreen({ onBack }: QuizScreenProps) {
  const { quizState, loading, error, startQuiz, submitAnswer, resetQuiz } = useQuiz()
  const { data: streak } = useStreak()
  const [answer, setAnswer] = useState("")
  const [showFeedback, setShowFeedback] = useState(false)

  // Auto-start quiz with a test resource (in production, user would select)
  useEffect(() => {
    if (!quizState.sessionId && !loading) {
      startQuiz("resources/multi-agent-systems.md", 3)
    }
  }, [])

  const handleSubmitAnswer = async () => {
    if (!answer.trim()) return

    const response = await submitAnswer(answer.trim())
    if (response) {
      setShowFeedback(true)
      setAnswer("")

      // Auto-hide feedback and move to next question after 3 seconds
      setTimeout(() => {
        setShowFeedback(false)
      }, 3000)
    }
  }

  const handleRestart = () => {
    resetQuiz()
    setShowFeedback(false)
    setAnswer("")
  }

  const progressDots = Array.from({ length: quizState.totalQuestions || 5 }, (_, i) => {
    const answered = quizState.progress.answered
    if (i < answered) return "completed"
    if (i === answered) return "current"
    return "upcoming"
  })

  // Loading state
  if (loading && !quizState.currentQuestion) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between px-5 pt-14 pb-4">
          <button onClick={onBack} className="text-text-secondary bg-transparent border-none" aria-label="Go back">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h2 className="text-[17px] font-bold text-foreground">Daily Challenge</h2>
          <div className="w-24" />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between px-5 pt-14 pb-4">
          <button onClick={onBack} className="text-text-secondary bg-transparent border-none" aria-label="Go back">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h2 className="text-[17px] font-bold text-foreground">Daily Challenge</h2>
          <div className="w-24" />
        </div>
        <div className="flex-1 flex items-center justify-center px-5">
          <div className="text-center">
            <p className="text-[15px] text-foreground font-medium">Unable to start quiz</p>
            <p className="text-[13px] text-text-secondary mt-1">{error.message}</p>
          </div>
        </div>
      </div>
    )
  }

  // Quiz complete state
  if (quizState.isComplete && quizState.finalScore !== null) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between px-5 pt-14 pb-4">
          <button onClick={onBack} className="text-text-secondary bg-transparent border-none" aria-label="Go back">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h2 className="text-[17px] font-bold text-foreground">Quiz Complete</h2>
          <div className="w-24" />
        </div>
        <div className="flex-1 flex items-center justify-center px-5">
          <div className="flex flex-col items-center gap-6 text-center">
            <div className="flex flex-col items-center gap-4">
              <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center">
                <CheckCircle2 className="h-12 w-12 text-primary" />
              </div>
              <div>
                <p className="text-[32px] font-bold text-foreground">{quizState.finalScore}%</p>
                <p className="text-[15px] text-text-secondary mt-1">Final Score</p>
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <p className="text-[15px] text-foreground">
                Answered {quizState.progress.answered} questions
              </p>
              <p className="text-[15px] text-foreground">
                Got {quizState.progress.correct} correct
              </p>
            </div>
            <button
              onClick={handleRestart}
              className="w-full rounded-full bg-primary text-primary-foreground py-3.5 text-[16px] font-medium border-none hover:opacity-90 transition-all"
            >
              Take Another Quiz
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-5 pt-14 pb-4">
        <button onClick={onBack} className="text-text-secondary bg-transparent border-none" aria-label="Go back">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h2 className="text-[17px] font-bold text-foreground">Daily Challenge</h2>
        {streak && (
          <div className="rounded-full bg-[rgba(249,115,22,0.12)] px-3 py-1 flex items-center gap-1">
            <Zap className="h-3 w-3 text-warning" fill="currentColor" />
            <span className="text-[11px] font-medium text-warning">{streak.current_days} day streak</span>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-5 pb-24">
        <div className="flex flex-col gap-6">
          {/* Progress Dots */}
          <div className="flex flex-col items-center gap-2">
            <div className="flex items-center gap-2.5">
              {progressDots.map((state, i) => (
                <span
                  key={i}
                  className={`rounded-full transition-all ${
                    state === "completed"
                      ? "h-2.5 w-2.5 bg-primary"
                      : state === "current"
                        ? "h-3 w-3 border-2 border-primary bg-transparent"
                        : "h-2.5 w-2.5 bg-[#D4D4D4]"
                  }`}
                />
              ))}
            </div>
            <span className="text-[12px] text-text-secondary">
              {quizState.progress.answered + 1} of {quizState.totalQuestions}
            </span>
          </div>

          {/* Topic Badge */}
          <div className="flex justify-center">
            <span className="rounded-full bg-[rgba(37,99,235,0.1)] px-4 py-1.5 text-[12px] font-medium text-primary">
              {quizState.resource || "Learning Resource"}
            </span>
          </div>

          {/* Question Card */}
          {quizState.currentQuestion && (
            <div className="relative rounded-2xl bg-card p-5 overflow-hidden border border-border card-shadow">
              <div className="absolute left-0 top-0 bottom-0 w-[3px] rounded-full bg-primary" />
              <div className="pl-4 flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-medium uppercase tracking-[0.06em] text-text-muted">
                    Rafiki Asks
                  </span>
                  <span className="text-[10px] font-medium uppercase tracking-[0.06em] text-primary">
                    {quizState.currentQuestion.difficulty}
                  </span>
                </div>
                <p className="text-[17px] text-foreground leading-relaxed">
                  {quizState.currentQuestion.question}
                </p>
                <div className="inline-flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1.5 self-start">
                  <BookOpen className="h-3 w-3 text-text-muted" />
                  <span className="text-[11px] text-text-muted">
                    {quizState.currentQuestion.type} question
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Feedback Display */}
          {showFeedback && quizState.lastFeedback && (
            <div className={`rounded-2xl p-5 border ${
              quizState.lastFeedback.correct
                ? "bg-green-50 border-green-200"
                : "bg-orange-50 border-orange-200"
            }`}>
              <div className="flex items-start gap-3">
                {quizState.lastFeedback.correct ? (
                  <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="h-5 w-5 text-orange-600 shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <p className={`text-[15px] font-medium ${
                    quizState.lastFeedback.correct ? "text-green-900" : "text-orange-900"
                  }`}>
                    Score: {quizState.lastFeedback.score}/100
                  </p>
                  <p className={`text-[13px] mt-2 ${
                    quizState.lastFeedback.correct ? "text-green-800" : "text-orange-800"
                  }`}>
                    {quizState.lastFeedback.feedback}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Answer Input */}
          <div className="flex flex-col gap-3">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Think out loud — Rafiki evaluates depth, not correctness"
              rows={5}
              disabled={loading || showFeedback}
              className="w-full resize-none rounded-2xl bg-secondary p-4 text-[15px] text-foreground leading-relaxed placeholder:text-text-muted outline-none focus:ring-2 focus:ring-primary/30 transition-all border-none disabled:opacity-50"
            />
          </div>

          {/* Submit Button */}
          <button
            onClick={handleSubmitAnswer}
            disabled={answer.length === 0 || loading || showFeedback}
            className={`w-full rounded-full py-3.5 text-[16px] font-medium transition-all border-none ${
              answer.length > 0 && !loading && !showFeedback
                ? "bg-primary text-primary-foreground hover:opacity-90"
                : "bg-secondary text-text-muted cursor-not-allowed"
            }`}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Evaluating...
              </span>
            ) : showFeedback ? (
              "Next question..."
            ) : (
              "Submit Answer"
            )}
          </button>

          <p className="text-center text-[12px] text-text-muted">
            Rafiki evaluates understanding depth, not just correctness
          </p>
        </div>
      </div>
    </div>
  )
}
