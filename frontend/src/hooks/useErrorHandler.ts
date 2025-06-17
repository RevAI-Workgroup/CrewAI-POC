import { useCallback } from 'react';
import { toast } from 'sonner';
import { useChatStore } from '@/stores/chatStore';
import type { ErrorType } from '@/components/chat/ErrorDisplay';

export interface ErrorContext {
  action?: string;
  threadId?: string;
  messageId?: string;
  graphId?: string;
  timestamp?: string;
}

export interface ErrorHandlerOptions {
  showToast?: boolean;
  logError?: boolean;
  reportError?: boolean;
  retryAction?: () => void | Promise<void>;
  context?: ErrorContext;
}

export const useErrorHandler = () => {
  const { setError, clearError } = useChatStore();

  const getErrorType = useCallback((error: Error | string): ErrorType => {
    const message = error instanceof Error ? error.message : error;
    const lowerMessage = message.toLowerCase();

    if (lowerMessage.includes('network') || lowerMessage.includes('connection') || 
        lowerMessage.includes('timeout') || lowerMessage.includes('fetch')) {
      return 'network';
    }
    
    if (lowerMessage.includes('validation') || lowerMessage.includes('invalid') ||
        lowerMessage.includes('required') || lowerMessage.includes('empty')) {
      return 'validation';
    }
    
    if (lowerMessage.includes('execution') || lowerMessage.includes('crew') ||
        lowerMessage.includes('failed to process') || lowerMessage.includes('streaming')) {
      return 'execution';
    }
    
    if (lowerMessage.includes('auth') || lowerMessage.includes('unauthorized') ||
        lowerMessage.includes('forbidden') || lowerMessage.includes('token')) {
      return 'authentication';
    }

    return 'general';
  }, []);

  const getErrorMessage = useCallback((error: Error | string, context?: ErrorContext): string => {
    const baseMessage = error instanceof Error ? error.message : error;
    
    // Provide user-friendly messages for common errors
    const lowerMessage = baseMessage.toLowerCase();
    
    if (lowerMessage.includes('network error') || lowerMessage.includes('failed to fetch')) {
      return 'Unable to connect to the server. Please check your internet connection and try again.';
    }
    
    if (lowerMessage.includes('unauthorized') || lowerMessage.includes('401')) {
      return 'Your session has expired. Please log in again.';
    }
    
    if (lowerMessage.includes('forbidden') || lowerMessage.includes('403')) {
      return 'You do not have permission to perform this action.';
    }
    
    if (lowerMessage.includes('not found') || lowerMessage.includes('404')) {
      return context?.action === 'thread' 
        ? 'The conversation thread was not found. It may have been deleted.'
        : 'The requested resource was not found.';
    }
    
    if (lowerMessage.includes('conflict') || lowerMessage.includes('409')) {
      return 'The crew is already executing. Please wait for it to complete before sending another message.';
    }
    
    if (lowerMessage.includes('single crew') || lowerMessage.includes('only one thread')) {
      return 'This graph already has an active chat thread. Only one conversation per graph is supported.';
    }
    
    if (lowerMessage.includes('crew execution') || lowerMessage.includes('streaming')) {
      return 'There was an error processing your message. Please try again.';
    }

    // Return original message if no specific handling
    return baseMessage;
  }, []);

  const handleError = useCallback((
    error: Error | string,
    options: ErrorHandlerOptions = {}
  ) => {
    const {
      showToast = true,
      logError = true,
      reportError = false,
      retryAction,
      context,
    } = options;

    const errorType = getErrorType(error);
    const errorMessage = getErrorMessage(error, context);
    const timestamp = new Date().toISOString();

    // Log error for debugging
    if (logError) {
      console.error('Error handled:', {
        error: error instanceof Error ? error : new Error(error),
        type: errorType,
        context: { ...context, timestamp },
        stack: error instanceof Error ? error.stack : undefined,
      });
    }

    // Set error in chat store
    setError(errorMessage);

    // Show toast notification
    if (showToast) {
      const toastAction = retryAction ? {
        label: 'Retry',
        onClick: retryAction,
      } : undefined;

      switch (errorType) {
        case 'network':
          toast.error('Connection Error', {
            description: errorMessage,
            action: toastAction,
          });
          break;
        case 'validation':
          toast.warning('Validation Error', {
            description: errorMessage,
          });
          break;
        case 'execution':
          toast.error('Execution Error', {
            description: errorMessage,
            action: toastAction,
          });
          break;
        case 'authentication':
          toast.error('Authentication Error', {
            description: errorMessage,
            action: {
              label: 'Login',
              onClick: () => window.location.href = '/login',
            },
          });
          break;
        default:
          toast.error('Error', {
            description: errorMessage,
            action: toastAction,
          });
      }
    }

    // Report error to external service
    if (reportError && typeof window !== 'undefined' && (window as any).reportError) {
      (window as any).reportError(error, {
        type: errorType,
        context: { ...context, timestamp },
        userAgent: navigator.userAgent,
        url: window.location.href,
      });
    }

    return {
      type: errorType,
      message: errorMessage,
      timestamp,
    };
  }, [getErrorType, getErrorMessage, setError]);

  const handleAsyncError = useCallback(async (
    asyncFn: () => Promise<any>,
    options: ErrorHandlerOptions = {}
  ) => {
    try {
      return await asyncFn();
    } catch (error) {
      handleError(error as Error, options);
      throw error; // Re-throw so calling code can handle if needed
    }
  }, [handleError]);

  const clearCurrentError = useCallback(() => {
    clearError();
  }, [clearError]);

  const createRetryHandler = useCallback((
    originalFn: () => void | Promise<void>,
    options: ErrorHandlerOptions = {}
  ) => {
    return async () => {
      try {
        clearCurrentError();
        await originalFn();
      } catch (error) {
        handleError(error as Error, {
          ...options,
          showToast: true,
        });
      }
    };
  }, [handleError, clearCurrentError]);

  return {
    handleError,
    handleAsyncError,
    clearError: clearCurrentError,
    createRetryHandler,
    getErrorType,
    getErrorMessage,
  };
}; 