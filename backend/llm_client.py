"""
LLM Client for SPARK Coach
Abstraction layer for Claude API (primary) and Gemini (fallback)
"""
import json
import logging
import asyncio
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
            from google import genai
            self.gemini = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.default_model = "gemini-2.5-flash"
            self.use_gemini = True
            logger.info("Using Gemini (google-genai SDK) as LLM provider")
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
        last_exc = None
        for attempt in range(self.max_retries + 1):
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
                last_exc = e
                if "429" in str(e) and attempt < self.max_retries:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"Rate limited (429), retrying in {wait}s… (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(wait)
                else:
                    break
        logger.error(f"LLM completion failed after {self.max_retries + 1} attempts: {str(last_exc)}")
        raise last_exc

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
        """Complete using Gemini (google-genai SDK)"""
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
            temperature=temperature,
        )

        response = await self.gemini.aio.models.generate_content(
            model=model or self.default_model,
            contents=user_message,
            config=config,
        )

        logger.info("Gemini completion successful")
        return response.text

    async def complete_json(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        Get a JSON-structured completion from LLM

        Args:
            system_prompt: System instructions for the LLM
            user_message: User message/query
            model: Model to use (defaults to configured model)
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON response as dictionary

        Raises:
            Exception: If LLM call fails or JSON parsing fails
        """
        try:
            if self.use_gemini:
                return await self._complete_json_gemini(
                    system_prompt, user_message, model, max_tokens
                )
            else:
                # Claude fallback with text parsing
                json_system_prompt = f"""{system_prompt}

CRITICAL: You MUST respond with valid JSON only. No markdown code blocks, no preamble, no explanation.
Just pure JSON that can be directly parsed."""

                json_user_message = f"""{user_message}

Remember: Respond with valid JSON only. No markdown formatting."""

                response_text = await self.complete(
                    system_prompt=json_system_prompt,
                    user_message=json_user_message,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.7
                )

                # Clean up the response - remove markdown code blocks if present
                cleaned = response_text.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                try:
                    parsed = json.loads(cleaned)
                    logger.info("LLM JSON completion successful")
                    return parsed
                except json.JSONDecodeError:
                    # Attempt to repair truncated JSON (e.g. missing closing brackets)
                    repaired = self._try_repair_json(cleaned)
                    if repaired is not None:
                        logger.warning("LLM JSON was truncated but repaired successfully")
                        return repaired
                    raise

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {str(e)}")
            raise ValueError(f"LLM did not return valid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"LLM JSON completion failed: {str(e)}")
            raise

    @staticmethod
    def _try_repair_json(text: str):
        """Attempt to repair truncated JSON by closing open brackets/strings"""
        # Common truncation: string cut mid-value, missing ] or }
        # Strategy: try progressively adding closing tokens
        candidates = [
            text,
            text + '"}]',       # truncated inside a string value in an array
            text + '"}',        # truncated inside a string value in an object
            text + '"]',        # truncated inside a string in an array
            text + ']',         # missing array close
            text + '}]',        # missing object + array close
            text + '}',         # missing object close
        ]
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return None

    @staticmethod
    def _sanitize_for_json_prompt(text: str) -> str:
        """Remove characters from vault content that confuse LLMs generating JSON.

        Strips control chars, excessive whitespace, and YAML frontmatter fences
        that can cause unescaped quotes/backslashes in the LLM JSON output.
        """
        import re
        # Strip YAML frontmatter block
        text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL)
        # Replace backslashes (common in file paths) with forward slashes
        text = text.replace('\\', '/')
        # Remove control characters except newlines
        text = re.sub(r'[\x00-\x09\x0b-\x0c\x0e-\x1f]', '', text)
        # Collapse excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Strip markdown code block fences that might confuse JSON output
        text = re.sub(r'```\w*\n?', '', text)
        return text.strip()

    async def _complete_json_gemini(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str],
        max_tokens: int
    ) -> Dict[str, Any]:
        """Complete with JSON output using Gemini's native JSON mode"""
        from google.genai import types

        last_raw = ""
        for attempt in range(2):
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                temperature=0.7 if attempt == 0 else 0.3,
                response_mime_type="application/json",
            )

            response = await self.gemini.aio.models.generate_content(
                model=model or self.default_model,
                contents=user_message,
                config=config,
            )

            last_raw = response.text or ""
            logger.debug(f"Gemini JSON raw response (attempt {attempt+1}): {last_raw[:200]}...")

            # Try direct parse
            try:
                parsed = json.loads(last_raw)
                logger.info("Gemini JSON completion successful")
                return parsed
            except json.JSONDecodeError:
                pass

            # Try repair
            repaired = self._try_repair_json(last_raw.strip())
            if repaired is not None:
                logger.warning(f"Gemini JSON repaired on attempt {attempt+1}")
                return repaired

            # Retry with stricter prompt on second attempt
            if attempt == 0:
                logger.warning(f"Gemini JSON invalid on attempt 1, retrying. Raw: {last_raw[:300]}")
                user_message = user_message + "\n\nIMPORTANT: Your previous response was invalid JSON. Return ONLY a valid JSON array, no other text. Keep strings short."

        # Both attempts failed
        raise json.JSONDecodeError(
            f"Gemini failed to produce valid JSON after 2 attempts",
            last_raw, 0
        )

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

Question types (use exactly one per question):
- "recall": Test memory of a specific fact, definition, or concept from the content
- "application": Present a realistic scenario and ask how to apply a concept
- "connection": Ask to relate two ideas from the content or connect to broader principles

Rules for GOOD questions:
- Reference specific terms, tools, or concepts from the content (not generic)
- Ask "why" or "how" — avoid yes/no or simple definition lookups
- Each question should test a DIFFERENT concept from the content
- Keep questions concise (1-2 sentences max)
- expected_answer_hints should list 2-3 key points a strong answer would cover

Rules to AVOID bad questions:
- Do NOT ask vague questions like "What is important about X?"
- Do NOT repeat the same concept across questions
- Do NOT ask questions answerable without reading the content

You MUST return valid JSON. Keep your response compact."""

        # Sanitize and limit content to prevent JSON issues
        trimmed_content = self._sanitize_for_json_prompt(content[:2000])

        user_message = f"""Generate exactly {num_questions} quiz questions from this content at {difficulty} difficulty.

Content:
{trimmed_content}

Return ONLY a JSON array (no extra text):
[{{"question":"...","type":"recall","difficulty":"{difficulty}","expected_answer_hints":"..."}}]"""

        result = await self.complete_json(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=1500
        )

        # Handle both array and wrapped responses
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "questions" in result:
            return result["questions"]
        return result

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
{self._sanitize_for_json_prompt(content_context[:1500])}

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
