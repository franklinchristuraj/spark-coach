"use client"

import { useState } from "react"
import { ArrowLeft, BookOpen, Zap } from "lucide-react"

interface QuizScreenProps {
  onBack: () => void
}

export function QuizScreen({ onBack }: QuizScreenProps) {
  const [answer, setAnswer] = useState("")
  const currentQuestion = 2
  const totalQuestions = 5

  const progressDots = Array.from({ length: totalQuestions }, (_, i) => {
    if (i < currentQuestion - 1) return "completed"
    if (i === currentQuestion - 1) return "current"
    return "upcoming"
  })

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-5 pt-14 pb-4">
        <button onClick={onBack} className="text-text-secondary bg-transparent border-none" aria-label="Go back">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h2 className="text-[17px] font-bold text-foreground">Daily Challenge</h2>
        <div className="rounded-full bg-[rgba(249,115,22,0.12)] px-3 py-1 flex items-center gap-1">
          <Zap className="h-3 w-3 text-warning" fill="currentColor" />
          <span className="text-[11px] font-medium text-warning">7 day streak</span>
        </div>
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
              {currentQuestion} of {totalQuestions}
            </span>
          </div>

          {/* Topic Badge */}
          <div className="flex justify-center">
            <span className="rounded-full bg-[rgba(37,99,235,0.1)] px-4 py-1.5 text-[12px] font-medium text-primary">
              Multi-agent orchestration
            </span>
          </div>

          {/* Question Card */}
          <div className="relative rounded-2xl bg-card p-5 overflow-hidden border border-border card-shadow">
            <div className="absolute left-0 top-0 bottom-0 w-[3px] rounded-full bg-primary" />
            <div className="pl-4 flex flex-col gap-4">
              <span className="text-[10px] font-medium uppercase tracking-[0.06em] text-text-muted">
                Rafiki Asks
              </span>
              <p className="text-[17px] text-foreground leading-relaxed">
                {"When you last implemented an automation workflow \u2014 what was the real bottleneck? The logic design, the data structure, or the handoff between steps?"}
              </p>
              <div className="inline-flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1.5 self-start">
                <BookOpen className="h-3 w-3 text-text-muted" />
                <span className="text-[11px] text-text-muted">{"From: Product Agent notes \u00B7 Nov 2025"}</span>
              </div>
            </div>
          </div>

          {/* Answer Input */}
          <div className="flex flex-col gap-3">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Think out loud — Rafiki evaluates depth, not correctness"
              rows={5}
              className="w-full resize-none rounded-2xl bg-secondary p-4 text-[15px] text-foreground leading-relaxed placeholder:text-text-muted outline-none focus:ring-2 focus:ring-primary/30 transition-all border-none"
            />
          </div>

          {/* Submit Button */}
          <button
            disabled={answer.length === 0}
            className={`w-full rounded-full py-3.5 text-[16px] font-medium transition-all border-none ${
              answer.length > 0
                ? "bg-primary text-primary-foreground hover:opacity-90"
                : "bg-secondary text-text-muted cursor-not-allowed"
            }`}
          >
            Submit Answer
          </button>

          <p className="text-center text-[12px] text-text-muted">
            Rafiki will connect your answer to your vault notes
          </p>
        </div>
      </div>
    </div>
  )
}
