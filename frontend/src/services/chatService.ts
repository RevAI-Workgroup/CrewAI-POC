import { apiClient } from './api';
import { getAuthCookie } from '@/utils/cookies';
import { apiConfig } from '@/config/api';
import type {
  Thread,
  Message,
  ThreadCreateRequest,
  ThreadUpdateRequest,
  ThreadListResponse,
  ChatMessageRequest,
  StreamingChunk,
} from '@/types/chat.types';

/**
 * Chat API endpoints
 */
const CHAT_ROUTES = {
  THREADS: {
    CREATE: '/api/threads',
    LIST: '/api/threads',
    GET: (id: string) => `/api/threads/${id}`,
    UPDATE: (id: string) => `/api/threads/${id}`,
    DELETE: (id: string) => `/api/threads/${id}`,
    BY_GRAPH: (graphId: string) => `/api/threads/graph/${graphId}`,
  },
  MESSAGES: {
    LIST: (threadId: string) => `/api/messages/thread/${threadId}`,
    CHAT_STREAM: '/api/messages/chat/stream',
  },
} as const;

/**
 * Chat Service Class
 * Handles all chat-related API operations including HTTP streaming
 */
class ChatService {
  /**
   * Thread Management Operations
   */

  /**
   * Create a new thread for a graph
   */
  async createThread(graphId: string, name: string, description?: string): Promise<Thread> {
    try {
      const requestData: ThreadCreateRequest = {
        graph_id: graphId,
        name,
        description,
      };

      const response = await apiClient.post<Thread>(
        CHAT_ROUTES.THREADS.CREATE,
        requestData
      );

      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to create thread');
    }
  }

  /**
   * Get all threads for a specific graph
   */
  async getGraphThreads(graphId: string): Promise<Thread[]> {
    try {
      const response = await apiClient.get<ThreadListResponse>(
        CHAT_ROUTES.THREADS.BY_GRAPH(graphId)
      );

      return response.data.threads;
    } catch (error) {
      throw this.handleError(error, 'Failed to get threads');
    }
  }

  /**
   * Get a specific thread by ID
   */
  async getThread(threadId: string): Promise<Thread> {
    try {
      const response = await apiClient.get<Thread>(
        CHAT_ROUTES.THREADS.GET(threadId)
      );

      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get thread');
    }
  }

  /**
   * Update a thread
   */
  async updateThread(threadId: string, updates: Partial<ThreadUpdateRequest>): Promise<Thread> {
    try {
      const response = await apiClient.put<Thread>(
        CHAT_ROUTES.THREADS.UPDATE(threadId),
        updates
      );

      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to update thread');
    }
  }

  /**
   * Delete a thread (soft delete)
   */
  async deleteThread(threadId: string): Promise<void> {
    try {
      await apiClient.delete(CHAT_ROUTES.THREADS.DELETE(threadId));
    } catch (error) {
      throw this.handleError(error, 'Failed to delete thread');
    }
  }

  /**
   * Message Management Operations
   */

  /**
   * Get all messages for a thread
   */
  async getThreadMessages(threadId: string): Promise<Message[]> {
    try {
      const response = await apiClient.get<{ messages: Message[] }>(
        CHAT_ROUTES.MESSAGES.LIST(threadId)
      );

      return response.data.messages;
    } catch (error) {
      throw this.handleError(error, 'Failed to get messages');
    }
  }

  /**
   * Send a message with streaming response
   * Uses fetch API for HTTP streaming support
   */
  async sendMessageStream(
    threadId: string,
    message: string,
    output?: string,
    onChunk?: (chunk: StreamingChunk) => void
  ): Promise<void> {
    const { accessToken } = getAuthCookie();

    if (!accessToken) {
      throw new Error('Authentication required');
    }

    try {
      const requestData: ChatMessageRequest = {
        message,
        output,
        threadId,
      };

      const response = await fetch(`${apiConfig.baseURL}${CHAT_ROUTES.MESSAGES.CHAT_STREAM}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      // Handle streaming response
      await this.processStreamingResponse(response, onChunk);

    } catch (error) {
      throw this.handleError(error, 'Failed to send message');
    }
  }

  /**
   * Process HTTP streaming response
   */
  private async processStreamingResponse(
    response: Response,
    onChunk?: (chunk: StreamingChunk) => void
  ): Promise<void> {
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('Response body is not readable');
    }

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        // Decode chunk and process lines
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.trim() === '') continue;

          // Parse event-stream format: "data: {json}"
          if (line.startsWith('data: ')) {
            try {
              const jsonData = line.slice(6); // Remove "data: " prefix
              const streamingChunk: StreamingChunk = JSON.parse(jsonData);
              
              // Call chunk handler if provided
              if (onChunk) {
                onChunk(streamingChunk);
              }

              // Check if stream is complete
              if (streamingChunk.done) {
                return;
              }

              // Check for errors
              if (streamingChunk.error) {
                throw new Error(streamingChunk.error);
              }

            } catch (parseError) {
              console.warn('Failed to parse streaming data:', line, parseError);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Utility Methods
   */

  /**
   * Handle API errors with consistent error messages
   */
  private handleError(error: unknown, defaultMessage: string): Error {
    if (error instanceof Error) {
      return error;
    }

    // Handle Axios errors
    if (typeof error === 'object' && error !== null && 'response' in error) {
      const axiosError = error as any;
      const message = axiosError.response?.data?.detail || 
                     axiosError.response?.data?.message || 
                     axiosError.message ||
                     defaultMessage;
      return new Error(message);
    }

    return new Error(defaultMessage);
  }

  /**
   * Check if authentication is available
   */
  private isAuthenticated(): boolean {
    const { accessToken } = getAuthCookie();
    return Boolean(accessToken);
  }

  /**
   * Retry failed requests with exponential backoff
   */
  private async retryWithBackoff<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    baseDelay: number = 1000
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        
        if (attempt === maxRetries) {
          throw lastError;
        }

        // Exponential backoff delay
        const delay = baseDelay * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw lastError!;
  }
}

// Export singleton instance
export const chatService = new ChatService();
export default chatService; 