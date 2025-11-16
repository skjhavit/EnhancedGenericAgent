/**
 * Admin panel for managing agents and knowledge bases
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@services/api';
import { Agent, KnowledgeBase } from '@types/index';

export const AdminPanel: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [agentsData, kbsData] = await Promise.all([
        apiClient.getAgents(),
        apiClient.getKnowledgeBases(),
      ]);
      setAgents(agentsData);
      setKnowledgeBases(kbsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Admin Panel</h1>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded"
          >
            Back to Dashboard
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Agents Section */}
        <section className="mb-12">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-800">Agents</h2>
            <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              Create Agent
            </button>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    LLM Provider
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Tools
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {agents.map((agent) => (
                  <tr key={agent.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {agent.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {agent.description || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {agent.llm_config.provider || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {agent.enabled_tools.length} tools
                    </td>
                    <td className="px-6 py-4 text-right text-sm font-medium">
                      <button className="text-blue-600 hover:text-blue-900 mr-4">
                        Edit
                      </button>
                      <button className="text-red-600 hover:text-red-900">
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Knowledge Bases Section */}
        <section>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-800">
              Knowledge Bases
            </h2>
            <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              Create Knowledge Base
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {knowledgeBases.map((kb) => (
              <div key={kb.id} className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  {kb.name}
                </h3>
                <p className="text-gray-600 text-sm mb-4">
                  {kb.description || 'No description'}
                </p>
                <p className="text-xs text-gray-500">
                  {kb.document_count} documents
                </p>
                <div className="mt-4 flex space-x-2">
                  <button className="flex-1 px-3 py-2 bg-blue-50 text-blue-600 text-sm rounded hover:bg-blue-100">
                    Manage
                  </button>
                  <button className="flex-1 px-3 py-2 bg-red-50 text-red-600 text-sm rounded hover:bg-red-100">
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
};
