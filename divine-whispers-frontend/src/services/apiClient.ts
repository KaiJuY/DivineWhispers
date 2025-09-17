import axios from 'axios';
import { AuthState, LoginCredentials, RegisterCredentials } from '../types/index';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: any;
  private tokenRefreshInProgress = false;
  private tokenRefreshTimer: NodeJS.Timeout | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
    this.initializeTokenRefresh();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config: any) => {
        const token = this.getStoredToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: any) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response: any) => response,
      async (error: any) => {
        const originalRequest = error.config as any;
        
        if (error.response?.status === 401 && !originalRequest._retry && !this.tokenRefreshInProgress) {
          originalRequest._retry = true;
          
          try {
            await this.refreshToken();
            const token = this.getStoredToken();
            if (token && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return this.client(originalRequest);
          } catch (refreshError) {
            // Token refresh failed, clear tokens but don't force redirect
            this.clearTokens();
            console.warn('Authentication failed, user needs to re-login');
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private initializeTokenRefresh() {
    // Check for existing token on startup and schedule refresh if valid
    const token = this.getStoredToken();
    if (token) {
      const payload = this.decodeJWT(token);
      if (payload && payload.exp) {
        const now = Math.floor(Date.now() / 1000);
        const timeUntilExpiry = payload.exp - now;

        if (timeUntilExpiry > 300) { // Only schedule if more than 5 minutes left
          this.scheduleTokenRefresh(timeUntilExpiry);
          console.log('Existing token found, scheduled automatic refresh');
        } else if (timeUntilExpiry > 0) {
          // Token expires soon, try to refresh immediately
          console.log('Token expires soon, attempting immediate refresh');
          this.refreshToken().catch(() => {
            console.warn('Failed to refresh token on startup');
          });
        } else {
          // Token already expired, clear it
          console.log('Found expired token, clearing...');
          this.clearTokens();
        }
      }
    }
  }

  private getStoredToken(): string | null {
    return localStorage.getItem('divine-whispers-access-token');
  }

  private getStoredRefreshToken(): string | null {
    return localStorage.getItem('divine-whispers-refresh-token');
  }

  private setTokens(accessToken: string, refreshToken: string) {
    localStorage.setItem('divine-whispers-access-token', accessToken);
    localStorage.setItem('divine-whispers-refresh-token', refreshToken);
  }

  private clearTokens() {
    localStorage.removeItem('divine-whispers-access-token');
    localStorage.removeItem('divine-whispers-refresh-token');
    // Clear the refresh timer when tokens are cleared
    this.clearTokenRefreshTimer();
  }

  private decodeJWT(token: string): any {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      return JSON.parse(jsonPayload);
    } catch (e) {
      console.error('Error decoding JWT:', e);
      return null;
    }
  }

  private clearTokenRefreshTimer() {
    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
      this.tokenRefreshTimer = null;
    }
  }

  private scheduleTokenRefresh(expiresIn: number) {
    // Clear any existing timer
    this.clearTokenRefreshTimer();

    // Schedule refresh 5 minutes (300 seconds) before expiry
    const refreshTime = (expiresIn - 300) * 1000; // Convert to milliseconds

    if (refreshTime > 0) {
      console.log(`Scheduling token refresh in ${Math.floor(refreshTime / 1000)} seconds`);
      this.tokenRefreshTimer = setTimeout(async () => {
        try {
          console.log('Automatically refreshing token...');
          await this.refreshToken();
          console.log('Token refreshed successfully');

          // Get the new token and schedule the next refresh
          const newToken = this.getStoredToken();
          if (newToken) {
            const payload = this.decodeJWT(newToken);
            if (payload && payload.exp) {
              const now = Math.floor(Date.now() / 1000);
              const newExpiresIn = payload.exp - now;
              this.scheduleTokenRefresh(newExpiresIn);
            }
          }
        } catch (error) {
          console.error('Automatic token refresh failed:', error);
          // Optionally, you could emit an event here for the UI to handle
          // For now, we'll let the next API call handle the 401 error
        }
      }, refreshTime);
    } else {
      console.warn('Token expires too soon, cannot schedule refresh');
    }
  }

  // Authentication Methods
  async login(credentials: LoginCredentials): Promise<AuthState> {
    try {
      const response = await this.client.post('/api/v1/auth/login', {
        email: credentials.email,
        password: credentials.password
      });

      const { user, tokens } = response.data;
      this.setTokens(tokens.access_token, tokens.refresh_token);

      // Schedule automatic token refresh
      this.scheduleTokenRefresh(tokens.expires_in);

      return {
        user: {
          user_id: user.user_id,
          email: user.email,
          username: user.username,
          role: user.role,
          points_balance: user.points_balance,
          created_at: user.created_at,
          birth_date: user.birth_date,
          gender: user.gender,
          location: user.location
        },
        tokens: {
          access_token: tokens.access_token,
          refresh_token: tokens.refresh_token,
          expires_in: tokens.expires_in
        },
        isAuthenticated: true,
        loading: false
      };
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async register(credentials: RegisterCredentials): Promise<AuthState> {
    try {
      const response = await this.client.post('/api/v1/auth/register', {
        email: credentials.email,
        password: credentials.password,
        confirm_password: credentials.confirm_password,
        username: credentials.username,
        birth_date: credentials.birth_date,
        gender: credentials.gender,
        location: credentials.location
      });

      const { user, tokens } = response.data;
      this.setTokens(tokens.access_token, tokens.refresh_token);

      // Schedule automatic token refresh
      this.scheduleTokenRefresh(tokens.expires_in);

      return {
        user: {
          user_id: user.user_id,
          email: user.email,
          username: user.username,
          role: user.role,
          points_balance: user.points_balance,
          created_at: user.created_at,
          birth_date: user.birth_date,
          gender: user.gender,
          location: user.location
        },
        tokens: {
          access_token: tokens.access_token,
          refresh_token: tokens.refresh_token,
          expires_in: tokens.expires_in
        },
        isAuthenticated: true,
        loading: false
      };
    } catch (error) {
      console.error('Register error:', error);
      throw error;
    }
  }

  async refreshToken(): Promise<void> {
    if (this.tokenRefreshInProgress) {
      return;
    }

    this.tokenRefreshInProgress = true;
    
    try {
      const refreshToken = this.getStoredRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await this.client.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken
      });

      const { tokens } = response.data;
      this.setTokens(tokens.access_token, tokens.refresh_token);
    } finally {
      this.tokenRefreshInProgress = false;
    }
  }

  async logout(): Promise<void> {
    try {
      const refreshToken = this.getStoredRefreshToken();
      await this.client.post('/api/v1/auth/logout', {
        refresh_token: refreshToken
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearTokens();
    }
  }

  async getCurrentUser(): Promise<any> {
    try {
      const response = await this.client.get('/api/v1/auth/me');
      return response.data;
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  }

  async verifyToken(): Promise<boolean> {
    try {
      await this.client.post('/api/v1/auth/verify-token');
      return true;
    } catch (error) {
      return false;
    }
  }

  // Health Check
  async healthCheck(): Promise<boolean> {
    try {
      await this.client.get('/health');
      return true;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  // Generic API methods for other services
  async get(url: string, params?: any): Promise<any> {
    const response = await this.client.get(url, { params });
    return response.data;
  }

  async post(url: string, data?: any): Promise<any> {
    const response = await this.client.post(url, data);
    return response.data;
  }

  async put(url: string, data?: any): Promise<any> {
    const response = await this.client.put(url, data);
    return response.data;
  }

  async delete(url: string): Promise<any> {
    const response = await this.client.delete(url);
    return response.data;
  }
}

// Create singleton instance
const apiClient = new ApiClient();
export default apiClient;