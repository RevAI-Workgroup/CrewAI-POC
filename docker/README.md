# CrewAI Docker Setup

This directory contains Docker configuration for running the complete CrewAI backend stack with all required services.

## Services Included

### Core Services
- **PostgreSQL**: Main database with pgvector extension
- **Redis**: Message broker and cache for Celery
- **FastAPI Backend**: Main application server
- **Celery Worker**: Async task processor for crew execution
- **Celery Flower**: Web-based monitoring for Celery tasks

### Supporting Services
- **MLFlow**: Experiment tracking and model registry
- **DBGate**: Database administration interface

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp env.example .env

# Edit the .env file with your secure passwords and settings
nano .env
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Or start specific services
docker-compose up -d postgres redis
docker-compose up -d backend celery-worker
```

### 3. Check Status

```bash
# View all services
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs celery-worker
```

## Service URLs

Once running, services are available at:

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Celery Flower**: http://localhost:5555
- **MLFlow**: http://localhost:5001
- **DBGate**: http://localhost:5000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Environment Variables

Key variables to configure in `.env`:

```bash
# Security (REQUIRED - generate secure values)
POSTGRES_PASSWORD=your-secure-postgres-password
REDIS_PASSWORD=your-secure-redis-password
SECRET_KEY=your-secret-key-min-32-chars
ENCRYPTION_KEY=your-encryption-key

# Optional customization
BACKEND_PORT=8000
MLFLOW_PORT=5001
FLOWER_PORT=5555
DEBUG=false
```

## Development Setup

### Backend Development with Hot Reload

```bash
# Start dependencies only
docker-compose up -d postgres redis mlflow

# Run backend locally for development
cd ../backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker locally
cd ../backend
celery -A celery_app worker --loglevel=info
```

### Database Management

```bash
# Access database directly
docker-compose exec postgres psql -U crewai -d crewai

# Run migrations
docker-compose exec backend python manage_db.py run-migrations

# View database in DBGate
# Open http://localhost:5000
```

## Production Deployment

### Security Considerations

1. **Generate secure passwords** for all services
2. **Use secrets management** instead of environment files
3. **Configure TLS/SSL** for external access
4. **Set up monitoring** and log aggregation
5. **Configure backups** for PostgreSQL and Redis
6. **Use non-root users** (already configured)
7. **Enable firewall rules** for network security

### Resource Limits

Services are configured with resource limits:

- **Backend**: 2GB RAM, 1 CPU (limit) / 512MB RAM, 0.5 CPU (reserved)
- **Celery Worker**: 2GB RAM, 1 CPU (limit) / 512MB RAM, 0.5 CPU (reserved)
- **PostgreSQL**: 2GB RAM, 1 CPU (limit) / 512MB RAM, 0.5 CPU (reserved)
- **Redis**: 1GB RAM, 0.5 CPU (limit) / 256MB RAM, 0.25 CPU (reserved)

### Scaling

```bash
# Scale Celery workers
docker-compose up -d --scale celery-worker=3

# Use Docker Swarm for multi-node deployment
docker swarm init
docker stack deploy -c compose.yaml crewai
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in `.env` file
2. **Permission errors**: Ensure Docker has proper permissions
3. **Database connection**: Check PostgreSQL is healthy before starting backend
4. **Celery tasks failing**: Check Redis connection and worker logs

### Debugging Commands

```bash
# Check service health
docker-compose ps
docker-compose logs [service-name]

# Access service shells
docker-compose exec backend bash
docker-compose exec postgres psql -U crewai -d crewai
docker-compose exec redis redis-cli

# View resource usage
docker stats

# Check networks
docker network ls
docker network inspect crewai-network
```

### Log Management

```bash
# View logs with timestamps
docker-compose logs -t backend

# Follow logs in real-time
docker-compose logs -f celery-worker

# View last 100 lines
docker-compose logs --tail=100 backend
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U crewai -d crewai > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U crewai -d crewai < backup.sql
```

### Redis Backup

```bash
# Redis automatically creates snapshots in /data
# Copy the dump.rdb file for backup
docker cp crewai-redis:/data/dump.rdb ./redis-backup.rdb
```

## Monitoring

### Health Checks

All services include health checks:
- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`
- **Backend**: HTTP health endpoint
- **Services**: 10-30s intervals with retries

### Monitoring Tools

- **Celery Flower**: Task monitoring at http://localhost:5555
- **MLFlow**: Experiment tracking at http://localhost:5001
- **DBGate**: Database management at http://localhost:5000
- **Docker Stats**: `docker stats` for resource monitoring

## Network Architecture

Services communicate through the `crewai-network` bridge network:

- **Subnet**: 172.20.0.0/16
- **Internal DNS**: Services can reach each other by name
- **External Access**: Only specified ports are exposed to host

## Volume Management

Persistent data stored in Docker volumes:

- `postgres_data`: Database files
- `redis_data`: Redis persistence files
- `mlflow_data`: MLFlow artifacts and metadata
- `dbgate-data`: DBGate configuration

```bash
# List volumes
docker volume ls

# Backup volume
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore volume
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
``` 