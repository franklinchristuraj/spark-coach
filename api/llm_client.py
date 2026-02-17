"""
LLM Client for SPARK Coach
Abstraction layer for Claude API (primary) and Gemini (fallback)
"""
import json
import logging
from typing import Optional, Dict, Any, List
from config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with LLM APIs (Claude primary, Gemini fallback)"""

    def __init__(self):
        """Initialize LLM clients"""
        self.max_retries = 2

        # Determine which LLM to use
        self.use_gemini = False

        if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != "not_set":
            from anthropic import AsyncAnthropic
            self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.default_model = "claude-sonnet-4-5-20250929"
            logger.info("Using Claude (Anthropic) as LLM provider")
        elif settings.GEMINI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini = genai
            self.default_model = "gemini-1.5-pro-latest"  # Use stable model
            self.use_gemini = True
            logger.info("Using Gemini as LLM provider")
        else:
            raise ValueError("No LLM API key configured. Set ANTHROPIC_API_KEY or GEMINI_API_KEY")

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 1.0
    ) -> str:
        """
        Get a text completion from LLM (Claude or Gemini)

        Args:
            system_prompt: System instructions for the LLM
            user_message: User message/query
            model: Model to use (defaults to configured model)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Returns:
            LLM response text

        Raises:
            Exception: If LLM call fails
        """
        try:
            if self.use_gemini:
                return await self._complete_gemini(
                    system_prompt, user_message, model, max_tokens, temperature
                )
            else:
                return await self._complete_claude(
                    system_prompt, user_message, model, max_tokens, temperature
                )
        except Exception as e:
            logger.error(f"LLM completion failed: {str(e)}")
            raise

    async def _complete_claude(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Complete using Claude"""
        response = await self.anthropic.messages.create(
            model=model or self.default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )

        # Extract text from response
        text_content = ""
        for block in response.content:
            if hasattr(block, 'text'):
                text_content += block.text

        logger.info(f"Claude completion successful. Tokens: {response.usage.input_tokens + response.usage.output_tokens}")
        return text_content

    async def _complete_gemini(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Complete using Gemini"""
        import asyncio

        # Combine system prompt and user message for Gemini
        full_prompt = f"{system_prompt}\n\n{user_message}"

        # Create model instance
        model_instance = self.gemini.GenerativeModel(
            model_name=model or self.default_model,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
        )

        # Generate response (Gemini SDK is sync, so run in executor)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model_instance.generate_content(full_prompt)
        )

        logger.info(f"Gemini completion successful")
        return response.text

    async def complete_json(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        Get a JSON-structured completion from Claude

        Args:
            system_prompt: System instructions for the LLM
            user_message: User message/query
            model: Model to use (defaults to Sonnet 4.5)
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON response as dictionary

        Raises:
            Exception: If LLM call fails or JSON parsing fails
        """
        # Augment system prompt to ensure JSON output
        json_system_prompt = f"""{system_prompt}

CRITICAL: You MUST respond with valid JSON only. No markdown code blocks, no preamble, no explanation.
Just pure JSON that can be directly parsed."""

        json_user_message = f"""{user_message}

Remember: Respond with valid JSON only. No markdown formatting."""

        try:
            response_text = await self.complete(
                system_prompt=json_system_prompt,
                user_message=json_user_message,
                model=model,
                max_tokens=max_tokens,
                temperature=0.7  # Slightly lower temperature for structured output
            )

            # Clean up the response - remove markdown code blocks if present
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]  # Remove ```json
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]  # Remove ```
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]  # Remove trailing ```
            cleaned = cleaned.strip()

            # Parse JSON
            parsed = json.loads(cleaned)
            logger.info("LLM JSON completion successful")

            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {str(e)}")
            logger.error(f"Raw response: {response_text[:500]}")
            raise ValueError(f"LLM did not return valid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"LLM JSON completion failed: {str(e)}")
            raise

    async def coach_message(
        self,
        context: str,
        query: str,
        tone: str = "encouraging",
        max_tokens: int = 1024
    ) -> str:
        """
        Generate a coaching message with specific tone

        Args:
            context: Context about the learner's situation
            query: What to coach about
            tone: Coaching tone (encouraging, challenging, reflective)
            max_tokens: Maximum response length

        Returns:
            Coaching message text
        """
        tone_instructions = {
            "encouraging": "Be warm, supportive, and motivating. Celebrate progress and gently nudge forward.",
            "challenging": "Be direct and thought-provoking. Ask hard questions and push for deeper thinking.",
            "reflective": "Be contemplative and insightful. Help connect dots and see patterns.",
            "urgent": "Be firm but caring. Emphasize the importance of taking action now."
        }

        system_prompt = f"""You are an expert learning coach for the SPARK system - a personal knowledge management methodology.

Your coaching style: {tone_instructions.get(tone, tone_instructions['encouraging'])}

Key principles:
- Always reference specific details from the learner's context
- Focus on WHY something matters, not just WHAT to do
- Keep messages concise (2-3 sentences max)
- End with a clear, actionable next step
- Never be generic or templated - personalize every message"""

        user_message = f"""Context about the learner:
{context}

Coaching query:
{query}

Generate a coaching message."""

        return await self.complete(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=1.0
        )

    async def generate_quiz_questions(
        self,
        content: str,
        num_questions: int = 3,
        difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions from content

        Args:
            content: Content to generate questions from
            num_questions: Number of questions to generate
            difficulty: Question difficulty (easy, medium, hard)

        Returns:
            List of question dictionaries with question, type, and difficulty
        """
        system_prompt = """You are an expert educator creating quiz questions for spaced repetition learning.

Question types:
- recall: Test basic memory of facts and concepts
- application: Test ability to apply concepts to new situations
- connection: Test ability to relate concepts across domains

Create questions that:
- Are specific and unambiguous
- Have clear, verifiable answers
- Progress from concrete (recall) to abstract (connection)
- Match the requested difficulty level"""

        user_message = f"""Generate {num_questions} quiz questions from this content at {difficulty} difficulty.

Content:
{content[:3000]}  # Limit content length

Return as JSON array with format:
[
  {{
    "question": "question text",
    "type": "recall|application|connection",
    "difficulty": "easy|medium|hard",
    "expected_answer_hints": "guidance on what a good answer includes"
  }}
]"""

        return await self.complete_json(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=2048
        )

    async def score_quiz_answer(
        self,
        question: str,
        user_answer: str,
        content_context: str,
        expected_hints: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Score a quiz answer and provide feedback

        Args:
            question: The question asked
            user_answer: User's answer
            content_context: Original content for reference
            expected_hints: Hints about expected answer

        Returns:
            Dictionary with score (0-100), correct (bool), and feedback
        """
        system_prompt = """You are an expert educator evaluating quiz answers.

Scoring guidelines:
- 90-100: Excellent - accurate, complete, shows deep understanding
- 70-89: Good - mostly accurate, minor gaps
- 50-69: Partial - some understanding but significant gaps
- 30-49: Poor - major misunderstandings
- 0-29: Incorrect - fundamental misunderstanding

Provide constructive feedback that:
- Acknowledges what they got right
- Clarifies any misconceptions
- Suggests what to review"""

        user_message = f"""Score this quiz answer:

Question: {question}

User's answer: {user_answer}

Reference content:
{content_context[:1500]}

{f"Expected answer should include: {expected_hints}" if expected_hints else ""}

Return JSON:
{{
  "score": 0-100,
  "correct": true/false (true if score >= 70),
  "feedback": "constructive feedback message"
}}"""

        return await self.complete_json(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=1024
        )

    async def find_connections(
        self,
        note1_content: str,
        note2_content: str,
        note1_title: str,
        note2_title: str
    ) -> Optional[str]:
        """
        Find non-obvious connections between two notes

        Args:
            note1_content: Content of first note
            note2_content: Content of second note
            note1_title: Title of first note
            note2_title: Title of second note

        Returns:
            Connection insight or None if no meaningful connection
        """
        system_prompt = """You are an expert at finding non-obvious connections between ideas.

Look for:
- Underlying patterns or principles that apply to both
- Complementary perspectives on the same problem
- Cause-effect relationships
- Analogies and metaphors that bridge domains

Avoid:
- Surface-level keyword matches
- Generic platitudes
- Forced connections

Return a connection insight as a single compelling sentence, or return null if no meaningful connection exists."""

        user_message = f"""Find a non-obvious connection between these notes:

Note 1: {note1_title}
{note1_content[:1000]}

Note 2: {note2_title}
{note2_content[:1000]}

Return JSON:
{{
  "connection": "insight sentence or null"
}}"""

        try:
            result = await self.complete_json(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=512
            )
            return result.get("connection")
        except Exception as e:
            logger.error(f"Failed to find connections: {str(e)}")
            return None


# Global LLM client instance
llm_client = LLMClient()
