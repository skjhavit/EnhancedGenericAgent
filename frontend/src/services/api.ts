/**
 * API client for backend communication
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  User,
  AuthTokens,
  Agent,
  ChatSession,
  SessionDetail,
  KnowledgeBase,
  Document,
  ToolManifest,
} from '@types';
import { useAuthStore } from '@stores/authStore';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = useAuthStore.getState().accessToken;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        // If 401 and not already retried, try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = useAuthStore.getState().refreshToken;
            if (!refreshToken) {
              throw new Error('No refresh token available');
            }

            const response = await axios.post<AuthTokens>(
              `${API_BASE_URL}/api/auth/refresh`,
              { refresh_token: refreshToken }
            );

            useAuthStore.getState().updateTokens(response.data);

            // Retry original request
            originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, logout user
            useAuthStore.getState().logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async register(
    email: string,
    password: string,
    fullName?: string
  ): Promise<{ user: User; tokens: AuthTokens }> {
    const response = await this.client.post<AuthTokens>('/api/auth/register', {
      email,
      password,
      full_name: fullName,
    });

    const tokens = response.data;

    // Get user info
    const userResponse = await this.client.get<User>('/api/auth/me', {
      headers: { Authorization: `Bearer ${tokens.access_token}` },
    });

    return { user: userResponse.data, tokens };
  }

  async login(
    email: string,
    password: string
  ): Promise<{ user: User; tokens: AuthTokens }> {
    const response = await this.client.post<AuthTokens>('/api/auth/login', {
      email,
      password,
    });

    const tokens = response.data;

    // Get user info
    const userResponse = await this.client.get<User>('/api/auth/me', {
      headers: { Authorization: `Bearer ${tokens.access_token}` },
    });

    return { user: userResponse.data, tokens };
  }

  async getMe(): Promise<User> {
    const response = await this.client.get<User>('/api/auth/me');
    return response.data;
  }

  // Sessions
  async createSession(agentId: string, title?: string): Promise<ChatSession> {
    const response = await this.client.post<ChatSession>('/api/sessions', {
      agent_id: agentId,
      title,
    });
    return response.data;
  }

  async getSessions(): Promise<ChatSession[]> {
    const response = await this.client.get<ChatSession[]>('/api/sessions');
    return response.data;
  }

  async getSession(sessionId: string): Promise<SessionDetail> {
    const response = await this.client.get<SessionDetail>(
      `/api/sessions/${sessionId}`
    );
    return response.data;
  }

  async updateSession(sessionId: string, title: string): Promise<ChatSession> {
    const response = await this.client.patch<ChatSession>(
      `/api/sessions/${sessionId}`,
      { title }
    );
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.client.delete(`/api/sessions/${sessionId}`);
  }

  // Agents
  async getAgents(): Promise<Agent[]> {
    const response = await this.client.get<Agent[]>('/api/agents');
    return response.data;
  }

  async getAgent(agentId: string): Promise<Agent> {
    const response = await this.client.get<Agent>(`/api/agents/${agentId}`);
    return response.data;
  }

  async createAgent(agent: Partial<Agent>): Promise<Agent> {
    const response = await this.client.post<Agent>('/api/agents', agent);
    return response.data;
  }

  async updateAgent(agentId: string, agent: Partial<Agent>): Promise<Agent> {
    const response = await this.client.patch<Agent>(
      `/api/agents/${agentId}`,
      agent
    );
    return response.data;
  }

  async deleteAgent(agentId: string): Promise<void> {
    await this.client.delete(`/api/agents/${agentId}`);
  }

  // Tools
  async getTools(): Promise<ToolManifest[]> {
    const response = await this.client.get<ToolManifest[]>('/api/admin/tools');
    return response.data;
  }

  // Knowledge Bases
  async getKnowledgeBases(): Promise<KnowledgeBase[]> {
    const response = await this.client.get<KnowledgeBase[]>('/api/knowledge');
    return response.data;
  }

  async createKnowledgeBase(
    name: string,
    description?: string
  ): Promise<KnowledgeBase> {
    const response = await this.client.post<KnowledgeBase>('/api/knowledge', {
      name,
      description,
    });
    return response.data;
  }

  async getDocuments(kbId: string): Promise<Document[]> {
    const response = await this.client.get<Document[]>(
      `/api/knowledge/${kbId}/documents`
    );
    return response.data;
  }

  async uploadDocument(kbId: string, file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<Document>(
      `/api/knowledge/${kbId}/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }
}

export const apiClient = new ApiClient();
