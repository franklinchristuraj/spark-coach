"""
Configuration management for SPARK Coach API
Loads environment variables and provides settings object
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    TTS_API_KEY: str = os.getenv("TTS_API_KEY", "")

    # MCP Server Configuration
    MCP_SERVER_URL: str = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
    MCP_API_KEY: str = os.getenv("MCP_API_KEY", "")

    # SPARK Coach API Key (for client authentication)
    API_KEY: str = os.getenv("SPARK_COACH_API_KEY", "dev_test_key_12345")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/spark_coach.db")

    # FCM Configuration
    FCM_CREDENTIALS_PATH: str = os.getenv("FCM_CREDENTIALS_PATH", "/secrets/fcm.json")

    # App Configuration
    APP_NAME: str = "SPARK Coach API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()
