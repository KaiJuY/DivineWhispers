import apiClient from './apiClient';

// Types for purchase-related data structures
export interface CoinPackage {
  id: string;
  name: string;
  coins: number;
  price_usd: number;
  bonus_coins: number;
  description: string;
  popular: boolean;
}

export interface WalletBalance {
  wallet_id: number;
  user_id: number;
  balance: number;
  pending_amount: number;
  available_balance: number;
  last_updated: string;
}

export interface PurchaseSession {
  purchase_id: string;
  package: CoinPackage;
  payment_method: string;
  total_amount: number;
  status: string;
  payment_url?: string;
  expires_at: number;
  message: string;
}

export interface PurchaseCompletion {
  purchase_id: string;
  status: string;
  coins_added: number;
  breakdown: {
    purchased: number;
    bonus: number;
  };
  new_balance: number;
  transaction_id: number;
  message: string;
}

export interface PurchaseHistoryItem {
  purchase_id: string;
  amount: number;
  description: string;
  payment_method: string;
  package_type: string;
  created_at: string;
  status: string;
}

export interface PurchaseHistory {
  purchases: PurchaseHistoryItem[];
  total_count: number;
  has_more: boolean;
}

export interface PackagesResponse {
  packages: CoinPackage[];
  currency: string;
  payment_methods: string[];
}

class PurchaseService {
  /**
   * Get available coin packages from backend
   */
  async getPackages(): Promise<PackagesResponse> {
    try {
      const response = await apiClient.get('/api/v1/packages');
      return response;
    } catch (error: any) {
      console.error('Error fetching coin packages:', error);

      // Return fallback packages if API fails (for development/demo)
      return {
        packages: [
          {
            id: 'starter_pack',
            name: 'Starter Pack',
            coins: 5,
            price_usd: 1.00,
            bonus_coins: 0,
            description: 'Perfect for trying out fortune readings',
            popular: false
          },
          {
            id: 'value_pack',
            name: 'Value Pack',
            coins: 25,
            price_usd: 4.00,
            bonus_coins: 0,
            description: 'Most popular choice with bonus coins',
            popular: true
          },
          {
            id: 'premium_pack',
            name: 'Premium Pack',
            coins: 100,
            price_usd: 10.00,
            bonus_coins: 0,
            description: 'Best value for frequent users',
            popular: false
          }
        ],
        currency: 'USD',
        payment_methods: ['credit_card', 'paypal', 'apple_pay', 'google_pay']
      };
    }
  }

  /**
   * Get user's current wallet balance
   */
  async getWalletBalance(): Promise<WalletBalance> {
    try {
      const response = await apiClient.get('/api/v1/balance');
      return response;
    } catch (error: any) {
      console.error('Error fetching wallet balance:', error);

      // Handle authentication errors
      if (error.response?.status === 401) {
        throw new Error('Authentication required. Please log in again.');
      }

      // Handle other errors
      const errorMessage = error.response?.data?.detail || 'Failed to fetch wallet balance';
      throw new Error(errorMessage);
    }
  }

  /**
   * Initiate coin purchase process
   */
  async initiatePurchase(packageId: string, paymentMethod: string): Promise<PurchaseSession> {
    try {
      // Use query parameters as expected by the backend
      const response = await apiClient.post(`/api/v1/purchase?package_id=${packageId}&payment_method=${paymentMethod}`);

      return response;
    } catch (error: any) {
      console.error('Error initiating purchase:', error);

      // Handle specific error cases
      if (error.response?.status === 401) {
        throw new Error('Authentication required. Please log in again.');
      }

      if (error.response?.status === 404) {
        throw new Error('Selected package not found. Please try again.');
      }

      if (error.response?.status === 400) {
        const errorDetail = error.response?.data?.detail || 'Invalid purchase request';
        throw new Error(errorDetail);
      }

      const errorMessage = error.response?.data?.detail || 'Failed to initiate purchase';
      throw new Error(errorMessage);
    }
  }

  /**
   * Complete coin purchase after payment confirmation
   */
  async completePurchase(purchaseId: string, paymentConfirmation: any = {}): Promise<PurchaseCompletion> {
    try {
      const response = await apiClient.post(`/api/v1/purchase/${purchaseId}/complete`, paymentConfirmation);
      return response;
    } catch (error: any) {
      console.error('Error completing purchase:', error);

      // Handle specific error cases
      if (error.response?.status === 401) {
        throw new Error('Authentication required. Please log in again.');
      }

      if (error.response?.status === 404) {
        throw new Error('Purchase session not found or expired.');
      }

      if (error.response?.status === 400) {
        const errorDetail = error.response?.data?.detail || 'Invalid payment confirmation';
        throw new Error(errorDetail);
      }

      const errorMessage = error.response?.data?.detail || 'Failed to complete purchase';
      throw new Error(errorMessage);
    }
  }

  /**
   * Get user's purchase history
   */
  async getPurchaseHistory(limit: number = 10, offset: number = 0): Promise<PurchaseHistory> {
    try {
      const response = await apiClient.get('/api/v1/purchases', {
        params: { limit, offset }
      });

      return response;
    } catch (error: any) {
      console.error('Error fetching purchase history:', error);

      // Handle authentication errors
      if (error.response?.status === 401) {
        throw new Error('Authentication required. Please log in again.');
      }

      // Return empty history on error
      return {
        purchases: [],
        total_count: 0,
        has_more: false
      };
    }
  }

  /**
   * Get wallet overview with balance and recent transactions
   */
  async getWalletOverview() {
    try {
      const response = await apiClient.get('/api/v1/');
      return response;
    } catch (error: any) {
      console.error('Error fetching wallet overview:', error);

      if (error.response?.status === 401) {
        throw new Error('Authentication required. Please log in again.');
      }

      const errorMessage = error.response?.data?.detail || 'Failed to fetch wallet overview';
      throw new Error(errorMessage);
    }
  }

  /**
   * Validate purchase data before initiating purchase
   */
  validatePurchaseData(packageId: string, paymentMethod: string): { isValid: boolean; error?: string } {
    if (!packageId || typeof packageId !== 'string') {
      return { isValid: false, error: 'Package ID is required' };
    }

    if (!paymentMethod || typeof paymentMethod !== 'string') {
      return { isValid: false, error: 'Payment method is required' };
    }

    // Validate payment method
    const validPaymentMethods = ['card', 'paypal', 'apple-pay', 'google-pay'];
    if (!validPaymentMethods.includes(paymentMethod)) {
      return { isValid: false, error: 'Invalid payment method selected' };
    }

    return { isValid: true };
  }

  /**
   * Format currency amount for display
   */
  formatCurrency(amount: number, currency: string = 'USD'): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  }

  /**
   * Calculate price per coin for a package
   */
  calculatePricePerCoin(package_: CoinPackage): number {
    const totalCoins = package_.coins + package_.bonus_coins;
    return totalCoins > 0 ? package_.price_usd / totalCoins : 0;
  }
}

// Create singleton instance
const purchaseService = new PurchaseService();
export default purchaseService;