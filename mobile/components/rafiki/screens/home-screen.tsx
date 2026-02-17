"use client"

import { MessageCircle, Brain, TrendingUp, BookOpen, Loader2 } from "lucide-react"
import { useBriefing } from "@/hooks/use-api"

interface HomeScreenProps {
  onNavigate: (tab: "chat" | "quiz" | "insights") => void
}

function TodayFocusCard({ briefing }: { briefing: any }) {
  const dailyPlan = briefing?.briefing?.daily_plan?.[0] || "Focus on your active learning resources today.";

  return (
    <div className="rounded-2xl bg-card p-5 relative overflow-hidden border border-border card-shadow">
      <div className="absolute left-0 top-0 bottom-0 w-[3px] rounded-full bg-primary" />
      <div className="pl-4 flex flex-col gap-2.5">
        <span className="text-[11px] font-medium uppercase tracking-[0.06em] text-primary">
          {"Today's Focus"}
        </span>
        <p className="text-[17px] text-foreground leading-relaxed">
          {dailyPlan}
        </p>
        <div className="flex items-center gap-1.5">
          <BookOpen className="h-3.5 w-3.5 text-text-muted" />
          <span className="text-[12px] text-text-muted">From your learning progress</span>
        </div>
      </div>
    </div>
  )
}

function GoalsStrip({ briefing }: { briefing: any }) {
  const learningPath = briefing?.briefing?.learning_path_progress;

  // Mock goals for now (backend doesn't have goals system yet)
  const goals = learningPath ? [
    {
      title: learningPath.name || "Learning Path",
      progress: learningPath.overall_progress || 0,
      status: learningPath.overall_progress > 50 ? "On Track" : "In Progress",
      isBlocked: false
    },
  ] : [];

  const activeResources = briefing?.briefing?.stats?.active_resources || 0;
  const totalResources = briefing?.briefing?.stats?.active_resources || 0;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-[17px] font-bold text-foreground">This Week</h2>
        <div className="flex items-baseline gap-0.5">
          <span className="text-[17px] font-bold text-primary">{activeResources}</span>
          <span className="text-[15px] text-text-secondary">{" active"}</span>
        </div>
      </div>
      {goals.length > 0 ? (
        <div className="flex gap-3 overflow-x-auto scrollbar-hide pb-1 -mr-5">
          {goals.map((goal, i) => (
            <div key={i} className="min-w-[164px] rounded-2xl bg-card p-4 flex flex-col gap-2.5 shrink-0 border border-border card-shadow">
              <span className="text-[13px] text-foreground font-medium leading-snug line-clamp-1">
                {goal.title}
              </span>
              <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${goal.isBlocked ? "bg-warning" : "bg-primary"}`}
                  style={{ width: `${goal.progress}%` }}
                />
              </div>
              <div className="flex items-center gap-1.5">
                <span
                  className={`h-2 w-2 rounded-full ${goal.isBlocked ? "bg-warning" : "bg-success"}`}
                />
                <span className={`text-[11px] font-medium ${goal.isBlocked ? "text-warning" : "text-success"}`}>{goal.status}</span>
              </div>
            </div>
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

export function HomeScreen({ onNavigate }: HomeScreenProps) {
  const { data: briefing, loading, error } = useBriefing("Franklin");

  const now = new Date()
  const hour = now.getHours()
  const greeting = briefing?.briefing?.greeting ||
    (hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening");
  const dayName = now.toLocaleDateString("en-US", { weekday: "long" })
  const monthDay = now.toLocaleDateString("en-US", { month: "short", day: "numeric" })

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 px-5">
        <div className="text-center">
          <p className="text-[15px] text-foreground font-medium">Unable to load briefing</p>
          <p className="text-[13px] text-text-secondary mt-1">Make sure the backend is running</p>
          <p className="text-[11px] text-text-muted mt-2 font-mono">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 px-5 pt-14 pb-24">
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
      <GoalsStrip briefing={briefing} />

      {/* Action Cards */}
      <div className="flex gap-3">
        <ActionCard icon={MessageCircle} label="Chat" isPrimary onClick={() => onNavigate("chat")} />
        <ActionCard icon={Brain} label="Quiz" onClick={() => onNavigate("quiz")} />
        <ActionCard icon={TrendingUp} label="Insights" onClick={() => onNavigate("insights")} />
      </div>
    </div>
  )
}
