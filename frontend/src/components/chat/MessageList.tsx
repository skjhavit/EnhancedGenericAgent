/**
 * Message list component
 */

import React from 'react';
import { ChatMessage } from '@types/index';
import { Message } from './Message';

interface MessageListProps {
  messages: ChatMessage[];
}

export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <p>Start a conversation...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <Message key={message.id} message={message} />
      ))}
    </div>
  );
};
