/**
 * Chat input component
 */

import React, { useState } from 'react';
import { useChatStore } from '@stores/chatStore';
import { websocketService } from '@services/websocket';
import { ChatOverrides } from '@types';

interface ChatInputProps {
  overrides?: ChatOverrides;
}

export const ChatInput: React.FC<ChatInputProps> = ({ overrides }) => {
  const [message, setMessage] = useState('');
  const { isStreaming, addMessage } = useChatStore();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!message.trim() || isStreaming) return;

    // Add user message to chat
    addMessage({
      id: `temp-${Date.now()}`,
      message_type: 'human',
      content: message,
      metadata: {},
      created_at: new Date().toISOString(),
    });

    // Send to server with overrides
    websocketService.sendMessage(message, overrides);

    // Clear input
    setMessage('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center space-x-2">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder={
          isStreaming ? 'Agent is thinking...' : 'Type your message...'
        }
        disabled={isStreaming}
        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
      />
      <button
        type="submit"
        disabled={!message.trim() || isStreaming}
        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {isStreaming ? 'Thinking...' : 'Send'}
      </button>
    </form>
  );
};
