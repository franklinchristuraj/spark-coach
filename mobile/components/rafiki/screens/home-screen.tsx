"use client"

import { MessageCircle, Brain, TrendingUp, BookOpen, Loader2 } from "lucide-react"
import { BriefingResponse } from "@/lib/api"

interface HomeScreenProps {
  onNavigate: (tab: "chat" | "quiz" | "insights") => void
  briefing: BriefingResponse | null
  loading: boolean
}

function TodayFocusCard({ briefing }: { briefing: BriefingResponse | null }) {
  const dailyPlan = briefing?.briefing?.daily_plan ?? [];
  const reviewsCount = briefing?.briefing?.reviews_count ?? 0;
  const milestone = briefing?.briefing?.learning_path_progress?.current_milestone;
  const pathName = briefing?.briefing?.learning_path_progress?.name;

  // Build a meaningful focus headline from the briefing data
  const focusTopic = milestone
    ? `Continue: ${milestone}`
    : pathName
      ? `${pathName}`
      : "Focus on your active learning resources today.";

  return (
    <div className="rounded-2xl bg-card p-5 relative overflow-hidden border border-border card-shadow">
      <div className="absolute left-0 top-0 bottom-0 w-[3px] rounded-full bg-primary" />
      <div className="pl-4 flex flex-col gap-3">
        <span className="text-[11px] font-medium uppercase tracking-[0.06em] text-primary">
          {"Today's Focus"}
        </span>
        <p className="text-[17px] font-semibold text-foreground leading-snug">
          {focusTopic}
        </p>
        {dailyPlan.length > 0 && (
          <ul className="flex flex-col gap-1.5">
            {dailyPlan.slice(0, 3).map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-primary mt-1 text-[10px]">●</span>
                <span className="text-[14px] text-text-secondary leading-snug">{item}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="flex items-center gap-1.5">
          <BookOpen className="h-3.5 w-3.5 text-text-muted" />
          <span className="text-[12px] text-text-muted">
            {reviewsCount > 0
              ? `${reviewsCount} review${reviewsCount !== 1 ? "s" : ""} due today`
              : "No reviews due today"}
          </span>
        </div>
      </div>
    </div>
  )
}

interface GoalsStripProps {
  briefing: BriefingResponse | null
  onNavigate: (tab: "chat" | "quiz" | "insights") => void
}

function GoalsStrip({ briefing, onNavigate }: GoalsStripProps) {
  const learningPath = briefing?.briefing?.learning_path_progress;
  const reviewsDue = briefing?.briefing?.reviews_due ?? [];
  const activeResources = briefing?.briefing?.stats?.active_resources || 0;

  // Build cards from learning path + reviews due
  const cards: Array<{
    title: string
    subtitle: string
    progress: number
    statusLabel: string
    isWarning: boolean
    action?: () => void
  }> = [];

  // Learning path card
  if (learningPath?.name) {
    cards.push({
      title: learningPath.name,
      subtitle: learningPath.current_milestone || "In progress",
      progress: learningPath.overall_progress || 0,
      statusLabel: learningPath.overall_progress > 50 ? "On Track" : "In Progress",
      isWarning: false,
    });
  }

  // Review cards (clickable → quiz)
  for (const review of reviewsDue.slice(0, 4)) {
    cards.push({
      title: review.title || "Untitled",
      subtitle: review.days_overdue > 0
        ? `${review.days_overdue} day${review.days_overdue !== 1 ? "s" : ""} overdue`
        : "Due today",
      progress: 0,
      statusLabel: review.days_overdue > 3 ? "Overdue" : "Review",
      isWarning: review.days_overdue > 3,
      action: () => onNavigate("quiz"),
    });
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-[17px] font-bold text-foreground">This Week</h2>
        <div className="flex items-baseline gap-0.5">
          <span className="text-[17px] font-bold text-primary">{activeResources}</span>
          <span className="text-[15px] text-text-secondary">{" active"}</span>
        </div>
      </div>
      {cards.length > 0 ? (
        <div className="flex gap-3 overflow-x-auto scrollbar-hide pb-1 -mr-5">
          {cards.map((card, i) => (
            <button
              key={i}
              onClick={card.action}
              disabled={!card.action}
              className="min-w-[164px] rounded-2xl bg-card p-4 flex flex-col gap-2.5 shrink-0 border border-border card-shadow text-left disabled:cursor-default hover:bg-secondary/40 transition-colors"
            >
              <span className="text-[13px] text-foreground font-medium leading-snug line-clamp-2">
                {card.title}
              </span>
              {card.progress > 0 ? (
                <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
                  <div
                    className="h-full rounded-full bg-primary transition-all duration-500"
                    style={{ width: `${card.progress}%` }}
                  />
                </div>
              ) : (
                <span className="text-[11px] text-text-muted">{card.subtitle}</span>
              )}
              <div className="flex items-center gap-1.5">
                <span
                  className={`h-2 w-2 rounded-full ${card.isWarning ? "bg-warning" : "bg-success"}`}
                />
                <span className={`text-[11px] font-medium ${card.isWarning ? "text-warning" : "text-success"}`}>
                  {card.statusLabel}
                </span>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div className="rounded-2xl bg-card p-4 border border-border card-shadow">
          <p className="text-[13px] text-text-secondary">No active learning paths yet. Start your learning journey!</p>
        </div>
      )}
    </div>
  )
}

function HomeSkeleton() {
  return (
    <div className="flex flex-col gap-6 px-5 pt-14">
      {/* Header skeleton */}
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-2">
          <div className="h-7 w-48 bg-muted animate-pulse rounded-lg" />
          <div className="h-4 w-32 bg-muted animate-pulse rounded-lg" />
        </div>
        <div className="h-9 w-9 rounded-full bg-muted animate-pulse" />
      </div>
      {/* Today's focus skeleton */}
      <div className="rounded-2xl bg-muted animate-pulse h-28 rounded-2xl" />
      {/* Goals strip skeleton */}
      <div className="flex flex-col gap-3">
        <div className="h-5 w-24 bg-muted animate-pulse rounded-lg" />
        <div className="h-24 bg-muted animate-pulse rounded-2xl" />
      </div>
      {/* Action cards skeleton */}
      <div className="flex gap-3">
        <div className="flex-1 h-20 bg-muted animate-pulse rounded-2xl" />
        <div className="flex-1 h-20 bg-muted animate-pulse rounded-2xl" />
        <div className="flex-1 h-20 bg-muted animate-pulse rounded-2xl" />
      </div>
    </div>
  )
}

interface ActionCardProps {
  icon: React.ElementType
  label: string
  isPrimary?: boolean
  onClick?: () => void
}

function ActionCard({ icon: Icon, label, isPrimary, onClick }: ActionCardProps) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-1 flex-col items-center gap-2.5 rounded-2xl bg-card p-5 transition-colors hover:bg-secondary/60 border border-border card-shadow ${
        isPrimary ? "ring-1 ring-primary/20" : ""
      }`}
    >
      <Icon
        className={`h-6 w-6 ${isPrimary ? "text-primary" : "text-text-secondary"}`}
        strokeWidth={1.5}
      />
      <span className="text-[12px] font-medium text-text-secondary">{label}</span>
    </button>
  )
}

export function HomeScreen({ onNavigate, briefing, loading }: HomeScreenProps) {
  const now = new Date()
  const hour = now.getHours()
  const greeting = briefing?.briefing?.greeting ||
    (hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening");
  const dayName = now.toLocaleDateString("en-US", { weekday: "long" })
  const monthDay = now.toLocaleDateString("en-US", { month: "short", day: "numeric" })

  if (loading && !briefing) {
    return <HomeSkeleton />
  }

  return (
    <div className="flex flex-col gap-6 px-5 pt-14 pb-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-[26px] font-bold text-foreground leading-tight">
            {greeting}, Franklin
          </h1>
          <span className="text-[13px] text-text-secondary">
            {dayName} &middot; {monthDay}
          </span>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-secondary">
          <span className="text-[12px] font-medium text-text-secondary">FC</span>
        </div>
      </div>

      {/* Today's Focus */}
      <TodayFocusCard briefing={briefing} />

      {/* Goals Strip */}
      <GoalsStrip briefing={briefing} onNavigate={onNavigate} />

      {/* Action Cards */}
      <div className="flex gap-3">
        <ActionCard icon={MessageCircle} label="Chat" isPrimary onClick={() => onNavigate("chat")} />
        <ActionCard icon={Brain} label="Quiz" onClick={() => onNavigate("quiz")} />
        <ActionCard icon={TrendingUp} label="Insights" onClick={() => onNavigate("insights")} />
      </div>
    </div>
  )
}
