"""
Voice Router Agent
Classifies voice transcriptions and routes to appropriate actions
"""
from typing import Dict, Any, List
from datetime import datetime
import logging
import json
import re

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class VoiceRouterAgent(BaseAgent):
    """
    Routes voice transcriptions to appropriate SPARK actions

    Supported intents:
    - new_seed: Capture quick idea/insight
    - question: Query about existing notes
    - reflection: Learning reflection for daily note
    - quiz_answer: Answer to quiz question
    - journal: Personal journal entry
    """

    async def run(self, transcription: str, **kwargs) -> Dict[str, Any]:
        """
        Process voice transcription and route to action

        Args:
            transcription: Text from speech-to-text

        Returns:
            Dictionary with intent, action_taken, and results
        """
        logger.info(f"🎤 Processing voice input: {transcription[:100]}...")

        try:
            # Classify intent using LLM
            classification = await self._classify_intent(transcription)

            intent = classification.get("intent")
            confidence = classification.get("confidence", 0.8)

            logger.info(f"Classified as: {intent} (confidence: {confidence})")

            # Route to appropriate handler
            if intent == "new_seed":
                result = await self._handle_new_seed(transcription, classification)
            elif intent == "question":
                result = await self._handle_question(transcription, classification)
            elif intent == "reflection":
                result = await self._handle_reflection(transcription)
            elif intent == "quiz_answer":
                result = await self._handle_quiz_answer(transcription)
            elif intent == "journal":
                result = await self._handle_journal(transcription)
            else:
                # Fallback: treat as seed
                result = await self._handle_new_seed(transcription, classification)

            return {
                "status": "success",
                "intent": intent,
                "confidence": confidence,
                **result
            }

        except Exception as e:
            logger.error(f"Voice routing failed: {str(e)}")
            raise

    async def _classify_intent(self, transcription: str) -> Dict[str, Any]:
        """
        Use LLM to classify voice input intent

        Args:
            transcription: Voice input text

        Returns:
            Classification result with intent and metadata
        """
        system_prompt = """You are an intent classifier for a personal knowledge management system.

Classify voice inputs into these intents:
- new_seed: Quick ideas, insights, connections between concepts, "I just realized..."
- question: Questions about existing notes, "what did I write about...", "remind me..."
- reflection: Learning reflections, progress updates, "today I learned..."
- quiz_answer: Answering a quiz question (usually follows "the answer is...")
- journal: Personal thoughts, feelings, daily observations

Consider:
- Casual speech patterns
- Incomplete sentences
- Context clues (time references, question words)

Return JSON with: intent, confidence (0-1), key_concepts (list), suggested_title"""

        user_message = f"""Classify this voice input:

"{transcription}"

Return JSON only."""

        try:
            result = await self.llm.complete_json(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=512
            )
            return result

        except Exception as e:
            logger.error(f"Intent classification failed: {str(e)}")
            # Fallback classification
            return {
                "intent": "new_seed",
                "confidence": 0.5,
                "key_concepts": [],
                "suggested_title": ""
            }

    async def _handle_new_seed(
        self,
        transcription: str,
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new seed note from voice input

        Args:
            transcription: Voice text
            classification: Intent classification result

        Returns:
            Action result with note path and suggestions
        """
        try:
            # Generate title
            title = classification.get("suggested_title", "")
            if not title:
                # Extract from transcription (first few words)
                words = transcription.split()[:8]
                title = "-".join(words).lower()
                title = re.sub(r'[^a-z0-9-]', '', title)

            # Create seed note content
            content = f"""# Seed Note (Voice Captured)

{transcription}

---
**Captured:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Source:** Voice input
**Key concepts:** {', '.join(classification.get('key_concepts', []))}
"""

            # Generate note path
            note_path = f"01_seeds/{title}.md"

            # Create note via MCP
            await self.mcp.create_note(note_path, content)

            logger.info(f"Created seed note: {note_path}")

            # Check for potential connections
            key_concepts = classification.get("key_concepts", [])
            connections = []
            if key_concepts:
                # Search for related notes
                for concept in key_concepts[:2]:  # Limit to avoid too many searches
                    try:
                        related = await self.mcp.search_notes(concept)
                        if related:
                            connections.extend(related[:2])  # Top 2 per concept
                    except:
                        pass

            suggested_actions = []
            if connections:
                suggested_actions.append({
                    "type": "link_notes",
                    "label": f"Link to {len(connections)} related notes"
                })

            return {
                "action_taken": "created_note",
                "note_path": note_path,
                "message": f"Captured as a seed note: {title}",
                "suggested_actions": suggested_actions,
                "connections_found": len(connections)
            }

        except Exception as e:
            logger.error(f"Failed to create seed: {str(e)}")
            return {
                "action_taken": "failed",
                "message": f"Could not create seed note: {str(e)}",
                "suggested_actions": []
            }

    async def _handle_question(
        self,
        transcription: str,
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Answer question about vault contents

        Args:
            transcription: Question text
            classification: Intent classification

        Returns:
            Answer based on vault search
        """
        try:
            # Extract key terms from question
            key_concepts = classification.get("key_concepts", [])

            if not key_concepts:
                # Fallback: use simple word extraction
                words = transcription.lower().split()
                # Remove common question words
                stop_words = {"what", "when", "where", "why", "how", "did", "i", "about", "the"}
                key_concepts = [w for w in words if w not in stop_words and len(w) > 3][:3]

            # Search vault
            search_results = []
            for concept in key_concepts[:2]:
                try:
                    results = await self.mcp.search_notes(concept)
                    search_results.extend(results[:3])
                except:
                    pass

            if not search_results:
                return {
                    "action_taken": "no_results",
                    "message": "I couldn't find relevant notes in your vault. Try asking differently?",
                    "suggested_actions": [{
                        "type": "create_seed",
                        "label": "Capture this as a new seed"
                    }]
                }

            # Generate answer using LLM with context
            context_notes = []
            for result in search_results[:3]:
                try:
                    note = await self.mcp.read_note(result["path"])
                    context_notes.append(f"**{result.get('title', 'Untitled')}:**\n{note.get('content', '')[:500]}")
                except:
                    pass

            context = "\n\n".join(context_notes)

            answer = await self.llm.complete(
                system_prompt="You are a helpful assistant answering questions based on the user's personal notes. Be concise and reference specific notes.",
                user_message=f"Question: {transcription}\n\nContext from notes:\n{context}\n\nAnswer briefly:",
                max_tokens=512
            )

            return {
                "action_taken": "answered",
                "message": answer,
                "sources": [{"title": r.get("title"), "path": r["path"]} for r in search_results[:3]],
                "suggested_actions": []
            }

        except Exception as e:
            logger.error(f"Failed to answer question: {str(e)}")
            return {
                "action_taken": "failed",
                "message": "I had trouble searching your vault. Please try again.",
                "suggested_actions": []
            }

    async def _handle_reflection(self, transcription: str) -> Dict[str, Any]:
        """
        Append reflection to today's daily note

        Args:
            transcription: Reflection text

        Returns:
            Result of appending to daily note
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            daily_note_path = f"00_daily/{today}.md"

            reflection_entry = f"\n## 🎤 Voice Reflection ({datetime.now().strftime('%H:%M')})\n\n{transcription}\n\n---\n"

            # Try to append to daily note
            try:
                await self.mcp.append_note(daily_note_path, reflection_entry)
                action = "appended"
            except:
                # Create new daily note if doesn't exist
                content = f"# Daily Note - {today}\n\n{reflection_entry}"
                await self.mcp.create_note(daily_note_path, content)
                action = "created"

            return {
                "action_taken": action,
                "note_path": daily_note_path,
                "message": "Added reflection to your daily note",
                "suggested_actions": []
            }

        except Exception as e:
            logger.error(f"Failed to save reflection: {str(e)}")
            return {
                "action_taken": "failed",
                "message": f"Could not save reflection: {str(e)}",
                "suggested_actions": []
            }

    async def _handle_quiz_answer(self, transcription: str) -> Dict[str, Any]:
        """
        Handle voice quiz answer (requires context from active quiz session)

        Args:
            transcription: Answer text

        Returns:
            Instruction to use quiz API
        """
        return {
            "action_taken": "redirect",
            "message": "To submit quiz answers, please use the quiz API endpoint",
            "suggested_actions": [{
                "type": "use_quiz_api",
                "label": "Submit via /api/v1/quiz/answer"
            }]
        }

    async def _handle_journal(self, transcription: str) -> Dict[str, Any]:
        """
        Save personal journal entry

        Args:
            transcription: Journal text

        Returns:
            Result of creating journal entry
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            timestamp = datetime.now().strftime("%H:%M")

            journal_path = f"00_daily/journal-{today}.md"

            entry = f"\n## {timestamp}\n\n{transcription}\n\n---\n"

            try:
                await self.mcp.append_note(journal_path, entry)
                action = "appended"
            except:
                content = f"# Journal - {today}\n\n{entry}"
                await self.mcp.create_note(journal_path, content)
                action = "created"

            return {
                "action_taken": action,
                "note_path": journal_path,
                "message": "Saved to your journal",
                "suggested_actions": []
            }

        except Exception as e:
            logger.error(f"Failed to save journal: {str(e)}")
            return {
                "action_taken": "failed",
                "message": f"Could not save journal entry: {str(e)}",
                "suggested_actions": []
            }


# Global agent instance
voice_router_agent = VoiceRouterAgent()
