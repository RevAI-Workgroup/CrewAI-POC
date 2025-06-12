# Frontend Messages & Threads API Integration Guide

**Created**: December 17, 2024  
**Version**: 1.0  
**Backend Tasks**: PBI-001-8 (Thread Model), PBI-001-9 (Message Model), PBI-001-27 (Message Handling)

## Overview

This document provides comprehensive integration guidelines for frontend developers working with the CrewAI backend's messaging and thread management system. The backend provides full CRUD operations for messages and threads, real-time streaming via SSE, and execution triggering capabilities.

## Table of Contents

1. [Data Models](#data-models)
2. [Message APIs](#message-apis)
3. [Thread Integration](#thread-integration)
4. [Real-time Updates (SSE)](#real-time-updates-sse)
5. [Error Handling](#error-handling)
6. [Integration Patterns](#integration-patterns)
7. [Performance Considerations](#performance-considerations)

## Data Models

### Message Schema

```typescript
interface MessageResponse {
  id: string;
  thread_id: string;
  execution_id?: string;
  content: string;
  message_type: 'user' | 'assistant' | 'system' | 'error';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message_metadata?: Record<string, any>;
  sequence_number: number;
  triggers_execution: boolean;
  sent_at: string; // ISO datetime
  processed_at?: string; // ISO datetime
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

interface MessageCreateRequest {
  thread_id: string;
  content: string;
  message_type?: 'user' | 'assistant' | 'system' | 'error';
  triggers_execution?: boolean;
  message_metadata?: Record<string, any>;
}

interface MessageUpdateRequest {
  content?: string;
  status?: 'pending' | 'processing' | 'completed' | 'failed';
  message_metadata?: Record<string, any>;
}

interface MessageListResponse {
  messages: MessageResponse[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}
```

### Thread Schema

```typescript
interface Thread {
  id: string;
  graph_id: string;
  name: string;
  description?: string;
  status: 'active' | 'archived' | 'deleted';
  thread_config?: Record<string, any>;
  last_activity_at?: string; // ISO datetime
  is_active: boolean;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}
```

## Message APIs

### Base URL
All message endpoints are prefixed with `/api/messages`

### 1. Create Message

**POST** `/api/messages/`

Creates a new message in a thread. Optionally triggers CrewAI execution.

```typescript
// Request
const createMessage = async (messageData: MessageCreateRequest): Promise<MessageResponse> => {
  const response = await fetch('/api/messages/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(messageData)
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create message: ${response.statusText}`);
  }
  
  return response.json();
};

// Usage
const newMessage = await createMessage({
  thread_id: 'thread-uuid-here',
  content: 'Please run this graph with the latest data',
  message_type: 'user',
  triggers_execution: true,
  message_metadata: { source: 'chat-input' }
});
```

**Success Response**: `201 Created`
```json
{
  "id": "msg-uuid",
  "thread_id": "thread-uuid",
  "content": "Please run this graph with the latest data",
  "message_type": "user",
  "status": "pending",
  "sequence_number": 1,
  "triggers_execution": true,
  "sent_at": "2024-12-17T10:30:00Z",
  "created_at": "2024-12-17T10:30:00Z",
  "updated_at": "2024-12-17T10:30:00Z"
}
```

### 2. Get Single Message

**GET** `/api/messages/{message_id}`

```typescript
const getMessage = async (messageId: string): Promise<MessageResponse> => {
  const response = await fetch(`/api/messages/${messageId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Message not found');
    }
    throw new Error(`Failed to get message: ${response.statusText}`);
  }
  
  return response.json();
};
```

### 3. Get Thread Messages (Paginated)

**GET** `/api/messages/thread/{thread_id}`

Retrieves messages for a specific thread with pagination support.

**Query Parameters**:
- `page` (int, default: 1): Page number
- `page_size` (int, default: 50, max: 100): Messages per page
- `include_system` (bool, default: true): Include system messages

```typescript
const getThreadMessages = async (
  threadId: string,
  page: number = 1,
  pageSize: number = 50,
  includeSystem: boolean = true
): Promise<MessageListResponse> => {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
    include_system: includeSystem.toString()
  });
  
  const response = await fetch(`/api/messages/thread/${threadId}?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    throw new Error(`Failed to get thread messages: ${response.statusText}`);
  }
  
  return response.json();
};

// Usage with pagination
const loadMoreMessages = async (threadId: string, currentPage: number) => {
  const data = await getThreadMessages(threadId, currentPage + 1, 25);
  
  return {
    messages: data.messages,
    hasMore: data.has_next,
    totalCount: data.total
  };
};
```

### 4. Update Message

**PUT** `/api/messages/{message_id}`

```typescript
const updateMessage = async (
  messageId: string, 
  updates: MessageUpdateRequest
): Promise<MessageResponse> => {
  const response = await fetch(`/api/messages/${messageId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(updates)
  });
  
  if (!response.ok) {
    throw new Error(`Failed to update message: ${response.statusText}`);
  }
  
  return response.json();
};

// Usage - Edit message content
await updateMessage('msg-uuid', {
  content: 'Updated message content',
  message_metadata: { edited: true, edit_timestamp: new Date().toISOString() }
});
```

### 5. Process Message for Execution

**POST** `/api/messages/{message_id}/process`

Triggers CrewAI execution for a specific message.

```typescript
interface MessageProcessingRequest {
  execution_config?: Record<string, any>;
}

interface MessageProcessingResponse {
  message_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  execution_id?: string;
  processing_started: boolean;
  message: string;
}

const processMessage = async (
  messageId: string,
  config?: Record<string, any>
): Promise<MessageProcessingResponse> => {
  const response = await fetch(`/api/messages/${messageId}/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ execution_config: config })
  });
  
  if (!response.ok) {
    throw new Error(`Failed to process message: ${response.statusText}`);
  }
  
  return response.json();
};
```

### 6. Delete Message (Soft Delete)

**DELETE** `/api/messages/{message_id}`

```typescript
const deleteMessage = async (messageId: string): Promise<void> => {
  const response = await fetch(`/api/messages/${messageId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    throw new Error(`Failed to delete message: ${response.statusText}`);
  }
};
```

## Thread Integration

### Thread Access via Graph APIs

Threads are accessed through the graph management system. Refer to graph APIs for thread creation and management.

### Thread Validation

```typescript
const validateThreadAccess = async (threadId: string): Promise<boolean> => {
  try {
    // Attempt to get thread messages (will fail if no access)
    await getThreadMessages(threadId, 1, 1);
    return true;
  } catch (error) {
    return false;
  }
};
```

## Real-time Updates (SSE)

### SSE Connection Setup

The backend provides Server-Sent Events for real-time message and execution updates.

```typescript
class MessageSSEClient {
  private eventSource: EventSource | null = null;
  private connectionId: string | null = null;
  
  async connect(token: string): Promise<void> {
    // First, establish SSE connection
    const connectResponse = await fetch('/api/sse/connect', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!connectResponse.ok) {
      throw new Error('Failed to establish SSE connection');
    }
    
    const { connection_id } = await connectResponse.json();
    this.connectionId = connection_id;
    
    // Create EventSource for the stream
    this.eventSource = new EventSource(
      `/api/sse/stream/${connection_id}?token=${token}`
    );
    
    this.setupEventListeners();
  }
  
  private setupEventListeners(): void {
    if (!this.eventSource) return;
    
    this.eventSource.addEventListener('message_created', (event) => {
      const data = JSON.parse(event.data);
      this.handleMessageCreated(data);
    });
    
    this.eventSource.addEventListener('execution_status', (event) => {
      const data = JSON.parse(event.data);
      this.handleExecutionUpdate(data);
    });
    
    this.eventSource.addEventListener('error', (event) => {
      console.error('SSE error:', event);
      this.reconnect();
    });
  }
  
  private handleMessageCreated(data: any): void {
    // Handle new message creation
    console.log('New message created:', data.message_id);
    // Update UI with new message
  }
  
  private handleExecutionUpdate(data: any): void {
    // Handle execution status changes
    console.log('Execution update:', data.execution_id, data.status);
    // Update UI with execution progress
  }
  
  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}

// Usage
const sseClient = new MessageSSEClient();
await sseClient.connect(authToken);
```

### SSE Event Types

The backend broadcasts these event types:

1. **`message_created`**: New message added to thread
2. **`execution_status`**: CrewAI execution status updates
3. **`connection`**: Connection status events
4. **`heartbeat`**: Keep-alive events

## Error Handling

### Standard Error Responses

```typescript
interface APIError {
  detail: string;
  status_code: number;
}

// Common error handling pattern
const handleAPIError = (error: any, operation: string): void => {
  if (error.status === 400) {
    // Bad request - validation error
    console.error(`${operation} validation error:`, error.detail);
  } else if (error.status === 403) {
    // Forbidden - permission error
    console.error(`${operation} permission denied:`, error.detail);
  } else if (error.status === 404) {
    // Not found
    console.error(`${operation} resource not found:`, error.detail);
  } else if (error.status === 500) {
    // Server error
    console.error(`${operation} server error:`, error.detail);
  } else {
    console.error(`${operation} unknown error:`, error);
  }
};

// Usage in API calls
try {
  const message = await createMessage(messageData);
} catch (error) {
  handleAPIError(error, 'Create message');
}
```

### Permission Errors

Messages and threads are access-controlled through graph ownership:

- Users can only access messages in threads they own
- All operations validate user permissions
- `403 Forbidden` returned for unauthorized access

## Integration Patterns

### 1. Chat Interface Pattern

```typescript
class ChatInterface {
  private threadId: string;
  private messages: MessageResponse[] = [];
  private sseClient: MessageSSEClient;
  
  constructor(threadId: string) {
    this.threadId = threadId;
    this.sseClient = new MessageSSEClient();
  }
  
  async initialize(): Promise<void> {
    // Load initial messages
    await this.loadMessages();
    
    // Setup real-time updates
    await this.sseClient.connect(authToken);
    this.sseClient.onMessageCreated = (data) => {
      if (data.thread_id === this.threadId) {
        this.addMessageToUI(data);
      }
    };
  }
  
  async loadMessages(): Promise<void> {
    const data = await getThreadMessages(this.threadId, 1, 50);
    this.messages = data.messages;
    this.renderMessages();
  }
  
  async sendMessage(content: string, triggersExecution: boolean = false): Promise<void> {
    const message = await createMessage({
      thread_id: this.threadId,
      content,
      message_type: 'user',
      triggers_execution: triggersExecution
    });
    
    // Message will appear via SSE, no need to manually add
  }
  
  private renderMessages(): void {
    // Update UI with current messages
  }
  
  private addMessageToUI(messageData: any): void {
    // Add new message to UI
  }
}
```

### 2. Message Pagination Pattern

```typescript
class MessagePagination {
  private threadId: string;
  private currentPage: number = 1;
  private pageSize: number = 25;
  private hasMore: boolean = true;
  
  async loadMore(): Promise<MessageResponse[]> {
    if (!this.hasMore) return [];
    
    const data = await getThreadMessages(
      this.threadId, 
      this.currentPage + 1, 
      this.pageSize
    );
    
    this.currentPage++;
    this.hasMore = data.has_next;
    
    return data.messages;
  }
  
  async refresh(): Promise<MessageResponse[]> {
    this.currentPage = 1;
    this.hasMore = true;
    
    const data = await getThreadMessages(this.threadId, 1, this.pageSize);
    this.hasMore = data.has_next;
    
    return data.messages;
  }
}
```

### 3. Execution Tracking Pattern

```typescript
class ExecutionTracker {
  private executionStatuses: Map<string, string> = new Map();
  
  async triggerExecution(messageId: string): Promise<string | null> {
    const result = await processMessage(messageId);
    
    if (result.execution_id) {
      this.executionStatuses.set(result.execution_id, result.status);
      return result.execution_id;
    }
    
    return null;
  }
  
  handleExecutionUpdate(data: any): void {
    if (data.execution_id) {
      this.executionStatuses.set(data.execution_id, data.status);
      this.updateExecutionUI(data.execution_id, data);
    }
  }
  
  private updateExecutionUI(executionId: string, data: any): void {
    // Update UI with execution progress
    console.log(`Execution ${executionId}: ${data.status} (${data.progress_percentage}%)`);
  }
}
```

## Performance Considerations

### 1. Message Loading Optimization

```typescript
// Load recent messages first, older messages on demand
const loadMessagesOptimized = async (threadId: string) => {
  // Load first page (most recent)
  const recentMessages = await getThreadMessages(threadId, 1, 25);
  
  // Only load more if user scrolls up
  return {
    messages: recentMessages.messages,
    loadMore: () => getThreadMessages(threadId, 2, 25)
  };
};
```

### 2. SSE Connection Management

```typescript
// Manage SSE connections efficiently
class SSEManager {
  private static instance: SSEManager;
  private client: MessageSSEClient | null = null;
  private subscribers: Map<string, Function[]> = new Map();
  
  static getInstance(): SSEManager {
    if (!SSEManager.instance) {
      SSEManager.instance = new SSEManager();
    }
    return SSEManager.instance;
  }
  
  async ensureConnection(token: string): Promise<void> {
    if (!this.client) {
      this.client = new MessageSSEClient();
      await this.client.connect(token);
    }
  }
  
  subscribe(eventType: string, callback: Function): void {
    if (!this.subscribers.has(eventType)) {
      this.subscribers.set(eventType, []);
    }
    this.subscribers.get(eventType)!.push(callback);
  }
}
```

### 3. Memory Management

```typescript
// Clean up resources properly
class MessageComponent {
  private sseClient: MessageSSEClient;
  
  componentWillUnmount(): void {
    // Clean up SSE connection
    this.sseClient?.disconnect();
  }
  
  // Use pagination to avoid loading too many messages
  private maxMessages = 100;
  
  private trimMessages(messages: MessageResponse[]): MessageResponse[] {
    if (messages.length > this.maxMessages) {
      return messages.slice(-this.maxMessages);
    }
    return messages;
  }
}
```

## Security Notes

1. **Authentication**: All endpoints require JWT bearer token
2. **Authorization**: Users can only access their own threads/messages
3. **Validation**: Content length limits enforced (max 50,000 characters)
4. **Rate Limiting**: Consider implementing client-side rate limiting for message creation

## Testing

### Unit Test Examples

```typescript
// Mock API responses for testing
const mockMessageResponse: MessageResponse = {
  id: 'test-msg-1',
  thread_id: 'test-thread-1',
  content: 'Test message',
  message_type: 'user',
  status: 'completed',
  sequence_number: 1,
  triggers_execution: false,
  sent_at: '2024-12-17T10:30:00Z',
  created_at: '2024-12-17T10:30:00Z',
  updated_at: '2024-12-17T10:30:00Z'
};

// Test message creation
test('should create message successfully', async () => {
  fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => mockMessageResponse
  });
  
  const result = await createMessage({
    thread_id: 'test-thread-1',
    content: 'Test message',
    message_type: 'user'
  });
  
  expect(result.id).toBe('test-msg-1');
  expect(result.content).toBe('Test message');
});
```

---

**Last Updated**: December 17, 2024  
**Related Backend Tasks**: PBI-001-8, PBI-001-9, PBI-001-27  
**Frontend Integration**: For questions or clarifications, refer to the backend API documentation or contact the backend development team. 