# PBI-003: Chat Interface with CrewAI Integration

## Overview
This PBI implements a chat interface that allows users to interact with their CrewAI graphs through natural language messages. The feature provides real-time conversation capabilities where user messages trigger CrewAI execution and stream responses back to the user.

## Problem Statement
Users currently need to manually execute CrewAI graphs through the interface, which lacks conversational interaction. There's no way to:
- Chat with CrewAI agents in natural language
- Receive streaming responses during execution
- Maintain conversation context across interactions
- Dynamically create tasks from chat messages

## User Stories

### Primary User Story
**As a user**, I need a chat interface that allows me to communicate with my CrewAI graphs through natural language messages, **so that** I can interact with my crews conversationally and receive streamed responses in real-time.

### Supporting User Stories
- **As a user**, I want to create chat threads for my graphs **so that** I can organize different conversations
- **As a user**, I want to see my messages and crew responses in real-time **so that** I can have fluid conversations
- **As a user**, I want to specify expected output formats **so that** I can get responses in the format I need
- **As a user**, I want to navigate between different chat threads **so that** I can manage multiple conversations

## Technical Approach

### Architecture
- **Backend**: FastAPI with HTTP streaming responses
- **Frontend**: React with real-time UI updates
- **Database**: PostgreSQL with existing Thread/Message models
- **Integration**: GraphTranslationService for CrewAI object creation
- **Streaming**: HTTP text/event-stream without SSE infrastructure

### Key Components
1. **Thread Management**: CRUD operations for chat threads
2. **Message Processing**: Real-time message handling and streaming
3. **CrewAI Integration**: Dynamic task creation from messages
4. **UI Components**: Chat interface with thread navigation
5. **Error Handling**: Comprehensive error management

### Single Crew Restriction
- Each graph can only have one active chat thread
- Enforced at both backend and frontend levels
- Prevents complex multi-crew chat scenarios

## UX/UI Considerations

### Navigation Flow
1. **From Graph Editor**: "Chat" button → `/graphs/:id/chat`
2. **Thread Creation**: Welcome screen → "Start New Chat" → Thread creation
3. **Chat Interface**: Thread sidebar + message area + input field

### Real-time Experience
- Messages appear immediately (optimistic updates)
- Streaming responses show incremental content
- Visual indicators for processing states
- Error messages with clear feedback

### Responsive Design
- Mobile-friendly chat interface
- Sidebar collapsible on smaller screens
- Touch-friendly message input

## Acceptance Criteria

### Thread Management
- ✅ Users can create new chat threads for graphs
- ✅ Users can view list of existing threads
- ✅ Users can navigate between threads
- ✅ Only one active thread per graph (single crew restriction)
- ✅ Proper access control (users only see their own threads)

### Chat Functionality
- ✅ Users can send messages and receive responses
- ✅ CrewAI execution triggered by messages
- ✅ Real-time streaming of responses
- ✅ Message history persistence
- ✅ Error handling for failed executions

### Integration
- ✅ Graph data properly translated to CrewAI objects
- ✅ Dynamic task creation from message content
- ✅ Execution status tracking
- ✅ Database transaction management during streaming

### UI/UX
- ✅ Modern chat interface with message bubbles
- ✅ Thread sidebar with navigation
- ✅ Message input with send functionality
- ✅ Loading states and error displays
- ✅ Integration with existing sidebar navigation

## Dependencies
- Existing Thread and Message models
- GraphTranslationService for CrewAI integration
- Current authentication system
- Existing UI component library

## Open Questions
1. **File Attachments**: Should initial version support file uploads in chat?
2. **Message Limits**: Are there any message length or thread size limits needed?
3. **Conversation Memory**: Should CrewAI maintain context across messages?
4. **Concurrent Execution**: How should multiple users handle the same graph?

## Related Tasks
Link to task index: [PBI-003 Tasks](mdc:tasks.md)

---

**Parent Backlog**: [Product Backlog](mdc:../backlog.md)
**Status**: Agreed
**Last Updated**: 2024-12-27 