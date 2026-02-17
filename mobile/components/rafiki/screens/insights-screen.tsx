"use client"

import { useState } from "react"
import { RefreshCw, Loader2 } from "lucide-react"
import { StatusBadge } from "../status-badge"
import { cn } from "@/lib/utils"
import { useStats } from "@/hooks/use-api"

type FilterType = "all" | "gaps" | "stale" | "strong"

const filters: { id: FilterType; label: string }[] = [
  { id: "all", label: "All" },
  { id: "gaps", label: "Gaps" },
  { id: "stale", label: "Stale" },
  { id: "strong", label: "Strong" },
]

const insights = [
  {
    title: "Agentic AI \u2014 many seeds, no deep projects",
    severity: "high" as const,
    severityLabel: "High",
    description: "You've captured 12 seeds on this topic but never promoted to a Project.",
    filter: "gaps" as FilterType,
  },
  {
    title: "LangGraph \u2014 last touched 6 weeks ago",
    severity: "medium" as const,
    severityLabel: "Medium",
    description: "Strong notes exist but no recent activity. Time to revisit?",
    filter: "stale" as FilterType,
  },
  {
    title: "Make.com workflows \u2014 well documented",
    severity: "good" as const,
    severityLabel: "Good",
    description: "Your most complete knowledge area. Could be workshop content.",
    filter: "strong" as FilterType,
  },
]

const sparkLayers = [
  { label: "Seeds", percentage: 40 },
  { label: "Projects", percentage: 65 },
  { label: "Areas", percentage: 80 },
  { label: "Resources", percentage: 55 },
  { label: "Knowledge", percentage: 30 },
]

interface HealthScoreProps {
  score: number
  trend: string
  resources: {
    active: number
    at_risk: number
    mastered: number
    total_in_path: number
  }
}

function HealthScoreCard({ score, trend, resources }: HealthScoreProps) {
  const trendValue = trend === "up" ? 4 : trend === "down" ? -2 : 0
  const trendSymbol = trend === "up" ? "↑" : trend === "down" ? "↓" : "→"
  const displayScore = Math.round(score)

  const total = resources.total_in_path || 1
  const strongPct = (resources.mastered / total) * 100
  const growingPct = (resources.active / total) * 100
  const gapsPct = (resources.at_risk / total) * 100
  const unexploredPct = Math.max(0, 100 - strongPct - growingPct - gapsPct)

  return (
    <div className="rounded-2xl bg-card p-5 flex flex-col gap-5 border border-border card-shadow">
      <div className="flex items-start justify-between">
        {/* Left: Score */}
        <div className="flex flex-col gap-1">
          <div className="flex items-baseline">
            <span className="text-[52px] font-bold text-primary leading-none">{displayScore}</span>
            <span className="text-[28px] font-bold text-primary ml-0.5">%</span>
          </div>
          <span className="text-[13px] text-text-secondary">Average Retention</span>
          {trendValue !== 0 && (
            <span className={`text-[12px] font-medium ${trendValue > 0 ? "text-success" : "text-warning"}`}>
              {trendSymbol} {Math.abs(trendValue)}pts this week
            </span>
          )}
        </div>
        {/* Right: Sparkline */}
        <div className="flex items-end gap-[3px] h-10 pt-2">
          {[18, 22, 20, 28, 25, 32, 34].map((h, i) => (
            <div
              key={i}
              className="w-1.5 rounded-full bg-primary/40"
              style={{ height: `${h}px` }}
            />
          ))}
        </div>
      </div>

      {/* Segmented Bar */}
      <div className="flex flex-col gap-2.5">
        <div className="flex h-1.5 w-full overflow-hidden rounded-full">
          <div className="bg-primary" style={{ width: `${strongPct}%` }} />
          <div className="bg-primary/40" style={{ width: `${growingPct}%` }} />
          <div className="bg-secondary" style={{ width: `${gapsPct}%` }} />
          <div className="bg-[#E5E2DE]" style={{ width: `${unexploredPct}%` }} />
        </div>
        <div className="flex items-center gap-4 flex-wrap">
          {[
            { label: "Strong", color: "bg-primary" },
            { label: "Growing", color: "bg-primary/40" },
            { label: "Gaps", color: "bg-secondary" },
            { label: "Unexplored", color: "bg-[#E5E2DE]" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${item.color}`} />
              <span className="text-[10px] text-text-secondary">{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export function InsightsScreen() {
  const [activeFilter, setActiveFilter] = useState<FilterType>("all")
  const { data: stats, loading, error, refetch } = useStats("this_week")

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 px-5">
        <div className="text-center">
          <p className="text-[15px] text-foreground font-medium">Unable to load insights</p>
          <p className="text-[13px] text-text-secondary mt-1">
            {error?.message || "No data available"}
          </p>
        </div>
      </div>
    )
  }

  // Generate insights from real data
  const insights = []

  // At-risk resources
  if (stats.resources.at_risk > 0) {
    insights.push({
      title: `${stats.resources.at_risk} resources need attention`,
      severity: "high" as const,
      severityLabel: "High",
      description: "These resources haven't been reviewed recently and may be at risk of being forgotten.",
      filter: "stale" as FilterType,
    })
  }

  // Declining resources
  if (stats.retention.declining && stats.retention.declining.length > 0) {
    insights.push({
      title: `${stats.retention.declining.length} resources declining`,
      severity: "medium" as const,
      severityLabel: "Medium",
      description: `Retention scores are dropping for: ${stats.retention.declining.slice(0, 2).join(", ")}`,
      filter: "gaps" as FilterType,
    })
  }

  // Improving resources
  if (stats.retention.improving && stats.retention.improving.length > 0) {
    insights.push({
      title: `${stats.retention.improving.length} resources improving`,
      severity: "good" as const,
      severityLabel: "Good",
      description: `Great progress on: ${stats.retention.improving.slice(0, 2).join(", ")}`,
      filter: "strong" as FilterType,
    })
  }

  // Mastered resources
  if (stats.resources.mastered > 0) {
    insights.push({
      title: `${stats.resources.mastered} resources mastered`,
      severity: "good" as const,
      severityLabel: "Good",
      description: "You've achieved high retention on these resources. Consider sharing your knowledge.",
      filter: "strong" as FilterType,
    })
  }

  const filteredInsights =
    activeFilter === "all"
      ? insights
      : insights.filter((i) => i.filter === activeFilter)

  return (
    <div className="flex flex-col gap-5 px-5 pt-14 pb-24">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-[26px] font-bold text-foreground leading-tight">Knowledge Map</h1>
        <div className="flex items-center gap-2">
          <span className="text-[13px] text-text-secondary">
            {stats.resources.total_in_path} resources tracked
          </span>
          <button
            onClick={() => refetch()}
            className="bg-transparent border-none p-0"
            aria-label="Refresh data"
          >
            <RefreshCw className="h-3.5 w-3.5 text-text-muted hover:text-text-secondary transition-colors" />
          </button>
        </div>
      </div>

      {/* Health Score */}
      <HealthScoreCard
        score={stats.retention.average_score}
        trend={stats.learning_hours.trend}
        resources={stats.resources}
      />

      {/* Filter Chips */}
      <div className="flex gap-2">
        {filters.map((f) => (
          <button
            key={f.id}
            onClick={() => setActiveFilter(f.id)}
            className={cn(
              "rounded-full px-4 py-2 text-[13px] font-medium transition-all border-none",
              activeFilter === f.id
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-text-secondary hover:bg-[#E8E5E0]"
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Insights List */}
      <div className="flex flex-col gap-3">
        {filteredInsights.map((insight, i) => (
          <div key={i} className="rounded-2xl bg-card p-5 flex flex-col gap-2.5 border border-border card-shadow">
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-[15px] font-bold text-foreground leading-snug flex-1">
                {insight.title}
              </h3>
              <StatusBadge variant={insight.severity}>{insight.severityLabel}</StatusBadge>
            </div>
            <p className="text-[13px] text-text-secondary leading-relaxed">{insight.description}</p>
            <div className="flex justify-end pt-1">
              <button className="text-[13px] text-primary font-medium bg-transparent border-none hover:opacity-80 transition-opacity">
                {"Explore with Rafiki \u2192"}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Resource Stats */}
      <div className="flex flex-col gap-4">
        <span className="text-[11px] font-medium uppercase tracking-[0.06em] text-text-muted">
          Resource Distribution
        </span>
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-2xl bg-card p-4 border border-border card-shadow">
            <p className="text-[24px] font-bold text-primary">{stats.resources.active}</p>
            <p className="text-[12px] text-text-secondary mt-1">Active Resources</p>
          </div>
          <div className="rounded-2xl bg-card p-4 border border-border card-shadow">
            <p className="text-[24px] font-bold text-warning">{stats.resources.at_risk}</p>
            <p className="text-[12px] text-text-secondary mt-1">At Risk</p>
          </div>
          <div className="rounded-2xl bg-card p-4 border border-border card-shadow">
            <p className="text-[24px] font-bold text-success">{stats.resources.mastered}</p>
            <p className="text-[12px] text-text-secondary mt-1">Mastered</p>
          </div>
          <div className="rounded-2xl bg-card p-4 border border-border card-shadow">
            <p className="text-[24px] font-bold text-primary">{stats.quizzes.completed_this_week}</p>
            <p className="text-[12px] text-text-secondary mt-1">Quizzes This Week</p>
          </div>
        </div>
      </div>

      {/* Learning Hours */}
      <div className="rounded-2xl bg-card p-5 border border-border card-shadow">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[15px] font-bold text-foreground">Learning Hours</span>
          <span className="text-[12px] text-text-secondary">This Week</span>
        </div>
        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-[32px] font-bold text-primary">{stats.learning_hours.this_week.toFixed(1)}</span>
          <span className="text-[15px] text-text-secondary">/ {stats.learning_hours.target}h goal</span>
        </div>
        <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${Math.min((stats.learning_hours.this_week / stats.learning_hours.target) * 100, 100)}%` }}
          />
        </div>
      </div>
    </div>
  )
}
