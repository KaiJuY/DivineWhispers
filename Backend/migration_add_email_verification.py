"""
Database migration to add email_verification_tokens table
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine


async def create_email_verification_tokens_table():
    """Create the email_verification_tokens table"""

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS email_verification_tokens (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        email VARCHAR(255) NOT NULL,
        token VARCHAR(255) NOT NULL UNIQUE,
        is_used BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user_id
        ON email_verification_tokens(user_id);
    CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_email
        ON email_verification_tokens(email);
    CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_token
        ON email_verification_tokens(token);
    """

    async with engine.begin() as conn:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in create_table_sql.split(';') if s.strip()]
        for statement in statements:
            await conn.execute(text(statement))
        print("[OK] email_verification_tokens table and indexes created successfully")


async def main():
    """Run migration"""
    print("Creating email_verification_tokens table...")
    await create_email_verification_tokens_table()
    print("Migration completed successfully!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
