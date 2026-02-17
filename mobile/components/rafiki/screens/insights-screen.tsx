"use client"

import { useState } from "react"
import { RefreshCw } from "lucide-react"
import { StatusBadge } from "../status-badge"
import { cn } from "@/lib/utils"

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

function HealthScoreCard() {
  return (
    <div className="rounded-2xl bg-card p-5 flex flex-col gap-5 border border-border card-shadow">
      <div className="flex items-start justify-between">
        {/* Left: Score */}
        <div className="flex flex-col gap-1">
          <div className="flex items-baseline">
            <span className="text-[52px] font-bold text-primary leading-none">73</span>
            <span className="text-[28px] font-bold text-primary ml-0.5">%</span>
          </div>
          <span className="text-[13px] text-text-secondary">Knowledge Coverage</span>
          <span className="text-[12px] text-success font-medium">&#8593; 4pts this week</span>
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
          <div className="bg-primary" style={{ width: "30%" }} />
          <div className="bg-primary/40" style={{ width: "35%" }} />
          <div className="bg-secondary" style={{ width: "20%" }} />
          <div className="bg-[#E5E2DE]" style={{ width: "15%" }} />
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
          <span className="text-[13px] text-text-secondary">{"847 notes synced \u00B7 2h ago"}</span>
          <button className="bg-transparent border-none p-0" aria-label="Sync now">
            <RefreshCw className="h-3.5 w-3.5 text-text-muted hover:text-text-secondary transition-colors" />
          </button>
        </div>
      </div>

      {/* Health Score */}
      <HealthScoreCard />

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

      {/* SPARK Coverage Chart */}
      <div className="flex flex-col gap-4">
        <span className="text-[11px] font-medium uppercase tracking-[0.06em] text-text-muted">
          Vault Coverage by Layer
        </span>
        <div className="flex flex-col gap-4">
          {sparkLayers.map((layer) => (
            <div key={layer.label} className="flex items-center gap-3">
              <span className="text-[13px] text-text-secondary w-20 shrink-0">{layer.label}</span>
              <div className="flex-1 h-1.5 rounded-full bg-secondary overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-700"
                  style={{ width: `${layer.percentage}%` }}
                />
              </div>
              <span className="text-[13px] font-bold text-primary w-10 text-right">{layer.percentage}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
