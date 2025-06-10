# CrewAI Project

This project consists of Docker services, a Python backend, and a frontend application. Follow the steps below to get the entire system running.

## Prerequisites

- Docker and Docker Compose
- Python 3.x
- Bun (for frontend package management and development)
- Node.js (if using npm/yarn as alternative to Bun)

## Environment Setup

1. Create a `.env` file in the root directory with the following variables:

```env
# Database Configuration
POSTGRES_DB=crewai
POSTGRES_USER=crewai
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=5432

# Redis Configuration
REDIS_PASSWORD=your_redis_password_here
REDIS_PORT=6379
```

## Quick Start

### 1. Launch Docker Services

Start the PostgreSQL database, Redis cache, and DBGate database manager:

```bash
# Navigate to the docker directory
cd docker

# Start all services in detached mode
docker-compose up -d

# Check service status
docker-compose ps

# View logs if needed
docker-compose logs -f
```

The following services will be available:
- **PostgreSQL**: `localhost:5432` (with pgvector extension)
- **Redis**: `localhost:6379` 
- **DBGate**: `http://localhost:5000` (Database management interface)

### 2. Start the Backend

```bash
# Navigate to the backend directory
cd backend

# Install dependencies (if needed)
pip install -r requirements.txt

# Run the backend server
python main.py
```

### 3. Start the Frontend

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
bun install

# Start development server
bun run dev
```

## Frontend Commands

### Development
```bash
cd frontend
bun run dev          # Start development server
```

### Production Build
```bash
cd frontend
bun run build        # Build for production
bun run start        # Start production server
```

### Other Useful Commands
```bash
bun install          # Install dependencies
bun run lint         # Run linting
bun run test         # Run tests (if configured)
```

## Docker Services Details

### PostgreSQL Database
- **Image**: pgvector/pgvector:pg15
- **Port**: 5432
- **Database**: crewai
- **Extensions**: pgvector for vector operations
- **Health Check**: Automatic readiness checks

### Redis Cache
- **Image**: redis:7-alpine
- **Port**: 6379
- **Persistence**: AOF enabled
- **Password**: Set via REDIS_PASSWORD environment variable

### DBGate Database Manager
- **Image**: dbgate/dbgate
- **Port**: 5000
- **Access**: http://localhost:5000
- **Pre-configured**: Automatically connects to PostgreSQL

## Stopping Services

### Stop Docker Services
```bash
cd docker
docker-compose down
```

### Stop All Services (with volume cleanup)
```bash
cd docker
docker-compose down -v  # Removes volumes (data will be lost)
```

## Troubleshooting

### Docker Issues
- Ensure Docker is running
- Check port availability (5432, 6379, 5000)
- Verify environment variables in `.env` file

### Backend Issues
- Check Python version compatibility
- Ensure all dependencies are installed
- Verify database connection settings

### Frontend Issues
- Ensure Bun is installed: `curl -fsSL https://bun.sh/install | bash`
- Check Node.js version compatibility
- Clear cache: `bun pm cache rm`

### Database Connection
- Wait for PostgreSQL health check to pass
- Use DBGate at http://localhost:5000 to verify database connectivity
- Check logs: `docker-compose logs postgres`

## Development Workflow

1. Start Docker services first
2. Start backend development server
3. Start frontend development server
4. Make changes and test
5. Stop services when done

## Documentation

This project uses a structured documentation approach for managing Product Backlog Items (PBIs) and tasks.

### Documentation Structure

The `docs/` directory contains:

- **`docs/delivery/`**: Main delivery documentation
  - **`backlog.md`**: Single source of truth for all PBIs, ordered by priority
  - **`<PBI-ID>/`**: Individual PBI directories containing:
    - **`prd.md`**: Mini-PRD (Product Requirements Document) for each PBI
    - **`tasks.md`**: Task index listing all tasks for the PBI
    - **`<PBI-ID>-<TASK-ID>.md`**: Individual task files with detailed specifications
    - **`guides/`**: Package-specific guides and documentation
- **`docs/technical/`**: API and interface technical documentation

### How to Use Documentation

1. **View Current Backlog**: Check `docs/delivery/backlog.md` for all PBIs and their status
2. **PBI Details**: Navigate to `docs/delivery/<PBI-ID>/prd.md` for specific PBI requirements
3. **Task Management**: Use `docs/delivery/<PBI-ID>/tasks.md` to track task progress
4. **Technical References**: Find API docs and guides in respective PBI directories

### Documentation Workflow

- All code changes must be associated with an approved task
- Tasks must be linked to an agreed-upon PBI
- Status updates are tracked in both task files and index files
- Technical documentation is created for APIs and interfaces

## Project Structure

```
├── docker/
│   ├── compose.yaml          # Docker services configuration
│   └── init-scripts/         # Database initialization scripts
├── backend/
│   ├── main.py              # Backend entry point
│   └── ...                  # Backend source code
├── frontend/
│   ├── package.json         # Frontend dependencies
│   └── ...                  # Frontend source code
├── docs/
│   ├── delivery/
│   │   ├── backlog.md       # Product backlog (single source of truth)
│   │   └── <PBI-ID>/        # Individual PBI documentation
│   │       ├── prd.md       # PBI requirements document
│   │       ├── tasks.md     # Task index for the PBI
│   │       ├── tasks/      # Package-specific guides
│   │       │   └── <PBI-ID>-<TASK-ID>.md  # Individual task files
│   │       └── guides/      # Package-specific guides
│   └── technical/           # API and technical documentation
└── README.md               # This file
``` 