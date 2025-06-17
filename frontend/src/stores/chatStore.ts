import { create } from 'zustand';
import { persist, subscribeWithSelector } from 'zustand/middleware';
import type {
  Thread,
  Message,
  ChatState,
  ThreadCreateRequest,
  ThreadUpdateRequest,
  ChatMessageRequest,
  StreamingChunk,
  ChatError,
} from '@/types/chat.types';

interface ChatStoreActions {
  // Thread management
  createThread: (graphId: string, name: string, description?: string) => Promise<Thread>;
  getGraphThreads: (graphId: string) => Promise<void>;
  getThread: (threadId: string) => Promise<Thread>;
  updateThread: (threadId: string, updates: Partial<ThreadUpdateRequest>) => Promise<Thread>;
  deleteThread: (threadId: string) => Promise<void>;
  setCurrentThread: (thread: Thread | undefined) => void;
  clearCurrentThread: () => void;

  // Message management
  getThreadMessages: (threadId: string) => Promise<void>;
  sendMessage: (threadId: string, message: string, output?: string) => Promise<void>;
  addMessage: (message: Message) => void;
  updateMessage: (messageId: string, updates: Partial<Message>) => void;

  // Streaming support
  handleStreamingChunk: (threadId: string, chunk: StreamingChunk) => void;
  setStreaming: (streaming: boolean) => void;

  // State management
  setLoading: (loading: boolean) => void;
  setError: (error: string | undefined) => void;
  clearError: () => void;
  reset: () => void;

  // Single crew restriction validation
  validateSingleCrewRestriction: (graphId: string) => boolean;
}

interface ChatStore extends ChatState, ChatStoreActions {}

const initialState: ChatState = {
  threads: [],
  messages: {},
  currentThread: undefined,
  loading: false,
  error: undefined,
  streaming: false,
};

export const useChatStore = create<ChatStore>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        ...initialState,

        // Thread management actions
        createThread: async (graphId: string, name: string, description?: string): Promise<Thread> => {
          set({ loading: true, error: undefined });
          
          try {
            // Frontend validation: Check single crew restriction
            const canCreate = get().validateSingleCrewRestriction(graphId);
            if (!canCreate) {
              throw new Error('This graph already has an active chat thread. Only one crew per graph is supported.');
            }

            // This will be implemented in Task 3-17 (Chat Service)
            // For now, create a placeholder implementation
            const thread: Thread = {
              id: `temp-${Date.now()}`,
              graph_id: graphId,
              name,
              description,
              status: 'active',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              message_count: 0,
            };

            set(state => ({ 
              threads: [thread, ...state.threads],
              loading: false 
            }));

            return thread;
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to create thread';
            set({ error: errorMessage, loading: false });
            throw new Error(errorMessage);
          }
        },

        getGraphThreads: async (graphId: string): Promise<void> => {
          set({ loading: true, error: undefined });
          
          try {
            // This will be implemented in Task 3-17 (Chat Service)
            // For now, filter existing threads by graph_id
            const graphThreads = get().threads.filter(t => t.graph_id === graphId && t.status === 'active');
            set({ loading: false });
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to get threads';
            set({ error: errorMessage, loading: false });
          }
        },

        getThread: async (threadId: string): Promise<Thread> => {
          const thread = get().threads.find(t => t.id === threadId);
          if (!thread) {
            throw new Error('Thread not found');
          }
          return thread;
        },

        updateThread: async (threadId: string, updates: Partial<ThreadUpdateRequest>): Promise<Thread> => {
          set({ loading: true, error: undefined });
          
          try {
            // This will be implemented in Task 3-17 (Chat Service)
            const thread = get().threads.find(t => t.id === threadId);
            if (!thread) {
              throw new Error('Thread not found');
            }

            const updatedThread: Thread = {
              ...thread,
              ...updates,
              updated_at: new Date().toISOString(),
            };

            set(state => ({
              threads: state.threads.map(t => t.id === threadId ? updatedThread : t),
              currentThread: state.currentThread?.id === threadId ? updatedThread : state.currentThread,
              loading: false,
            }));

            return updatedThread;
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to update thread';
            set({ error: errorMessage, loading: false });
            throw new Error(errorMessage);
          }
        },

        deleteThread: async (threadId: string): Promise<void> => {
          set({ loading: true, error: undefined });
          
          try {
            // This will be implemented in Task 3-17 (Chat Service)
            set(state => ({
              threads: state.threads.filter(t => t.id !== threadId),
              messages: Object.fromEntries(
                Object.entries(state.messages).filter(([id]) => id !== threadId)
              ),
              currentThread: state.currentThread?.id === threadId ? undefined : state.currentThread,
              loading: false,
            }));
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to delete thread';
            set({ error: errorMessage, loading: false });
          }
        },

        setCurrentThread: (thread: Thread | undefined) => {
          set({ currentThread: thread });
        },

        clearCurrentThread: () => {
          set({ currentThread: undefined });
        },

        // Message management actions
        getThreadMessages: async (threadId: string): Promise<void> => {
          set({ loading: true, error: undefined });
          
          try {
            // This will be implemented in Task 3-17 (Chat Service)
            // For now, return existing messages if any
            const existingMessages = get().messages[threadId] || [];
            set({ loading: false });
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to get messages';
            set({ error: errorMessage, loading: false });
          }
        },

        sendMessage: async (threadId: string, message: string, output?: string): Promise<void> => {
          try {
            // Optimistic update: Add user message immediately
            const userMessage: Message = {
              id: `temp-user-${Date.now()}`,
              thread_id: threadId,
              content: message,
              message_type: 'user',
              status: 'pending',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            };

            get().addMessage(userMessage);
            set({ streaming: true });

            // This will be implemented in Task 3-17 (Chat Service) with actual API call
            // For now, create a mock assistant response
            setTimeout(() => {
              const assistantMessage: Message = {
                id: `temp-assistant-${Date.now()}`,
                thread_id: threadId,
                content: `Mock response to: ${message}`,
                message_type: 'assistant',
                status: 'completed',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              };
              
              get().addMessage(assistantMessage);
              set({ streaming: false });
            }, 1000);

          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
            set({ error: errorMessage, streaming: false });
          }
        },

        addMessage: (message: Message) => {
          set(state => ({
            messages: {
              ...state.messages,
              [message.thread_id]: [...(state.messages[message.thread_id] || []), message]
            }
          }));
        },

        updateMessage: (messageId: string, updates: Partial<Message>) => {
          set(state => {
            const newMessages = { ...state.messages };
            
            Object.keys(newMessages).forEach(threadId => {
              newMessages[threadId] = newMessages[threadId].map(msg =>
                msg.id === messageId ? { ...msg, ...updates, updated_at: new Date().toISOString() } : msg
              );
            });

            return { messages: newMessages };
          });
        },

        // Streaming support
        handleStreamingChunk: (threadId: string, chunk: StreamingChunk) => {
          if (chunk.error) {
            set({ error: chunk.error, streaming: false });
            return;
          }

          if (chunk.done) {
            set({ streaming: false });
            return;
          }

          if (chunk.content && chunk.message_id) {
            // Update the message with new content
            get().updateMessage(chunk.message_id, { 
              content: chunk.content,
              status: 'processing'
            });
          }
        },

        setStreaming: (streaming: boolean) => {
          set({ streaming });
        },

        // State management
        setLoading: (loading: boolean) => {
          set({ loading });
        },

        setError: (error: string | undefined) => {
          set({ error });
        },

        clearError: () => {
          set({ error: undefined });
        },

        reset: () => {
          set(initialState);
        },

        // Single crew restriction validation
        validateSingleCrewRestriction: (graphId: string): boolean => {
          const activeThreadsForGraph = get().threads.filter(
            t => t.graph_id === graphId && t.status === 'active'
          );
          return activeThreadsForGraph.length === 0;
        },
      }),
      {
        name: 'chat-store',
        partialize: (state) => ({
          threads: state.threads,
          messages: state.messages,
        }),
      }
    )
  )
);

// Export individual actions for convenience (following authStore pattern)
export const createThread = (graphId: string, name: string, description?: string) =>
  useChatStore.getState().createThread(graphId, name, description);

export const getGraphThreads = (graphId: string) =>
  useChatStore.getState().getGraphThreads(graphId);

export const sendMessage = (threadId: string, message: string, output?: string) =>
  useChatStore.getState().sendMessage(threadId, message, output);

export const setCurrentThread = (thread: Thread | undefined) =>
  useChatStore.getState().setCurrentThread(thread);

export const clearError = () =>
  useChatStore.getState().clearError();

export default useChatStore; 