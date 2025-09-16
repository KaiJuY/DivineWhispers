/**
 * Simplified Async Chat Service using Task Queue + SSE
 * Replaces the complex WebSocket implementation
 */

// Types
export interface FortuneQuestionRequest {
  deity_id: string;
  fortune_number: number;
  question: string;
  context?: Record<string, any>;
}

export interface TaskResponse {
  task_id: string;
  sse_url: string;
  status: string;
  message: string;
}

export interface TaskResult {
  response: string;
  confidence: number;
  sources_used: string[];
  processing_time_ms: number;
  can_generate_report: boolean;
}

export interface TaskProgress {
  type: 'status' | 'progress' | 'complete' | 'error' | 'ping';
  status?: string;
  progress?: number;
  message?: string;
  result?: TaskResult;
  error?: string;
}

export interface ChatHistoryItem {
  task_id: string;
  deity_id: string;
  fortune_number: number;
  question: string;
  status: string;
  response?: string;
  created_at: string;
  completed_at?: string;
}

// Service Class
export class AsyncChatService {
  private baseUrl = '/api/v1/async-chat';
  private activeConnections = new Map<string, EventSource>();

  /**
   * Submit a fortune question for async processing
   */
  async askQuestion(request: FortuneQuestionRequest): Promise<TaskResponse> {
    const response = await fetch(`${this.baseUrl}/ask-question`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Failed to submit question');
    }

    return response.json();
  }

  /**
   * Subscribe to task progress updates via SSE
   */
  subscribeToProgress(
    taskId: string,
    onProgress: (progress: TaskProgress) => void,
    onError?: (error: Error) => void
  ): () => void {
    // Close existing connection for this task
    this.unsubscribeFromProgress(taskId);

    const eventSource = new EventSource(
      `/api/v1/async-chat/sse/${taskId}`,
      {
        withCredentials: true,
      }
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as TaskProgress;
        onProgress(data);

        // Auto-close connection when task is complete or failed
        if (data.type === 'complete' || data.type === 'error') {
          this.unsubscribeFromProgress(taskId);
        }
      } catch (err) {
        console.error('Failed to parse SSE message:', err);
        onError?.(new Error('Failed to parse progress update'));
      }
    };

    eventSource.onerror = (event) => {
      console.error('SSE connection error:', event);
      onError?.(new Error('Connection to server lost'));
      this.unsubscribeFromProgress(taskId);
    };

    this.activeConnections.set(taskId, eventSource);

    // Return cleanup function
    return () => this.unsubscribeFromProgress(taskId);
  }

  /**
   * Unsubscribe from task progress updates
   */
  unsubscribeFromProgress(taskId: string): void {
    const eventSource = this.activeConnections.get(taskId);
    if (eventSource) {
      eventSource.close();
      this.activeConnections.delete(taskId);
    }
  }

  /**
   * Get task status (fallback for SSE)
   */
  async getTaskStatus(taskId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/task/${taskId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Failed to get task status');
    }

    return response.json();
  }

  /**
   * Get user's chat history
   */
  async getChatHistory(limit = 10, offset = 0): Promise<{
    history: ChatHistoryItem[];
    total_count: number;
    has_more: boolean;
  }> {
    const response = await fetch(
      `${this.baseUrl}/history?limit=${limit}&offset=${offset}`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Failed to get chat history');
    }

    return response.json();
  }

  /**
   * Clean up all active connections
   */
  cleanup(): void {
    this.activeConnections.forEach((_, taskId) => {
      this.unsubscribeFromProgress(taskId);
    });
  }
}

// Export singleton instance
export const asyncChatService = new AsyncChatService();

// Auto-cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    asyncChatService.cleanup();
  });
}