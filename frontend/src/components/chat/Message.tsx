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
  const isTool = message.message_type === 'tool';

  if (isThought) {
    return (
      <div className="flex justify-center my-4">
        <div className="px-4 py-2 bg-purple-50 text-purple-700 text-sm rounded-full border border-purple-200">
          💭 {message.content}
        </div>
      </div>
    );
  }

  if (isTool) {
    return (
      <div className="flex justify-center my-4">
        <div className="px-4 py-2 bg-green-50 text-green-700 text-sm rounded-lg border border-green-200">
          <div className="font-semibold mb-1">🔧 Tool Result</div>
          <div className="text-xs">{message.content}</div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex ${isHuman ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div className="flex items-start space-x-2 max-w-3xl">
        {/* Avatar */}
        {!isHuman && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm">
            AI
          </div>
        )}

        {/* Message Bubble */}
        <div
          className={`px-4 py-3 rounded-2xl shadow-sm ${
            isHuman
              ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-br-none'
              : 'bg-white text-gray-800 border border-gray-200 rounded-bl-none'
          }`}
        >
          <div className={`prose prose-sm max-w-none ${isHuman ? 'prose-invert' : ''}`}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>

          {/* Timestamp */}
          <div className={`text-xs mt-2 ${isHuman ? 'text-blue-100' : 'text-gray-400'}`}>
            {new Date(message.created_at).toLocaleTimeString()}
          </div>
        </div>

        {/* User Avatar */}
        {isHuman && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-600 flex items-center justify-center text-white font-semibold text-sm">
            U
          </div>
        )}
      </div>
    </div>
  );
};
