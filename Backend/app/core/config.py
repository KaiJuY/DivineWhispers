"""
Application configuration using Pydantic settings - Simplified Version
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings - simplified to avoid startup issues"""
    
    # Basic app settings
    APP_NAME: str = "Divine Whispers"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS settings - simplified
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database settings - use environment variables directly
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@db:5432/divine_whispers"
    
    # Security settings
    SECRET_KEY: str = "your-super-secret-key-change-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password validation settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = False
    PASSWORD_REQUIRE_LOWERCASE: bool = False
    PASSWORD_REQUIRE_NUMBERS: bool = False
    PASSWORD_REQUIRE_SYMBOLS: bool = False
    
    # Payment system
    DEFAULT_USER_POINTS: int = 100
    FORTUNE_DRAW_COST: int = 10
    FORTUNE_INTERPRET_COST: int = 15
    
    # LLM settings
    OPENAI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "mock"  # openai, ollama, mock
    
    # ChromaDB settings - adjusted for local development
    CHROMA_DB_PATH: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "fortune_knowledge"
    
    # Fortune Service settings
    FORTUNE_CACHE_TIMEOUT_SECONDS: int = 300
    FORTUNE_JOB_TIMEOUT_SECONDS: int = 300
    
    # Use simple configuration
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


# Global settings instance
settings = get_settings()