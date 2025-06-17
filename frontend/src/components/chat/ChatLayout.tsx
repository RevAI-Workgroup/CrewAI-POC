import React from 'react';
import { Outlet } from 'react-router-dom';

/**
 * Chat Layout Component
 * Provides the main layout for chat functionality with nested routing
 * This is a placeholder component for task 3-18 (Chat Routes Configuration)
 */
export const ChatLayout: React.FC = () => {
  return (
    <div className="flex h-full w-full">
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
  );
}; 