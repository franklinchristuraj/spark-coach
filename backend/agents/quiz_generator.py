"""
Quiz Generator Agent
Generates quiz questions from resource content and scores answers
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

from agents.base_agent import BaseAgent
from models.database import QuizSession, QuizAnswer, LearningLog, get_db_sync

logger = logging.getLogger(__name__)


class QuizGeneratorAgent(BaseAgent):
    """
    Generates quizzes from resource content and manages quiz sessions
    """

    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Main entry point - not used directly, use specific methods instead
        """
        action = kwargs.get("action")
        if action == "start":
            return await self.start_quiz(**kwargs)
        elif action == "answer":
            return await self.score_answer(**kwargs)
        else:
            raise ValueError(f"Unknown action: {action}")

    async def start_quiz(
        self,
        resource_path: str,
        num_questions: int = 3,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Start a new quiz session for a resource

        Args:
            resource_path: Path to the resource
            num_questions: Number of questions to generate
            difficulty: Difficulty level

        Returns:
            Dictionary with session ID and first question
        """
        logger.info(f"Starting quiz for {resource_path}")

        try:
            # Read the resource note
            note = await self.mcp.read_note(resource_path)
            content = note.get("content", "")
            frontmatter = note.get("frontmatter", {})
            title = frontmatter.get("title", resource_path.split("/")[-1].replace(".md", ""))

            if not content:
                raise ValueError("Resource has no content to generate questions from")

            # Check if there are pre-generated questions in frontmatter
            existing_questions = frontmatter.get("key_questions", [])

            if existing_questions and len(existing_questions) >= num_questions:
                logger.info(f"Using {num_questions} pre-generated questions from frontmatter")
                questions = existing_questions[:num_questions]
                # Convert to standard format if needed
                questions = self._normalize_questions(questions)
            else:
                # Generate new questions using LLM
                logger.info(f"Generating {num_questions} new questions via LLM")
                questions = await self.llm.generate_quiz_questions(
                    content=content,
                    num_questions=num_questions,
                    difficulty=difficulty
                )

            if not questions:
                raise ValueError("Failed to generate quiz questions")

            # Create quiz session
            session_id = self._generate_session_id()
            db = get_db_sync()

            try:
                session = QuizSession(
                    id=session_id,
                    resource_path=resource_path,
                    started_at=datetime.utcnow(),
                    total_questions=len(questions),
                    status="in_progress"
                )
                db.add(session)
                db.commit()

                # Store questions as metadata for later retrieval
                self._store_session_questions(session_id, questions)

                logger.info(f"Quiz session {session_id} created with {len(questions)} questions")

                # Return first question
                first_question = questions[0]
                return {
                    "session_id": session_id,
                    "resource": title,
                    "resource_path": resource_path,
                    "total_questions": len(questions),
                    "current_question": {
                        "index": 1,
                        "type": first_question.get("type", "recall"),
                        "question": first_question.get("question"),
                        "difficulty": first_question.get("difficulty", difficulty)
                    }
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to start quiz: {str(e)}")
            raise

    async def score_answer(
        self,
        session_id: str,
        question_index: int,
        user_answer: str
    ) -> Dict[str, Any]:
        """
        Score a quiz answer and return feedback

        Args:
            session_id: Quiz session ID
            question_index: Question number (1-indexed)
            user_answer: User's answer

        Returns:
            Dictionary with score, feedback, and next question
        """
        logger.info(f"Scoring answer for session {session_id}, question {question_index}")

        db = get_db_sync()
        try:
            # Get session
            session = db.query(QuizSession).filter_by(id=session_id).first()
            if not session:
                raise ValueError(f"Quiz session {session_id} not found")

            if session.status == "completed":
                raise ValueError("Quiz session already completed")

            # Get questions for this session
            questions = self._get_session_questions(session_id)
            if question_index < 1 or question_index > len(questions):
                raise ValueError(f"Invalid question index: {question_index}")

            current_question = questions[question_index - 1]

            # Read resource content for context
            note = await self.mcp.read_note(session.resource_path)
            content = note.get("content", "")

            # Score the answer using LLM
            result = await self.llm.score_quiz_answer(
                question=current_question.get("question"),
                user_answer=user_answer,
                content_context=content,
                expected_hints=current_question.get("expected_answer_hints")
            )

            score = result.get("score", 0)
            is_correct = result.get("correct", False)
            feedback = result.get("feedback", "")

            # Store answer
            answer = QuizAnswer(
                session_id=session_id,
                question_index=question_index,
                question_text=current_question.get("question"),
                question_type=current_question.get("type"),
                difficulty=current_question.get("difficulty"),
                user_answer=user_answer,
                is_correct=is_correct,
                score=score,
                feedback=feedback
            )
            db.add(answer)
            db.flush()  # Flush to make answer visible to count query

            # Update session stats
            if is_correct:
                session.correct_answers += 1

            # Check if quiz is complete
            answered_count = db.query(QuizAnswer).filter_by(session_id=session_id).count()
            quiz_complete = answered_count >= session.total_questions

            response = {
                "correct": is_correct,
                "score": int(score),
                "feedback": feedback,
                "session_progress": {
                    "answered": answered_count,
                    "remaining": session.total_questions - answered_count,
                    "correct_so_far": session.correct_answers
                },
                "quiz_complete": quiz_complete
            }

            if quiz_complete:
                # Calculate final score
                final_score = await self._finalize_quiz(session_id, db)
                response["final_score"] = final_score

                # Update retention score in vault
                retention_updated = await self._update_vault_retention(
                    session.resource_path,
                    final_score,
                    db
                )
                response["retention_updated"] = retention_updated

            else:
                # Return next question
                next_q = questions[question_index]  # question_index is 0-indexed for next
                response["next_question"] = {
                    "index": question_index + 1,
                    "type": next_q.get("type", "recall"),
                    "question": next_q.get("question"),
                    "difficulty": next_q.get("difficulty", "medium")
                }

            db.commit()
            return response

        except Exception as e:
            logger.error(f"Failed to score answer: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()

    async def _finalize_quiz(self, session_id: str, db) -> int:
        """Calculate final quiz score and update session"""
        session = db.query(QuizSession).filter_by(id=session_id).first()

        # Get all answers
        answers = db.query(QuizAnswer).filter_by(session_id=session_id).all()

        # Calculate average score
        if answers:
            total_score = sum(a.score for a in answers)
            final_score = int(total_score / len(answers))
        else:
            final_score = 0

        # Update session
        session.score = final_score
        session.completed_at = datetime.utcnow()
        session.status = "completed"

        # Log learning activity
        duration = (session.completed_at - session.started_at).total_seconds() / 60
        log = LearningLog(
            resource_path=session.resource_path,
            action="quiz",
            duration_minutes=duration,
            score=final_score,
            meta_data=json.dumps({"session_id": session_id, "questions": session.total_questions})
        )
        db.add(log)

        logger.info(f"Quiz {session_id} finalized with score {final_score}")

        return final_score

    async def _update_vault_retention(
        self,
        resource_path: str,
        quiz_score: int,
        db
    ) -> bool:
        """Update retention score and next_review date in vault"""
        try:
            # Read current note
            note = await self.mcp.read_note(resource_path)
            frontmatter = note.get("frontmatter", {})

            # Calculate new retention score (weighted average with previous)
            old_retention = int(frontmatter.get("retention_score", 50))
            review_count = int(frontmatter.get("review_count", 0))

            # Weight: 70% new score, 30% old score
            new_retention = int(quiz_score * 0.7 + old_retention * 0.3)

            # Calculate next review date using spaced repetition
            today = datetime.now().strftime("%Y-%m-%d")
            next_review = self.calculate_next_review_date(new_retention, today)

            # Update frontmatter
            updates = {
                "retention_score": new_retention,
                "last_reviewed": today,
                "next_review": next_review,
                "review_count": review_count + 1
            }

            success = await self.update_resource_metadata(resource_path, updates)

            if success:
                logger.info(f"Updated {resource_path}: retention={new_retention}, next_review={next_review}")

            return success

        except Exception as e:
            logger.error(f"Failed to update vault retention: {str(e)}")
            return False

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"quiz_{timestamp}"

    def _store_session_questions(self, session_id: str, questions: List[Dict]):
        """Store questions for retrieval during quiz"""
        # Simple in-memory cache (could use Redis in production)
        if not hasattr(self, '_question_cache'):
            self._question_cache = {}
        self._question_cache[session_id] = questions

    def _get_session_questions(self, session_id: str) -> List[Dict]:
        """Retrieve stored questions for session"""
        if not hasattr(self, '_question_cache'):
            self._question_cache = {}
        return self._question_cache.get(session_id, [])

    def _normalize_questions(self, questions: List) -> List[Dict]:
        """Normalize question format from frontmatter"""
        normalized = []
        for q in questions:
            if isinstance(q, str):
                # Simple string question
                normalized.append({
                    "question": q,
                    "type": "recall",
                    "difficulty": "medium"
                })
            elif isinstance(q, dict):
                # Already in dict format
                normalized.append(q)
        return normalized


# Global agent instance
quiz_generator_agent = QuizGeneratorAgent()
