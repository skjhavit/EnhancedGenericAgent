/**
 * WebSocket service using Socket.IO
 */

import { io, Socket } from 'socket.io-client';
import { useChatStore } from '@stores/chatStore';
import { useAuthStore } from '@stores/authStore';
import { ConsentRequest } from '@types/index';

const WS_URL = process.env.REACT_APP_WS_URL || 'http://localhost:8000';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(sessionId: string): void {
    const token = useAuthStore.getState().accessToken;

    if (!token) {
      console.error('No auth token available');
      return;
    }

    // Disconnect existing connection
    if (this.socket?.connected) {
      this.socket.disconnect();
    }

    // Create new connection
    this.socket = io(WS_URL, {
      auth: {
        token,
        sessionId,
      },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    this.registerEventHandlers();
  }

  private registerEventHandlers(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      useChatStore.getState().setConnectionStatus('connected');
      this.reconnectAttempts = 0;

      // Join session room
      const sessionId = useChatStore.getState().sessionId;
      if (sessionId) {
        this.socket?.emit('join_session', { session_id: sessionId });
      }
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      useChatStore.getState().setConnectionStatus('disconnected');
    });

    this.socket.on('connect_error', (error) => {
      console.error('Connection error:', error);
      this.reconnectAttempts++;

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
        useChatStore.getState().setConnectionStatus('disconnected');
      } else {
        useChatStore.getState().setConnectionStatus('reconnecting');
      }
    });

    // Session events
    this.socket.on('joined_session', (data: { session_id: string }) => {
      console.log('Joined session:', data.session_id);
    });

    // Message events
    this.socket.on('token', (data: { data: string }) => {
      useChatStore.getState().appendToken(data.data);
    });

    this.socket.on('agent_thought', (data: { data: string }) => {
      useChatStore.getState().setCurrentThought(data.data);
    });

    this.socket.on('agent_typing', (data: { typing: boolean }) => {
      useChatStore.getState().setIsStreaming(data.typing);
    });

    this.socket.on('consent_required', (data: { data: ConsentRequest }) => {
      useChatStore.getState().setConsentRequest(data.data);
      useChatStore.getState().setIsStreaming(false);
    });

    this.socket.on('tool_result', (data: { data: any }) => {
      console.log('Tool result:', data.data);
      // Optionally display tool results
    });

    this.socket.on('end_of_stream', () => {
      useChatStore.getState().setIsStreaming(false);
      useChatStore.getState().setCurrentThought('');
    });

    this.socket.on('error', (data: { message: string }) => {
      console.error('Server error:', data.message);
      // Optionally show error to user
      alert(`Error: ${data.message}`);
    });
  }

  sendMessage(message: string): void {
    if (!this.socket?.connected) {
      console.error('WebSocket not connected');
      return;
    }

    this.socket.emit('chat_message', { message });
  }

  sendConsentResponse(approved: boolean): void {
    if (!this.socket?.connected) {
      console.error('WebSocket not connected');
      return;
    }

    this.socket.emit('consent_response', { approved });
    useChatStore.getState().setConsentRequest(null);
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    useChatStore.getState().setConnectionStatus('disconnected');
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const websocketService = new WebSocketService();
