/**
 * Individual message component
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { ChatMessage } from '@types';

interface MessageProps {
  message: ChatMessage;
}

/**
 * Preprocess markdown to fix common LLM formatting issues
 */
const preprocessMarkdown = (content: string): string => {
  let processed = content;

  // Replace HTML <br> tags with markdown line breaks
  processed = processed.replace(/<br\s*\/?>/gi, '  \n');

  // Fix inline table rows (most aggressive fix for LLM output)
  // This handles cases where entire tables are on one line like:
  // | Category | Tool | |----------|------| | Row | Cell |
  // Strategy: Match complete rows (greedy to get all cells), split when followed by another row
  // Example: "| A | B | |---| | C |" becomes "| A | B |\n|---|\n| C |"
  processed = processed.replace(/(\|[^\n]+\|)\s+(?=\|)/g, '$1\n');

  // Fix broken markdown tables (add newlines between table rows if missing)
  processed = processed.replace(/\|\s*\n(?!\|)/g, '|\n');

  // Ensure blank line before and after tables
  processed = processed.replace(/([^\n])\n(\|[^\n]+\|)/g, '$1\n\n$2');
  processed = processed.replace(/(\|[^\n]+\|)\n([^\n|])/g, '$1\n\n$2');

  // Convert <code> tags to markdown code
  processed = processed.replace(/<code>(.*?)<\/code>/gi, '`$1`');

  // Ensure double newline before headers for proper spacing
  processed = processed.replace(/([^\n])\n(#{1,6}\s)/g, '$1\n\n$2');

  return processed;
};

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
          <div className="text-xs font-mono whitespace-pre-wrap">{message.content}</div>
        </div>
      </div>
    );
  }

  // Preprocess content before rendering
  const processedContent = preprocessMarkdown(message.content);

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
          <div className={`prose prose-sm max-w-none ${isHuman ? 'prose-invert' : 'prose-slate'}`}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
              components={{
                // Customize table styling
                table: ({ node, ...props }) => (
                  <table className="border-collapse border border-gray-300 my-2" {...props} />
                ),
                th: ({ node, ...props }) => (
                  <th className="border border-gray-300 px-3 py-2 bg-gray-50 font-semibold text-left" {...props} />
                ),
                td: ({ node, ...props }) => (
                  <td className="border border-gray-300 px-3 py-2" {...props} />
                ),
                // Customize code blocks
                code: ({ node, ...props }: any) => {
                  const isInline = !props.className?.includes('language-');
                  return isInline ? (
                    <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
                  ) : (
                    <code className="block bg-gray-900 text-gray-100 p-3 rounded text-sm font-mono overflow-x-auto" {...props} />
                  );
                },
                // Better list styling
                ul: ({ node, ...props }) => (
                  <ul className="list-disc list-inside space-y-1 my-2" {...props} />
                ),
                ol: ({ node, ...props }) => (
                  <ol className="list-decimal list-inside space-y-1 my-2" {...props} />
                ),
              }}
            >
              {processedContent}
            </ReactMarkdown>
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
