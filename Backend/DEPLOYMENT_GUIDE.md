# Divine Whispers Backend Deployment Guide

This guide covers deployment options for the Divine Whispers fortune-telling backend system.

## Quick Start

### Development Environment

#### **Option 1: UV Local Development (Recommended for Development)**
1. **Install UV** (much faster than pip):
   ```bash
   # Unix/Linux/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows PowerShell
   irm https://astral.sh/uv/install.ps1 | iex
   ```

2. **Quick Setup**:
   ```bash
   git clone <repository>
   cd Backend
   
   # Run automated setup script
   chmod +x scripts/dev-setup.sh && ./scripts/dev-setup.sh  # Linux/macOS
   # OR scripts\dev-setup.bat  # Windows
   ```

3. **Manual Setup**:
   ```bash
   cp .env.example .env
   uv venv --python 3.11
   source .venv/bin/activate  # Linux/macOS (.venv\Scripts\activate on Windows)
   uv pip install -r requirements.txt
   uv pip install -e ".[dev]"
   uvicorn app.main:app --reload
   ```

#### **Option 2: Docker Development**  
1. **Clone and Setup**:
   ```bash
   git clone <repository>
   cd Backend
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start Development Environment** (now UV-optimized for faster builds):
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
   ```

3. **Run Database Migrations**:
   ```bash
   docker-compose exec app python -m alembic upgrade head
   ```

4. **Access Services**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - pgAdmin: http://localhost:5050

### Production Environment

1. **Setup Production Environment**:
   ```bash
   cp .env.production .env
   # Edit .env with secure production values
   ```

2. **Deploy with Production Settings**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   ```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │  FastAPI App    │    │  PostgreSQL DB  │
│   (Production)  │◄──►│                 │◄──►│                 │
│   Port 80/443   │    │   Port 8000     │    │   Port 5432     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  ChromaDB       │
                       │  (Embedded)     │
                       └─────────────────┘
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `SECRET_KEY` | - | JWT signing secret (CHANGE IN PRODUCTION!) |
| `OPENAI_API_KEY` | - | OpenAI API key for LLM services |
| `LLM_PROVIDER` | mock | LLM provider (openai/ollama/mock) |
| `DEBUG` | false | Enable debug mode |
| `FORTUNE_DRAW_COST` | 10 | Points cost for fortune drawing |
| `FORTUNE_INTERPRET_COST` | 15 | Points cost for interpretations |

### Database Configuration

The system uses PostgreSQL with the following tables:
- `users` - User accounts and authentication
- `wallets` - Point-based payment system
- `transactions` - Financial transaction records
- `jobs` - Async job processing queue
- `job_results` - Job execution results
- `audit_logs` - System activity logging
- `token_blacklist` - JWT token revocation
- `fortune_jobs` - Fortune-specific job data

## Deployment Options

### 1. Simple Docker Deployment (Recommended)

**Pros**: Easy setup, single-server deployment
**Best for**: Small to medium applications

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f app

# Scale workers (if needed)
docker-compose up -d --scale app=3
```

### 2. Cloud Platform Deployment

#### GCP Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/divine-whispers-backend
gcloud run deploy --image gcr.io/PROJECT-ID/divine-whispers-backend --platform managed
```

#### AWS ECS/Fargate
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker build -t divine-whispers-backend .
docker tag divine-whispers-backend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/divine-whispers-backend:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/divine-whispers-backend:latest
```

### 3. Kubernetes Deployment

For high-availability and scalability:

```yaml
# See k8s-manifests/ directory for complete Kubernetes configuration
```

## Performance Optimization

### Database Optimization
- Connection pooling is configured in SQLAlchemy
- Database indexes on frequently queried columns
- Async operations throughout the application

### Caching Strategy
- In-memory caching for frequently accessed poems
- TTL-based cache expiration
- No external Redis required (simplified architecture)

### Background Jobs
- Async job processing with configurable concurrency
- Database-based job queue (no external message broker)
- Automatic job cleanup and retry logic

## Monitoring and Logging

### Health Checks
- Application health: `GET /health`
- Database health: `GET /health/db`
- ChromaDB health: `GET /health/chroma`

### Logging
```bash
# View application logs
docker-compose logs -f app

# View specific log levels
docker-compose logs app | grep ERROR
```

### Metrics
- Built-in FastAPI metrics at `/metrics` (if enabled)
- Custom business metrics for fortune services
- Financial transaction monitoring

## Security

### Authentication
- JWT tokens with refresh token rotation
- Bcrypt password hashing
- Role-based access control (USER/MODERATOR/ADMIN)

### Data Protection
- HTTPS enforced in production
- Database connection encryption
- Secrets managed via environment variables
- Input validation and sanitization

### Financial Security
- Atomic transaction processing
- Double-spending prevention
- Complete audit trails
- Point balance verification

## Backup and Recovery

### Database Backup
```bash
# Backup database
docker-compose exec db pg_dump -U postgres divine_whispers > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U postgres divine_whispers
```

### ChromaDB Backup
```bash
# Backup ChromaDB data
docker-compose exec app tar -czf /app/chroma_backup.tar.gz -C /app chroma_db/
docker cp $(docker-compose ps -q app):/app/chroma_backup.tar.gz ./
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check database status
   docker-compose ps db
   docker-compose logs db
   
   # Reset database
   docker-compose down -v
   docker-compose up db
   ```

2. **ChromaDB Initialization Failed**
   ```bash
   # Check ChromaDB path and permissions
   docker-compose exec app ls -la /app/chroma_db/
   
   # Reinitialize ChromaDB
   docker-compose exec app python -c "from app.services.poem_service import poem_service; import asyncio; asyncio.run(poem_service.initialize_system())"
   ```

3. **Job Processing Stopped**
   ```bash
   # Check job processor status
   docker-compose logs app | grep "job processor"
   
   # Restart application
   docker-compose restart app
   ```

### Performance Issues
- Monitor resource usage: `docker stats`
- Check database performance: Connect to pgAdmin
- Review application logs for slow queries
- Adjust worker concurrency in production settings

### Memory Issues
- Configure memory limits in docker-compose.yml
- Monitor ChromaDB memory usage
- Implement result cleanup for old job data

## Maintenance

### Regular Tasks

1. **Database Maintenance**
   ```bash
   # Run weekly
   docker-compose exec db psql -U postgres -d divine_whispers -c "VACUUM ANALYZE;"
   ```

2. **Log Rotation**
   ```bash
   # Configure log rotation for production
   # See logrotate configuration in production setup
   ```

3. **Job Cleanup**
   ```bash
   # Cleanup old jobs (runs automatically)
   docker-compose exec app python -c "from app.services.job_processor import job_processor; import asyncio; asyncio.run(job_processor.cleanup_expired_jobs())"
   ```

## Support

For deployment issues:
1. Check the logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose config`
3. Test database connection: `docker-compose exec app python -c "from app.core.database import DatabaseManager; import asyncio; print(asyncio.run(DatabaseManager.health_check()))"`
4. Validate fortune system: `GET /health/chroma`

The system is designed to be resilient and self-healing, with automatic retry logic and graceful degradation when services are unavailable.