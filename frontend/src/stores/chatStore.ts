/**
 * Chat state management using Zustand
 */

import { create } from 'zustand';
import {
  ChatMessage,
  ConsentRequest,
  ConnectionStatus,
} from '@types';
import { apiClient } from '@services/api';

interface ChatState {
  // Session
  sessionId: string | null;
  agentId: string | null;
  agentName: string | null;

  // Messages
  chatHistory: ChatMessage[];
  currentMessage: string;
  isStreaming: boolean;
  currentThought: string;

  // Consent
  consentRequest: ConsentRequest | null;

  // Connection
  connectionStatus: ConnectionStatus;

  // Actions
  setSessionId: (id: string) => void;
  setAgentInfo: (agentId: string, agentName: string) => void;
  addMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  appendToken: (token: string) => void;
  setCurrentMessage: (message: string) => void;
  setIsStreaming: (streaming: boolean) => void;
  setCurrentThought: (thought: string) => void;
  setConsentRequest: (request: ConsentRequest | null) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  clearChat: () => void;
  loadHistoryFromDB: (sessionId: string) => Promise<void>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  sessionId: null,
  agentId: null,
  agentName: null,
  chatHistory: [],
  currentMessage: '',
  isStreaming: false,
  currentThought: '',
  consentRequest: null,
  connectionStatus: 'disconnected',

  // Actions
  setSessionId: (id: string) => set({ sessionId: id }),

  setAgentInfo: (agentId: string, agentName: string) =>
    set({ agentId, agentName }),

  addMessage: (message: ChatMessage) =>
    set((state) => ({
      chatHistory: [...state.chatHistory, message],
    })),

  setMessages: (messages: ChatMessage[]) =>
    set({ chatHistory: messages }),

  appendToken: (token: string) =>
    set((state) => {
      const history = [...state.chatHistory];
      const lastMsg = history[history.length - 1];

      if (lastMsg && lastMsg.message_type === 'ai') {
        // Append to existing AI message
        lastMsg.content += token;
      } else {
        // Create new AI message
        history.push({
          id: `temp-${Date.now()}`,
          message_type: 'ai',
          content: token,
          metadata: {},
          created_at: new Date().toISOString(),
        });
      }

      return { chatHistory: history };
    }),

  setCurrentMessage: (message: string) => set({ currentMessage: message }),

  setIsStreaming: (streaming: boolean) => set({ isStreaming: streaming }),

  setCurrentThought: (thought: string) => set({ currentThought: thought }),

  setConsentRequest: (request: ConsentRequest | null) =>
    set({ consentRequest: request }),

  setConnectionStatus: (status: ConnectionStatus) =>
    set({ connectionStatus: status }),

  clearChat: () =>
    set({
      chatHistory: [],
      currentMessage: '',
      currentThought: '',
      consentRequest: null,
    }),

  loadHistoryFromDB: async (sessionId: string) => {
    try {
      const session = await apiClient.getSession(sessionId);
      set({
        sessionId: session.id,
        agentId: session.agent_id,
        agentName: session.agent_name,
        chatHistory: session.messages,
      });
    } catch (error) {
      console.error('Failed to load chat history:', error);
      throw error;
    }
  },
}));
