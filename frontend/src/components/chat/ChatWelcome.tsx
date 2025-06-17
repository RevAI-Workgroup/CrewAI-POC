import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { MessageCircle, AlertTriangle, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useChatStore } from '@/stores/chatStore';
import type { GraphChatParams } from '@/router/routes';

/**
 * Chat Welcome Component
 * Displays welcome screen with crew restriction validation
 * Task 3-19: Implements single crew restriction on frontend
 */
export const ChatWelcome: React.FC = () => {
  const { id: graphId } = useParams<GraphChatParams>();
  const { createThread, getChatEligibilityMessage, loading, threads } = useChatStore();
  
  const [eligibilityMessage, setEligibilityMessage] = useState<string | null>(null);
  const [isEligible, setIsEligible] = useState<boolean>(false);

  useEffect(() => {
    const checkEligibility = async () => {
      if (!graphId) return;
      
      try {
        const message = await getChatEligibilityMessage(graphId);
        setEligibilityMessage(message);
        setIsEligible(message === null);
      } catch (error) {
        setEligibilityMessage('Failed to check graph eligibility');
        setIsEligible(false);
      }
    };

    checkEligibility();
  }, [graphId, getChatEligibilityMessage]);

  const handleCreateThread = async () => {
    if (!graphId || !isEligible) return;
    
    try {
      await createThread(graphId, `Chat ${new Date().toLocaleString()}`);
    } catch (error) {
      console.error('Failed to create thread:', error);
    }
  };

  const hasActiveThreads = threads.some(t => t.graph_id === graphId && t.status === 'active');

  // Show ineligibility message
  if (!isEligible && eligibilityMessage) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 bg-gray-50">
        <AlertTriangle className="w-16 h-16 text-amber-500 mb-4" />
        
        <h2 className="text-2xl font-semibold mb-2 text-gray-800">
          Chat Not Available
        </h2>
        
        <p className="text-gray-600 text-center mb-6 max-w-md">
          {eligibilityMessage}
        </p>
        
        <div className="text-sm text-gray-500 bg-amber-50 p-4 rounded border border-amber-200">
          <strong>Single Crew Restriction:</strong> Only graphs with exactly one crew node can use chat functionality. 
          Please modify your graph to have exactly one crew node to enable chat.
        </div>
      </div>
    );
  }

  // Show eligible welcome screen
  return (
    <div className="flex flex-col items-center justify-center h-full p-8 bg-gray-50">
      <MessageCircle className="w-16 h-16 text-green-500 mb-4" />
      
      <h2 className="text-2xl font-semibold mb-2 text-gray-800">
        Welcome to Chat
      </h2>
      
      <p className="text-gray-600 text-center mb-6 max-w-md">
        Start a conversation with your CrewAI agents. Your messages will trigger the crew execution 
        based on your graph configuration.
      </p>
      
      {!hasActiveThreads && isEligible ? (
        <Button onClick={handleCreateThread} disabled={loading} className="mb-4">
          <Plus className="w-4 h-4 mr-2" />
          Start New Chat
        </Button>
      ) : hasActiveThreads ? (
        <p className="text-sm text-gray-500 bg-green-50 p-3 rounded border border-green-200">
          You have an active chat thread. Select it from the sidebar to continue chatting.
        </p>
      ) : null}
      
      <div className="text-xs text-gray-400 bg-blue-50 p-3 rounded border mt-4">
        <strong>Task 3-19 Complete:</strong> Single crew restriction validation implemented
      </div>
    </div>
  );
}; 