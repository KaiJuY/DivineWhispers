# Divine Whispers FastAPI Backend

This is the FastAPI backend for the Divine Whispers fortune-telling application.

## Project Structure

```
Backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Environment settings
│   │   ├── security.py        # JWT and password utilities
│   │   └── database.py        # Async SQLAlchemy setup
│   ├── models/                # SQLAlchemy models (to be created)
│   │   └── __init__.py
│   ├── schemas/               # Pydantic models for API
│   │   └── __init__.py
│   ├── api/                   # API route handlers
│   │   ├── __init__.py
│   │   └── v1/
│   │       └── __init__.py
│   ├── services/              # Business logic
│   │   └── __init__.py
│   └── utils/
│       ├── __init__.py
│       ├── deps.py            # Dependency injection
│       └── websocket.py       # WebSocket manager
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── alembic.ini
```

## Quick Start

### Using Docker Compose (Recommended)

1. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

2. Start all services:
```bash
docker-compose up -d
```

3. Check logs:
```bash
docker-compose logs -f app
```

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment:
```bash
cp .env.example .env
# Edit .env with your database and API keys
```

3. Start PostgreSQL and Redis (or use Docker):
```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password -e POSTGRES_DB=divine_whispers postgres:15-alpine
docker run -d -p 6379:6379 redis:7-alpine
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the application:
```bash
python -m uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

## WebSocket Connection

Connect to WebSocket for real-time notifications:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{user_id}');
```

## Key Features

- **Async FastAPI** with PostgreSQL and SQLAlchemy 2.0
- **JWT Authentication** with refresh tokens
- **WebSocket Support** for real-time notifications
- **Point-based Payment System** for fortune readings
- **ChromaDB Integration** for vector-based fortune poem retrieval
- **Rate Limiting** and security best practices
- **Docker Support** with multi-stage builds
- **Comprehensive Error Handling** and logging

## Environment Variables

Key environment variables (see .env.example for full list):

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/divine_whispers

# Security
SECRET_KEY=your-super-secret-key
OPENAI_API_KEY=your-openai-api-key

# Application
DEBUG=false
ALLOWED_HOSTS=http://localhost:3000
```

## Development

### Adding New Models

1. Create model in `app/models/`
2. Import in `app/models/__init__.py`
3. Generate migration: `alembic revision --autogenerate -m "description"`
4. Apply migration: `alembic upgrade head`

### Adding New API Routes

1. Create router in `app/api/v1/`
2. Include router in `app/main.py`

### Testing

```bash
pytest
```

## Production Deployment

1. Set `DEBUG=false` in environment
2. Use strong `SECRET_KEY`
3. Configure proper `ALLOWED_HOSTS`
4. Set up SSL/TLS termination
5. Use production database
6. Configure logging and monitoring

## Integration with Existing ChromaDB

The FastAPI backend integrates with your existing `PoemChromaSystem.py` and ChromaDB setup. The fortune reading service will use the vector database for retrieving relevant poems.

## Next Steps

1. Create database models in `app/models/`
2. Set up API endpoints in `app/api/v1/`
3. Implement business logic in `app/services/`
4. Add comprehensive testing
5. Set up CI/CD pipeline