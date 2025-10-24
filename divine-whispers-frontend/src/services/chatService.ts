import apiClient from './apiClient';

// Types for chat API
interface ChatSession {
  id: number;
  user_id: number;
  session_name: string;
  context_data: any;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  message_count: number;
}

interface ChatMessage {
  id: number;
  session_id: number;
  user_id: number;
  message_type: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: any;
  created_at: string;
}

interface FortuneConversationRequest {
  deity_id: string;
  fortune_number: number;
  initial_question?: string;
  context?: any;
}

// WebSocket message types
interface WebSocketMessage {
  type: string;
  session_id?: number;
  content?: string;
  timestamp?: number;
}

interface WebSocketResponse {
  type: string;
  content?: string;
  is_complete?: boolean;
  is_typing?: boolean;
  error?: string;
}

class ChatService {
  private websocket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private messageHandlers: Map<string, Function[]> = new Map();
  private currentUserId: string | null = null;
  
  // WebSocket connection management
  async connectWebSocket(userId: string): Promise<void> {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      return;
    }

    this.currentUserId = userId;
    // Get WebSocket URL from API base URL
    const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
    const wsProtocol = apiBaseUrl.startsWith('https') ? 'wss' : 'ws';
    const wsHost = apiBaseUrl.replace(/^https?:\/\//, '');
    const wsUrl = `${wsProtocol}://${wsHost}/ws/${userId}`;
    
    return new Promise((resolve, reject) => {
      this.websocket = new WebSocket(wsUrl);
      
      this.websocket.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        resolve();
      };
      
      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      this.websocket.onclose = () => {
        console.log('WebSocket disconnected');
        this.websocket = null;
        this.attemptReconnect();
      };
      
      this.websocket.onerror = (error) => {
        const errorMessage = 'WebSocket connection failed - falling back to REST API';
        console.warn('WebSocket error:', errorMessage);
        // Don't reject - allow fallback to REST API
        resolve();
      };
    });
  }

  private handleWebSocketMessage(data: any) {
    const handlers = this.messageHandlers.get(data.type) || [];
    handlers.forEach(handler => handler(data));
  }

  onMessage(type: string, handler: Function) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);
  }

  offMessage(type: string, handler: Function) {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.currentUserId) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      setTimeout(() => {
        this.connectWebSocket(this.currentUserId!).catch(() => {
          // Silently handle reconnection failures - app will use REST API
        });
      }, 2000 * this.reconnectAttempts);
    } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('WebSocket reconnection attempts exhausted - using REST API only');
    }
  }

  sendWebSocketMessage(message: WebSocketMessage): boolean {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(message));
      return true;
    }
    console.warn('WebSocket not connected');
    return false;
  }

  disconnectWebSocket() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.messageHandlers.clear();
    this.currentUserId = null;
  }

  // Create a new chat session
  async createChatSession(sessionName: string, contextData?: any) {
    try {
      const response = await apiClient.post('/api/v1/chat/sessions', {
        session_name: sessionName,
        context_data: contextData || {}
      });
      return response;
    } catch (error) {
      console.error('Error creating chat session:', error);
      throw error;
    }
  }

  // Start a fortune conversation
  async startFortuneConversation(request: FortuneConversationRequest) {
    try {
      const response = await apiClient.post('/api/v1/chat/fortune-conversation', request);
      return response;
    } catch (error) {
      console.error('Error starting fortune conversation:', error);
      throw error;
    }
  }

  // Send a message in a session (REST API)
  async sendMessage(sessionId: number, content: string, metadata?: any) {
    try {
      const response = await apiClient.post(`/api/v1/chat/sessions/${sessionId}/messages`, {
        content,
        metadata
      });
      return response;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  // Send real-time message via WebSocket
  sendRealtimeMessage(sessionId: number, content: string): boolean {
    return this.sendWebSocketMessage({
      type: 'chat_message',
      session_id: sessionId,
      content: content
    });
  }

  // Get messages for a session
  async getSessionMessages(sessionId: number, limit: number = 50, offset: number = 0) {
    try {
      const response = await apiClient.get(`/api/v1/chat/sessions/${sessionId}/messages`, {
        params: { limit, offset }
      });
      return response;
    } catch (error) {
      console.error('Error getting session messages:', error);
      return { messages: [], total_count: 0, has_more: false };
    }
  }

  // Get user's chat sessions
  async getChatSessions(limit: number = 20, offset: number = 0, activeOnly: boolean = true) {
    try {
      const response = await apiClient.get('/api/v1/chat/sessions', {
        params: { limit, offset, active_only: activeOnly }
      });
      return response;
    } catch (error) {
      console.error('Error getting chat sessions:', error);
      return { sessions: [], total_count: 0 };
    }
  }

  // Deactivate a chat session
  async deactivateSession(sessionId: number) {
    try {
      const response = await apiClient.delete(`/api/v1/chat/sessions/${sessionId}`);
      return response;
    } catch (error) {
      console.error('Error deactivating session:', error);
      throw error;
    }
  }

  // Mock chat functionality for development
  async mockFortuneResponse(userMessage: string, deityId: string, fortuneNumber: number): Promise<string> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

    const responses = [
      `The divine wisdom of ${deityId} speaks to your question: "${userMessage}". Fortune #${fortuneNumber} reveals that patience and perseverance are your allies. Trust in the process and remain open to guidance.`,
      
      `Your inquiry "${userMessage}" resonates with the energy of fortune #${fortuneNumber}. The celestial signs suggest a time of transformation approaches. Embrace change with courage and maintain faith in your path.`,
      
      `The ancient wisdom embedded in fortune #${fortuneNumber} offers insight into your question: "${userMessage}". Balance is key - neither force nor complete passivity, but mindful action guided by inner wisdom.`,
      
      `Through the lens of fortune #${fortuneNumber}, your question "${userMessage}" reveals hidden opportunities. The divine suggests focusing on what you can control while releasing attachment to specific outcomes.`,
      
      `The sacred teachings within fortune #${fortuneNumber} illuminate your path regarding "${userMessage}". Trust in your intuition, for it is aligned with universal wisdom at this time.`
    ];

    return responses[Math.floor(Math.random() * responses.length)];
  }

  // Set up streaming response handlers (for real-time WebSocket streaming)
  setupStreamingHandlers(): {
    onChunk: (handler: (chunk: string) => void) => void;
    onComplete: (handler: () => void) => void;
    onTyping: (handler: (isTyping: boolean) => void) => void;
    onError: (handler: (error: string) => void) => void;
    cleanup: () => void;
  } {
    const chunkHandlers: ((chunk: string) => void)[] = [];
    const completeHandlers: (() => void)[] = [];
    const typingHandlers: ((isTyping: boolean) => void)[] = [];
    const errorHandlers: ((error: string) => void)[] = [];

    const chunkHandler = (data: any) => {
      if (data.type === 'chat_response_stream') {
        if (data.is_complete) {
          completeHandlers.forEach(handler => handler());
        } else if (data.content) {
          chunkHandlers.forEach(handler => handler(data.content));
        }
      }
    };

    const typingHandler = (data: any) => {
      if (data.type === 'chat_typing_indicator') {
        typingHandlers.forEach(handler => handler(data.is_typing));
      }
    };

    const errorHandler = (data: any) => {
      if (data.type === 'error_notification') {
        errorHandlers.forEach(handler => handler(data.error || 'Unknown error'));
      }
    };

    // Register handlers
    this.onMessage('chat_response_stream', chunkHandler);
    this.onMessage('chat_typing_indicator', typingHandler);
    this.onMessage('error_notification', errorHandler);

    return {
      onChunk: (handler) => chunkHandlers.push(handler),
      onComplete: (handler) => completeHandlers.push(handler),
      onTyping: (handler) => typingHandlers.push(handler),
      onError: (handler) => errorHandlers.push(handler),
      cleanup: () => {
        this.offMessage('chat_response_stream', chunkHandler);
        this.offMessage('chat_typing_indicator', typingHandler);
        this.offMessage('error_notification', errorHandler);
        chunkHandlers.length = 0;
        completeHandlers.length = 0;
        typingHandlers.length = 0;
        errorHandlers.length = 0;
      }
    };
  }
}

// Create singleton instance
const chatService = new ChatService();
export default chatService;