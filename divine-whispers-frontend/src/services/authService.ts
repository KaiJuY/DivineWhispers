import apiClient from './apiClient';
import { AuthState, LoginCredentials, RegisterCredentials } from '../types/index';

class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthState> {
    try {
      const authState = await apiClient.login(credentials);
      return authState;
    } catch (error: any) {
      // Handle API errors
      const errorMessage = error.response?.data?.error?.message || 'Login failed';
      throw new Error(errorMessage);
    }
  }

  async register(credentials: RegisterCredentials): Promise<AuthState> {
    try {
      const authState = await apiClient.register(credentials);
      return authState;
    } catch (error: any) {
      // Handle API errors
      const errorMessage = error.response?.data?.error?.message || 'Registration failed';
      throw new Error(errorMessage);
    }
  }

  async logout(): Promise<void> {
    try {
      await apiClient.logout();
    } catch (error: any) {
      console.error('Logout error:', error);
      // Continue with logout even if API call fails
    }
  }

  async getCurrentUser(): Promise<any> {
    try {
      return await apiClient.getCurrentUser();
    } catch (error: any) {
      const errorMessage = error.response?.data?.error?.message || 'Failed to get user info';
      throw new Error(errorMessage);
    }
  }

  async verifyToken(): Promise<boolean> {
    try {
      return await apiClient.verifyToken();
    } catch (error) {
      return false;
    }
  }

  async refreshToken(): Promise<void> {
    try {
      await apiClient.refreshToken();
    } catch (error: any) {
      throw new Error('Token refresh failed');
    }
  }

  // Check if backend is available
  async healthCheck(): Promise<boolean> {
    try {
      return await apiClient.healthCheck();
    } catch (error) {
      return false;
    }
  }

  // Get stored token for checking authentication state
  getStoredToken(): string | null {
    return localStorage.getItem('divine-whispers-access-token');
  }

  // Check if user has valid stored session
  hasValidSession(): boolean {
    const token = this.getStoredToken();
    const refreshToken = localStorage.getItem('divine-whispers-refresh-token');
    return !!(token && refreshToken);
  }
}

const authService = new AuthService();
export default authService;