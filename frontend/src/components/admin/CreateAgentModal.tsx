/**
 * Modal for creating a new agent
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '@services/api';
import { ToolManifest } from '@types';

interface CreateAgentModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateAgentModal: React.FC<CreateAgentModalProps> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    system_prompt_template: 'You are a helpful AI assistant.',
    provider: 'openai',
    model: 'gpt-4',
    api_key: '',
    temperature: 0.7,
    enabled_tools: [] as string[],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [availableTools, setAvailableTools] = useState<ToolManifest[]>([]);
  const [toolsLoading, setToolsLoading] = useState(true);

  // Fetch available tools on mount
  useEffect(() => {
    const loadTools = async () => {
      try {
        const tools = await apiClient.getTools();
        setAvailableTools(tools);
      } catch (err: any) {
        console.error('Failed to load tools:', err);
        setError('Failed to load available tools');
      } finally {
        setToolsLoading(false);
      }
    };

    loadTools();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Determine which enabled tools require consent
      const writeOperationTools = formData.enabled_tools.filter(toolName => {
        const tool = availableTools.find(t => t.name === toolName);
        return tool?.requires_consent === true;
      });

      await apiClient.createAgent({
        name: formData.name,
        description: formData.description,
        system_prompt_template: formData.system_prompt_template,
        llm_config: {
          provider: formData.provider,
          model: formData.model,
          api_key: formData.api_key,
          temperature: formData.temperature,
        },
        embedding_config: {
          provider: 'openai',
          model: 'text-embedding-3-small',
        },
        enabled_tools: formData.enabled_tools,
        write_operation_tools: writeOperationTools,
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create agent');
    } finally {
      setLoading(false);
    }
  };

  const toggleTool = (tool: string) => {
    setFormData(prev => ({
      ...prev,
      enabled_tools: prev.enabled_tools.includes(tool)
        ? prev.enabled_tools.filter(t => t !== tool)
        : [...prev.enabled_tools, tool]
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-4">Create New Agent</h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Basic Info */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Agent Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={e => setFormData({...formData, name: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
                placeholder="My Assistant"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={e => setFormData({...formData, description: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
                rows={2}
                placeholder="A helpful assistant that can..."
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                System Prompt
              </label>
              <textarea
                value={formData.system_prompt_template}
                onChange={e => setFormData({...formData, system_prompt_template: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder="You are a helpful AI assistant..."
              />
            </div>

            {/* LLM Config */}
            <div className="mb-4 grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  LLM Provider *
                </label>
                <select
                  value={formData.provider}
                  onChange={e => setFormData({...formData, provider: e.target.value})}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
                >
                  <option value="openai">OpenAI</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="ollama">Ollama (Local)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model *
                </label>
                <input
                  type="text"
                  required
                  value={formData.model}
                  onChange={e => setFormData({...formData, model: e.target.value})}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
                  placeholder="gpt-4"
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Key {formData.provider !== 'ollama' && '*'}
              </label>
              <input
                type="password"
                required={formData.provider !== 'ollama'}
                value={formData.api_key}
                onChange={e => setFormData({...formData, api_key: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
                placeholder="sk-..."
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Temperature: {formData.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={formData.temperature}
                onChange={e => setFormData({...formData, temperature: parseFloat(e.target.value)})}
                className="w-full"
              />
            </div>

            {/* Tools */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enabled Tools
              </label>
              {toolsLoading ? (
                <div className="text-sm text-gray-500">Loading tools...</div>
              ) : availableTools.length === 0 ? (
                <div className="text-sm text-gray-500">No tools available</div>
              ) : (
                <div className="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto border rounded p-2">
                  {availableTools.map(tool => (
                    <label
                      key={tool.name}
                      className="flex items-start space-x-2 cursor-pointer p-2 hover:bg-gray-50 rounded"
                    >
                      <input
                        type="checkbox"
                        checked={formData.enabled_tools.includes(tool.name)}
                        onChange={() => toggleTool(tool.name)}
                        className="rounded mt-1"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">{tool.name}</span>
                          {tool.requires_consent && (
                            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                              Requires Consent
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-0.5">{tool.description}</p>
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border rounded hover:bg-gray-50"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                disabled={loading}
              >
                {loading ? 'Creating...' : 'Create Agent'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
