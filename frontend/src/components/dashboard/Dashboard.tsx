/**
 * Main dashboard component
 * Shows list of agents and recent chat sessions
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@stores/authStore';
import { apiClient } from '@services/api';
import { Agent, ChatSession } from '@types';

export const Dashboard: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [agentsData, sessionsData] = await Promise.all([
        apiClient.getAgents(),
        apiClient.getSessions(),
      ]);
      setAgents(agentsData);
      setSessions(sessionsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = async (agentId: string) => {
    try {
      const session = await apiClient.createSession(agentId);
      navigate(`/chat/${session.id}`);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleOpenSession = (sessionId: string) => {
    navigate(`/chat/${sessionId}`);
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
          <h1 className="text-2xl font-bold text-gray-800">
            Agent Platform
          </h1>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">{user?.email}</span>
            {user?.role === 'admin' && (
              <button
                onClick={() => navigate('/admin')}
                className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded"
              >
                Admin
              </button>
            )}
            <button
              onClick={() => logout()}
              className="px-4 py-2 text-red-600 hover:bg-red-50 rounded"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Agents Section */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Available Agents
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
              >
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  {agent.name}
                </h3>
                <p className="text-gray-600 text-sm mb-4">
                  {agent.description || 'No description'}
                </p>
                <button
                  onClick={() => handleNewChat(agent.id)}
                  className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
                >
                  Start Chat
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* Recent Sessions */}
        <section>
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Recent Conversations
          </h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {sessions.length === 0 ? (
              <p className="p-6 text-gray-500">No conversations yet</p>
            ) : (
              <div className="divide-y">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    onClick={() => handleOpenSession(session.id)}
                    className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-gray-800">
                          {session.title || session.agent_name}
                        </h3>
                        <p className="text-sm text-gray-500 mt-1">
                          {session.message_count} messages
                        </p>
                      </div>
                      <span className="text-xs text-gray-400">
                        {new Date(session.last_message_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
};
