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

class ChatService {
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

  // Send a message in a session
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

  // Generate streaming response (mock for development)
  async* generateStreamingResponse(sessionId: number, userMessage: string): AsyncGenerator<string, void, unknown> {
    const fullResponse = await this.mockFortuneResponse(userMessage, 'guan_yin', 7);
    const words = fullResponse.split(' ');
    
    for (let i = 0; i < words.length; i++) {
      const chunk = words.slice(0, i + 1).join(' ');
      yield JSON.stringify({ content: chunk, complete: i === words.length - 1 });
      await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 100));
    }
  }
}

// Create singleton instance
const chatService = new ChatService();
export default chatService;