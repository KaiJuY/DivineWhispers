# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies including curl for uv installation
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv via pip first (more reliable in Docker)
RUN pip install --no-cache-dir uv

# Verify uv installation
RUN uv --version

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy project files
COPY Backend/pyproject.toml .
COPY Backend/requirements.txt .

# Install Python dependencies with uv (much faster than pip for the packages)
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY Backend/app ./app
COPY Backend/fortune_module ./fortune_module
COPY Backend/alembic.ini ./
COPY Backend/alembic ./alembic

# Copy source data for ChromaDB initialization (instead of pre-built DB)
COPY SourceCrawler/outputs ./SourceCrawler/outputs

# Copy ChromaDB initialization script
COPY Backend/init_chromadb_deployment.py ./

# Copy Asset directory (for deity images, logos)
COPY Asset ./Asset

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/uploads /app/chroma_db \
    && chown -R appuser:appuser /app

# Initialize ChromaDB from source data (run as root before switching user)
# Set SOURCE_DATA_PATH to match the copied location
ENV SOURCE_DATA_PATH=/app/SourceCrawler/outputs
RUN python init_chromadb_deployment.py \
    && chown -R appuser:appuser /app/chroma_db

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE $PORT

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]