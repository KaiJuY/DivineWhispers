"""
Database configuration and session management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool if settings.DEBUG else None,
    pool_pre_ping=True,
)

# Create async session maker
async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

# Import Base from models to ensure consistency
from app.models.base import Base


async def get_database_session() -> AsyncSession:
    """
    Dependency function to get database session
    Used with FastAPI's Depends()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_async_session():
    """
    Get async session context manager for background tasks
    Returns the session maker directly for use with 'async with'
    """
    return async_session_maker()


async def create_tables():
    """Create all database tables"""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered with SQLAlchemy metadata
            from app.models.user import User
            from app.models.wallet import Wallet
            from app.models.transaction import Transaction
            from app.models.job import Job
            from app.models.job_result import JobResult
            from app.models.audit_log import AuditLog
            from app.models.token_blacklist import TokenBlacklist
            from app.models.fortune_job import FortuneJob
            from app.models.chat_message import ChatSession, ChatMessage
            
            # Now create all tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


async def drop_tables():
    """Drop all database tables (use with caution)"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {str(e)}")
        raise


class DatabaseManager:
    """Database manager utility class"""
    
    @staticmethod
    async def health_check() -> bool:
        """Check database connectivity"""
        try:
            async with async_session_maker() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    @staticmethod
    async def get_version() -> str:
        """Get database version"""
        try:
            async with async_session_maker() as session:
                result = await session.execute("SELECT version()")
                version = result.scalar()
                return version
        except Exception as e:
            logger.error(f"Failed to get database version: {str(e)}")
            return "Unknown"