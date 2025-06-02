# CrewAI Frontend Development Prompt

## Project Overview
Create a modern React frontend application for the CrewAI backend that provides a visual crew creation interface and chat functionality. The frontend should be built with React + Vite, TypeScript, Tailwind CSS, and HeroUI components.

## Development Methodology
This project follows a **Test-Driven Development (TDD)** approach with **phased implementation**. Each phase must be fully functional and tested before proceeding to the next phase. **No phase is considered complete until 100% of tests pass**.

### Phase Completion Requirements:
1. All features for the phase are implemented
2. All tests pass (100% success rate)
3. Application runs without errors
4. User approval is obtained before proceeding to next phase

### Test Strategy:
Tests are organized by **theme/functionality**, not by development phases:
- **Unit Tests**: Components, hooks, utilities, services
- **Integration Tests**: API integration, WebSocket connections, state management
- **E2E Tests**: Complete user workflows and interactions
- **Performance Tests**: Loading times, memory usage, rendering performance

## Development Phases

### Phase 1: Foundation & Basic Layout
**Goal**: Establish project foundation with basic layout and navigation

**Deliverables**:
- React + Vite + TypeScript project setup in `frontend/` directory
- Tailwind CSS and HeroUI integration
- Basic layout components (Header, Sidebar, Main content area)
- Theme system (Dark/Light/System modes)
- Basic routing setup
- Context providers for global state

**Features**:
- Responsive layout with sidebar navigation
- Theme toggle functionality
- Basic crew list display (mock data)
- Settings page foundation
- Error boundaries

**Tests Required**:
- Layout component rendering
- Theme switching functionality
- Responsive design tests
- Context provider tests
- Basic navigation tests

**Acceptance Criteria**:
- App runs without errors
- Theme switching works correctly
- Layout is responsive on different screen sizes
- All unit tests pass (100%)
- User can navigate between basic pages

---

### Phase 2: Crew Management & CRUD Operations
**Goal**: Implement crew creation, editing, and management

**Deliverables**:
- Crew CRUD operations with backend integration
- Basic crew creation/editing forms
- Crew list with real backend data
- TypeScript types for all backend models
- API service layer with error handling
- Loading states and error handling

**Features**:
- Create new crews
- Edit existing crews
- Delete crews with confirmation
- View crew details
- Real-time data persistence to backend

**Tests Required**:
- API service tests
- Crew CRUD operation tests
- Form validation tests
- Error handling tests
- Loading state tests

**Acceptance Criteria**:
- Users can create, read, update, delete crews
- Data persists correctly to backend
- Proper error handling for API failures
- Loading states provide good UX
- All tests pass (100%)

**⚠️ Wait for user approval before proceeding to Phase 3**

---

### Phase 3: Visual Crew Editor (React Flow Integration)
**Goal**: Implement the visual node-based crew editor

**Deliverables**:
- React Flow integration
- Basic node types (Crew, Agent, Tool nodes)
- Drag and drop functionality
- Node connection system
- Dual node addition methods (toolbar + inline buttons)
- Real-time autosave

**Features**:
- Visual crew configuration interface
- Draggable agent and tool nodes
- Node connections for relationships
- Toolbar for adding nodes
- Inline '+' buttons for node addition
- Immediate backend persistence

**Tests Required**:
- React Flow component tests
- Node creation and deletion tests
- Connection system tests
- Autosave functionality tests
- Visual editor interaction tests

**Acceptance Criteria**:
- Users can visually create and edit crews
- Node addition works via both methods
- Connections between nodes work correctly
- Changes save immediately to backend
- All tests pass (100%)

**⚠️ Wait for user approval before proceeding to Phase 4**

---

### Phase 4: Advanced Visual Editor Features
**Goal**: Implement advanced visual editor features and business logic

**Deliverables**:
- Manager agent linking system
- Dynamic vs Manual crew toggle
- Node property panels
- Field visibility management
- Alert dialogs for destructive operations
- Advanced node styling and feedback

**Features**:
- Manager agent designation with field hiding
- Dynamic/Manual crew type switching
- Confirmation dialogs for agent deletion
- Node property editing panels
- Visual feedback for node states
- Tool assignment to agents

**Tests Required**:
- Manager agent linking tests
- Dynamic/Manual toggle tests
- Alert dialog tests
- Field visibility tests
- Node state management tests

**Acceptance Criteria**:
- Manager agent linking works correctly
- Field visibility toggles properly
- Users get proper warnings for destructive actions
- All visual feedback works as expected
- All tests pass (100%)

**⚠️ Wait for user approval before proceeding to Phase 5**

---

### Phase 5: Chat Interface & Streaming
**Goal**: Implement chat functionality with crew execution

**Deliverables**:
- Chat interface components
- Server-Sent Events (SSE) integration
- Message history with localStorage adapter
- Crew execution integration
- Streaming message display
- Execution status monitoring

**Features**:
- Send messages to crews
- Receive streaming responses
- Display conversation history
- Show execution progress
- Handle different message types
- Chat history persistence

**Tests Required**:
- Chat component tests
- SSE streaming tests
- Message history tests
- Execution status tests
- localStorage adapter tests

**Acceptance Criteria**:
- Users can chat with created crews
- Messages stream in real-time
- Conversation history persists
- Execution status displays correctly
- All tests pass (100%)

**⚠️ Wait for user approval before proceeding to Phase 6**

---

### Phase 6: Real-time Features & WebSocket Integration
**Goal**: Add real-time features and WebSocket functionality

**Deliverables**:
- WebSocket connection management
- Real-time execution monitoring
- Live crew updates
- Connection status indicators
- Retry logic for failed connections
- Performance optimizations

**Features**:
- Real-time execution progress
- Live crew configuration updates
- Connection status display
- Automatic reconnection
- Global event notifications
- Performance monitoring

**Tests Required**:
- WebSocket connection tests
- Real-time update tests
- Connection recovery tests
- Performance benchmark tests
- Event handling tests

**Acceptance Criteria**:
- Real-time updates work reliably
- Connection failures are handled gracefully
- Performance remains smooth with real-time features
- All tests pass (100%)

**⚠️ Wait for user approval before proceeding to Phase 7**

---

### Phase 7: Settings & Configuration
**Goal**: Complete settings management and advanced configuration

**Deliverables**:
- Complete settings page
- LLM provider management
- Advanced configuration options
- Import/export functionality
- Data management features
- User preferences

**Features**:
- LLM provider configuration
- Execution parameter settings
- Data export/import
- Application data management
- User preference persistence
- Advanced theme options

**Tests Required**:
- Settings page tests
- Configuration persistence tests
- Import/export functionality tests
- Data management tests
- User preference tests

**Acceptance Criteria**:
- All settings work correctly
- Configuration persists properly
- Import/export functions work
- Data management is reliable
- All tests pass (100%)

**⚠️ Wait for user approval before proceeding to Phase 8**

---

### Phase 8: Docker Integration & Production Setup
**Goal**: Integrate frontend with existing Docker setup and prepare for production

**Deliverables**:
- Frontend Dockerfile
- Docker Compose integration with existing `/docker/compose.yml`
- Production build optimization
- Environment configuration
- Nginx configuration for serving static files
- Multi-stage Docker builds

**Docker Integration**:
```dockerfile
# Frontend Dockerfile (frontend/Dockerfile)
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Docker Compose Updates**:
```yaml
# Update /docker/compose.yml to include frontend service
services:
  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    environment:
      - VITE_API_BASE_URL=http://backend:8000
      - VITE_WS_BASE_URL=ws://backend:8000
    depends_on:
      - backend
    networks:
      - crewai-network
```

**Features**:
- Production-ready Docker setup
- Frontend served via Nginx
- Environment-based configuration
- Integration with existing backend services
- Health checks and monitoring
- Production optimizations

**Tests Required**:
- Docker build tests
- Container integration tests
- Production build tests
- Environment configuration tests
- Health check tests

**Acceptance Criteria**:
- Frontend builds successfully in Docker
- Integration with existing Docker Compose works
- Production build is optimized
- All environment configurations work
- Health checks pass
- All tests pass (100%)

**Final Deliverable**: Complete, production-ready CrewAI frontend application running in Docker alongside the backend

## Technology Stack
- **Framework**: React 18+ with Vite
- **Language**: TypeScript with strict type safety
- **Routing**: React Router v6
- **Styling**: Tailwind CSS
- **UI Components**: HeroUI (NextUI)
- **State Management**: React Context + useReducer
- **Visual Editor**: React Flow
- **HTTP Client**: Axios with React Query for caching
- **Real-time**: Server-Sent Events (SSE) for streaming, WebSockets for real-time updates
- **Icons**: Lucide React or HeroIcons

## Development Environment
- **Operating System**: Windows
- **Shell**: PowerShell (pwsh.exe)
- **Node.js**: Version 18+ recommended
- **Package Manager**: npm (included with Node.js)

## Testing Framework Requirements

### Test Organization Structure:
```
frontend/src/__tests__/
├── unit/
│   ├── components/           # Component unit tests
│   ├── hooks/               # Custom hook tests
│   ├── services/            # API service tests
│   └── utils/               # Utility function tests
├── integration/
│   ├── api/                 # API integration tests
│   ├── websocket/           # WebSocket connection tests
│   ├── state/               # State management tests
│   └── workflows/           # Multi-component workflows
├── e2e/
│   ├── crew-creation/       # Complete crew creation flows
│   ├── chat-interface/      # Chat functionality tests
│   ├── visual-editor/       # Visual editor interactions
│   └── settings/            # Settings management tests
└── performance/
    ├── rendering/           # Component rendering performance
    ├── memory/              # Memory usage tests
    └── load-testing/        # Load testing scenarios
```

### Testing Tools:
- **Unit/Integration**: Vitest + React Testing Library
- **E2E**: Playwright
- **Performance**: Lighthouse CI
- **Coverage**: c8 (built into Vitest)

### Test Requirements per Phase:
Each phase must achieve:
- **100% test success rate** (no failing tests)
- **Minimum 80% code coverage** for new code
- **All E2E scenarios pass** for implemented features
- **Performance benchmarks met** (load times < 2s)

## Phase Implementation Guidelines

### Development Workflow:
1. **Write tests first** (TDD approach)
2. **Implement minimum viable feature**
3. **Refactor and optimize**
4. **Ensure all tests pass**
5. **Get user approval**
6. **Proceed to next phase**

### Inter-Phase Dependencies:
- Each phase builds upon the previous
- No skipping phases allowed
- Critical bugs must be fixed before proceeding
- Performance regressions block phase completion

### Docker Integration Notes:
- Development environment should mirror production
- Use Docker Compose for local development
- Environment variables properly configured
- Health checks implemented for all services

This prompt provides a comprehensive foundation for building a modern, feature-rich React frontend that integrates seamlessly with the CrewAI backend through a structured, test-driven development approach with proper Docker integration.

## Core Features Overview

### 1. Visual Crew Creation Interface
Build a node-based visual editor using React Flow that allows users to create and configure crews through drag-and-drop interactions.

#### Node Types:
1. **Crew Node** (Default, non-deletable)
   - Always present when creating/editing a crew
   - Contains crew-level configuration: name, description, verbose mode
   - Toggle for Manual vs Dynamic crew type
   - When switching from Manual to Dynamic: Show alert dialog warning that all agents (except manager) will be deleted

2. **Agent Nodes** (User-addable)
   - Standard fields: role, goal, backstory, tools, llm_provider
   - When linked as manager agent: Hide role, goal, backstory fields and change node title to "Manager Agent"
   - When unlinked from manager: Show all fields again
   - Visual connection points for tools and manager relationships

3. **Tool Nodes** (User-addable)
   - Represent tools from the backend tool registry
   - Display tool name, description, and configuration options
   - Connect to agent nodes to assign tools

#### Adding Nodes:
Implement **dual addition methods** for all addable nodes:
1. **Toolbar buttons** at the top of the visual editor container
2. **Inline '+' buttons** next to fields that require nodes (e.g., "+ Add Tool" next to agent's tools field)

#### Data Persistence:
- **Immediate save**: Every user action (node creation, deletion, field changes, connections) should immediately save to backend
- Use crew/agent CRUD endpoints for persistence
- Implement optimistic updates with error handling

### 2. Chat Interface
Create a modern chat interface for interacting with crews.

#### Features:
- **Message Input**: Textarea with send button
- **Streaming Responses**: Use Server-Sent Events (SSE) for real-time message streaming
- **Message History**: Display conversation history with crew
- **Execution Status**: Show crew execution progress and status
- **Message Types**: Support text messages and system notifications

#### Chat History Adapter:
Create an adapter pattern for chat history storage:
```typescript
interface ChatHistoryAdapter {
  saveMessage(crewId: string, message: Message): Promise<void>;
  getMessages(crewId: string): Promise<Message[]>;
  clearHistory(crewId: string): Promise<void>;
}

// Initial implementation using localStorage
class LocalStorageChatAdapter implements ChatHistoryAdapter {
  // Implementation for localStorage with future database migration path
}
```

### 3. Layout & Navigation

#### React Router v6 Integration:
Implement modern routing with React Router v6:
```typescript
// App routing structure
const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Navigate to="/crews" replace />
      },
      {
        path: "crews",
        children: [
          {
            index: true,
            element: <CrewList />
          },
          {
            path: ":crewId",
            children: [
              {
                path: "editor",
                element: <VisualEditor />
              },
              {
                path: "chat",
                element: <ChatInterface />
              },
              {
                path: "execution",
                element: <ExecutionMonitor />
              }
            ]
          }
        ]
      },
      {
        path: "settings",
        element: <SettingsPage />
      }
    ]
  }
]);
```

#### Sidebar:
- **Crew List**: Display all user crews with creation dates
- **Conversation History**: Show recent conversations per crew
- **Theme Toggle**: Dark/Light/System theme support
- **Settings Access**: Navigate to settings page

#### Crew Selection:
- Clicking a crew in sidebar sets it as current crew
- Loads associated chat history
- Navigates to chat interface for that crew
- Updates URL for deep linking (e.g., `/crews/123/chat`)

#### Main Content Area:
- **Visual Editor Tab**: Crew configuration interface (`/crews/:id/editor`)
- **Chat Tab**: Conversation interface with selected crew (`/crews/:id/chat`)
- **Execution Tab**: Real-time execution monitoring (`/crews/:id/execution`)

### 4. Settings Page
Comprehensive configuration options:

#### Sections:
1. **Appearance**
   - Theme selection (Dark/Light/System)
   - UI density options
   - Color scheme preferences

2. **LLM Providers**
   - Configure available LLM providers
   - API key management
   - Default provider selection

3. **Execution**
   - Default execution parameters
   - Timeout settings
   - Verbose mode preferences

4. **Data & Storage**
   - Chat history management
   - Export/import crew configurations
   - Clear application data

## Backend Integration

### API Endpoints
Integrate with existing CrewAI backend endpoints:

#### Core CRUD:
- `GET/POST/PUT/DELETE /api/v1/crews/` - Crew management
- `GET/POST/PUT/DELETE /api/v1/agents/` - Agent management
- `GET /api/v1/tools/` - Available tools registry
- `GET /api/v1/llm-providers/` - LLM provider management

#### Execution:
- `POST /api/v1/crews/{crew_id}/execute` - Execute crew
- `GET /api/v1/crews/{crew_id}/execution-status` - Check execution status

#### Real-time Features:
- **WebSocket Connections**: `/ws/executions/{execution_id}`, `/ws/crews/{crew_id}`, `/ws/global`
- **SSE Streaming**: For chat message streaming during crew execution

### Type Safety
Generate TypeScript types from backend schemas:

```typescript
// Base types from backend models
interface Crew {
  id: string;
  name: string;
  description?: string;
  is_dynamic: boolean;
  manager_agent_id?: string;
  verbose: boolean;
  agents: Agent[];
  created_at: string;
  updated_at: string;
}

interface Agent {
  id: string;
  crew_id: string;
  role: string;
  goal: string;
  backstory: string;
  tools: string[];
  llm_provider?: string;
  is_manager: boolean;
}

// Frontend-specific types
interface NodeData {
  id: string;
  type: 'crew' | 'agent' | 'tool';
  data: Crew | Agent | Tool;
  position: { x: number; y: number };
}
```

## State Management Architecture

### Context Structure:
```typescript
// Global app context
interface AppState {
  currentCrew: Crew | null;
  crews: Crew[];
  theme: 'light' | 'dark' | 'system';
  settings: AppSettings;
}

// Visual editor context
interface EditorState {
  nodes: Node[];
  edges: Edge[];
  selectedNode: string | null;
  isLoading: boolean;
  lastSaved: Date | null;
}

// Chat context
interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  executionStatus: ExecutionStatus | null;
}
```

### Actions:
```typescript
type AppAction = 
  | { type: 'SET_CURRENT_CREW'; payload: Crew }
  | { type: 'ADD_CREW'; payload: Crew }
  | { type: 'UPDATE_CREW'; payload: Partial<Crew> }
  | { type: 'DELETE_CREW'; payload: string }
  | { type: 'SET_THEME'; payload: Theme };

type EditorAction =
  | { type: 'ADD_NODE'; payload: Node }
  | { type: 'UPDATE_NODE'; payload: { id: string; data: Partial<NodeData> } }
  | { type: 'DELETE_NODE'; payload: string }
  | { type: 'ADD_EDGE'; payload: Edge }
  | { type: 'DELETE_EDGE'; payload: string };
```

## Real-time Features Implementation

### WebSocket Integration:
1. **Execution Monitoring**: Connect to `/ws/executions/{id}` for real-time execution updates
2. **Crew Updates**: Connect to `/ws/crews/{id}` for collaborative editing (future)
3. **Global Events**: Connect to `/ws/global` for system-wide notifications

### SSE for Chat Streaming:
```typescript
// Chat streaming implementation
const streamChatResponse = async (crewId: string, message: string) => {
  const eventSource = new EventSource(`/api/v1/crews/${crewId}/chat/stream`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Update chat state with streaming response
  };
  
  eventSource.onerror = () => {
    // Handle stream errors
    eventSource.close();
  };
};
```

## Component Architecture

### Core Components:
The frontend directory structure should be organized as follows:

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Layout.tsx
│   │   ├── crew-editor/
│   │   │   ├── VisualEditor.tsx
│   │   │   ├── NodeToolbar.tsx
│   │   │   ├── nodes/
│   │   │   │   ├── CrewNode.tsx
│   │   │   │   ├── AgentNode.tsx
│   │   │   │   └── ToolNode.tsx
│   │   │   └── panels/
│   │   │       ├── NodePropertiesPanel.tsx
│   │   │       └── ToolsPanel.tsx
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── ExecutionStatus.tsx
│   │   ├── settings/
│   │   │   ├── SettingsPage.tsx
│   │   │   ├── ThemeSettings.tsx
│   │   │   ├── LLMProviderSettings.tsx
│   │   │   └── ExecutionSettings.tsx
│   │   └── common/
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorBoundary.tsx
│   │       └── ConfirmDialog.tsx
│   ├── contexts/
│   │   ├── AppContext.tsx
│   │   ├── EditorContext.tsx
│   │   └── ChatContext.tsx
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useSSE.ts
│   │   ├── useChatHistory.ts
│   │   └── useCrewExecution.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── chatHistory.ts
│   ├── types/
│   │   ├── crew.ts
│   │   ├── agent.ts
│   │   ├── chat.ts
│   │   └── api.ts
│   └── utils/
│       ├── theme.ts
│       ├── validation.ts
│       └── constants.ts
├── public/
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Key Implementation Requirements

### Visual Editor Behavior:
1. **Dynamic vs Manual Toggle**: 
   - Show confirmation dialog when switching from Manual to Dynamic
   - Automatically delete non-manager agents when confirmed
   - Preserve manager agent and crew configuration

2. **Manager Agent Linking**:
   - Visual indicator when agent becomes manager
   - Hide/show fields based on manager status
   - Update node appearance and title

3. **Node Addition**:
   - Implement both toolbar and inline addition methods
   - Provide visual feedback for available connection points
   - Auto-position new nodes intelligently

### Error Handling:
- Implement comprehensive error boundaries
- Show user-friendly error messages
- Provide retry mechanisms for failed operations
- Handle offline scenarios gracefully

### Performance Optimization:
- Implement virtual scrolling for large crew lists
- Lazy load crew data and chat history
- Debounce autosave operations
- Optimize React Flow rendering for large diagrams

### Accessibility:
- Keyboard navigation support
- Screen reader compatibility
- High contrast theme support
- Focus management for modal dialogs

## Development Setup

### Project Structure:
Create the React project in the `frontend` directory as the root of the frontend application:

```powershell
# From the main project root (d:\Dev\RevAI\CrewAI-4\)
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install @heroui/react tailwindcss @tailwindcss/typography
npm install reactflow lucide-react
npm install axios @tanstack/react-query
npm install react-router-dom@6
npm install @types/node
# Install testing dependencies
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom
npm install --save-dev @playwright/test
```

## Technology Stack
- **Framework**: React 18+ with Vite
- **Language**: TypeScript with strict type safety
- **Routing**: React Router v6
- **Styling**: Tailwind CSS
- **UI Components**: HeroUI (NextUI)
- **State Management**: React Context + useReducer
- **Visual Editor**: React Flow
- **HTTP Client**: Axios with React Query for caching
- **Real-time**: Server-Sent Events (SSE) for streaming, WebSockets for real-time updates
- **Icons**: Lucide React or HeroIcons

## Development Environment
- **Operating System**: Windows
- **Shell**: PowerShell (pwsh.exe)
- **Node.js**: Version 18+ recommended
- **Package Manager**: npm (included with Node.js)

## Testing Framework Requirements

### Test Organization Structure:
```
frontend/src/__tests__/
├── unit/
│   ├── components/           # Component unit tests
│   ├── hooks/               # Custom hook tests
│   ├── services/            # API service tests
│   └── utils/               # Utility function tests
├── integration/
│   ├── api/                 # API integration tests
│   ├── websocket/           # WebSocket connection tests
│   ├── state/               # State management tests
│   └── workflows/           # Multi-component workflows
├── e2e/
│   ├── crew-creation/       # Complete crew creation flows
│   ├── chat-interface/      # Chat functionality tests
│   ├── visual-editor/       # Visual editor interactions
│   └── settings/            # Settings management tests
└── performance/
    ├── rendering/           # Component rendering performance
    ├── memory/              # Memory usage tests
    └── load-testing/        # Load testing scenarios
```

### Testing Tools:
- **Unit/Integration**: Vitest + React Testing Library
- **E2E**: Playwright
- **Performance**: Lighthouse CI
- **Coverage**: c8 (built into Vitest)

### Test Requirements per Phase:
Each phase must achieve:
- **100% test success rate** (no failing tests)
- **Minimum 80% code coverage** for new code
- **All E2E scenarios pass** for implemented features
- **Performance benchmarks met** (load times < 2s)

## Phase Implementation Guidelines

### Development Workflow:
1. **Write tests first** (TDD approach)
2. **Implement minimum viable feature**
3. **Refactor and optimize**
4. **Ensure all tests pass**
5. **Get user approval**
6. **Proceed to next phase**

### Inter-Phase Dependencies:
- Each phase builds upon the previous
- No skipping phases allowed
- Critical bugs must be fixed before proceeding
- Performance regressions block phase completion

### Docker Integration Notes:
- Development environment should mirror production
- Use Docker Compose for local development
- Environment variables properly configured
- Health checks implemented for all services

This prompt provides a comprehensive foundation for building a modern, feature-rich React frontend that integrates seamlessly with the CrewAI backend through a structured, test-driven development approach with proper Docker integration.

## Core Features Overview

### 1. Visual Crew Creation Interface
Build a node-based visual editor using React Flow that allows users to create and configure crews through drag-and-drop interactions.

#### Node Types:
1. **Crew Node** (Default, non-deletable)
   - Always present when creating/editing a crew
   - Contains crew-level configuration: name, description, verbose mode
   - Toggle for Manual vs Dynamic crew type
   - When switching from Manual to Dynamic: Show alert dialog warning that all agents (except manager) will be deleted

2. **Agent Nodes** (User-addable)
   - Standard fields: role, goal, backstory, tools, llm_provider
   - When linked as manager agent: Hide role, goal, backstory fields and change node title to "Manager Agent"
   - When unlinked from manager: Show all fields again
   - Visual connection points for tools and manager relationships

3. **Tool Nodes** (User-addable)
   - Represent tools from the backend tool registry
   - Display tool name, description, and configuration options
   - Connect to agent nodes to assign tools

#### Adding Nodes:
Implement **dual addition methods** for all addable nodes:
1. **Toolbar buttons** at the top of the visual editor container
2. **Inline '+' buttons** next to fields that require nodes (e.g., "+ Add Tool" next to agent's tools field)

#### Data Persistence:
- **Immediate save**: Every user action (node creation, deletion, field changes, connections) should immediately save to backend
- Use crew/agent CRUD endpoints for persistence
- Implement optimistic updates with error handling

### 2. Chat Interface
Create a modern chat interface for interacting with crews.

#### Features:
- **Message Input**: Textarea with send button
- **Streaming Responses**: Use Server-Sent Events (SSE) for real-time message streaming
- **Message History**: Display conversation history with crew
- **Execution Status**: Show crew execution progress and status
- **Message Types**: Support text messages and system notifications

#### Chat History Adapter:
Create an adapter pattern for chat history storage:
```typescript
interface ChatHistoryAdapter {
  saveMessage(crewId: string, message: Message): Promise<void>;
  getMessages(crewId: string): Promise<Message[]>;
  clearHistory(crewId: string): Promise<void>;
}

// Initial implementation using localStorage
class LocalStorageChatAdapter implements ChatHistoryAdapter {
  // Implementation for localStorage with future database migration path
}
```

### 3. Layout & Navigation

#### Sidebar:
- **Crew List**: Display all user crews with creation dates
- **Conversation History**: Show recent conversations per crew
- **Theme Toggle**: Dark/Light/System theme support
- **Settings Access**: Navigate to settings page

#### Crew Selection:
- Clicking a crew in sidebar sets it as current crew
- Loads associated chat history
- Navigates to chat interface for that crew
- Updates URL for deep linking

#### Main Content Area:
- **Visual Editor Tab**: Crew configuration interface
- **Chat Tab**: Conversation interface with selected crew
- **Execution Tab**: Real-time execution monitoring

### 4. Settings Page
Comprehensive configuration options:

#### Sections:
1. **Appearance**
   - Theme selection (Dark/Light/System)
   - UI density options
   - Color scheme preferences

2. **LLM Providers**
   - Configure available LLM providers
   - API key management
   - Default provider selection

3. **Execution**
   - Default execution parameters
   - Timeout settings
   - Verbose mode preferences

4. **Data & Storage**
   - Chat history management
   - Export/import crew configurations
   - Clear application data

## Backend Integration

### API Endpoints
Integrate with existing CrewAI backend endpoints:

#### Core CRUD:
- `GET/POST/PUT/DELETE /api/v1/crews/` - Crew management
- `GET/POST/PUT/DELETE /api/v1/agents/` - Agent management
- `GET /api/v1/tools/` - Available tools registry
- `GET /api/v1/llm-providers/` - LLM provider management

#### Execution:
- `POST /api/v1/crews/{crew_id}/execute` - Execute crew
- `GET /api/v1/crews/{crew_id}/execution-status` - Check execution status

#### Real-time Features:
- **WebSocket Connections**: `/ws/executions/{execution_id}`, `/ws/crews/{crew_id}`, `/ws/global`
- **SSE Streaming**: For chat message streaming during crew execution

### Type Safety
Generate TypeScript types from backend schemas:

```typescript
// Base types from backend models
interface Crew {
  id: string;
  name: string;
  description?: string;
  is_dynamic: boolean;
  manager_agent_id?: string;
  verbose: boolean;
  agents: Agent[];
  created_at: string;
  updated_at: string;
}

interface Agent {
  id: string;
  crew_id: string;
  role: string;
  goal: string;
  backstory: string;
  tools: string[];
  llm_provider?: string;
  is_manager: boolean;
}

// Frontend-specific types
interface NodeData {
  id: string;
  type: 'crew' | 'agent' | 'tool';
  data: Crew | Agent | Tool;
  position: { x: number; y: number };
}
```

## State Management Architecture

### Context Structure:
```typescript
// Global app context
interface AppState {
  currentCrew: Crew | null;
  crews: Crew[];
  theme: 'light' | 'dark' | 'system';
  settings: AppSettings;
}

// Visual editor context
interface EditorState {
  nodes: Node[];
  edges: Edge[];
  selectedNode: string | null;
  isLoading: boolean;
  lastSaved: Date | null;
}

// Chat context
interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  executionStatus: ExecutionStatus | null;
}
```

### Actions:
```typescript
type AppAction = 
  | { type: 'SET_CURRENT_CREW'; payload: Crew }
  | { type: 'ADD_CREW'; payload: Crew }
  | { type: 'UPDATE_CREW'; payload: Partial<Crew> }
  | { type: 'DELETE_CREW'; payload: string }
  | { type: 'SET_THEME'; payload: Theme };

type EditorAction =
  | { type: 'ADD_NODE'; payload: Node }
  | { type: 'UPDATE_NODE'; payload: { id: string; data: Partial<NodeData> } }
  | { type: 'DELETE_NODE'; payload: string }
  | { type: 'ADD_EDGE'; payload: Edge }
  | { type: 'DELETE_EDGE'; payload: string };
```

## Real-time Features Implementation

### WebSocket Integration:
1. **Execution Monitoring**: Connect to `/ws/executions/{id}` for real-time execution updates
2. **Crew Updates**: Connect to `/ws/crews/{id}` for collaborative editing (future)
3. **Global Events**: Connect to `/ws/global` for system-wide notifications

### SSE for Chat Streaming:
```typescript
// Chat streaming implementation
const streamChatResponse = async (crewId: string, message: string) => {
  const eventSource = new EventSource(`/api/v1/crews/${crewId}/chat/stream`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Update chat state with streaming response
  };
  
  eventSource.onerror = () => {
    // Handle stream errors
    eventSource.close();
  };
};
```

## Component Architecture

### Core Components:
The frontend directory structure should be organized as follows:

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Layout.tsx
│   │   ├── crew-editor/
│   │   │   ├── VisualEditor.tsx
│   │   │   ├── NodeToolbar.tsx
│   │   │   ├── nodes/
│   │   │   │   ├── CrewNode.tsx
│   │   │   │   ├── AgentNode.tsx
│   │   │   │   └── ToolNode.tsx
│   │   │   └── panels/
│   │   │       ├── NodePropertiesPanel.tsx
│   │   │       └── ToolsPanel.tsx
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── ExecutionStatus.tsx
│   │   ├── settings/
│   │   │   ├── SettingsPage.tsx
│   │   │   ├── ThemeSettings.tsx
│   │   │   ├── LLMProviderSettings.tsx
│   │   │   └── ExecutionSettings.tsx
│   │   └── common/
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorBoundary.tsx
│   │       └── ConfirmDialog.tsx
│   ├── contexts/
│   │   ├── AppContext.tsx
│   │   ├── EditorContext.tsx
│   │   └── ChatContext.tsx
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useSSE.ts
│   │   ├── useChatHistory.ts
│   │   └── useCrewExecution.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── chatHistory.ts
│   ├── types/
│   │   ├── crew.ts
│   │   ├── agent.ts
│   │   ├── chat.ts
│   │   └── api.ts
│   └── utils/
│       ├── theme.ts
│       ├── validation.ts
│       └── constants.ts
├── public/
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Key Implementation Requirements

### Visual Editor Behavior:
1. **Dynamic vs Manual Toggle**: 
   - Show confirmation dialog when switching from Manual to Dynamic
   - Automatically delete non-manager agents when confirmed
   - Preserve manager agent and crew configuration

2. **Manager Agent Linking**:
   - Visual indicator when agent becomes manager
   - Hide/show fields based on manager status
   - Update node appearance and title

3. **Node Addition**:
   - Implement both toolbar and inline addition methods
   - Provide visual feedback for available connection points
   - Auto-position new nodes intelligently

### Error Handling:
- Implement comprehensive error boundaries
- Show user-friendly error messages
- Provide retry mechanisms for failed operations
- Handle offline scenarios gracefully

### Performance Optimization:
- Implement virtual scrolling for large crew lists
- Lazy load crew data and chat history
- Debounce autosave operations
- Optimize React Flow rendering for large diagrams

### Accessibility:
- Keyboard navigation support
- Screen reader compatibility
- High contrast theme support
- Focus management for modal dialogs

## Development Setup

### Project Structure:
Create the React project in the `frontend` directory as the root of the frontend application:

```bash
# From the main project root (d:\Dev\RevAI\CrewAI-4\)
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install @heroui/react tailwindcss @tailwindcss/typography
npm install reactflow lucide-react
npm install axios @tanstack/react-query
npm install @types/node
```

### Environment Configuration:
```typescript
// frontend/src/config/env.ts
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  wsBaseUrl: import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000',
  environment: import.meta.env.MODE,
} as const;
```

### Project Root Structure:
After setup, your project structure will be:
```
d:\Dev\RevAI\CrewAI-4\
├── backend/           # Existing CrewAI backend
├── frontend/          # New React frontend (project root)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
├── docker/
└── phase-summaries/
```

### Deployment Considerations:
- Build optimized production bundles
- Configure environment variables for different deployment stages
- Implement proper error logging and monitoring
- Set up CI/CD pipelines for automated testing and deployment

## Core Features

### 1. Visual Crew Creation Interface
Build a node-based visual editor using React Flow that allows users to create and configure crews through drag-and-drop interactions.

#### Node Types:
1. **Crew Node** (Default, non-deletable)
   - Always present when creating/editing a crew
   - Contains crew-level configuration: name, description, verbose mode
   - Toggle for Manual vs Dynamic crew type
   - When switching from Manual to Dynamic: Show alert dialog warning that all agents (except manager) will be deleted

2. **Agent Nodes** (User-addable)
   - Standard fields: role, goal, backstory, tools, llm_provider
   - When linked as manager agent: Hide role, goal, backstory fields and change node title to "Manager Agent"
   - When unlinked from manager: Show all fields again
   - Visual connection points for tools and manager relationships

3. **Tool Nodes** (User-addable)
   - Represent tools from the backend tool registry
   - Display tool name, description, and configuration options
   - Connect to agent nodes to assign tools

#### Adding Nodes:
Implement **dual addition methods** for all addable nodes:
1. **Toolbar buttons** at the top of the visual editor container
2. **Inline '+' buttons** next to fields that require nodes (e.g., "+ Add Tool" next to agent's tools field)

#### Data Persistence:
- **Immediate save**: Every user action (node creation, deletion, field changes, connections) should immediately save to backend
- Use crew/agent CRUD endpoints for persistence
- Implement optimistic updates with error handling

### 2. Chat Interface
Create a modern chat interface for interacting with crews.

#### Features:
- **Message Input**: Textarea with send button
- **Streaming Responses**: Use Server-Sent Events (SSE) for real-time message streaming
- **Message History**: Display conversation history with crew
- **Execution Status**: Show crew execution progress and status
- **Message Types**: Support text messages and system notifications

#### Chat History Adapter:
Create an adapter pattern for chat history storage:
```typescript
interface ChatHistoryAdapter {
  saveMessage(crewId: string, message: Message): Promise<void>;
  getMessages(crewId: string): Promise<Message[]>;
  clearHistory(crewId: string): Promise<void>;
}

// Initial implementation using localStorage
class LocalStorageChatAdapter implements ChatHistoryAdapter {
  // Implementation for localStorage with future database migration path
}
```

### 3. Layout & Navigation

#### Sidebar:
- **Crew List**: Display all user crews with creation dates
- **Conversation History**: Show recent conversations per crew
- **Theme Toggle**: Dark/Light/System theme support
- **Settings Access**: Navigate to settings page

#### Crew Selection:
- Clicking a crew in sidebar sets it as current crew
- Loads associated chat history
- Navigates to chat interface for that crew
- Updates URL for deep linking

#### Main Content Area:
- **Visual Editor Tab**: Crew configuration interface
- **Chat Tab**: Conversation interface with selected crew
- **Execution Tab**: Real-time execution monitoring

### 4. Settings Page
Comprehensive configuration options:

#### Sections:
1. **Appearance**
   - Theme selection (Dark/Light/System)
   - UI density options
   - Color scheme preferences

2. **LLM Providers**
   - Configure available LLM providers
   - API key management
   - Default provider selection

3. **Execution**
   - Default execution parameters
   - Timeout settings
   - Verbose mode preferences

4. **Data & Storage**
   - Chat history management
   - Export/import crew configurations
   - Clear application data

## Backend Integration

### API Endpoints
Integrate with existing CrewAI backend endpoints:

#### Core CRUD:
- `GET/POST/PUT/DELETE /api/v1/crews/` - Crew management
- `GET/POST/PUT/DELETE /api/v1/agents/` - Agent management
- `GET /api/v1/tools/` - Available tools registry
- `GET /api/v1/llm-providers/` - LLM provider management

#### Execution:
- `POST /api/v1/crews/{crew_id}/execute` - Execute crew
- `GET /api/v1/crews/{crew_id}/execution-status` - Check execution status

#### Real-time Features:
- **WebSocket Connections**: `/ws/executions/{execution_id}`, `/ws/crews/{crew_id}`, `/ws/global`
- **SSE Streaming**: For chat message streaming during crew execution

### Type Safety
Generate TypeScript types from backend schemas:

```typescript
// Base types from backend models
interface Crew {
  id: string;
  name: string;
  description?: string;
  is_dynamic: boolean;
  manager_agent_id?: string;
  verbose: boolean;
  agents: Agent[];
  created_at: string;
  updated_at: string;
}

interface Agent {
  id: string;
  crew_id: string;
  role: string;
  goal: string;
  backstory: string;
  tools: string[];
  llm_provider?: string;
  is_manager: boolean;
}

// Frontend-specific types
interface NodeData {
  id: string;
  type: 'crew' | 'agent' | 'tool';
  data: Crew | Agent | Tool;
  position: { x: number; y: number };
}
```

## State Management Architecture

### Context Structure:
```typescript
// Global app context
interface AppState {
  currentCrew: Crew | null;
  crews: Crew[];
  theme: 'light' | 'dark' | 'system';
  settings: AppSettings;
}

// Visual editor context
interface EditorState {
  nodes: Node[];
  edges: Edge[];
  selectedNode: string | null;
  isLoading: boolean;
  lastSaved: Date | null;
}

// Chat context
interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  executionStatus: ExecutionStatus | null;
}
```

### Actions:
```typescript
type AppAction = 
  | { type: 'SET_CURRENT_CREW'; payload: Crew }
  | { type: 'ADD_CREW'; payload: Crew }
  | { type: 'UPDATE_CREW'; payload: Partial<Crew> }
  | { type: 'DELETE_CREW'; payload: string }
  | { type: 'SET_THEME'; payload: Theme };

type EditorAction =
  | { type: 'ADD_NODE'; payload: Node }
  | { type: 'UPDATE_NODE'; payload: { id: string; data: Partial<NodeData> } }
  | { type: 'DELETE_NODE'; payload: string }
  | { type: 'ADD_EDGE'; payload: Edge }
  | { type: 'DELETE_EDGE'; payload: string };
```

## Real-time Features Implementation

### WebSocket Integration:
1. **Execution Monitoring**: Connect to `/ws/executions/{id}` for real-time execution updates
2. **Crew Updates**: Connect to `/ws/crews/{id}` for collaborative editing (future)
3. **Global Events**: Connect to `/ws/global` for system-wide notifications

### SSE for Chat Streaming:
```typescript
// Chat streaming implementation
const streamChatResponse = async (crewId: string, message: string) => {
  const eventSource = new EventSource(`/api/v1/crews/${crewId}/chat/stream`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Update chat state with streaming response
  };
  
  eventSource.onerror = () => {
    // Handle stream errors
    eventSource.close();
  };
};
```

## Component Architecture

### Core Components:
The frontend directory structure should be organized as follows:

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Layout.tsx
│   │   ├── crew-editor/
│   │   │   ├── VisualEditor.tsx
│   │   │   ├── NodeToolbar.tsx
│   │   │   ├── nodes/
│   │   │   │   ├── CrewNode.tsx
│   │   │   │   ├── AgentNode.tsx
│   │   │   │   └── ToolNode.tsx
│   │   │   └── panels/
│   │   │       ├── NodePropertiesPanel.tsx
│   │   │       └── ToolsPanel.tsx
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── ExecutionStatus.tsx
│   │   ├── settings/
│   │   │   ├── SettingsPage.tsx
│   │   │   ├── ThemeSettings.tsx
│   │   │   ├── LLMProviderSettings.tsx
│   │   │   └── ExecutionSettings.tsx
│   │   └── common/
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorBoundary.tsx
│   │       └── ConfirmDialog.tsx
│   ├── contexts/
│   │   ├── AppContext.tsx
│   │   ├── EditorContext.tsx
│   │   └── ChatContext.tsx
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useSSE.ts
│   │   ├── useChatHistory.ts
│   │   └── useCrewExecution.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── chatHistory.ts
│   ├── types/
│   │   ├── crew.ts
│   │   ├── agent.ts
│   │   ├── chat.ts
│   │   └── api.ts
│   └── utils/
│       ├── theme.ts
│       ├── validation.ts
│       └── constants.ts
├── public/
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Key Implementation Requirements

### Visual Editor Behavior:
1. **Dynamic vs Manual Toggle**: 
   - Show confirmation dialog when switching from Manual to Dynamic
   - Automatically delete non-manager agents when confirmed
   - Preserve manager agent and crew configuration

2. **Manager Agent Linking**:
   - Visual indicator when agent becomes manager
   - Hide/show fields based on manager status
   - Update node appearance and title

3. **Node Addition**:
   - Implement both toolbar and inline addition methods
   - Provide visual feedback for available connection points
   - Auto-position new nodes intelligently

### Error Handling:
- Implement comprehensive error boundaries
- Show user-friendly error messages
- Provide retry mechanisms for failed operations
- Handle offline scenarios gracefully

### Performance Optimization:
- Implement virtual scrolling for large crew lists
- Lazy load crew data and chat history
- Debounce autosave operations
- Optimize React Flow rendering for large diagrams

### Accessibility:
- Keyboard navigation support
- Screen reader compatibility
- High contrast theme support
- Focus management for modal dialogs

## Development Setup

### Project Structure:
Create the React project in the `frontend` directory as the root of the frontend application:

```bash
# From the main project root (d:\Dev\RevAI\CrewAI-4\)
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install @heroui/react tailwindcss @tailwindcss/typography
npm install reactflow lucide-react
npm install axios @tanstack/react-query
npm install @types/node
```

### Environment Configuration:
```typescript
// frontend/src/config/env.ts
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  wsBaseUrl: import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000',
  environment: import.meta.env.MODE,
} as const;
```

### Project Root Structure:
After setup, your project structure will be:
```
d:\Dev\RevAI\CrewAI-4\
├── backend/           # Existing CrewAI backend
├── frontend/          # New React frontend (project root)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
├── docker/
└── phase-summaries/
```

### Deployment Considerations:
- Build optimized production bundles
- Configure environment variables for different deployment stages
- Implement proper error logging and monitoring
- Set up CI/CD pipelines for automated testing and deployment

## Testing Strategy

### Unit Tests:
- Test all custom hooks
- Test state management reducers
- Test utility functions and API services

### Integration Tests:
- Test WebSocket connections
- Test chat streaming functionality
- Test visual editor interactions

### E2E Tests:
- Test complete crew creation workflow
- Test chat conversations
- Test settings management

This prompt provides a comprehensive foundation for building a modern, feature-rich React frontend that integrates seamlessly with the CrewAI backend while providing an excellent user experience for crew creation and management.
