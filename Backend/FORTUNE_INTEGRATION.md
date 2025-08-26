# Divine Whispers Fortune Integration

This document describes the integration of the existing ChromaDB-based fortune poem system with the new FastAPI backend.

## Overview

The integration provides a complete fortune-telling service with:
- **Authenticated API endpoints** with point-based payment system
- **Async job processing** for AI-powered interpretations
- **WebSocket notifications** for real-time updates
- **Admin management tools** for system monitoring
- **Vector search capabilities** using ChromaDB

## Architecture

### Core Components

1. **Fortune Service (`services/poem_service.py`)**
   - Wraps the existing fortune module system
   - Provides async interface to ChromaDB operations
   - Handles caching and connection management
   - Integrates with LLM providers (OpenAI, Ollama, Mock)

2. **Job Processor (`services/job_processor.py`)**
   - Async background job processing system
   - Manages fortune drawing and interpretation tasks
   - Handles job lifecycle and error recovery
   - Provides WebSocket notifications

3. **API Endpoints (`api/v1/fortune.py`)**
   - User endpoints for fortune services
   - Admin endpoints for system management
   - Point-based payment integration
   - Job status tracking

4. **Data Models**
   - `FortuneJob` - Simplified job model for async tasks
   - Enhanced existing models with fortune-specific enums
   - Pydantic schemas for API requests/responses

## API Endpoints

### User Endpoints

#### Fortune Drawing
```http
POST /api/v1/fortune/draw
Authorization: Bearer <token>
Content-Type: application/json

{
  "question": "What does my future hold?",
  "temple_preference": "Asakusa",
  "language": "zh"
}
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "estimated_completion_time": 30,
  "points_charged": 10,
  "message": "Your fortune is being prepared..."
}
```

#### Specific Poem Interpretation
```http
POST /api/v1/fortune/interpret/{poem_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "question": "How does this poem relate to my career?",
  "language": "en",
  "additional_context": "I'm considering a job change"
}
```

#### Job Status & Results
```http
GET /api/v1/fortune/jobs/{job_id}/status
GET /api/v1/fortune/jobs/{job_id}/result
Authorization: Bearer <token>
```

#### Free Browsing Endpoints
```http
GET /api/v1/fortune/poems/{poem_id}           # Poem details
GET /api/v1/fortune/search?q=love&limit=10    # Search poems
GET /api/v1/fortune/categories                # Fortune categories
GET /api/v1/fortune/temples/{name}/stats      # Temple statistics
GET /api/v1/fortune/history                   # User's consultation history
```

### Admin Endpoints

```http
GET /api/v1/fortune/admin/stats               # System statistics
POST /api/v1/fortune/admin/refresh            # Refresh ChromaDB
GET /api/v1/fortune/admin/health              # System health check
```

## Configuration

Add to `.env`:

```bash
# ChromaDB settings
CHROMA_DB_PATH=../chroma_db
CHROMA_COLLECTION_NAME=fortune_poems

# Fortune service settings
FORTUNE_DRAW_COST_POINTS=10
FORTUNE_INTERPRET_COST_POINTS=15
FORTUNE_SEARCH_RATE_LIMIT=30
FORTUNE_MAX_SEARCH_RESULTS=10
FORTUNE_CACHE_TIMEOUT_SECONDS=300
SOURCE_CRAWLER_PATH=../SourceCrawler/outputs
FORTUNE_JOB_TIMEOUT_SECONDS=300

# LLM settings
OPENAI_API_KEY=your_openai_key
LLM_MODEL=gpt-3.5-turbo
LLM_MAX_TOKENS=1000
LLM_TEMPERATURE=0.7
```

## Database Migration

Run the migration to add the fortune_jobs table:

```bash
cd Backend
alembic upgrade head
```

## Usage Workflow

### 1. Fortune Drawing Process

1. **User Request**: Client calls `/fortune/draw` endpoint
2. **Authentication**: Verify JWT token and user permissions
3. **Payment**: Check user points and deduct cost atomically
4. **Job Creation**: Create async job record in database
5. **Background Processing**: 
   - Select random poem using weighted algorithm
   - Generate personalized interpretation with LLM
   - Save result to database
6. **Notification**: Send WebSocket notification when complete
7. **Result Retrieval**: Client polls or receives notification, then fetches result

### 2. Poem Interpretation Process

1. **User Request**: Client calls `/fortune/interpret/{poem_id}` 
2. **Validation**: Verify poem exists in ChromaDB
3. **Payment**: Process point deduction
4. **Job Creation**: Create interpretation job
5. **Background Processing**:
   - Retrieve specific poem data
   - Generate contextual interpretation
   - Save personalized result
6. **Notification**: Real-time WebSocket update
7. **Result Delivery**: Client retrieves interpretation

## Data Flow

```
User Request → Authentication → Payment → Job Creation → Background Processing → Notification → Result Retrieval
     ↓              ↓              ↓            ↓                    ↓                ↓             ↓
  JWT Token    Point Check    Deduct Points   Database        ChromaDB Query    WebSocket    API Response
               Wallet API     Transaction     fortune_jobs    Fortune System    Message      Job Result
```

## Error Handling

### Payment Failures
- Insufficient points: HTTP 402 with detailed error
- Transaction failures: Rollback and retry logic
- Atomic operations to prevent double charging

### System Failures
- ChromaDB unavailable: HTTP 503 with retry information
- LLM failures: Fallback to template-based responses
- Job timeouts: Automatic cleanup and user notification

### Job Processing Errors
- Poem not found: Mark job as failed with clear message
- LLM errors: Use fallback interpretation system
- Database errors: Retry logic with exponential backoff

## Monitoring & Admin Tools

### System Health Checks
- ChromaDB connection status
- Database connection health  
- Job queue metrics
- Cache performance
- LLM provider availability

### Admin Statistics
- Total poems and temples in database
- Average interpretation generation times
- Popular fortune categories
- User usage patterns
- System performance metrics

## Security Considerations

### Authentication
- JWT token validation on all paid endpoints
- Role-based access control for admin endpoints
- Rate limiting on free search endpoints

### Data Protection
- User questions and interpretations are logged securely
- Personal data encryption in database
- GDPR compliance for user data deletion

### Payment Security
- Atomic point deduction transactions
- Audit trail for all financial operations
- Fraud detection for suspicious patterns

## Performance Optimizations

### Caching Strategy
- Redis/TTL cache for frequently accessed poems
- ChromaDB query result caching
- LLM response caching for similar questions

### Database Optimizations
- Indexed queries on job status and user ID
- Partitioning for large job tables
- Automated cleanup of expired jobs

### Background Processing
- Configurable worker pool size
- Priority queuing for premium users
- Load balancing across multiple instances

## Deployment Considerations

### Dependencies
- ChromaDB server or embedded mode
- PostgreSQL for job storage
- Redis for caching (optional)
- LLM provider access (OpenAI/Ollama)

### Scaling
- Horizontal scaling of job workers
- ChromaDB sharding for large datasets
- Load balancer for API endpoints
- WebSocket connection pooling

### Monitoring
- Prometheus metrics for job processing
- Health check endpoints for load balancers
- Log aggregation for error tracking
- Performance monitoring dashboards

## Testing

### Unit Tests
- Fortune service functionality
- Job processor logic
- API endpoint validation
- Payment system integration

### Integration Tests
- End-to-end fortune drawing workflow
- ChromaDB integration
- WebSocket notification delivery
- Admin functionality

### Performance Tests
- Concurrent job processing
- Database query performance
- Memory usage under load
- Response time measurements

## Troubleshooting

### Common Issues

**ChromaDB Connection Errors**
```bash
# Check database path
ls -la ../chroma_db/
# Verify permissions
chmod 755 ../chroma_db/
```

**Job Processing Stuck**
```bash
# Check job processor status
curl http://localhost:8000/api/v1/fortune/admin/health
# Restart job processor
systemctl restart divine-whispers
```

**Memory Usage High**
- Check cache size configuration
- Monitor ChromaDB memory usage
- Review job cleanup settings

## Future Enhancements

### Planned Features
1. **Multi-language LLM Support**: Native interpretation in Chinese, English, Japanese
2. **User Preference Learning**: Personalized poem selection based on history
3. **Advanced Analytics**: Detailed interpretation accuracy metrics
4. **Mobile Push Notifications**: Integration with mobile app notifications
5. **Premium Features**: Extended interpretations, fortune tracking, personal insights

### API Versioning
- v2 endpoints with enhanced features
- Backward compatibility maintenance
- Feature flags for gradual rollout

This integration provides a robust, scalable foundation for the Divine Whispers fortune-telling service while maintaining compatibility with existing systems and providing room for future enhancements.