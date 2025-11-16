/**
 * Main chat container component
 */

import React, { useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useChatStore } from '@stores/chatStore';
import { websocketService } from '@services/websocket';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ConsentModal } from './ConsentModal';
import { ConnectionIndicator } from './ConnectionIndicator';

export const ChatContainer: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const {
    chatHistory,
    consentRequest,
    connectionStatus,
    loadHistoryFromDB,
    setSessionId,
    clearChat,
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load chat history and connect WebSocket on mount
  useEffect(() => {
    if (!sessionId) {
      navigate('/');
      return;
    }

    // Set session ID in store
    setSessionId(sessionId);

    // Load history if chat is empty
    const loadHistory = async () => {
      if (chatHistory.length === 0) {
        try {
          await loadHistoryFromDB(sessionId);
        } catch (error) {
          console.error('Failed to load chat history:', error);
          // Handle error (show notification, redirect, etc.)
        }
      }

      // Connect WebSocket after history is loaded
      websocketService.connect(sessionId);
    };

    loadHistory();

    // Cleanup on unmount
    return () => {
      websocketService.disconnect();
    };
  }, [sessionId]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white border-b shadow-sm">
        <div>
          <h1 className="text-xl font-semibold text-gray-800">
            {useChatStore.getState().agentName || 'Chat'}
          </h1>
          <p className="text-sm text-gray-500">Session: {sessionId}</p>
        </div>
        <ConnectionIndicator status={connectionStatus} />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <MessageList messages={chatHistory} />
        <div ref={messagesEndRef} />
      </div>

      {/* Consent Modal */}
      {consentRequest && <ConsentModal request={consentRequest} />}

      {/* Input */}
      <div className="border-t bg-white px-4 py-4">
        <ChatInput />
      </div>
    </div>
  );
};
