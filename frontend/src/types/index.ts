/**
 * Type definitions for the Agent Platform frontend
 */

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: 'admin' | 'user';
}

export interface Agent {
  id: string;
  name: string;
  description: string | null;
  system_prompt_template: string;
  llm_config: Record<string, any>;
  embedding_config: Record<string, any>;
  enabled_tools: string[];
  write_operation_tools: string[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  agent_id: string;
  agent_name: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  last_message_at: string;
  message_count: number;
}

export interface ChatMessage {
  id: string;
  message_type: 'human' | 'ai' | 'system' | 'tool' | 'thought';
  content: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface SessionDetail {
  id: string;
  agent_id: string;
  agent_name: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  last_message_at: string;
  messages: ChatMessage[];
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  vectorstore_config: Record<string, any>;
  created_at: string;
  document_count: number;
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: string | null;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  uploaded_at: string;
  processed_at: string | null;
}

export interface ConsentRequest {
  tool_name: string;
  tool_description: string;
  parameters: Record<string, any>;
  action_impact: string;
}

export interface ToolManifest {
  name: string;
  description: string;
  parameters: Record<string, any>;
  requires_consent: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// WebSocket event types
export type SocketEvent =
  | { type: 'token'; data: string }
  | { type: 'agent_thought'; data: string }
  | { type: 'consent_required'; data: ConsentRequest }
  | { type: 'tool_result'; data: any }
  | { type: 'error'; data: string }
  | { type: 'end_of_stream' }
  | { type: 'agent_typing'; typing: boolean };

// API Response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// Connection status
export type ConnectionStatus = 'connected' | 'disconnected' | 'reconnecting';
