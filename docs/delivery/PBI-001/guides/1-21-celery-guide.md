# Celery Async Execution Service Guide

**Task**: 1-21 Async Execution Service  
**Date**: 2024-12-27  
**Source**: [Celery Documentation](https://docs.celeryq.dev/en/stable/)

## Overview

This guide covers the implementation of Celery-based async execution service for CrewAI crew execution. The service allows queueing crew execution tasks and processing them asynchronously in the background.

## Architecture

### Components

1. **Celery App** (`celery_app.py`):
   - Celery application configuration
   - Redis broker and result backend setup
   - Task routing and queue management

2. **Async Execution Service** (`async_execution_service.py`):
   - Service class for managing async operations
   - Celery tasks for crew execution and cleanup
   - Status tracking and error handling

3. **Configuration**:
   - Redis as message broker and result backend
   - Environment variables for connection settings
   - Queue management with priorities

## Setup Requirements

### 1. Install Dependencies

```bash
pip install celery==5.4.0 redis==5.2.1
```

### 2. Redis Server

Ensure Redis is running on localhost:6379 or configure alternative connection in environment variables:

```bash
# Start Redis (example for Ubuntu/Debian)
sudo service redis-server start

# Or using Docker
docker run -d -p 6379:6379 redis:alpine
```

### 3. Environment Configuration

Add to your `.env` file:

```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Usage

### Starting Celery Worker

```bash
# From backend directory
celery -A celery_app worker --loglevel=info --queues=crew_execution,cleanup
```

### Monitoring Tasks

```bash
# Monitor task activity
celery -A celery_app monitor

# View active tasks
celery -A celery_app inspect active

# Check registered tasks
celery -A celery_app inspect registered
```

## API Usage

### Queue Execution

```python
from services.async_execution_service import AsyncExecutionService

service = AsyncExecutionService()

# Queue crew execution
task_id = service.queue_execution(
    graph_id=UUID("..."),
    thread_id=UUID("..."),
    user_id=UUID("..."),
    inputs={"key": "value"},
    priority=5
)
```

### Check Task Status

```python
# Get task status
status = service.get_task_status(task_id)
print(f"Status: {status['status']}")
print(f"Result: {status['result']}")
```

### Cancel Task

```python
# Cancel running task
success = service.cancel_task(task_id)
```

## Task Flow

1. **Queue**: Task queued with execution parameters
2. **Execute**: Celery worker picks up task
3. **Database**: Execution record created in database
4. **Translate**: Graph translated to CrewAI objects
5. **Run**: Crew execution with progress tracking
6. **Store**: Results stored in database
7. **Complete**: Task marked as completed/failed

## Error Handling

- **Retry Logic**: Failed tasks retry up to 3 times with 60-second delay
- **Database Rollback**: Failed transactions properly rolled back
- **Error Logging**: Comprehensive error logging with stack traces
- **Status Tracking**: Execution status tracked in database

## Queue Management

- **Priorities**: Tasks support priority levels (1-10, lower = higher priority)
- **Queues**: Separate queues for execution and cleanup tasks
- **Cancellation**: Tasks can be cancelled and terminated
- **Monitoring**: Worker and task monitoring capabilities

## Testing

### Unit Tests

```bash
# Run async execution tests
pytest backend/tests/test_async_execution.py -v
```

### Integration Tests

Integration tests require Redis setup and are marked with `@pytest.mark.integration`.

## Troubleshooting

### Common Issues

1. **Redis Connection Error**:
   - Verify Redis is running
   - Check connection URL in environment

2. **Task Not Processing**:
   - Ensure Celery worker is running
   - Check worker logs for errors
   - Verify queue names match

3. **Database Connection Issues**:
   - Verify database credentials
   - Check connection pooling settings

### Debugging

```bash
# Enable verbose logging
celery -A celery_app worker --loglevel=debug

# Check Celery configuration
python -c "from celery_app import celery_app; print(celery_app.conf)"
```

## Security Considerations

- **Redis Access**: Secure Redis instance in production
- **Task Arguments**: Avoid sensitive data in task arguments
- **Error Messages**: Sanitize error messages in production
- **Authentication**: Implement proper authentication for task management

## Performance Tuning

- **Worker Concurrency**: Adjust based on system resources
- **Prefetch**: Configure worker prefetch multiplier
- **Result Expiry**: Set appropriate result expiration time
- **Queue Routing**: Use separate queues for different task types

## Production Deployment

- Use Redis Cluster for high availability
- Configure Celery with proper monitoring
- Set up log aggregation
- Implement health checks
- Use process managers (supervisor, systemd)

## References

- [Celery Documentation](https://docs.celeryq.dev/en/stable/)
- [Redis Documentation](https://redis.io/documentation)
- [CrewAI Documentation](https://docs.crewai.com/) 