"""
Database models for SPARK Coach
SQLite models for quiz sessions, answers, and learning logs
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class QuizSession(Base):
    """Tracks quiz sessions for resources"""
    __tablename__ = "quiz_sessions"

    id = Column(String, primary_key=True)  # quiz_YYYYMMDD_NNN format
    resource_path = Column(String, nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, default=0)
    score = Column(Float, default=0.0)  # Final score 0-100
    status = Column(String, default="in_progress")  # in_progress, completed, abandoned

    def __repr__(self):
        return f"<QuizSession {self.id} for {self.resource_path}: {self.score}%>"


class QuizAnswer(Base):
    """Individual answers within quiz sessions"""
    __tablename__ = "quiz_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    question_index = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String)  # recall, application, connection
    difficulty = Column(String)  # easy, medium, hard
    user_answer = Column(Text)
    is_correct = Column(Boolean)
    score = Column(Float)  # Score for this individual answer (0-100)
    feedback = Column(Text)  # LLM feedback on the answer
    answered_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<QuizAnswer {self.id}: Q{self.question_index} {'✓' if self.is_correct else '✗'}>"


class LearningLog(Base):
    """Tracks all learning activities for analytics"""
    __tablename__ = "learning_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_path = Column(String, index=True)
    action = Column(String, nullable=False)  # quiz, review, voice_capture, chat
    duration_minutes = Column(Float, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    meta_data = Column(Text)  # JSON string for flexible data (renamed from metadata)
    score = Column(Float)  # Optional score for scored activities

    def __repr__(self):
        return f"<LearningLog {self.action} on {self.resource_path} at {self.timestamp}>"


class NudgeHistory(Base):
    """Tracks nudges sent to user for abandonment prevention"""
    __tablename__ = "nudge_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_path = Column(String, index=True)
    nudge_type = Column(String, nullable=False)  # abandonment, review_due, milestone
    message = Column(Text, nullable=False)
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<NudgeHistory {self.nudge_type} for {self.resource_path}>"


# Database engine and session management
engine = None
SessionLocal = None


def init_db():
    """Initialize database and create tables"""
    global engine, SessionLocal

    try:
        # Parse database URL
        db_url = settings.DATABASE_URL
        if db_url.startswith("sqlite:///"):
            # Make sure data directory exists
            import os
            db_path = db_url.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

        # Create engine
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
        )

        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create all tables
        Base.metadata.create_all(bind=engine)

        logger.info(f"✓ Database initialized: {db_url}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False


def get_db():
    """Get database session (dependency injection for FastAPI)"""
    if SessionLocal is None:
        init_db()

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_sync():
    """Get database session synchronously"""
    if SessionLocal is None:
        init_db()

    return SessionLocal()
