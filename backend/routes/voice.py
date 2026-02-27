"""
Voice & Chat API Routes
Endpoints for voice processing and coaching conversations
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

from auth import verify_token
from agents.voice_router import voice_router_agent
from llm_client import llm_client

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["voice", "chat"],
    dependencies=[Depends(verify_token)]
)


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class VoiceProcessRequest(BaseModel):
    transcription: str = Field(..., description="Speech-to-text transcription")


class SuggestedAction(BaseModel):
    type: str
    label: str


class VoiceProcessResponse(BaseModel):
    status: str
    intent: str
    confidence: float
    action_taken: str
    message: str
    note_path: Optional[str] = None
    suggested_actions: List[SuggestedAction]


class ChatMessage(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Previous messages in conversation"
    )
    include_vault_context: bool = Field(
        default=True,
        description="Whether to include vault context in response"
    )


class ChatResponse(BaseModel):
    status: str
    message: str
    sources: Optional[List[Dict[str, str]]] = None
    conversation_id: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Voice Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/voice/process", response_model=VoiceProcessResponse)
async def process_voice_input(request: VoiceProcessRequest) -> Dict[str, Any]:
    """
    Process voice transcription and route to appropriate action

    The voice router analyzes the transcription and determines intent:
    - **new_seed**: Creates a seed note for quick ideas/insights
    - **question**: Searches vault and answers questions about notes
    - **reflection**: Appends to daily note
    - **quiz_answer**: Routes to quiz API
    - **journal**: Creates/appends to journal entry

    Args:
        request: Voice transcription from speech-to-text

    Returns:
        Routed action result with intent, message, and suggested follow-ups
    """
    try:
        logger.info(f"Processing voice input: {request.transcription[:50]}...")

        result = await voice_router_agent.run(transcription=request.transcription)

        return result

    except Exception as e:
        logger.error(f"Voice processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process voice input: {str(e)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Chat Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def coach_chat(request: ChatRequest) -> Dict[str, Any]:
    """
    Free-form coaching conversation with Rafiki

    Rafiki is a Socratic coach that:
    - Asks clarifying questions rather than lecturing
    - References your vault notes to provide personalized guidance
    - Helps you think through problems, not solve them for you
    - Maintains conversation context across messages

    Args:
        request: Chat message with optional conversation history

    Returns:
        Rafiki's response with optional source references
    """
    try:
        logger.info(f"Chat message: {request.message[:50]}...")

        # Build context from vault if requested
        vault_context = ""
        sources = []

        if request.include_vault_context:
            # Search for relevant notes based on message keywords
            # Extract key terms (simple approach - could be improved)
            words = request.message.lower().split()
            # Remove common words
            stop_words = {"i", "me", "my", "the", "a", "an", "is", "are", "what", "how", "why"}
            key_terms = [w for w in words if w not in stop_words and len(w) > 3][:3]

            if key_terms:
                from mcp_client import mcp_client
                for term in key_terms:
                    try:
                        results = await mcp_client.search_notes(term)
                        for result in results[:2]:  # Top 2 per term
                            try:
                                note = await mcp_client.read_note(result["path"])
                                vault_context += f"\n**{result.get('title', 'Note')}:** {note.get('content', '')[:300]}\n"
                                sources.append({
                                    "title": result.get('title', 'Untitled'),
                                    "path": result["path"]
                                })
                            except:
                                pass
                    except:
                        pass

        # Build conversation history for LLM
        conversation = ""
        for msg in request.conversation_history[-5:]:  # Last 5 messages
            role = "User" if msg.role == "user" else "Rafiki"
            conversation += f"{role}: {msg.content}\n\n"

        # Generate response using Socratic coaching style
        system_prompt = """You are Rafiki, a Socratic AI coach for personal knowledge management using the SPARK methodology.

Your coaching philosophy:
- Ask clarifying questions rather than giving direct answers
- Help the user think through problems themselves
- Reference their own notes and insights to guide them
- Be warm but intellectually rigorous
- Challenge assumptions gently
- Focus on "why" and "how" questions

Your style:
- 2-3 sentences max per response
- One good question > three pieces of advice
- Personal and direct (use "you", reference their specific notes)
- No generic productivity advice

When you see vault context, connect it to their current thinking."""

        user_message = f"""Current question: {request.message}

{f"Context from their vault:\n{vault_context}" if vault_context else ""}

{f"Recent conversation:\n{conversation}" if conversation else ""}

Respond as Rafiki:"""

        response_text = await llm_client.complete(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=512,
            temperature=0.9  # Higher for more personality
        )

        return {
            "status": "success",
            "message": response_text.strip(),
            "sources": sources[:3] if sources else None,  # Limit to top 3
            "conversation_id": None  # Could implement session tracking later
        }

    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/chat/hello")
async def chat_hello() -> Dict[str, Any]:
    """
    Get a greeting from Rafiki (for testing chat connectivity)

    Returns:
        Simple greeting message
    """
    return {
        "status": "success",
        "message": "Hey! I'm Rafiki, your AI coach. What's on your mind today?",
        "available": True
    }
