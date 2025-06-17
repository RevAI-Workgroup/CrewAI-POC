/**
 * Chat feature type definitions
 * Provides TypeScript interfaces for threads, messages, and chat state management
 */

/**
 * Thread status enumeration
 */
export type ThreadStatus = 'active' | 'archived' | 'deleted';

/**
 * Message type enumeration
 */
export type MessageType = 'user' | 'assistant' | 'system' | 'error';

/**
 * Message status enumeration
 */
export type MessageStatus = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * Thread interface representing a conversation context
 */
export interface Thread {
  /** Unique thread identifier */
  id: string;
  /** Associated graph identifier */
  graph_id: string;
  /** Human-readable thread name */
  name: string;
  /** Optional thread description */
  description?: string;
  /** Current thread status */
  status: ThreadStatus;
  /** Thread-specific configuration */
  thread_config?: Record<string, any>;
  /** Last activity timestamp */
  last_activity_at?: string;
  /** Thread creation timestamp */
  created_at: string;
  /** Last modification timestamp */
  updated_at: string;
  /** Number of messages in thread */
  message_count: number;
}

/**
 * Message interface representing a single chat message
 */
export interface Message {
  /** Unique message identifier */
  id: string;
  /** Parent thread identifier */
  thread_id: string;
  /** Message content text */
  content: string;
  /** Type of message (user, assistant, system, error) */
  message_type: MessageType;
  /** Current processing status */
  status: MessageStatus;
  /** Message creation timestamp */
  created_at: string;
  /** Last modification timestamp */
  updated_at: string;
  /** Optional execution ID for messages that trigger CrewAI */
  execution_id?: string;
  /** Optional metadata for the message */
  metadata?: Record<string, any>;
}

/**
 * Chat state interface for Zustand store
 */
export interface ChatState {
  /** List of available threads */
  threads: Thread[];
  /** Messages organized by thread ID */
  messages: Record<string, Message[]>;
  /** Currently active thread */
  currentThread?: Thread;
  /** Loading state indicator */
  loading: boolean;
  /** Error message if any */
  error?: string;
  /** Streaming status for real-time updates */
  streaming: boolean;
}

/**
 * Thread creation request interface
 */
export interface ThreadCreateRequest {
  /** Graph ID to associate with thread */
  graph_id: string;
  /** Thread name */
  name: string;
  /** Optional description */
  description?: string;
  /** Optional thread configuration */
  thread_config?: Record<string, any>;
}

/**
 * Thread update request interface
 */
export interface ThreadUpdateRequest {
  /** Updated name */
  name?: string;
  /** Updated description */
  description?: string;
  /** Updated status */
  status?: ThreadStatus;
  /** Updated configuration */
  thread_config?: Record<string, any>;
}

/**
 * Thread list response interface
 */
export interface ThreadListResponse {
  /** Array of threads */
  threads: Thread[];
  /** Total number of threads */
  total: number;
  /** Associated graph ID */
  graph_id: string;
}

/**
 * Chat message request interface for sending messages
 */
export interface ChatMessageRequest {
  /** Message content */
  message: string;
  /** Optional expected output format */
  output?: string;
  /** Thread ID for the message */
  threadId: string;
}

/**
 * Streaming response chunk interface
 */
export interface StreamingChunk {
  /** Content chunk */
  content?: string;
  /** Message ID being updated */
  message_id?: string;
  /** Error message if any */
  error?: string;
  /** Indicates end of stream */
  done?: boolean;
  /** Stream metadata */
  metadata?: Record<string, any>;
}

/**
 * Chat error interface for error handling
 */
export interface ChatError {
  /** Error code */
  code: string;
  /** Human-readable error message */
  message: string;
  /** Additional error details */
  details?: Record<string, any>;
  /** Timestamp of error */
  timestamp: string;
} 