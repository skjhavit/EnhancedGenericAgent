/**
 * Main chat container component
 */

import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useChatStore } from '@stores/chatStore';
import { websocketService } from '@services/websocket';
import { ChatOverrides, Agent } from '@types';
import { apiClient } from '@services/api';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ConsentModal } from './ConsentModal';
import { ConnectionIndicator } from './ConnectionIndicator';
import { ChatSettingsPanel } from './ChatSettingsPanel';

const OVERRIDES_STORAGE_KEY = 'chat_overrides';

export const ChatContainer: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const {
    chatHistory,
    consentRequest,
    connectionStatus,
    loadHistoryFromDB,
    setSessionId,
    isStreaming,
    currentThought,
    agentId,
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [overrides, setOverrides] = useState<ChatOverrides>({});

  // Load overrides from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(`${OVERRIDES_STORAGE_KEY}_${sessionId}`);
      if (stored) {
        setOverrides(JSON.parse(stored));
      }
    } catch (error) {
      console.error('Failed to load overrides from localStorage:', error);
    }
  }, [sessionId]);

  // Save overrides to localStorage when they change
  const handleOverridesChange = (newOverrides: ChatOverrides) => {
    setOverrides(newOverrides);
    try {
      localStorage.setItem(
        `${OVERRIDES_STORAGE_KEY}_${sessionId}`,
        JSON.stringify(newOverrides)
      );
    } catch (error) {
      console.error('Failed to save overrides to localStorage:', error);
    }
  };

  // Load agent data when agentId is available
  useEffect(() => {
    if (agentId) {
      loadAgent(agentId);
    }
  }, [agentId]);

  const loadAgent = async (id: string) => {
    try {
      const agentData = await apiClient.getAgent(id);
      setAgent(agentData);
    } catch (error) {
      console.error('Failed to load agent:', error);
    }
  };

  // Load chat history and connect WebSocket on mount
  useEffect(() => {
    if (!sessionId) {
      navigate('/');
      return;
    }

    // Set session ID in store
    setSessionId(sessionId);

    // Load history from database
    const loadHistory = async () => {
      try {
        await loadHistoryFromDB(sessionId);
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    };

    loadHistory();

    // Connect WebSocket with a small delay to avoid React StrictMode double-mount issues
    const timer = setTimeout(() => {
      console.log('[ChatContainer] Connecting WebSocket for session:', sessionId);
      websocketService.connect(sessionId);
    }, 100);

    // Cleanup ONLY on unmount or sessionId change
    return () => {
      clearTimeout(timer);
      console.log('[ChatContainer] Disconnecting WebSocket');
      websocketService.disconnect();
    };
  }, [sessionId, navigate, setSessionId, loadHistoryFromDB]);

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

      {/* Settings Panel */}
      {agent && sessionId && (
        <ChatSettingsPanel
          sessionId={sessionId}
          agentProvider={agent.llm_config.provider || 'unknown'}
          agentEmbeddingProvider={agent.embedding_config.provider || 'unknown'}
          overrides={overrides}
          onOverridesChange={handleOverridesChange}
        />
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <MessageList messages={chatHistory} />

        {/* Agent Thinking Indicator */}
        {isStreaming && currentThought && (
          <div className="flex justify-start mb-4">
            <div className="max-w-3xl px-4 py-2 bg-purple-50 text-purple-700 text-sm rounded-lg border border-purple-200">
              <div className="flex items-center space-x-2">
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>💭 {currentThought}</span>
              </div>
            </div>
          </div>
        )}

        {/* Typing Indicator */}
        {isStreaming && !currentThought && (
          <div className="flex justify-start mb-4">
            <div className="max-w-3xl px-4 py-3 bg-gray-100 rounded-lg">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Consent Modal */}
      {consentRequest && <ConsentModal request={consentRequest} />}

      {/* Input */}
      <div className="border-t bg-white px-4 py-4">
        <ChatInput overrides={overrides} />
      </div>
    </div>
  );
};
