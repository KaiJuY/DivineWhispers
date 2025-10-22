#!/usr/bin/env bash
# Build script for Render.com deployment
# This script runs during the build phase on Render

set -o errexit  # Exit on error
set -o pipefail # Exit on pipe failure
set -o nounset  # Exit on undefined variable

echo "🚀 Starting Divine Whispers build process..."

# 1. Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 2. Run database migrations
echo "🗄️  Running database migrations..."
# Render provides DATABASE_URL automatically for PostgreSQL
if [ -n "${DATABASE_URL:-}" ]; then
    echo "✅ DATABASE_URL detected, running Alembic migrations..."
    alembic upgrade head
else
    echo "⚠️  WARNING: No DATABASE_URL found, skipping migrations"
fi

# 3. Verify ChromaDB data exists
echo "🔍 Verifying ChromaDB data..."
if [ -d "chroma_db" ]; then
    echo "✅ ChromaDB directory found"
    ls -lh chroma_db/ || true
else
    echo "⚠️  WARNING: ChromaDB directory not found!"
    echo "   The RAG system may not work without fortune poem data."
fi

# 4. Verify fortune_module exists
echo "🔍 Verifying fortune_module..."
if [ -d "fortune_module" ]; then
    echo "✅ fortune_module directory found"
else
    echo "❌ ERROR: fortune_module directory not found!"
    exit 1
fi

# 5. Verify Asset directory exists
echo "🔍 Verifying Asset directory..."
if [ -d "Asset" ]; then
    echo "✅ Asset directory found"
else
    echo "⚠️  WARNING: Asset directory not found"
fi

echo "✅ Build completed successfully!"
echo "🌟 Divine Whispers is ready for deployment"
