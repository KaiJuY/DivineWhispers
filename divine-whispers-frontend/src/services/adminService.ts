import apiClient from './apiClient';

// Types for Admin API responses
export interface DashboardOverview {
  users: {
    total: number;
    active: number;
    new_today: number;
    suspended: number;
  };
  revenue: {
    total_transactions: number;
    total_revenue: number;
    currency: string;
  };
  engagement: {
    chat_sessions: number;
    chat_messages: number;
    fortune_readings: number;
    success_rate: number;
  };
  system: {
    uptime: string;
    api_calls_today: number;
    error_rate: string;
  };
}

export interface Customer {
  user_id: number;
  email: string;
  full_name?: string;
  status: string;
  role: string;
  created_at: string;
  updated_at: string;
  last_login?: string;
  wallet_balance: number;
  total_spent: number;
  recent_activity?: string;
}

export interface CustomerListResponse {
  customers: Customer[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
  filters: {
    search?: string;
    status?: string;
    sort_by: string;
    sort_order: string;
  };
}

export interface FAQ {
  id: number;
  question: string;
  answer: string;
  category: string;
  is_published: boolean;
  view_count: number;
  created_at: string;
  updated_at: string;
  display_order: number;
  tags?: string[];
}

export interface FAQListResponse {
  faqs: FAQ[];
  total_count: number;
  categories: string[];
}

export interface SystemStats {
  total_users: number;
  role_distribution: Array<{
    role: string;
    count: number;
    percentage: number;
    active_count: number;
    suspended_count: number;
  }>;
  permission_usage: Array<{
    permission: string;
    category: string;
    users_with_permission: number;
    usage_count: number;
    last_used?: string;
  }>;
  recent_role_changes: number;
  recent_suspensions: number;
  critical_permission_usage: number;
}

export interface UserAnalytics {
  summary: {
    total_users: number;
    new_users_period: number;
    active_users: number;
    growth_rate: number;
    period: string;
  };
  charts: {
    daily_registrations: Array<{
      date: string;
      registrations: number;
    }>;
    status_breakdown: Record<string, number>;
    role_distribution: Record<string, number>;
  };
  insights: {
    activation_rate: number;
    avg_daily_signups?: number;
  };
}

export interface RevenueAnalytics {
  summary: {
    total_revenue: number;
    period_revenue: number;
    avg_transaction_value: number;
    period: string;
  };
  charts: {
    daily_revenue: Array<{
      date: string;
      revenue: number;
      transactions: number;
    }>;
    top_spenders: Array<{
      email: string;
      total_spent: number;
    }>;
  };
  insights: {
    avg_daily_revenue?: number;
    revenue_growth: string;
  };
}

export interface EngagementAnalytics {
  summary: {
    total_chat_sessions: number;
    total_chat_messages: number;
    avg_messages_per_session: number;
    total_fortune_readings: number;
    reading_success_rate: number;
    active_chatters: number;
    period: string;
  };
  charts: {
    daily_engagement: Array<{
      date: string;
      sessions: number;
      messages: number;
    }>;
  };
  insights: {
    engagement_trend: string;
    avg_daily_sessions?: number;
  };
}

class AdminService {
  // Dashboard Overview
  async getDashboardOverview(): Promise<DashboardOverview> {
    return await apiClient.get('/api/v1/admin/dashboard/overview');
  }

  // System Statistics
  async getSystemStats(): Promise<SystemStats> {
    return await apiClient.get('/api/v1/admin/stats');
  }

  // Customer Management
  async getCustomers(params: {
    page?: number;
    limit?: number;
    search?: string;
    status_filter?: string;
    sort_by?: string;
    sort_order?: string;
  } = {}): Promise<CustomerListResponse> {
    return await apiClient.get('/api/v1/admin/customers', params);
  }

  async getCustomerDetails(userId: number): Promise<any> {
    return await apiClient.get(`/api/v1/admin/customers/${userId}`);
  }

  async performCustomerAction(
    userId: number,
    action: string,
    reason?: string
  ): Promise<any> {
    return await apiClient.post(`/api/v1/admin/customers/${userId}/actions`, {
      action,
      reason
    });
  }

  // User Management (from existing admin.py endpoints)
  async getUsers(params: {
    page?: number;
    per_page?: number;
    role?: string;
    status?: string;
    search?: string;
  } = {}): Promise<any> {
    return await apiClient.get('/api/v1/admin/users', params);
  }

  async getUserDetails(userId: number): Promise<any> {
    return await apiClient.get(`/api/v1/admin/users/${userId}`);
  }

  async createUser(userData: {
    email: string;
    password: string;
    role: string;
    initial_points?: number;
  }): Promise<any> {
    return await apiClient.post('/api/v1/admin/users', userData);
  }

  async changeUserRole(
    userId: number,
    roleData: {
      target_user_id: number;
      new_role: string;
      reason?: string;
    }
  ): Promise<any> {
    return await apiClient.put(`/api/v1/admin/users/${userId}/role`, roleData);
  }

  async suspendUser(
    userId: number,
    suspensionData: {
      target_user_id: number;
      reason?: string;
    }
  ): Promise<any> {
    return await apiClient.put(`/api/v1/admin/users/${userId}/suspend`, suspensionData);
  }

  async activateUser(
    userId: number,
    activationData: {
      target_user_id: number;
      reason?: string;
    }
  ): Promise<any> {
    return await apiClient.put(`/api/v1/admin/users/${userId}/activate`, activationData);
  }

  async adjustUserPoints(
    userId: number,
    adjustmentData: {
      target_user_id: number;
      amount: number;
      reason?: string;
      adjustment_type: string;
    }
  ): Promise<any> {
    return await apiClient.put(`/api/v1/admin/users/${userId}/points`, adjustmentData);
  }

  async deleteUser(
    userId: number,
    deletionData: {
      target_user_id: number;
      reason?: string;
      permanent?: boolean;
      transfer_data_to?: number;
    }
  ): Promise<any> {
    return await apiClient.delete(`/api/v1/admin/users/${userId}`, deletionData);
  }

  // FAQ Management
  async getFAQs(params: {
    category?: string;
    published_only?: boolean;
    page?: number;
    limit?: number;
  } = {}): Promise<FAQListResponse> {
    return await apiClient.get('/api/v1/admin/faq', params);
  }

  async createFAQ(faqData: {
    question: string;
    answer: string;
    category: string;
    tags?: string[];
    display_order?: number;
    is_published?: boolean;
  }): Promise<FAQ> {
    return await apiClient.post('/api/v1/admin/faq', faqData);
  }

  async updateFAQ(faqId: number, faqData: Partial<FAQ>): Promise<FAQ> {
    return await apiClient.put(`/api/v1/admin/faq/${faqId}`, faqData);
  }

  async deleteFAQ(faqId: number): Promise<any> {
    return await apiClient.delete(`/api/v1/admin/faq/${faqId}`);
  }

  async getFAQAnalytics(): Promise<any> {
    return await apiClient.get('/api/v1/admin/faq/analytics');
  }

  // Analytics
  async getUserAnalytics(period: string = '30d'): Promise<UserAnalytics> {
    return await apiClient.get('/api/v1/admin/analytics/users', { period });
  }

  async getRevenueAnalytics(period: string = '30d'): Promise<RevenueAnalytics> {
    return await apiClient.get('/api/v1/admin/analytics/revenue', { period });
  }

  async getEngagementAnalytics(period: string = '30d'): Promise<EngagementAnalytics> {
    return await apiClient.get('/api/v1/admin/analytics/engagement', { period });
  }

  async getSystemAnalytics(): Promise<any> {
    return await apiClient.get('/api/v1/admin/analytics/system');
  }

  // Audit Logs
  async getAuditLogs(params: {
    page?: number;
    per_page?: number;
    user_id?: number;
    action?: string;
    resource_type?: string;
    start_date?: string;
    end_date?: string;
    critical_only?: boolean;
  } = {}): Promise<any> {
    return await apiClient.get('/api/v1/admin/audit-logs', params);
  }

  // Permissions and Roles
  async getPermissions(): Promise<any> {
    return await apiClient.get('/api/v1/admin/permissions');
  }

  async getRoles(): Promise<any> {
    return await apiClient.get('/api/v1/admin/roles');
  }

  async checkPermission(permissionData: {
    permission: string;
    resource_owner_id?: number;
  }): Promise<any> {
    return await apiClient.post('/api/v1/admin/check-permission', permissionData);
  }

  async checkPermissionsBulk(permissionData: {
    permissions: string[];
    resource_owner_id?: number;
  }): Promise<any> {
    return await apiClient.post('/api/v1/admin/check-permissions-bulk', permissionData);
  }

  // Export
  async exportReport(params: {
    report_type: string;
    format?: string;
    period?: string;
  }): Promise<any> {
    return await apiClient.get('/api/v1/admin/reports/export', params);
  }

  // Poem Management
  async getPoems(params: {
    page?: number;
    limit?: number;
    deity_filter?: string;
    search?: string;
  } = {}): Promise<any> {
    return await apiClient.get('/api/v1/admin/poems', params);
  }

  // Reports Storage
  async getReports(params: {
    page?: number;
    limit?: number;
    user_search?: string;
    deity_filter?: string;
    date_filter?: string;
  } = {}): Promise<any> {
    return await apiClient.get('/api/v1/admin/reports', params);
  }

  async deleteReport(reportId: string): Promise<any> {
    return await apiClient.delete(`/api/v1/admin/reports/${reportId}`);
  }
}

// Create singleton instance
const adminService = new AdminService();
export default adminService;