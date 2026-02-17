"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# Quiz Schemas

class QuizStartRequest(BaseModel):
    """Request to start a quiz session"""
    resource_path: str = Field(..., description="Path to the resource to quiz on")
    num_questions: Optional[int] = Field(3, ge=1, le=10, description="Number of questions to generate")
    difficulty: Optional[str] = Field("medium", description="Question difficulty: easy, medium, hard")


class Question(BaseModel):
    """A single quiz question"""
    index: int = Field(..., description="Question number (1-indexed)")
    type: str = Field(..., description="Question type: recall, application, connection")
    question: str = Field(..., description="The question text")
    difficulty: str = Field(..., description="Difficulty level")


class QuizStartResponse(BaseModel):
    """Response when starting a quiz"""
    status: str = "success"
    session_id: str = Field(..., description="Unique quiz session ID")
    resource: str = Field(..., description="Resource title")
    resource_path: str = Field(..., description="Resource path")
    total_questions: int = Field(..., description="Total number of questions")
    current_question: Question = Field(..., description="First question")


class QuizAnswerRequest(BaseModel):
    """Request to submit an answer"""
    session_id: str = Field(..., description="Quiz session ID")
    question_index: int = Field(..., description="Question number being answered")
    answer: str = Field(..., description="User's answer to the question")


class QuizAnswerResponse(BaseModel):
    """Response after submitting an answer"""
    status: str = "success"
    correct: bool = Field(..., description="Whether the answer was correct")
    score: int = Field(..., description="Score for this answer (0-100)")
    feedback: str = Field(..., description="Feedback on the answer")
    next_question: Optional[Question] = Field(None, description="Next question if quiz continues")
    session_progress: dict = Field(..., description="Progress through the quiz")
    quiz_complete: bool = Field(False, description="Whether the quiz is finished")
    final_score: Optional[int] = Field(None, description="Final quiz score if complete")
    retention_updated: bool = Field(False, description="Whether vault retention score was updated")


# Learning Path Schemas

class LearningPathSummary(BaseModel):
    """Summary of a learning path"""
    name: str
    current_milestone: Optional[str]
    overall_progress: int
    weekly_hours: dict
    resource_count: int


# Stats Schemas

class StatsResponse(BaseModel):
    """Dashboard statistics"""
    period: str
    streaks: dict
    learning_hours: dict
    retention: dict
    resources: dict
    quizzes: dict


# Voice Input Schemas

class VoiceProcessRequest(BaseModel):
    """Request to process voice transcription"""
    transcription: str = Field(..., description="Transcribed text from speech-to-text")


class VoiceProcessResponse(BaseModel):
    """Response after processing voice input"""
    status: str = "success"
    intent: str = Field(..., description="Detected intent: new_seed, question, reflection, quiz_answer")
    action_taken: str = Field(..., description="Action performed")
    note_path: Optional[str] = Field(None, description="Path to created/modified note")
    message: str = Field(..., description="Human-readable message")
    suggested_actions: List[dict] = Field(default_factory=list, description="Suggested follow-up actions")
