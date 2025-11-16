/**
 * Individual message component
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { ChatMessage } from '@types';

interface MessageProps {
  message: ChatMessage;
}

export const Message: React.FC<MessageProps> = ({ message }) => {
  const isHuman = message.message_type === 'human';
  const isThought = message.message_type === 'thought';

  if (isThought) {
    return (
      <div className="flex justify-center">
        <div className="px-4 py-2 bg-purple-50 text-purple-700 text-sm rounded-full border border-purple-200">
          💭 {message.content}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex ${isHuman ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-3xl px-4 py-3 rounded-lg ${
          isHuman
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-800 border border-gray-200'
        }`}
      >
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {message.message_type === 'tool' && (
          <div className="mt-2 pt-2 border-t border-gray-300 text-xs text-gray-500">
            Tool Result
          </div>
        )}
      </div>
    </div>
  );
};
