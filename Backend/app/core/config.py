"""
Application configuration using Pydantic settings - Simplified Version
"""

from functools import lru_cache
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings - simplified to avoid startup issues"""

    # Basic app settings
    APP_NAME: str = "Divine Whispers"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS settings - restrict to specific domains (override in .env)
    ALLOWED_HOSTS: Union[str, List[str]] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator('ALLOWED_HOSTS', mode='before')
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Handle ALLOWED_HOSTS as either comma-separated string or list"""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [host.strip() for host in v.split(',') if host.strip()]
        return v

    # Database settings - MUST use environment variables
    # Render provides DATABASE_URL as postgresql://, but we need postgresql+asyncpg:// for async
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./divine_whispers.db")

    @field_validator('DATABASE_URL', mode='before')
    @classmethod
    def convert_postgres_url_to_asyncpg(cls, v):
        """Convert postgresql:// to postgresql+asyncpg:// for async SQLAlchemy"""
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Security settings - MUST override SECRET_KEY in production
    SECRET_KEY: str = os.getenv("SECRET_KEY", "INSECURE_DEFAULT_DO_NOT_USE_IN_PRODUCTION")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 3

    # Password validation settings - ENABLED for security
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SYMBOLS: bool = True
    
    # Payment system
    DEFAULT_USER_POINTS: int = 100
    FORTUNE_DRAW_COST: int = 10
    FORTUNE_INTERPRET_COST: int = 15
    
    # LLM settings
    OPENAI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "ollama"  # openai, ollama, mock
    LLM_MODEL: str = "gpt-oss:20b"  # Default Ollama model
    OLLAMA_BASE_URL: Optional[str] = "http://localhost:11434"
    
    # ChromaDB settings - use environment variables
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "fortune_knowledge")
    
    # Fortune Service settings
    FORTUNE_CACHE_TIMEOUT_SECONDS: int = 300
    FORTUNE_JOB_TIMEOUT_SECONDS: int = 300
    FORTUNE_MAX_SEARCH_RESULTS: int = 10

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    # Email/SMTP settings (Zoho)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.zoho.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", os.getenv("SMTP_USER", ""))
    FROM_NAME: str = os.getenv("FROM_NAME", "Divine Whispers")
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", os.getenv("SMTP_USER", ""))

    # Frontend URL for email links
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
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
