# CrewAI Chat Feature Development - AI Agent Task Brief

## Project Context
You are implementing a chat feature for the CrewAI Graph Builder application. This feature will allow users to interact with their CrewAI graphs through a conversational interface, where messages trigger CrewAI execution and stream responses in real-time.

## Compliance Requirements
This development MUST follow the AI Coding Agent Policy. All work requires:
- Task-driven development with agreed-upon authorizing tasks
- PBI association for all tasks
- Proper documentation structure in `docs/delivery/`
- Status synchronization between index and individual task files
- External package research with guide creation

## Product Backlog Item (PBI)

### PBI-003: Chat Interface with CrewAI Integration

**User Story**: As a user, I need a chat interface that allows me to communicate with my CrewAI graphs through natural language messages, so that I can interact with my crews conversationally and receive streamed responses in real-time.

**Status**: Proposed → (awaiting User approval to move to Agreed)

**Conditions of Satisfaction**:
1. Thread management system for organizing conversations per graph
2. Single crew restriction per graph for chat functionality
3. HTTP streaming response system (no SSE) for real-time chat
4. CrewAI integration that translates graph data to executable crews
5. Dynamic task creation from chat messages with optional output specification
6. Message persistence with execution linking and status tracking
7. Comprehensive error handling for graph validation and crew execution
8. Frontend chat interface with thread navigation and message streaming
9. Access control ensuring users can only chat with their own graphs
10. Protection against concurrent crew executions for the same graph
11. Database transaction management during streaming operations
12. Complete chat UI components with modern design patterns

## Technical Stack Requirements
- **Backend**: FastAPI with streaming responses
- **Frontend**: React with TypeScript, Zustand state management
- **Database**: PostgreSQL with existing models (Thread, Message, Graph, Execution)
- **Integration**: Existing GraphTranslationService for CrewAI object creation
- **Streaming**: HTTP streaming (text/event-stream) without SSE infrastructure
- **Authentication**: JWT tokens with existing auth system
- **UI Components**: Existing UI component library (shadcn/ui)
- **Location**: Extends existing `backend/` and `frontend/` directories

## Current Architecture Analysis

### Backend Current State

**Models:**
- `Thread` model exists with relationships to `Graph` and `Message`
- `Message` model exists with support for different types and statuses
- `Graph` model contains `graph_data` JSON field with nodes and edges
- Message processing service exists in `backend/services/message_processing_service.py`
- Graph translation service exists in `backend/services/graph_translation.py`

**APIs:**
- Message endpoints: `/api/messages/` (CRUD operations)
- Graph endpoints: `/api/graphs/` (existing graph management)
- **Missing:** Thread management endpoints
- **Missing:** Streaming chat endpoints

**Existing Features:**
- User authentication and authorization
- Message creation and retrieval
- Graph-thread relationships
- CrewAI object translation from graph data

### Frontend Current State

**Architecture:**
- React with TypeScript
- Zustand for state management
- React Router for navigation
- Axios for API communication
- Sidebar-based navigation with content switching

**Current Routes:**
- `/` - Dashboard
- `/graphs` - Graph listing
- `/graphs/:id` - Graph editor

**Missing Components:**
- Chat interface components
- Thread management
- HTTP streaming response handling
- Chat routes

## Task Breakdown Strategy

The PBI will be broken into minimal, testable tasks following these categories:

### Phase 1: Infrastructure Cleanup (Tasks 3-1 through 3-2)
1. **3-1**: Remove existing SSE infrastructure if present
2. **3-2**: Validate existing models (Thread, Message, Graph, Execution) compatibility

### Phase 2: Backend Thread Management (Tasks 3-3 through 3-8)
3. **3-3**: Thread schemas implementation (Create, Update, List responses)
4. **3-4**: Complete ThreadService with CRUD operations and validation
5. **3-5**: Thread router with all endpoints and error handling
6. **3-6**: Single crew per graph validation service
7. **3-7**: Execution protection (prevent concurrent crew runs)
8. **3-8**: Thread management testing suite

### Phase 3: CrewAI Chat Integration (Tasks 3-9 through 3-14)
9. **3-9**: Chat message schema and request/response models
10. **3-10**: Chat streaming endpoint with CrewAI integration
11. **3-11**: Dynamic task creation from messages with output specification
12. **3-12**: Execution record management during streaming
13. **3-13**: Error handling for graph translation and crew execution
14. **3-14**: Chat backend integration testing

### Phase 4: Frontend Chat Foundation (Tasks 3-15 through 3-20)
15. **3-15**: Chat types and interfaces definition
16. **3-16**: Chat store implementation with Zustand
17. **3-17**: Chat service with HTTP streaming support
18. **3-18**: Chat routes and router configuration
19. **3-19**: Single crew restriction on frontend
20. **3-20**: Frontend error handling and validation

### Phase 5: Chat UI Components (Tasks 3-21 through 3-26)
21. **3-21**: Chat layout and structure components
22. **3-22**: Thread sidebar with navigation and creation
23. **3-23**: Message list and message input components
24. **3-24**: Chat header and welcome screen
25. **3-25**: Streaming message handling and real-time updates
26. **3-26**: UI component testing and validation

### Phase 6: Navigation Integration (Tasks 3-27 through 3-30)
27. **3-27**: Sidebar navigation updates for chat access
28. **3-28**: Graph editor chat entry points
29. **3-29**: Route transitions and state management
30. **3-30**: Navigation testing and user flow validation

### Phase 7: Testing & Documentation (Tasks 3-31 through 3-35)
31. **3-31**: Backend unit tests for thread service and chat endpoints
32. **3-32**: Frontend component and integration tests
33. **3-33**: End-to-end chat flow testing
34. **3-34**: Performance testing for streaming responses
35. **3-35**: E2E CoS Test for complete PBI verification

## Implementation Details

### Phase 1: Infrastructure Cleanup

**Important:** Since the current codebase may contain SSE implementation, remove it to avoid conflicts:

#### Task 3-1: Remove Existing SSE Infrastructure
- Remove or disable `backend/routers/sse.py` endpoints
- Remove SSE service usage from message processing
- Update `main.py` to remove SSE router registration:
```python
# Remove this line if present:
# app.include_router(sse_router, prefix="/api")
```
- Remove any SSE connection handling from existing components
- Remove SSE-related state management if present
- Ensure no EventSource usage in the codebase

### Phase 2: Backend Thread Management API

#### 1.1 Create Thread Router (`backend/routers/threads.py`)

```python
"""
Thread management router for conversation handling
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from models.user import User
from models.thread import Thread, ThreadStatus
from models.graph import Graph
from schemas.thread_schemas import (
    ThreadCreateRequest, ThreadResponse, ThreadListResponse, 
    ThreadUpdateRequest
)
from services.thread_service import ThreadService
from utils.dependencies import get_current_user, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/threads", tags=["Threads"])

@router.post("/", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    request: ThreadCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreadResponse:
    """Create a new thread for a graph"""
    try:
        service = ThreadService(db)
        thread = service.create_thread(
            graph_id=request.graph_id,
            user_id=str(current_user.id),
            name=request.name,
            description=request.description,
            thread_config=request.thread_config
        )
        
        return ThreadResponse.from_orm(thread)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create thread: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                          detail="Failed to create thread")

@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreadResponse:
    """Get a specific thread by ID"""
    try:
        service = ThreadService(db)
        thread = service.get_thread(thread_id, str(current_user.id))
        
        if not thread:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                              detail="Thread not found")
        
        return ThreadResponse.from_orm(thread)
        
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get thread {thread_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Failed to retrieve thread")

@router.get("/graph/{graph_id}", response_model=ThreadListResponse)
async def get_graph_threads(
    graph_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreadListResponse:
    """Get all threads for a specific graph"""
    try:
        service = ThreadService(db)
        threads = service.get_graph_threads(graph_id, str(current_user.id))
        
        thread_responses = [ThreadResponse.from_orm(thread) for thread in threads]
        
        return ThreadListResponse(
            threads=thread_responses,
            total=len(thread_responses),
            graph_id=graph_id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get threads for graph {graph_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Failed to retrieve threads")

@router.put("/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: str,
    request: ThreadUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreadResponse:
    """Update a thread"""
    try:
        service = ThreadService(db)
        thread = service.update_thread(
            thread_id=thread_id,
            user_id=str(current_user.id),
            name=request.name,
            description=request.description,
            status=ThreadStatus(request.status) if request.status else None,
            thread_config=request.thread_config
        )
        
        return ThreadResponse.from_orm(thread)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update thread {thread_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Failed to update thread")

@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a thread (soft delete)"""
    try:
        service = ThreadService(db)
        success = service.delete_thread(thread_id, str(current_user.id))
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail="Thread not found")
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete thread {thread_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Failed to delete thread")
```

#### 1.2 Create Thread Schemas (`backend/schemas/thread_schemas.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ThreadStatusSchema(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class ThreadCreateRequest(BaseModel):
    graph_id: str = Field(..., description="Graph ID")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    thread_config: Optional[Dict[str, Any]] = None

class ThreadUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[ThreadStatusSchema] = None
    thread_config: Optional[Dict[str, Any]] = None

class ThreadResponse(BaseModel):
    id: str
    graph_id: str
    name: str
    description: Optional[str]
    status: ThreadStatusSchema
    thread_config: Optional[Dict[str, Any]]
    last_activity_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True

class ThreadListResponse(BaseModel):
    threads: List[ThreadResponse]
    total: int
    graph_id: str
```

#### 1.3 Create Thread Service (`backend/services/thread_service.py`)

```python
"""
Thread management service for conversation handling
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime

from models.thread import Thread, ThreadStatus
from models.graph import Graph
from models.message import Message
from models.execution import Execution

logger = logging.getLogger(__name__)

class ThreadService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_thread(self, graph_id: str, user_id: str, name: str, 
                     description: Optional[str] = None,
                     thread_config: Optional[Dict[str, Any]] = None) -> Thread:
        """Create a new thread"""
        try:
            # Validate graph access
            graph = self._validate_graph_access(graph_id, user_id)
            
            # Validate graph has only one crew (restriction)
            self._validate_single_crew_graph(graph)
            
            thread = Thread(
                id=str(uuid4()),
                graph_id=graph_id,
                name=name,
                description=description,
                status=ThreadStatus.ACTIVE,
                thread_config=thread_config or {}
            )
            
            self.db.add(thread)
            self.db.commit()
            self.db.refresh(thread)
            
            logger.info(f"Created thread {thread.id} for graph {graph_id}")
            return thread
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create thread: {e}")
            raise
    
    def get_thread(self, thread_id: str, user_id: str) -> Optional[Thread]:
        """Get a specific thread by ID"""
        thread = self.db.query(Thread).filter(Thread.id == thread_id).first()
        
        if not thread:
            return None
            
        # Validate user access through graph ownership
        if not thread.can_be_accessed_by(user_id):
            raise PermissionError(f"User {user_id} cannot access thread {thread_id}")
            
        return thread
    
    def get_graph_threads(self, graph_id: str, user_id: str) -> List[Thread]:
        """Get all threads for a graph"""
        # Validate graph access first
        self._validate_graph_access(graph_id, user_id)
        
        threads = self.db.query(Thread).filter(
            and_(
                Thread.graph_id == graph_id,
                Thread.status != ThreadStatus.DELETED
            )
        ).order_by(Thread.updated_at.desc()).all()
        
        # Add message count to each thread
        for thread in threads:
            message_count = self.db.query(func.count(Message.id)).filter(
                Message.thread_id == thread.id
            ).scalar()
            thread.message_count = message_count or 0
            
        return threads
    
    def update_thread(self, thread_id: str, user_id: str, 
                     name: Optional[str] = None,
                     description: Optional[str] = None,
                     status: Optional[ThreadStatus] = None,
                     thread_config: Optional[Dict[str, Any]] = None) -> Thread:
        """Update a thread"""
        try:
            thread = self.get_thread(thread_id, user_id)
            if not thread:
                raise ValueError(f"Thread {thread_id} not found")
            
            # Update fields if provided
            if name is not None:
                thread.name = name
            if description is not None:
                thread.description = description
            if status is not None:
                thread.set_status(status)
            if thread_config is not None:
                thread.set_thread_config(thread_config)
            
            thread.update_last_activity()
            self.db.commit()
            self.db.refresh(thread)
            
            logger.info(f"Updated thread {thread_id}")
            return thread
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update thread {thread_id}: {e}")
            raise
    
    def delete_thread(self, thread_id: str, user_id: str) -> bool:
        """Soft delete a thread"""
        try:
            thread = self.get_thread(thread_id, user_id)
            if not thread:
                raise ValueError(f"Thread {thread_id} not found")
            
            thread.soft_delete()
            self.db.commit()
            
            logger.info(f"Deleted thread {thread_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete thread {thread_id}: {e}")
            raise
    
    def is_crew_executing(self, graph_id: str) -> bool:
        """Check if crew is currently executing for this graph"""
        active_executions = self.db.query(Execution).filter(
            and_(
                Execution.graph_id == graph_id,
                Execution.status.in_(['running', 'pending'])
            )
        ).count()
        
        return active_executions > 0
    
    def _validate_graph_access(self, graph_id: str, user_id: str) -> Graph:
        """Validate user has access to graph"""
        graph = self.db.query(Graph).filter(
            and_(
                Graph.id == graph_id,
                Graph.user_id == user_id,
                Graph.is_active == True
            )
        ).first()
        
        if not graph:
            raise ValueError(f"Graph {graph_id} not found or access denied")
            
        return graph
    
    def _validate_single_crew_graph(self, graph: Graph) -> None:
        """Validate graph has exactly one crew node (placeholder validation)"""
        # TODO: Implement proper graph validation
        # For now, just check if graph_data exists
        if not graph.graph_data:
            raise ValueError("Graph has no data")
        
        nodes = graph.graph_data.get("nodes", [])
        crew_nodes = [n for n in nodes if n.get("type") == "crew"]
        
        if not crew_nodes:
            raise ValueError("Graph must have at least one crew node for chat")
        
        if len(crew_nodes) > 1:
            raise ValueError("Graph can only have one crew node for chat functionality")
        
        # Placeholder for additional validation
        logger.debug(f"Graph {graph.id} validation passed - single crew found")
```

#### 1.4 Create Chat Message Schema

Create chat message request schema:

```python
# Add to backend/schemas/message_schemas.py
class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The message content")
    output: Optional[str] = Field(None, description="Expected output format or constraints")
    threadId: str = Field(..., description="Thread ID for the conversation")
```

#### 1.5 Add Chat Message Endpoint with CrewAI Integration

Create `/api/messages/chat/stream` endpoint:

```python
import json
import logging
from datetime import datetime
from uuid import uuid4
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from models.user import User
from models.thread import Thread
from models.graph import Graph
from models.message import Message, MessageType, MessageStatus
from models.execution import Execution
from services.message_processing_service import MessageProcessingService
from services.graph_translation import GraphTranslationService
from services.thread_service import ThreadService
from schemas.message_schemas import ChatMessageRequest
from utils.dependencies import get_current_user, get_db

logger = logging.getLogger(__name__)

@router.post("/chat/stream")
async def send_chat_message_stream(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """Send chat message and return streaming CrewAI execution response"""
    
    try:
        # Validate thread access
        thread_service = ThreadService(db)
        thread = thread_service.get_thread(request.threadId, str(current_user.id))
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Validate graph access through thread service
        graph = thread_service._validate_graph_access(thread.graph_id, str(current_user.id))
        
        # Check if crew is already executing for this graph
        if thread_service.is_crew_executing(thread.graph_id):
            raise HTTPException(status_code=409, detail="Crew is already executing for this graph")
        
        # Validate graph for chat (single crew restriction)
        thread_service._validate_single_crew_graph(graph)
        
        # Create user message
        with MessageProcessingService(db) as message_service:
            user_message = message_service.create_message(
                thread_id=request.threadId,
                content=request.message,
                user_id=str(current_user.id),
                message_type=MessageType.USER,
                triggers_execution=True
            )
        
        # Create streaming response
        async def generate_stream():
            execution = None
            assistant_message = None
            
            try:
                # Create assistant message placeholder
                assistant_message = message_service.create_message(
                    thread_id=request.threadId,
                    content="",
                    user_id=str(current_user.id),
                    message_type=MessageType.ASSISTANT,
                    triggers_execution=False
                )
                assistant_message.mark_processing()
                
                # Create execution record before starting
                execution = Execution(
                    id=str(uuid4()),
                    graph_id=thread.graph_id,
                    user_id=str(current_user.id),
                    status='running',
                    execution_config={
                        'message': request.message,
                        'output': request.output,
                        'thread_id': request.threadId
                    }
                )
                db.add(execution)
                
                # Link execution to message
                assistant_message.link_execution(execution.id)
                db.commit()
                
                # Translate graph to CrewAI objects
                translation_service = GraphTranslationService(db)
                crew = translation_service.translate_graph(graph)
                
                # Create a new task from the message
                from crewai import Task
                crew_task = Task(
                    description=request.message,
                    expected_output=request.output or "A helpful and detailed response",
                    agent=crew.agents[0] if crew.agents else None
                )
                
                # Add the new task to the crew
                crew.tasks.append(crew_task)
                
                # Execute CrewAI and stream response
                accumulated_content = ""
                async for chunk in execute_crew_stream(crew, execution.id, db):
                    accumulated_content += chunk
                    
                    # Update assistant message
                    assistant_message.content = accumulated_content
                    db.commit()
                    
                    # Stream chunk
                    yield f"data: {json.dumps({'content': chunk, 'message_id': assistant_message.id})}\n\n"
                
                # Mark execution and message as completed
                execution.status = 'completed'
                execution.result_data = {'content': accumulated_content}
                assistant_message.mark_completed()
                db.commit()
                
                yield f"data: {json.dumps({'done': True, 'message_id': assistant_message.id})}\n\n"
                
            except Exception as e:
                logger.error(f"Chat stream error: {e}")
                
                # Mark execution as failed
                if execution:
                    execution.status = 'failed'
                    execution.error_message = str(e)
                
                # Mark assistant message as failed
                if assistant_message:
                    assistant_message.content = f"Error: {str(e)}"
                    assistant_message.mark_failed()
                
                db.commit()
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat message processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

async def execute_crew_stream(crew, execution_id: str, db: Session) -> AsyncGenerator[str, None]:
    """Execute CrewAI crew and yield streaming response chunks"""
    try:
        # Update execution status
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if execution:
            execution.started_at = datetime.utcnow()
            db.commit()
        
        # Execute crew (this is synchronous, but we'll simulate streaming)
        result = crew.kickoff()
        
        # Simulate streaming by yielding chunks of the result
        content = str(result.raw) if hasattr(result, 'raw') else str(result)
        
        # Split content into chunks for streaming effect
        chunk_size = 50
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield chunk
            # Small delay to simulate streaming
            import asyncio
            await asyncio.sleep(0.1)
        
        # Update execution completion
        if execution:
            execution.completed_at = datetime.utcnow()
            db.commit()
            
    except Exception as e:
        # Update execution with error
        if execution:
            execution.error_message = str(e)
            execution.status = 'failed'
            execution.completed_at = datetime.utcnow()
            db.commit()
        
        yield f"Error executing CrewAI: {str(e)}"
```

#### 1.6 Register Thread Router in Main Application

Add to `backend/main.py`:

```python
# Add to imports
from routers.threads import router as threads_router

# Add to router registration
app.include_router(threads_router, prefix="/api")
```

### Phase 2: Frontend Implementation

#### 2.1 Add Chat Routes (`frontend/src/router/routes.ts`)

```typescript
export const ROUTES = {
  // ... existing routes
  GRAPH_CHAT: '/graphs/:id/chat',
  GRAPH_CHAT_THREAD: '/graphs/:id/chat/:threadId',
} as const;

export interface GraphChatParams {
  id: string;
  threadId?: string;
}
```

#### 2.2 Create Chat Types (`frontend/src/types/chat.types.ts`)

```typescript
export interface Thread {
  id: string;
  graph_id: string;
  name: string;
  description?: string;
  status: 'active' | 'archived' | 'deleted';
  thread_config?: Record<string, any>;
  last_activity_at?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: string;
  thread_id: string;
  content: string;
  message_type: 'user' | 'assistant' | 'system' | 'error';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface ChatState {
  threads: Thread[];
  messages: Record<string, Message[]>;
  currentThread?: Thread;
  loading: boolean;
  error?: string;
}
```

#### 2.3 Create Chat Store (`frontend/src/stores/chatStore.ts`)

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Thread, Message, ChatState } from '@/types/chat.types';
import { chatService } from '@/services/chatService';

interface ChatStore extends ChatState {
  // Actions
  createThread: (graphId: string, name: string) => Promise<Thread>;
  getGraphThreads: (graphId: string) => Promise<void>;
  getThread: (threadId: string) => Promise<Thread>;
  getThreadMessages: (threadId: string) => Promise<void>;
  sendMessage: (threadId: string, message: string, output?: string) => Promise<void>;
  setCurrentThread: (thread: Thread) => void;
  clearCurrentThread: () => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      threads: [],
      messages: {},
      currentThread: undefined,
      loading: false,
      error: undefined,

      createThread: async (graphId: string, name: string) => {
        set({ loading: true, error: undefined });
        try {
          // Frontend validation: Check if graph already has threads (single crew restriction)
          const existingThreads = get().threads.filter(t => t.graph_id === graphId && t.status === 'active');
          if (existingThreads.length > 0) {
            throw new Error('This graph already has an active chat thread. Only one crew per graph is supported.');
          }
          
          const thread = await chatService.createThread(graphId, name);
          set(state => ({ 
            threads: [thread, ...state.threads],
            loading: false 
          }));
          return thread;
        } catch (error) {
          set({ error: error.message, loading: false });
          throw error;
        }
      },

      getGraphThreads: async (graphId: string) => {
        set({ loading: true, error: undefined });
        try {
          const threads = await chatService.getGraphThreads(graphId);
          set({ threads, loading: false });
        } catch (error) {
          set({ error: error.message, loading: false });
        }
      },

             sendMessage: async (threadId: string, message: string, output?: string) => {
         // Optimistic update
         const userMessage: Message = {
           id: `temp-${Date.now()}`,
           thread_id: threadId,
           content: message,
           message_type: 'user',
           status: 'pending',
           created_at: new Date().toISOString(),
           updated_at: new Date().toISOString(),
         };

         set(state => ({
           messages: {
             ...state.messages,
             [threadId]: [...(state.messages[threadId] || []), userMessage]
           }
         }));

         try {
           await chatService.sendMessageStream(threadId, message, output, (chunk) => {
             // Handle streaming chunks
             set(state => {
               const messages = state.messages[threadId] || [];
               const lastMessage = messages[messages.length - 1];
               
               if (lastMessage && lastMessage.message_type === 'assistant') {
                 // Update existing assistant message
                 lastMessage.content += chunk;
                 return { messages: { ...state.messages, [threadId]: [...messages] } };
               } else {
                 // Create new assistant message
                 const assistantMessage: Message = {
                   id: `assistant-${Date.now()}`,
                   thread_id: threadId,
                   content: chunk,
                   message_type: 'assistant',
                   status: 'processing',
                   created_at: new Date().toISOString(),
                   updated_at: new Date().toISOString(),
                 };
                 return { 
                   messages: { 
                     ...state.messages, 
                     [threadId]: [...messages, assistantMessage] 
                   } 
                 };
               }
             });
           });
         } catch (error) {
           set({ error: error.message });
         }
       },

      // ... other actions
    }),
    {
      name: 'chat-store',
      partialize: (state) => ({ 
        threads: state.threads,
        messages: state.messages 
      }),
    }
  )
);
```

#### 2.4 Create Chat Service (`frontend/src/services/chatService.ts`)

```typescript
import { apiClient } from './api';
import { Thread, Message } from '@/types/chat.types';
import { getAuthCookie } from '@/utils/cookies';

class ChatService {
  async createThread(graphId: string, name: string, description?: string): Promise<Thread> {
    const response = await apiClient.post('/threads', {
      graph_id: graphId,
      name,
      description,
    });
    return response.data;
  }

  async getGraphThreads(graphId: string): Promise<Thread[]> {
    const response = await apiClient.get(`/threads/graph/${graphId}`);
    return response.data.threads;
  }

  async getThread(threadId: string): Promise<Thread> {
    const response = await apiClient.get(`/threads/${threadId}`);
    return response.data;
  }

  async getThreadMessages(threadId: string): Promise<Message[]> {
    const response = await apiClient.get(`/messages/thread/${threadId}`);
    return response.data.messages;
  }

  async sendMessageStream(
    threadId: string, 
    message: string,
    output?: string,
    onChunk: (chunk: string) => void
  ): Promise<void> {
    const { accessToken } = getAuthCookie();
    
    const response = await fetch('/api/messages/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ 
        message,
        output,
        threadId 
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader!.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) {
              onChunk(data.content);
            }
            if (data.error) {
              throw new Error(data.error);
            }
            if (data.done) {
              return;
            }
          } catch (parseError) {
            console.error('Failed to parse streaming data:', parseError);
          }
        }
      }
    }
  }
}

export const chatService = new ChatService();
```

#### 2.5 Create Chat Components

**Chat Layout (`frontend/src/components/chat/ChatLayout.tsx`):**

```typescript
import React from 'react';
import { Outlet } from 'react-router-dom';
import { ThreadSidebar } from './ThreadSidebar';
import { ChatHeader } from './ChatHeader';

export const ChatLayout: React.FC = () => {
  return (
    <div className="flex h-full">
      <ThreadSidebar />
      <div className="flex-1 flex flex-col">
        <ChatHeader />
        <Outlet />
      </div>
    </div>
  );
};
```

**Thread Sidebar (`frontend/src/components/chat/ThreadSidebar.tsx`):**

```typescript
import React, { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useChatStore } from '@/stores/chatStore';
import { Button } from '@/components/ui/button';
import { Plus, MessageCircle } from 'lucide-react';

export const ThreadSidebar: React.FC = () => {
  const { id: graphId } = useParams<{ id: string }>();
  const { threads, getGraphThreads, createThread, loading, error } = useChatStore();
  
  useEffect(() => {
    if (graphId) {
      getGraphThreads(graphId);
    }
  }, [graphId]);

  const handleCreateThread = async () => {
    if (!graphId) return;
    
    try {
      const thread = await createThread(graphId, `Chat ${new Date().toLocaleString()}`);
      // Navigate to new thread would be handled by router
    } catch (error) {
      console.error('Failed to create thread:', error);
    }
  };

  const graphThreads = threads.filter(t => t.graph_id === graphId && t.status === 'active');

  return (
    <div className="w-64 border-r bg-gray-50 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Chat Threads</h3>
        <Button 
          size="sm" 
          onClick={handleCreateThread}
          disabled={loading || graphThreads.length > 0} // Single crew restriction
        >
          <Plus className="w-4 h-4" />
        </Button>
      </div>
      
      {error && (
        <div className="text-sm text-red-600 mb-4 p-2 bg-red-50 rounded">
          {error}
        </div>
      )}
      
      {graphThreads.length === 0 ? (
        <div className="text-sm text-gray-600 text-center py-8">
          No chat threads yet. Create one to start chatting with your crew.
        </div>
      ) : (
        <div className="space-y-2">
          {graphThreads.map(thread => (
            <Link
              key={thread.id}
              to={`/graphs/${graphId}/chat/${thread.id}`}
              className="block p-3 rounded hover:bg-gray-100 border"
            >
              <div className="flex items-start gap-2">
                <MessageCircle className="w-4 h-4 mt-1 text-gray-500" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm truncate">{thread.name}</div>
                  <div className="text-xs text-gray-500">
                    {thread.message_count} messages
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};
```

**Chat Header (`frontend/src/components/chat/ChatHeader.tsx`):**

```typescript
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useChatStore } from '@/stores/chatStore';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

export const ChatHeader: React.FC = () => {
  const { id: graphId, threadId } = useParams<{ id: string; threadId?: string }>();
  const { currentThread } = useChatStore();

  return (
    <div className="border-b p-4 flex items-center gap-4">
      <Link to={`/graphs/${graphId}`}>
        <Button variant="ghost" size="sm">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Graph
        </Button>
      </Link>
      
      <div className="flex-1">
        {threadId && currentThread ? (
          <div>
            <h2 className="font-semibold">{currentThread.name}</h2>
            <p className="text-sm text-gray-600">
              Chat with your CrewAI agents
            </p>
          </div>
        ) : (
          <div>
            <h2 className="font-semibold">Chat Interface</h2>
            <p className="text-sm text-gray-600">
              Select or create a thread to start chatting
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
```

**Message List (`frontend/src/components/chat/MessageList.tsx`):**

```typescript
import React from 'react';
import { Message } from '@/types/chat.types';
import { User, Bot, AlertCircle } from 'lucide-react';

interface MessageListProps {
  messages: Message[];
}

export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex gap-3 ${
            message.message_type === 'user' ? 'justify-end' : 'justify-start'
          }`}
        >
          <div
            className={`max-w-[70%] rounded-lg p-3 ${
              message.message_type === 'user'
                ? 'bg-blue-600 text-white'
                : message.message_type === 'error'
                ? 'bg-red-100 text-red-800 border border-red-200'
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            <div className="flex items-start gap-2">
              {message.message_type === 'user' ? (
                <User className="w-4 h-4 mt-1 flex-shrink-0" />
              ) : message.message_type === 'error' ? (
                <AlertCircle className="w-4 h-4 mt-1 flex-shrink-0" />
              ) : (
                <Bot className="w-4 h-4 mt-1 flex-shrink-0" />
              )}
              <div className="flex-1">
                <div className="whitespace-pre-wrap">{message.content}</div>
                {message.status === 'processing' && (
                  <div className="text-xs mt-1 opacity-70">Processing...</div>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
```

**Message Input (`frontend/src/components/chat/MessageInput.tsx`):**

```typescript
import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send } from 'lucide-react';

interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  value,
  onChange,
  onSend,
  disabled = false,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const handleSend = () => {
    if (value.trim() && !disabled) {
      onSend();
    }
  };

  return (
    <div className="flex gap-2">
      <Textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={disabled ? "Select a thread to start chatting..." : "Type your message..."}
        disabled={disabled}
        className="flex-1 min-h-[40px] max-h-[120px]"
        rows={1}
      />
      <Button 
        onClick={handleSend} 
        disabled={disabled || !value.trim()}
        size="sm"
      >
        <Send className="w-4 h-4" />
      </Button>
    </div>
  );
};
```

**Chat Welcome (`frontend/src/components/chat/ChatWelcome.tsx`):**

```typescript
import React from 'react';
import { useParams } from 'react-router-dom';
import { useChatStore } from '@/stores/chatStore';
import { Button } from '@/components/ui/button';
import { MessageCircle, Plus } from 'lucide-react';

export const ChatWelcome: React.FC = () => {
  const { id: graphId } = useParams<{ id: string }>();
  const { createThread, loading, threads } = useChatStore();

  const handleCreateThread = async () => {
    if (!graphId) return;
    
    try {
      await createThread(graphId, `Chat ${new Date().toLocaleString()}`);
    } catch (error) {
      console.error('Failed to create thread:', error);
    }
  };

  const hasActiveThreads = threads.some(t => t.graph_id === graphId && t.status === 'active');

  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <MessageCircle className="w-16 h-16 text-gray-400 mb-4" />
      <h2 className="text-2xl font-semibold mb-2">Welcome to Chat</h2>
      <p className="text-gray-600 text-center mb-6 max-w-md">
        Start a conversation with your CrewAI agents. Your messages will trigger the crew execution based on your graph configuration.
      </p>
      
      {!hasActiveThreads ? (
        <Button onClick={handleCreateThread} disabled={loading}>
          <Plus className="w-4 h-4 mr-2" />
          Start New Chat
        </Button>
      ) : (
        <p className="text-sm text-gray-500">
          You already have an active chat thread. Select it from the sidebar to continue.
        </p>
      )}
    </div>
  );
};
```

**Chat Interface (`frontend/src/components/chat/ChatInterface.tsx`):**

```typescript
import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useChatStore } from '@/stores/chatStore';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';

export const ChatInterface: React.FC = () => {
  const { id: graphId, threadId } = useParams<{ id: string; threadId?: string }>();
  const { currentThread, messages, sendMessage, getThreadMessages, setCurrentThread, getThread } = useChatStore();
  const [inputValue, setInputValue] = useState('');
  const [outputValue, setOutputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (threadId) {
      getThreadMessages(threadId);
      getThread(threadId).then(thread => {
        if (thread) setCurrentThread(thread);
      });
    }
  }, [threadId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !threadId) return;

    try {
      await sendMessage(threadId, inputValue, outputValue || undefined);
      setInputValue('');
      setOutputValue('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const threadMessages = threadId ? messages[threadId] || [] : [];

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList messages={threadMessages} />
        <div ref={messagesEndRef} />
      </div>
      <div className="border-t p-4 space-y-2">
        {/* Optional output specification */}
        <div className="text-xs text-gray-600">
          <input
            type="text"
            placeholder="Expected output format (optional)"
            value={outputValue}
            onChange={(e) => setOutputValue(e.target.value)}
            className="w-full px-2 py-1 text-xs border rounded"
          />
        </div>
        <MessageInput
          value={inputValue}
          onChange={setInputValue}
          onSend={handleSendMessage}
          disabled={!threadId}
        />
      </div>
    </div>
  );
};
```

#### 2.6 Update App Router (`frontend/src/router/index.tsx`)

```typescript
import { ChatLayout } from '@/components/chat/ChatLayout';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { ChatWelcome } from '@/components/chat/ChatWelcome';

// Add to routes configuration
{
  path: '/graphs/:id/chat',
  element: <ChatLayout />,
  children: [
    {
      index: true,
      element: <ChatWelcome />,
    },
    {
      path: ':threadId',
      element: <ChatInterface />,
    },
  ],
}
```

#### 2.7 Update Sidebar Navigation

**Add Chat Navigation to `app-sidebar.tsx`:**

```typescript
// Add to navigation items when in graph context
{
  title: "Chat",
  url: `/graphs/${graphId}/chat`,
  icon: MessageCircle,
  isActive: location.pathname.includes('/chat'),
}
```

### Phase 3: Integration Points

#### 3.1 Navigation Flow

1. **From Graph Editor:**
   - Add "Chat" button in graph editor toolbar
   - Navigate to `/graphs/:id/chat`

2. **From Sidebar:**
   - Add chat navigation when in graph context
   - Show recent threads

#### 3.2 Thread Creation Flow

1. **New Chat (`/graphs/:id/chat`):**
   - Show welcome screen with "Start New Chat" button
   - On first message, create thread and redirect to `/graphs/:id/chat/:threadId`

2. **Existing Chat (`/graphs/:id/chat/:threadId`):**
   - Load existing thread and messages
   - Enable direct messaging

#### 3.3 CrewAI Streaming Integration

1. **Message Send Flow:**
   - Create user message
   - Get associated graph data
   - Translate graph to CrewAI objects (agents, tasks, crews)
   - Create new task from message content
   - Execute CrewAI crew and stream response
   - Create placeholder assistant message
   - Update assistant message content as chunks arrive
   - Mark as complete when execution ends

2. **CrewAI Integration Details:**
   - Use existing `GraphTranslationService` to convert graph data to CrewAI objects
   - Handle relationships between agents, tasks, and crews based on graph edges
   - Create dynamic task from user message and optional output specification
   - Stream CrewAI execution output in real-time

3. **Error Handling:**
   - Handle CrewAI execution failures
   - Graph translation errors
   - Connection failures
   - Fallback error messages

### Phase 4: Testing Strategy

#### 4.1 Backend Tests

```python
# Test thread creation and management
def test_create_thread():
    # Test thread creation with valid graph
    # Test access control
    # Test validation

def test_chat_streaming():
    # Test streaming message endpoint
    # Test CrewAI integration and execution
    # Test graph translation
    # Test error handling
```

#### 4.2 Frontend Tests

```typescript
// Test chat store
describe('ChatStore', () => {
  it('should create thread', async () => {
    // Test thread creation
  });

  it('should handle streaming messages', async () => {
    // Test streaming message handling
  });
});

// Test chat components
describe('ChatInterface', () => {
  it('should render messages', () => {
    // Test message rendering
  });

  it('should handle user input', () => {
    // Test message input and sending
  });
});
```

### Phase 5: Deployment Considerations

#### 5.1 Backend Updates

1. **Database Migration:**
   - Thread table already exists
   - Ensure proper indexing for performance

2. **Environment Configuration:**
   - HTTP streaming configuration
   - CrewAI execution timeout settings
   - Memory and performance settings

#### 5.2 Frontend Updates

1. **Build Configuration:**
   - Ensure streaming response support in production
   - Proxy configuration for development

2. **State Management:**
   - Persistent chat state
   - Message caching strategy

### Phase 6: Future Enhancements

1. **File Attachments:**
   - Support for file uploads in chat
   - Image and document support

2. **Message Reactions:**
   - Like/dislike functionality
   - Message flagging

3. **Thread Management:**
   - Thread archiving
   - Thread search and filtering

4. **Collaborative Features:**
   - Multiple users in same thread
   - Real-time presence indicators

## Implementation Phases and Tasks

### Phase 0: Infrastructure Cleanup (0.5 days)
**Tasks:**
- [ ] Remove existing SSE router registration from `main.py`
- [ ] Disable SSE endpoints if present
- [ ] Remove SSE-related frontend code
- [ ] Clean up SSE state management

### Phase 1: Backend Foundation (2-3 days)
**Tasks:**
- [ ] Create complete thread schemas (`ThreadCreateRequest`, `ThreadUpdateRequest`, `ThreadListResponse`)
- [ ] Implement complete `ThreadService` with all CRUD operations
- [ ] Create complete thread router with all endpoints
- [ ] Add execution protection (prevent concurrent crew runs)
- [ ] Implement graph access validation
- [ ] Add single crew per graph validation (placeholder)
- [ ] Add proper error handling and logging

### Phase 2: CrewAI Chat Integration (2-3 days)
**Tasks:**
- [ ] Create chat message schema (`ChatMessageRequest`)
- [ ] Implement chat streaming endpoint with CrewAI integration
- [ ] Add execution record creation before streaming
- [ ] Implement streaming response with proper error handling
- [ ] Add database transaction management
- [ ] Link messages to executions
- [ ] Update execution status throughout process

### Phase 3: Frontend Chat Interface (2-3 days)
**Tasks:**
- [ ] Create chat types (`Thread`, `Message`, `ChatState`)
- [ ] Implement complete chat store with Zustand
- [ ] Create chat service with streaming support
- [ ] Build core chat components (`ChatLayout`, `ChatInterface`, `MessageList`, `MessageInput`)
- [ ] Add chat routes to router configuration
- [ ] Implement single crew restriction on frontend
- [ ] Add proper error handling in UI

### Phase 4: Navigation Integration (1-2 days)
**Tasks:**
- [ ] Update sidebar navigation for chat access
- [ ] Add chat entry points from graph editor
- [ ] Implement thread sidebar for navigation
- [ ] Add breadcrumb navigation
- [ ] Handle route transitions and state management

### Phase 5: Testing and Refinement (1-2 days)
**Tasks:**
- [ ] Backend unit tests for thread service
- [ ] Chat streaming endpoint tests
- [ ] Frontend component tests
- [ ] Integration tests for full chat flow
- [ ] Error handling validation
- [ ] Performance testing

### Phase 6: Deployment and Documentation (1 day)
**Tasks:**
- [ ] Update environment configuration
- [ ] Add deployment considerations
- [ ] Update API documentation
- [ ] Create user documentation
- [ ] Performance monitoring setup

## Success Metrics

- [ ] Users can create new chat threads from graph pages
- [ ] Users can navigate between existing threads
- [ ] Messages trigger CrewAI execution based on associated graph data
- [ ] CrewAI responses stream in real-time with proper error handling
- [ ] Chat state persists across browser sessions
- [ ] Integration with existing sidebar navigation works seamlessly
- [ ] Performance is acceptable with multiple concurrent users
- [ ] Graph-to-CrewAI translation works correctly for all node types
- [ ] Dynamic task creation from messages functions properly

## Additional Implementation Notes

### CrewAI Integration Details

1. **Graph Data Processing:**
   - The system uses the existing `GraphTranslationService` to convert graph JSON data into CrewAI objects
   - Agent nodes become CrewAI `Agent` objects with role, goal, and backstory
   - Task nodes become CrewAI `Task` objects with description and expected output
   - Crew nodes define the overall execution structure and process type

2. **Dynamic Task Creation:**
   - Each chat message creates a new `Task` object using the message content as description
   - The optional `output` field from the request specifies the expected output format
   - The new task is assigned to the first available agent from the crew

3. **Execution Flow:**
   - Graph data → CrewAI objects → Add dynamic task → Execute crew → Stream response
   - All execution happens within the HTTP stream to provide real-time feedback

4. **Error Handling:**
   - Graph translation errors (missing required fields, invalid structure)
   - CrewAI execution errors (agent failures, task failures)
   - Streaming response errors (connection issues, timeout)

### Considerations for Missing Functionality

If any part of the implementation seems incomplete or unclear:

1. **Advanced CrewAI Features:**
   - Tool integration for agents (if graph contains tool nodes)
   - Memory management for conversation context
   - Custom LLM configuration from graph data

2. **Performance Optimizations:**
   - Caching of translated CrewAI objects
   - Async execution for long-running tasks
   - Queue management for concurrent requests

3. **Enhanced Streaming:**
   - Progress indicators during execution
   - Intermediate step results
   - Token-level streaming for smoother UX

This implementation plan provides a comprehensive approach to building the chat feature with CrewAI integration while leveraging the existing architecture and maintaining consistency with current patterns.

## AI Agent Instructions

### Environment: Windows with PowerShell
- Use PowerShell commands for all terminal operations
- Use `npm` for frontend package management, `pip` for Python packages
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
1. **Before Starting**: Confirm PBI-003 association and get User approval
2. **Research Phase**: For new patterns (streaming, chat UI), create `<task_id>-<pattern>-guide.md` in `docs/delivery/PBI-003/guides/`
3. **Implementation**: Follow task scope exactly, no gold-plating
4. **Testing**: Implement tests per task's test plan
5. **Documentation**: Update technical docs for API/interface changes
6. **Status Updates**: Maintain status in both index and individual task files
7. **Completion**: Commit with format `<task_id> <task_description>`

### File Structure Required:
```
docs/delivery/PBI-003/
├── prd.md                           # PBI detail document
├── tasks.md                         # Task index
├── guides/                          # Implementation research guides
│   ├── 3-10-streaming-guide.md     # HTTP streaming patterns
│   ├── 3-16-zustand-guide.md       # Chat state management
│   └── 3-25-realtime-ui-guide.md   # Real-time UI updates
└── tasks/                           # Individual task files
    ├── PBI-003-1.md                 # Task 3-1 details
    ├── PBI-003-2.md                 # Task 3-2 details
    └── ...
```

### Technical Constraints:
- All database operations through existing SQLAlchemy patterns
- Follow existing FastAPI endpoint conventions
- Use existing authentication and authorization patterns
- Maintain consistency with current UI component patterns
- Follow existing error handling and logging patterns
- Use existing environment variable configuration
- Type hints throughout TypeScript and Python code
- Async/await patterns for streaming operations

### Chat-Specific Requirements:
- Single crew per graph restriction enforced at both backend and frontend
- No SSE infrastructure - use direct HTTP streaming only
- Message content validation without sanitization (as requested)
- Execution protection to prevent concurrent crew runs
- Proper transaction management during streaming operations
- Error handling for graph translation and CrewAI execution failures
- Real-time UI updates during message streaming

### Success Metrics:
- Each task passes its defined test plan
- Thread management works with proper access control
- Chat streaming provides real-time CrewAI responses
- Single crew restriction prevents multiple threads per graph
- UI components follow existing design patterns
- Error handling provides clear user feedback
- Performance is acceptable for real-time chat interaction

## Next Steps
1. User approves PBI-003 (Proposed → Agreed)
2. Create PBI detail document (`docs/delivery/PBI-003/prd.md`)
3. Create task index (`docs/delivery/PBI-003/tasks.md`)
4. Begin with Task 3-1: Remove existing SSE infrastructure

## Questions for User Approval:
1. Does the task breakdown look appropriate for incremental chat development?
2. Are there any specific chat UX requirements or constraints to add?
3. Should any tasks be combined or further split for better manageability?
4. Do you approve the single crew per graph restriction approach?
5. Are you satisfied with HTTP streaming instead of SSE for real-time updates?
6. Do you approve moving PBI-003 from Proposed to Agreed status?
