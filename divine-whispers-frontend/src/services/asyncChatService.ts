/**
 * Simplified Async Chat Service using Task Queue + SSE
 * Replaces the complex WebSocket implementation
 */

import apiClient from './apiClient';

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
  type: 'status' | 'progress' | 'streaming_progress' | 'complete' | 'error' | 'ping';
  status?: string;
  progress?: number;
  status_code?: number;  // Backend sends numeric status code
  message?: string;      // Deprecated: kept for backward compatibility
  result?: TaskResult;
  error?: string;
  task_id?: string;      // For streaming_progress events
  data?: any;            // Additional data from streaming_progress
  timestamp?: string;    // Timestamp from streaming_progress
  elapsed_seconds?: number; // Elapsed time from streaming_progress
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
  private retryAttempts = new Map<string, number>();
  private maxRetries = 3;

  // Map frontend deity IDs to backend deity IDs
  private mapDeityId(frontendDeityId: string): string {
    const deityMapping: Record<string, string> = {
      'zhusheng': 'mazu',
      'mazu': 'mazu',
      'guan_yin': 'guan_yin',
      'guan_yu': 'guan_yu',
      'yue_lao': 'yue_lao',
      'tianhou': 'mazu', // Tianhou is another name for Mazu
      'guanyin100': 'guan_yin', // GuanYin variations
      'asakusa': 'guan_yin', // Japanese temple, map to GuanYin
      'erawan': 'guan_yin', // Thai shrine, map to GuanYin
    };

    return deityMapping[frontendDeityId] || 'mazu'; // Default to mazu if unknown
  }

  /**
   * Submit a fortune question for async processing
   */
  async askQuestion(request: FortuneQuestionRequest): Promise<TaskResponse> {
    // Map frontend deity ID to backend deity ID
    const mappedRequest = {
      ...request,
      deity_id: this.mapDeityId(request.deity_id)
    };

    try {
      console.log('🔄 AsyncChatService: Sending request to backend...');
      const response = await apiClient.post(`${this.baseUrl}/ask-question`, mappedRequest);
      console.log('✅ AsyncChatService: Successfully got response from backend');
      return response;
    } catch (error: any) {
      console.error('❌ AsyncChatService ERROR:', error);
      console.error('❌ AsyncChatService Error code:', error?.code);
      console.error('❌ AsyncChatService Error response:', error?.response);
      console.error('❌ AsyncChatService Error response data:', error?.response?.data);

      // Handle authentication errors specifically
      if (error.code === 'AUTH_FAILED') {
        console.log('🔐 AsyncChatService: Detected AUTH_FAILED error');
        throw new Error('Authentication failed, please log in again');
      }

      // Check HTTP response for auth errors
      if (error.response?.status === 401) {
        console.log('🔐 AsyncChatService: Detected HTTP 401 error');
        throw new Error('Authentication failed, please log in again');
      }

      // Check for specific auth error messages
      const errorData = error.response?.data;
      if (errorData?.error?.message?.includes('Authorization header missing')) {
        console.log('🔐 AsyncChatService: Detected authorization header missing');
        throw new Error('Authentication failed, please log in again');
      }

      const errorMessage = error.response?.data?.detail ||
                          error.response?.data?.error?.message ||
                          error.message ||
                          'Failed to submit question';

      console.log('❌ AsyncChatService: Throwing error with message:', errorMessage);
      throw new Error(errorMessage);
    }
  }

  /**
   * Subscribe to task progress updates via SSE with automatic token refresh
   */
  subscribeToProgress(
    taskId: string,
    onProgress: (progress: TaskProgress) => void,
    onError?: (error: Error) => void
  ): () => void {
    // Close existing connection for this task
    this.unsubscribeFromProgress(taskId);

    // Reset retry counter for this task
    this.retryAttempts.set(taskId, 0);

    this.createSSEConnection(taskId, onProgress, onError);

    // Return cleanup function
    return () => this.unsubscribeFromProgress(taskId);
  }

  /**
   * Create SSE connection with token refresh handling
   */
  private createSSEConnection(
    taskId: string,
    onProgress: (progress: TaskProgress) => void,
    onError?: (error: Error) => void
  ): void {
    const token = localStorage.getItem('divine-whispers-access-token');

    if (!token) {
      onError?.(new Error('No authentication token available'));
      return;
    }

    console.log(`Creating SSE connection for task ${taskId}`);

    const eventSource = new EventSource(
      `/api/v1/async-chat/sse/${taskId}?token=${encodeURIComponent(token)}`,
      {
        withCredentials: true,
      }
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as TaskProgress;
        console.log('SSE message received:', data);

        // Reset retry counter on successful message
        this.retryAttempts.set(taskId, 0);

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

    eventSource.onerror = (event: any) => {
      console.error('SSE connection error for task', taskId, ':', event);

      // Check if this is a 401 error (token expired)
      if (event.target?.readyState === EventSource.CLOSED) {
        // Connection was closed, check if we should retry with token refresh
        const retryCount = this.retryAttempts.get(taskId) || 0;

        if (retryCount < this.maxRetries) {
          console.log(`Attempting SSE connection retry ${retryCount + 1}/${this.maxRetries} for task ${taskId}`);
          this.retryAttempts.set(taskId, retryCount + 1);

          // Close current connection
          this.unsubscribeFromProgress(taskId);

          // Try to refresh token and reconnect
          setTimeout(async () => {
            try {
              // Force token refresh by making a test API call
              await apiClient.get('/api/v1/auth/me');

              // Recreate connection with fresh token
              this.createSSEConnection(taskId, onProgress, onError);
            } catch (refreshError) {
              console.error('Token refresh failed during SSE retry:', refreshError);
              onError?.(new Error('Authentication failed, please log in again'));
            }
          }, 1000 * retryCount); // Exponential backoff
        } else {
          console.error(`Max SSE retry attempts reached for task ${taskId}`);
          onError?.(new Error('Connection failed after multiple attempts'));
        }
      } else {
        onError?.(new Error('Connection to server lost'));
      }
    };

    this.activeConnections.set(taskId, eventSource);
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
    // Clean up retry counter
    this.retryAttempts.delete(taskId);
  }

  /**
   * Get task status (fallback for SSE)
   */
  async getTaskStatus(taskId: string): Promise<any> {
    try {
      return await apiClient.get(`${this.baseUrl}/task/${taskId}`);
    } catch (error: any) {
      if (error.code === 'AUTH_FAILED') {
        throw new Error('Authentication failed, please log in again');
      }

      const errorMessage = error.response?.data?.detail || error.message || 'Failed to get task status';
      throw new Error(errorMessage);
    }
  }

  /**
   * Get user's chat history
   */
  async getChatHistory(limit = 10, offset = 0): Promise<{
    history: ChatHistoryItem[];
    total_count: number;
    has_more: boolean;
  }> {
    try {
      return await apiClient.get(`${this.baseUrl}/history`, { limit, offset });
    } catch (error: any) {
      if (error.code === 'AUTH_FAILED') {
        throw new Error('Authentication failed, please log in again');
      }

      const errorMessage = error.response?.data?.detail || error.message || 'Failed to get chat history';
      throw new Error(errorMessage);
    }
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