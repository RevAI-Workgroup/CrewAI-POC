# Frontend Prompt Generator Template

## Purpose
This document serves as a template to regenerate `frontend_prompt.md` as the backend API evolves and new endpoints are added. Use this to maintain consistency and ensure the frontend prompt stays current with backend capabilities.

## Template Structure

### Header Section
```markdown
# CrewAI Frontend Development - AI Agent Task Brief

## Project Context
You are implementing the frontend for a CrewAI Graph Builder application. The frontend will be located in the `frontend/` directory and connects to the backend API to allow users to create and execute CrewAI crews through visual graphs.

## Compliance Requirements
[Standard AI Coding Agent Policy requirements]
```

### PBI Definition Template
```markdown
### PBI-002: CrewAI Frontend Application Development

**User Story**: As a user, I need a modern React frontend application that allows me to [DYNAMIC: list current backend capabilities] through a visual graph interface, so that I can build and execute AI workflows without technical complexity.

**Status**: Proposed → (awaiting User approval to move to Agreed)

**Conditions of Satisfaction**:
[GENERATED: Based on available backend endpoints and features]
```

### Dynamic Sections to Update

#### 1. Backend API Integration Section
```markdown
### Backend API Integration:
- Base URL: `http://localhost:8000/api`
- Authentication: JWT Bearer tokens
- Available endpoints:
  [DYNAMIC: Auto-generate from backend router analysis]
```

**Current Endpoints Template:**
```
- `POST /auth/login` - User login
- `POST /auth/register` - User registration  
- `GET /graphs` - List user graphs
- `POST /graphs` - Create graph
- `PUT /graphs/{id}` - Update graph
- `DELETE /graphs/{id}` - Delete graph
- `GET /node-definitions/structure` - Get node types
[ADD_NEW_ENDPOINTS_HERE]
```

#### 2. Task Breakdown Generation Rules

**Core Phases (Always Include):**
1. **Foundation & Setup** - React/Vite/TypeScript setup
2. **Authentication System** - Based on auth endpoints
3. **Layout & Navigation** - React Router v6 + UI structure
4. **Graph Management** - Based on graph CRUD endpoints

**Dynamic Phases (Generate Based on Backend):**
- **React Flow Integration** - If node definitions available
- **Real-time Features** - If SSE/WebSocket endpoints exist
- **Chat Interface** - If message/thread endpoints exist
- **Admin Features** - If admin endpoints exist
- **Tool Management** - If tool endpoints exist
- **Execution Monitoring** - If execution endpoints exist

#### 3. Technical Stack Updates

**Fixed Requirements:**
- React 18 + Vite
- React Router v6 (mandatory)
- TypeScript (strict mode)
- Tailwind CSS + Headless UI

**Dynamic Additions Based on Backend:**
- Add Socket.io if WebSocket endpoints exist
- Add React Query if many API endpoints
- Add React Hook Form if complex forms needed
- Add Recharts if analytics endpoints exist

### Generation Process

#### Step 1: Analyze Backend Structure
```bash
# Scan backend routers for endpoints
find backend/routers -name "*.py" -exec grep -l "@router" {} \;

# Extract endpoint patterns
grep -r "@router\." backend/routers/ | grep -E "(get|post|put|delete)"
```

#### Step 2: Generate Endpoint List
For each router file, extract:
- HTTP method and path
- Authentication requirements  
- Description from docstring
- Request/response schemas

#### Step 3: Update Task Breakdown
Based on available endpoints, add/remove phases:

**Graph Endpoints → Graph Management Phase**
- GET /graphs → Graph list component
- POST /graphs → Graph creation
- PUT /graphs/{id} → Graph editing
- DELETE /graphs/{id} → Graph deletion

**Node Definition Endpoints → React Flow Phase** 
- GET /node-definitions/structure → Node type system
- Visual graph editor with dynamic node types

**Auth Endpoints → Authentication Phase**
- POST /auth/login → Login component
- POST /auth/register → Registration component
- JWT token management

**Thread/Message Endpoints → Chat Interface Phase**
- Chat components and real-time messaging

#### Step 4: Update Technical Constraints
Based on backend requirements:
- API response formats
- Authentication schemes
- Real-time communication methods
- Error handling patterns

### Example Usage

To regenerate the frontend prompt:

1. **Analyze Current Backend:**
   ```bash
   # Get all API endpoints
   python backend/main.py --list-routes
   ```

2. **Update Backend API Section:**
   - List all available endpoints
   - Update authentication requirements
   - Add new response schemas

3. **Adjust Task Breakdown:**
   - Add phases for new features
   - Update existing tasks based on API changes
   - Reorder tasks based on dependencies

4. **Update Success Metrics:**
   - Include new features in validation
   - Add performance requirements for new endpoints
   - Update integration test requirements

### Versioning

Track changes to maintain consistency:

```markdown
## Prompt Version History
- v1.0: Initial frontend prompt (Auth + Graph + React Flow)
- v1.1: Added chat interface based on message endpoints
- v1.2: Added real-time features based on SSE endpoints
- v1.3: Added admin features based on admin endpoints
```

### Maintenance Checklist

When updating the frontend prompt:

- [ ] Scan all backend routers for new endpoints
- [ ] Update Backend API Integration section
- [ ] Add new phases for significant features
- [ ] Update technical stack if needed
- [ ] Adjust success metrics
- [ ] Update file structure if new directories needed
- [ ] Increment version number
- [ ] Test that all referenced endpoints exist

### Notes

- Always keep React Router v6 as mandatory
- Maintain TypeScript strict mode requirement
- Keep core UI framework (Tailwind CSS) consistent
- Ensure all new endpoints are properly typed
- Add research tasks for new major libraries 