/**
 * Chat Settings Panel
 * Allows users to override LLM and embedding providers at runtime
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '@services/api';
import { ChatOverrides, ProvidersResponse } from '@types';

interface ChatSettingsPanelProps {
  sessionId: string;
  agentProvider: string;
  agentEmbeddingProvider: string;
  overrides: ChatOverrides;
  onOverridesChange: (overrides: ChatOverrides) => void;
}

export const ChatSettingsPanel: React.FC<ChatSettingsPanelProps> = ({
  sessionId,
  agentProvider,
  agentEmbeddingProvider,
  overrides,
  onOverridesChange,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [providers, setProviders] = useState<ProvidersResponse>({
    llm_providers: [],
    embedding_providers: [],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    try {
      const providersData = await apiClient.getAvailableProviders();
      setProviders(providersData);
    } catch (error) {
      console.error('Failed to load providers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLLMChange = (provider: string) => {
    const newOverrides = {
      ...overrides,
      llm_override: provider === 'agent-default' ? undefined : provider,
    };
    onOverridesChange(newOverrides);
  };

  const handleEmbeddingChange = (provider: string) => {
    const newOverrides = {
      ...overrides,
      embedding_override: provider === 'agent-default' ? undefined : provider,
    };
    onOverridesChange(newOverrides);
  };

  const getCurrentLLM = () => {
    return overrides.llm_override || 'agent-default';
  };

  const getCurrentEmbedding = () => {
    return overrides.embedding_override || 'agent-default';
  };

  const getProviderLabel = (provider: string) => {
    const labels: Record<string, string> = {
      'openai': 'OpenAI',
      'anthropic': 'Anthropic (Claude)',
      'gemini': 'Google Gemini',
      'ollama': 'Ollama (Local)',
      'agent-default': `Agent Default (${agentProvider})`,
    };
    return labels[provider] || provider;
  };

  if (loading) {
    return null;
  }

  return (
    <div className="border-b border-gray-200 bg-white">
      {/* Header Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg
            className="w-5 h-5 text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <span className="text-sm font-medium text-gray-700">
            Chat Settings
          </span>
          {(overrides.llm_override || overrides.embedding_override) && (
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
              Overridden
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 text-gray-600 transition-transform ${
            isOpen ? 'transform rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Settings Panel */}
      {isOpen && (
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
          <div className="space-y-4">
            {/* LLM Provider */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                LLM Provider
              </label>
              <select
                value={getCurrentLLM()}
                onChange={(e) => handleLLMChange(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="agent-default">
                  Agent Default ({agentProvider})
                </option>
                {providers.llm_providers.map((provider) => (
                  <option key={provider} value={provider}>
                    {getProviderLabel(provider)}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {overrides.llm_override
                  ? 'Using override (API key from server .env)'
                  : 'Using agent default configuration'}
              </p>
            </div>

            {/* Embedding Provider */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Embedding Provider
              </label>
              <select
                value={getCurrentEmbedding()}
                onChange={(e) => handleEmbeddingChange(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="agent-default">
                  Agent Default ({agentEmbeddingProvider})
                </option>
                {providers.embedding_providers.map((provider) => (
                  <option key={provider} value={provider}>
                    {getProviderLabel(provider)}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {overrides.embedding_override
                  ? 'Using override (existing KB embeddings unchanged)'
                  : 'Using agent default configuration'}
              </p>
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <div className="flex items-start gap-2">
                <svg
                  className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
                <div className="text-xs text-blue-800">
                  <p className="font-medium">Runtime Override</p>
                  <p className="mt-1">
                    Changes persist for this session. API keys are loaded from server
                    environment variables.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
