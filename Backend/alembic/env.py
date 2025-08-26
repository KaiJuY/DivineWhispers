"""
Alembic environment configuration for async SQLAlchemy
"""
import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Add the parent directory to sys.path so we can import our app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import our application config and models
from app.core.config import settings
from app.models import Base  # This imports all models via __init__.py

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata from our Base class
# This includes all models that inherit from Base
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from environment variables"""
    # For development, provide a fallback URL that works for migrations
    url = getattr(settings, 'DATABASE_URL', None)
    if url is None:
        # Fallback URL for offline migrations - doesn't need to be a real database
        url = "postgresql+asyncpg://postgres:password@localhost:5432/divine_whispers"
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations"""
    try:
        connectable = create_async_engine(
            get_url(),
            poolclass=pool.NullPool,
        )

        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await connectable.dispose()
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Falling back to offline mode for migration generation...")
        run_migrations_offline()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    try:
        asyncio.run(run_async_migrations())
    except Exception as e:
        print(f"Online migration failed: {e}")
        print("Running in offline mode...")
        run_migrations_offline()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()