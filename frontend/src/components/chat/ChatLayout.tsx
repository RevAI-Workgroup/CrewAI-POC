import React from 'react';
import { Outlet } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { ChatErrorBoundary } from './ChatErrorBoundary';
import { useErrorHandler } from '@/hooks/useErrorHandler';

/**
 * Chat Layout Component
 * Provides the main layout for chat functionality with comprehensive error handling
 */
export const ChatLayout: React.FC = () => {
  const { handleError } = useErrorHandler();

  const handleLayoutError = (error: Error, errorInfo: any) => {
    handleError(error, {
      context: {
        action: 'chat_layout',
        timestamp: new Date().toISOString(),
      },
      reportError: true,
    });
  };

  return (
    <ChatErrorBoundary onError={handleLayoutError}>
      <div className="flex h-full w-full">
        {/* Toast notifications */}
        <Toaster position="top-right" expand={true} richColors />
        
        {/* Thread Sidebar - Placeholder for task 3-22 */}
        <div className="w-64 border-r bg-gray-50 p-4">
          <div className="text-sm text-gray-500">Thread Sidebar (Coming in 3-22)</div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Header - Placeholder for task 3-24 */}
          <div className="border-b p-4 bg-white">
            <div className="text-sm text-gray-500">Chat Header (Coming in 3-24)</div>
          </div>

          {/* Chat Content - Outlet for nested routes */}
          <div className="flex-1 overflow-hidden">
            <Outlet />
          </div>
        </div>
      </div>
    </ChatErrorBoundary>
  );
}; 