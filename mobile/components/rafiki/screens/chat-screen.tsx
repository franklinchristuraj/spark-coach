"use client"

import { useState, useEffect, useRef } from "react"
import { ArrowLeft, Send, Mic, BookOpen, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useChat } from "@/hooks/use-api"

interface ChatScreenProps {
  onBack: () => void
}

type Mode = "text" | "voice"

interface Message {
  id: string
  role: "ai" | "user"
  content: string
}

const initialMessages: Message[] = [
  {
    id: "1",
    role: "ai",
    content:
      "What aspect of multi-agent systems feels least clear to you right now? I noticed you've added 4 seeds on this topic this week.",
  },
  {
    id: "2",
    role: "user",
    content: "I understand the concept but struggle with handoffs between agents",
  },
  {
    id: "3",
    role: "ai",
    content:
      "Interesting distinction. When you say handoffs \u2014 are you thinking about data passing, or control flow? They're quite different problems to solve.",
  },
]

const suggestions = ["Data passing", "Control flow", "Both actually"]

function VoiceListeningOverlay() {
  return (
    <div className="flex flex-col items-center gap-6 py-8">
      <div className="relative flex items-center justify-center">
        <div className="h-20 w-20 rounded-full bg-primary/10 animate-pulse-glow flex items-center justify-center">
          <div className="h-14 w-14 rounded-full bg-primary/20 flex items-center justify-center">
            <Mic className="h-7 w-7 text-primary" />
          </div>
        </div>
      </div>
      <div className="flex items-end gap-1 h-8">
        {[0.6, 0.8, 1, 0.7, 0.9, 1, 0.8, 0.5].map((scale, i) => (
          <div
            key={i}
            className="w-1 rounded-full bg-primary animate-bar-pulse"
            style={{
              height: `${scale * 32}px`,
              animationDelay: `${i * 0.15}s`,
            }}
          />
        ))}
      </div>
      <span className="text-[15px] text-text-secondary animate-pulse">Listening...</span>
      <span className="text-[12px] text-text-muted">Tap to stop</span>
    </div>
  )
}

export function ChatScreen({ onBack }: ChatScreenProps) {
  const [mode, setMode] = useState<Mode>("text")
  const { messages, loading, error, sendMessage } = useChat()
  const [inputValue, setInputValue] = useState("")
  const [isListening, setIsListening] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return

    await sendMessage(inputValue)
    setInputValue("")
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-5 pt-14 pb-3">
        <button onClick={onBack} className="text-text-secondary bg-transparent border-none" aria-label="Go back">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h2 className="text-[17px] font-bold text-foreground">Rafiki</h2>
        <div className="flex rounded-full bg-secondary p-0.5">
          <button
            onClick={() => { setMode("text"); setIsListening(false) }}
            className={cn(
              "rounded-full px-3.5 py-1.5 text-[12px] font-medium transition-all border-none",
              mode === "text" ? "bg-primary text-primary-foreground" : "bg-transparent text-text-secondary"
            )}
          >
            Text
          </button>
          <button
            onClick={() => setMode("voice")}
            className={cn(
              "rounded-full px-3.5 py-1.5 text-[12px] font-medium transition-all border-none",
              mode === "voice" ? "bg-primary text-primary-foreground" : "bg-transparent text-text-secondary"
            )}
          >
            Voice
          </button>
        </div>
      </div>

      {/* Session Context */}
      <div className="px-5 pb-3">
        <div className="inline-flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1.5">
          <BookOpen className="h-3 w-3 text-text-muted" />
          <span className="text-[11px] text-text-secondary">Based on your last 7 days &middot; 23 notes</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        <div className="flex flex-col gap-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-center px-8">
              <BookOpen className="h-12 w-12 text-text-muted" />
              <p className="text-[15px] text-foreground font-medium">Start a conversation</p>
              <p className="text-[13px] text-text-secondary">Ask Rafiki anything about your learning materials</p>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <div key={i} className={cn("flex flex-col gap-1", msg.role === "user" ? "items-end" : "items-start")}>
                  {msg.role === "assistant" && i === 0 && (
                    <span className="text-[11px] text-text-muted mb-0.5">Rafiki</span>
                  )}
                  <div
                    className={cn(
                      "max-w-[85%] rounded-2xl px-4 py-3",
                      msg.role === "assistant"
                        ? "bg-card border border-border card-shadow rounded-bl-md"
                        : "bg-[rgba(37,99,235,0.12)] rounded-br-md"
                    )}
                  >
                    <p className="text-[15px] text-foreground leading-relaxed">{msg.content}</p>
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-border/50">
                        <p className="text-[11px] text-text-muted mb-1.5">Sources:</p>
                        <div className="flex flex-col gap-1">
                          {msg.sources.map((source, idx) => (
                            <span key={idx} className="text-[12px] text-primary">
                              {source.title}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex items-start gap-1">
                  <div className="bg-card border border-border card-shadow rounded-2xl rounded-bl-md px-4 py-3">
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}


          {/* Voice Overlay */}
          {mode === "voice" && isListening && <VoiceListeningOverlay />}
        </div>
      </div>

      {/* Input Bar */}
      <div className="px-5 pb-20 pt-2">
        {error && (
          <div className="mb-3 rounded-2xl bg-red-50 border border-red-200 px-4 py-3">
            <p className="text-[13px] text-red-600">{error.message}</p>
          </div>
        )}
        {mode === "voice" ? (
          <div className="flex flex-col items-center gap-3">
            <p className="text-[13px] text-text-secondary text-center">Voice mode not yet implemented</p>
            <button
              onClick={() => setIsListening(!isListening)}
              className={cn(
                "flex h-14 w-14 items-center justify-center rounded-full transition-all border-none opacity-50 cursor-not-allowed",
                isListening
                  ? "bg-primary animate-pulse-glow"
                  : "bg-secondary"
              )}
              aria-label={isListening ? "Stop listening" : "Start listening"}
              disabled
            >
              <Mic className={cn("h-6 w-6", isListening ? "text-primary-foreground" : "text-primary")} />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3 rounded-full bg-secondary px-4 py-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask Rafiki..."
              disabled={loading}
              className="flex-1 bg-transparent text-[15px] text-foreground placeholder:text-text-muted outline-none border-none disabled:opacity-50"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || loading}
              className="bg-transparent border-none disabled:opacity-50"
              aria-label="Send message"
            >
              {loading ? (
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
              ) : (
                <Send
                  className={cn(
                    "h-5 w-5 transition-colors",
                    inputValue.length > 0 ? "text-primary" : "text-text-muted"
                  )}
                />
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
