"use client"

import { useState } from "react"
import { FloatingNav } from "@/components/rafiki/floating-nav"
import { HomeScreen } from "@/components/rafiki/screens/home-screen"
import { ChatScreen } from "@/components/rafiki/screens/chat-screen"
import { GoalsScreen } from "@/components/rafiki/screens/goals-screen"
import { QuizScreen } from "@/components/rafiki/screens/quiz-screen"
import { InsightsScreen } from "@/components/rafiki/screens/insights-screen"

type Tab = "home" | "chat" | "goals" | "quiz" | "insights"

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("home")

  return (
    <div className="flex min-h-dvh items-center justify-center bg-[#E8E5E0]">
      {/* Mobile Shell */}
      <div className="relative w-full max-w-[390px] min-h-dvh md:min-h-0 md:h-[844px] bg-background overflow-hidden md:rounded-[40px] md:border md:border-border md:shadow-xl md:my-8">
        <div className="h-full overflow-y-auto scrollbar-hide">
          {activeTab === "home" && (
            <HomeScreen onNavigate={(tab) => setActiveTab(tab)} />
          )}
          {activeTab === "chat" && (
            <ChatScreen onBack={() => setActiveTab("home")} />
          )}
          {activeTab === "goals" && <GoalsScreen />}
          {activeTab === "quiz" && (
            <QuizScreen onBack={() => setActiveTab("home")} />
          )}
          {activeTab === "insights" && <InsightsScreen />}
        </div>
        <FloatingNav activeTab={activeTab} onTabChange={setActiveTab} />
      </div>
    </div>
  )
}
