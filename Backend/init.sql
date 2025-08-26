-- PostgreSQL initialization script for Divine Whispers
-- This script will be executed when the PostgreSQL container starts

-- Create database if it doesn't exist (redundant but safe)
-- The database is created by POSTGRES_DB environment variable

-- Ensure UTF-8 encoding and proper collation
-- This is set by POSTGRES_INITDB_ARGS in docker-compose.yml

-- Create any additional extensions if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- The tables will be created by Alembic migrations
-- No table creation needed here

-- Log the initialization
\echo 'Divine Whispers PostgreSQL database initialization completed';