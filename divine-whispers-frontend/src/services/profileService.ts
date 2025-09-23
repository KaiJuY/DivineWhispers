import apiClient from './apiClient';

export interface UserProfile {
  user_id: number;
  email: string;
  full_name?: string;
  phone?: string;
  birth_date?: string;
  location?: string;
  preferred_language?: string;
  points_balance: number;
  role: 'user' | 'admin' | 'moderator';
  status: 'active' | 'suspended' | 'inactive' | 'banned';
  created_at: string;
  updated_at: string;
}

export interface UserProfileUpdate {
  full_name?: string;
  phone?: string;
  birth_date?: string;
  location?: string;
  preferred_language?: string;
}

export interface UserReport {
  id: string;
  created_at: string;
  type: string;
  title: string;
  summary: string;
  status: string;
}

export interface ReportsResponse {
  reports: UserReport[];
  total_count: number;
  has_more: boolean;
}

export interface Transaction {
  txn_id: number;
  amount: number;
  type: 'deposit' | 'spend' | 'refund' | 'transfer';
  status: 'pending' | 'success' | 'failed';
  description: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionHistoryResponse {
  transactions: Transaction[];
  total_count: number;
  page_info: {
    current_page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
  summary: {
    total_spent: number;
    total_deposited: number;
    net_balance_change: number;
  };
}

export interface PurchaseHistoryResponse {
  purchases: PurchaseRecord[];
  total_count: number;
  has_more: boolean;
}

export interface PurchaseRecord {
  purchase_id: string;
  amount: number;
  description: string;
  payment_method: string;
  package_type: string;
  created_at: string;
  status: string;
}

class ProfileService {
  async getUserProfile(): Promise<UserProfile> {
    try {
      const response = await apiClient.get('/api/v1/auth/profile');
      return response;
    } catch (error: any) {
      throw new Error(`Failed to fetch profile: ${error.message}`);
    }
  }

  async updateUserProfile(profileData: UserProfileUpdate): Promise<UserProfile> {
    try {
      const response = await apiClient.put('/api/v1/auth/profile', profileData);
      return response;
    } catch (error: any) {
      throw new Error(`Failed to update profile: ${error.message}`);
    }
  }

  async getUserReports(limit: number = 10, offset: number = 0): Promise<ReportsResponse> {
    try {
      const response = await apiClient.get('/api/v1/auth/profile/reports', {
        limit: limit.toString(),
        offset: offset.toString()
      });
      return response;
    } catch (error: any) {
      throw new Error(`Failed to fetch reports: ${error.message}`);
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    try {
      await apiClient.put('/api/v1/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: newPassword
      });
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || `Failed to change password: ${error.message}`);
    }
  }

  async logoutUser(): Promise<void> {
    try {
      await apiClient.logout();
    } catch (error: any) {
      console.error('Logout error:', error);
      // apiClient.logout() already handles token cleanup
    }
  }

  async getTransactionHistory(limit: number = 10, offset: number = 0): Promise<TransactionHistoryResponse> {
    try {
      const response = await apiClient.get('/api/v1/transactions', {
        limit: limit.toString(),
        offset: offset.toString()
      });
      return response;
    } catch (error: any) {
      throw new Error(`Failed to fetch transaction history: ${error.message}`);
    }
  }

  async getPurchaseHistory(limit: number = 10, offset: number = 0): Promise<PurchaseHistoryResponse> {
    try {
      const response = await apiClient.get('/api/v1/purchases', {
        limit: limit.toString(),
        offset: offset.toString()
      });
      return response;
    } catch (error: any) {
      throw new Error(`Failed to fetch purchase history: ${error.message}`);
    }
  }
}

export const profileService = new ProfileService();