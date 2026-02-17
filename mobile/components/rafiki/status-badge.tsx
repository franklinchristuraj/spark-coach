import { cn } from "@/lib/utils"

type BadgeVariant = "completed" | "on-track" | "blocked" | "not-started" | "high" | "medium" | "good"

interface StatusBadgeProps {
  variant: BadgeVariant
  children: React.ReactNode
  className?: string
}

const variantStyles: Record<BadgeVariant, string> = {
  "completed": "text-white bg-success",
  "on-track": "text-white bg-success",
  "blocked": "text-white bg-warning",
  "not-started": "text-text-secondary bg-secondary",
  "high": "text-white bg-destructive",
  "medium": "text-white bg-warning",
  "good": "text-white bg-success",
}

export function StatusBadge({ variant, children, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-[11px] font-medium tracking-wide",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  )
}
