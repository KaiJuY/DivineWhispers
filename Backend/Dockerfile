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
COPY pyproject.toml .
COPY requirements.txt .

# Install Python dependencies with uv (much faster than pip for the packages)
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY ./app ./app
COPY alembic.ini ./

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/uploads \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE $PORT

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]