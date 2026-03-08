"use client"

import { useState } from "react"
import { logout } from "@/services/api"
import { FloatingNav } from "@/components/rafiki/floating-nav"
import { HomeScreen } from "@/components/rafiki/screens/home-screen"
import { ChatScreen } from "@/components/rafiki/screens/chat-screen"
import { GoalsScreen } from "@/components/rafiki/screens/goals-screen"
import { QuizScreen } from "@/components/rafiki/screens/quiz-screen"
import { InsightsScreen } from "@/components/rafiki/screens/insights-screen"
import { useBriefing } from "@/hooks/use-api"

type Tab = "home" | "chat" | "goals" | "quiz" | "insights"

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("home")
  const { data: briefingData, loading: briefingLoading } = useBriefing("Franklin")

  const reviewsDue = briefingData?.briefing?.reviews_due ?? []

  return (
    <div className="relative flex min-h-dvh items-center justify-center bg-[#E8E5E0]">
      {/* Logout — small, unobtrusive, top-right */}
      <button
        onClick={logout}
        className="absolute top-4 right-4 z-50 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        Sign out
      </button>
      {/* Mobile Shell */}
      <div className="relative w-full max-w-[390px] min-h-dvh md:min-h-0 md:h-[844px] bg-background overflow-hidden md:rounded-[40px] md:border md:border-border md:shadow-xl md:my-8 flex flex-col">
        <div className="flex-1 min-h-0 overflow-y-auto scrollbar-hide pb-[72px]">
          {activeTab === "home" && (
            <HomeScreen
              onNavigate={(tab) => setActiveTab(tab)}
              briefing={briefingData}
              loading={briefingLoading}
            />
          )}
          {activeTab === "chat" && (
            <ChatScreen onBack={() => setActiveTab("home")} />
          )}
          {activeTab === "goals" && <GoalsScreen />}
          {activeTab === "quiz" && (
            <QuizScreen
              onBack={() => setActiveTab("home")}
              reviewsDue={reviewsDue}
            />
          )}
          {activeTab === "insights" && <InsightsScreen />}
        </div>
        <FloatingNav activeTab={activeTab} onTabChange={setActiveTab} />
      </div>
    </div>
  )
}
