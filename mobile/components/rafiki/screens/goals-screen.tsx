"use client"

import { GoalCard } from "../goal-card"

const goals = [
  {
    title: "Build end-to-end multi-agent workflow",
    description: "Create a working prototype with LangGraph and custom orchestration",
    progress: 60,
    status: "on-track" as const,
    statusLabel: "On Track",
    updatedAt: "Updated 2h ago",
  },
  {
    title: "Publish Frank About AI video on orchestration",
    description: "Script, record, and edit episode on agent orchestration patterns",
    progress: 20,
    status: "blocked" as const,
    statusLabel: "Blocked",
    updatedAt: "Updated 1d ago",
  },
  {
    title: "Complete LangGraph state management module",
    description: "Finish all exercises and document key learnings in vault",
    progress: 85,
    status: "on-track" as const,
    statusLabel: "On Track",
    updatedAt: "Updated 4h ago",
  },
  {
    title: "Document Product Agent system architecture",
    description: "Create comprehensive architecture docs for the Product Agent",
    progress: 0,
    status: "not-started" as const,
    statusLabel: "Not Started",
    updatedAt: "Not started",
  },
]

const legendItems = [
  { label: "Completed", color: "bg-success" },
  { label: "In Progress", color: "bg-primary" },
  { label: "Blocked", color: "bg-warning" },
  { label: "Not Started", color: "bg-secondary" },
]

export function GoalsScreen() {
  return (
    <div className="flex flex-col gap-5 px-5 pt-14 pb-24">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-[26px] font-bold text-foreground leading-tight">This Week</h1>
          <span className="text-[13px] text-text-secondary">Feb 17 &ndash; 23</span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] font-medium">
          <span className="text-primary">4 active</span>
          <span className="text-text-muted">&middot;</span>
          <span className="text-success">2 done</span>
          <span className="text-text-muted">&middot;</span>
          <span className="text-warning">1 blocked</span>
        </div>
      </div>

      {/* Master Progress Bar */}
      <div className="flex flex-col gap-2.5">
        <div className="flex h-1.5 w-full overflow-hidden rounded-full">
          <div className="bg-success" style={{ width: "30%" }} />
          <div className="bg-primary" style={{ width: "45%" }} />
          <div className="bg-warning" style={{ width: "15%" }} />
          <div className="bg-secondary" style={{ width: "10%" }} />
        </div>
        <div className="flex items-center gap-4">
          {legendItems.map((item) => (
            <div key={item.label} className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${item.color}`} />
              <span className="text-[11px] text-text-secondary">{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Goals List */}
      <div className="flex flex-col gap-4">
        {goals.map((goal, i) => (
          <GoalCard key={i} {...goal} />
        ))}
      </div>

      {/* Generate Next Week CTA */}
      <div className="rounded-2xl bg-card p-5 flex items-center justify-center border border-border card-shadow">
        <button className="text-[15px] text-primary font-medium bg-transparent border-none flex items-center gap-2 hover:opacity-80 transition-opacity">
          {"Generate Next Week's Goals"}
          <span className="text-primary">&rarr;</span>
        </button>
      </div>
    </div>
  )
}
