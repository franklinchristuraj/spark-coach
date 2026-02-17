"use client"

import { Home, MessageCircle, Target, Brain, TrendingUp } from "lucide-react"
import { cn } from "@/lib/utils"

type Tab = "home" | "chat" | "goals" | "quiz" | "insights"

interface FloatingNavProps {
  activeTab: Tab
  onTabChange: (tab: Tab) => void
}

const tabs: { id: Tab; icon: typeof Home; label: string }[] = [
  { id: "home", icon: Home, label: "Home" },
  { id: "chat", icon: MessageCircle, label: "Chat" },
  { id: "goals", icon: Target, label: "Goals" },
  { id: "quiz", icon: Brain, label: "Quiz" },
  { id: "insights", icon: TrendingUp, label: "Insights" },
]

export function FloatingNav({ activeTab, onTabChange }: FloatingNavProps) {
  return (
    <div className="absolute bottom-0 left-0 right-0 z-50">
      <nav
        className="flex h-[72px] items-center justify-around bg-card border-t border-border px-2"
        role="navigation"
        aria-label="Main navigation"
      >
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className="flex flex-col items-center gap-1 outline-none border-none bg-transparent px-3 py-2"
              aria-label={tab.label}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon
                className={cn(
                  "h-5 w-5 transition-colors duration-200",
                  isActive ? "text-primary" : "text-text-muted"
                )}
                strokeWidth={isActive ? 2.5 : 1.8}
              />
              <span
                className={cn(
                  "text-[10px] font-medium transition-colors duration-200",
                  isActive ? "text-primary" : "text-text-muted"
                )}
              >
                {tab.label}
              </span>
            </button>
          )
        })}
      </nav>
    </div>
  )
}
