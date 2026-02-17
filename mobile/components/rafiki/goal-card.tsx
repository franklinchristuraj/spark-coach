import { StatusBadge } from "./status-badge"

interface GoalCardProps {
  title: string
  description: string
  progress: number
  status: "completed" | "on-track" | "blocked" | "not-started"
  statusLabel: string
  updatedAt: string
}

export function GoalCard({ title, description, progress, status, statusLabel, updatedAt }: GoalCardProps) {
  return (
    <div className="rounded-2xl bg-card p-5 flex flex-col gap-3 border border-border card-shadow">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-[15px] font-bold text-foreground leading-snug flex-1">{title}</h3>
        <StatusBadge variant={status}>{statusLabel}</StatusBadge>
      </div>
      <p className="text-[13px] text-text-secondary leading-relaxed line-clamp-1">{description}</p>
      <div className="flex items-center gap-3">
        <div className="flex-1 h-1.5 rounded-full bg-secondary overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="text-[13px] font-bold text-primary">{progress}%</span>
      </div>
      <div className="flex items-center justify-between">
        <button className="rounded-full border border-border px-4 py-1.5 text-[12px] font-medium text-text-secondary hover:bg-secondary transition-colors bg-transparent">
          Log Update
        </button>
        <span className="text-[11px] text-text-muted">{updatedAt}</span>
      </div>
    </div>
  )
}
