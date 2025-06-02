# CrewAI Backend Development - AI Agent Task Brief

## Project Context
You are implementing the backend for a CrewAI Graph Builder application. The backend will be located in the `backend/` directory and serves a React frontend that allows users to create and execute CrewAI crews through visual graphs.

## Compliance Requirements
This development MUST follow the AI Coding Agent Policy. All work requires:
- Task-driven development with agreed-upon authorizing tasks
- PBI association for all tasks
- Proper documentation structure in `docs/delivery/`
- Status synchronization between index and individual task files
- External package research with guide creation

## Product Backlog Item (PBI)

### PBI-001: CrewAI Backend API Development

**User Story**: As a frontend developer, I need a complete backend API that handles user authentication, graph management, CrewAI execution, and real-time streaming so that users can create, configure, and execute CrewAI crews through a visual interface.

**Status**: Proposed → (awaiting User approval to move to Agreed)

**Conditions of Satisfaction**:
1. JWT + API key authentication system with user management
2. PostgreSQL database with all required models and relationships
3. CRUD operations for graphs, workspaces, threads, messages, and API keys
4. Graph validation service that ensures CrewAI compatibility
5. CrewAI execution service with async processing and queueing
6. SSE streaming for real-time execution updates
7. Integrated tool repository with hello world tool
8. MLFlow integration for metrics collection
9. Admin-only template management
10. Comprehensive error handling and logging
11. Docker support with docker-compose for development
12. Complete API documentation and testing suite

## Technical Stack Requirements
- **Framework**: FastAPI (async support, automatic OpenAPI docs)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens + API key storage
- **Queue**: Celery with Redis for async execution
- **Streaming**: Server-Sent Events (SSE)
- **ML Monitoring**: MLFlow integration
- **CrewAI Version**: 0.121.1
- **Location**: `backend/` directory

## Task Breakdown Strategy

The PBI will be broken into minimal, testable tasks following these categories:

### Phase 1: Foundation (Tasks 1-1 through 1-6)
1. **1-1**: Project structure and environment setup
2. **1-2**: Database configuration and connection
3. **1-3**: Basic FastAPI application with health check
4. **1-4**: Authentication models and JWT implementation
5. **1-5**: User registration and login endpoints
6. **1-6**: API key storage model and encryption

### Phase 2: Core Models (Tasks 1-7 through 1-12)
7. **1-7**: Graph model and basic CRUD
8. **1-8**: Workspace and thread models
9. **1-9**: Message model with execution linking
10. **1-10**: Execution log model and status tracking
11. **1-11**: Metrics model for MLFlow integration
12. **1-12**: Database migrations and seeding

### Phase 3: Graph Management (Tasks 1-13 through 1-18)
13. **1-13**: Node type definitions and schemas
14. **1-14**: Graph validation service foundation
15. **1-15**: Graph CRUD endpoints
16. **1-16**: Graph validation endpoints
17. **1-17**: Template management (admin only)
18. **1-18**: Graph testing and node validation

### Phase 4: CrewAI Integration (Tasks 1-19 through 1-24)
19. **1-19**: CrewAI package integration and research
20. **1-20**: Graph to CrewAI object translation service
21. **1-21**: Async execution service with Celery
22. **1-22**: Execution status management
23. **1-23**: Error handling for crew execution
24. **1-24**: Execution testing framework

### Phase 5: Real-time & Streaming (Tasks 1-25 through 1-29)
25. **1-25**: SSE implementation for execution streaming
26. **1-26**: Real-time status updates
27. **1-27**: Message handling with execution trigger
28. **1-28**: WebSocket alternative evaluation
29. **1-29**: Streaming performance testing

### Phase 6: Tools & MLFlow (Tasks 1-30 through 1-35)
30. **1-30**: Tool repository service foundation
31. **1-31**: Hello world tool implementation
32. **1-32**: Tool schema and execution framework
33. **1-33**: MLFlow integration and metrics collection
34. **1-34**: Tool testing and validation
35. **1-35**: MLFlow metrics dashboard endpoints

### Phase 7: Security & Deployment (Tasks 1-36 through 1-40)
36. **1-36**: API key encryption and secure storage
37. **1-37**: Rate limiting and security middleware
38. **1-38**: Docker configuration and containerization
39. **1-39**: Environment variable management
40. **1-40**: Production security hardening

### Phase 8: Testing & Documentation (Tasks 1-41 through 1-45)
41. **1-41**: Unit test suite setup and core tests
42. **1-42**: Integration tests for API endpoints
43. **1-43**: E2E testing for complete workflows
44. **1-44**: API documentation completion
45. **1-45**: E2E CoS Test for complete PBI verification

## AI Agent Instructions

### Environment: Windows with PowerShell
- Use PowerShell commands for all terminal operations
- Use `pip` for Python package installation
- Use `python` command (not `python3`)
- Use Windows-style paths with backslashes when needed

### Response Style: CONCISE
- Keep all responses brief and to the point
- No lengthy explanations unless specifically requested
- Focus on actionable items and direct answers
- Use bullet points or numbered lists for clarity
- Avoid verbose descriptions
- **Use as few command/tool calls as possible** - batch operations when feasible

### For Each Task:
1. **Before Starting**: Confirm PBI association and get User approval
2. **Research Phase**: For external packages (FastAPI, CrewAI, etc.), create `<task_id>-<package>-guide.md` in `docs/delivery/PBI-001/guides/`
3. **Implementation**: Follow task scope exactly, no gold-plating
4. **Testing**: Implement tests per task's test plan
5. **Documentation**: Update technical docs for API/interface changes
6. **Status Updates**: Maintain status in both index and individual task files
7. **Completion**: Commit with format `<task_id> <task_description>`

### File Structure Required:
```
docs/delivery/PBI-001/
├── prd.md                           # PBI detail document
├── tasks.md                         # Task index
├── guides/                          # Package research guides
│   ├── 1-19-crewai-guide.md
│   ├── 1-1-fastapi-guide.md
│   └── ...
└── tasks/                           # Individual task files
    ├── PBI-001-1.md                 # Task 1-1 details
    ├── PBI-001-2.md                 # Task 1-2 details
    └── ...
```

### Technical Constraints:
- All database operations through SQLAlchemy ORM
- All API endpoints follow RESTful conventions
- Environment variables for all configuration
- Comprehensive error handling with proper HTTP status codes
- Type hints throughout Python code
- Async/await patterns for I/O operations

### Success Metrics:
- Each task passes its defined test plan
- API endpoints return proper responses with correct status codes
- Graph validation catches invalid configurations
- CrewAI execution works end-to-end
- SSE streaming provides real-time updates
- All external package integrations are documented

## Next Steps
1. User approves PBI-001 (Proposed → Agreed)
2. Create PBI detail document (`docs/delivery/PBI-001/prd.md`)
3. Create task index (`docs/delivery/PBI-001/tasks.md`)
4. Begin with Task 1-1: Project structure and environment setup

## Questions for User Approval:
1. Does the task breakdown look appropriate for incremental development?
2. Are there any specific technical requirements or constraints to add?
3. Should any tasks be combined or further split for better manageability?
4. Do you approve moving PBI-001 from Proposed to Agreed status?