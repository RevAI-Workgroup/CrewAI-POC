import React from 'react';
import { useParams } from 'react-router-dom';
import { MessageCircle } from 'lucide-react';
import type { GraphChatParams } from '@/router/routes';

/**
 * Chat Welcome Component
 * Displays welcome screen when no thread is selected
 * This is a placeholder component for task 3-18 (Chat Routes Configuration)
 */
export const ChatWelcome: React.FC = () => {
  const { id: graphId } = useParams<GraphChatParams>();

  return (
    <div className="flex flex-col items-center justify-center h-full p-8 bg-gray-50">
      <MessageCircle className="w-16 h-16 text-gray-400 mb-4" />
      
      <h2 className="text-2xl font-semibold mb-2 text-gray-800">
        Welcome to Chat
      </h2>
      
      <p className="text-gray-600 text-center mb-6 max-w-md">
        Start a conversation with your CrewAI agents for graph {graphId}. 
        Select a thread from the sidebar or create a new one to begin.
      </p>
      
      <div className="text-sm text-gray-500 bg-blue-50 p-3 rounded border">
        <strong>Note:</strong> Full chat functionality will be available after tasks 3-19 through 3-26 are completed.
      </div>
    </div>
  );
}; 