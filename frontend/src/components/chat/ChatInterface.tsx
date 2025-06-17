import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { MessageSquare } from 'lucide-react';
import { ChatErrorBoundary } from './ChatErrorBoundary';
import { ErrorDisplay } from './ErrorDisplay';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { useChatStore } from '@/stores/chatStore';
import type { GraphChatParams } from '@/router/routes';

/**
 * Chat Interface Component
 * Handles individual thread chat interface with comprehensive error handling
 */
export const ChatInterface: React.FC = () => {
  const { id: graphId, threadId } = useParams<GraphChatParams>();
  const { error, loading, clearError } = useChatStore();
  const { handleError, clearError: clearHandlerError } = useErrorHandler();

  // Clear errors when component mounts or thread changes
  useEffect(() => {
    clearError();
    clearHandlerError();
  }, [threadId, clearError, clearHandlerError]);

  const handleErrorRetry = () => {
    clearError();
    clearHandlerError();
    // In a real implementation, this would retry the last failed action
    console.log('Retrying last action...');
  };

  const handleErrorDismiss = () => {
    clearError();
    clearHandlerError();
  };

  return (
    <ChatErrorBoundary>
      <div className="flex flex-col h-full">
        {/* Error Display */}
        {error && (
          <div className="p-4">
            <ErrorDisplay
              error={error}
              onRetry={handleErrorRetry}
              onDismiss={handleErrorDismiss}
              inline
            />
          </div>
        )}

        {/* Thread Info Header */}
        <div className="p-4 border-b bg-white">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-blue-500" />
            <div>
              <h3 className="font-semibold">Thread: {threadId}</h3>
              <p className="text-sm text-gray-600">Graph: {graphId}</p>
            </div>
          </div>
        </div>

        {/* Messages Area - Placeholder with loading state */}
        <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
          {loading ? (
            <div className="text-center text-gray-500 mt-8">
              <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-3"></div>
              <p className="text-sm">Loading chat...</p>
            </div>
          ) : (
            <div className="text-center text-gray-500 mt-8">
              <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <h4 className="font-medium mb-2">Chat Interface</h4>
              <p className="text-sm">
                Message list and input components will be implemented in tasks 3-23 through 3-25.
              </p>
            </div>
          )}
        </div>

        {/* Message Input Area - Placeholder */}
        <div className="border-t p-4 bg-white">
          <div className="text-sm text-gray-500 text-center">
            Message input component (Coming in task 3-23)
          </div>
        </div>
      </div>
    </ChatErrorBoundary>
  );
}; 