import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { AppStore, AuthState, Deity, PoemCollection, ConsultationResponse, PageType, Report, Language, LoginCredentials, RegisterCredentials } from '../types';
import { mockReports } from '../utils/mockData';
import authService from '../services/authService';
import purchaseService, { type WalletBalance, type PurchaseSession, type PurchaseCompletion, type CoinPackage } from '../services/purchaseService';

// Language detection function
const detectInitialLanguage = (): Language => {
  // Check localStorage first
  const storedLanguage = localStorage.getItem('divine-whispers-language');
  if (storedLanguage && ['en', 'zh', 'jp'].includes(storedLanguage)) {
    return storedLanguage as Language;
  }
  
  // Check browser language
  const browserLang = navigator.language.split('-')[0];
  switch (browserLang) {
    case 'zh':
      return 'zh';
    case 'ja':
      return 'jp';
    default:
      return 'en';
  }
};

const useAppStore = create<AppStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Navigation (now deprecated - use React Router instead)
        currentPage: 'landing' as PageType,
        setCurrentPage: (page: PageType) => set({ currentPage: page }),

        // New navigation function that will use React Router
        navigateToPage: (page: PageType, navigate?: (path: string) => void) => {
          // Update store state for backward compatibility
          set({ currentPage: page });

          // Navigate using React Router if navigate function is provided
          if (navigate) {
            const pageRoutes: Record<PageType, string> = {
              'landing': '/',
              'home': '/home',
              'deities': '/deities',
              'deity-selection': '/deities',
              'fortune-selection': '/fortune-selection',
              'fortune-analysis': '/fortune-analysis',
              'purchase': '/purchase',
              'account': '/account',
              'admin': '/admin',
              'contact': '/contact',
              'report': '/report',
              'auth-test': '/auth-test'
            };

            const route = pageRoutes[page] || '/';
            navigate(route);
          }
        },

        // Language
        currentLanguage: detectInitialLanguage(),
        setCurrentLanguage: (language: Language) => {
          // Store language in localStorage for persistence
          localStorage.setItem('divine-whispers-language', language);
          set({ currentLanguage: language });
        },

        // Authentication
        auth: {
          user: null,
          tokens: null,
          isAuthenticated: false,
          loading: false
        } as AuthState,
        setAuth: (authUpdates: Partial<AuthState>) => 
          set((state) => ({ 
            auth: { ...state.auth, ...authUpdates } 
          })),
        
        // Authentication Actions
        login: async (credentials: LoginCredentials) => {
          set((state) => ({ 
            auth: { ...state.auth, loading: true } 
          }));
          
          try {
            const authState = await authService.login(credentials);
            set({ auth: authState });
            return authState;
          } catch (error: any) {
            set((state) => ({ 
              auth: { ...state.auth, loading: false, isAuthenticated: false } 
            }));
            throw error;
          }
        },

        register: async (credentials: RegisterCredentials) => {
          set((state) => ({ 
            auth: { ...state.auth, loading: true } 
          }));
          
          try {
            const authState = await authService.register(credentials);
            set({ auth: authState });
            return authState;
          } catch (error: any) {
            set((state) => ({ 
              auth: { ...state.auth, loading: false, isAuthenticated: false } 
            }));
            throw error;
          }
        },

        logout: async () => {
          set((state) => ({ 
            auth: { ...state.auth, loading: true } 
          }));
          
          try {
            await authService.logout();
            set({ 
              auth: {
                user: null,
                tokens: null,
                isAuthenticated: false,
                loading: false
              }
            });
          } catch (error: any) {
            console.error('Logout error:', error);
            // Clear auth state even if logout API fails
            set({ 
              auth: {
                user: null,
                tokens: null,
                isAuthenticated: false,
                loading: false
              }
            });
          }
        },

        verifyAuth: async () => {
          // Check if we have stored tokens
          if (!authService.hasValidSession()) {
            return false;
          }

          set((state) => ({ 
            auth: { ...state.auth, loading: true } 
          }));

          try {
            let user = await authService.getCurrentUser();
            set({ 
              auth: {
                user,
                tokens: {
                  access_token: authService.getStoredToken() || '',
                  refresh_token: localStorage.getItem('divine-whispers-refresh-token') || '',
                  expires_in: 3600 // Default value
                },
                isAuthenticated: true,
                loading: false
              }
            });
            return true;
          } catch (error: any) {
            // If unauthorized, attempt a token refresh once and retry
            try {
              await authService.refreshToken();
              const user = await authService.getCurrentUser();
              set({ 
                auth: {
                  user,
                  tokens: {
                    access_token: authService.getStoredToken() || '',
                    refresh_token: localStorage.getItem('divine-whispers-refresh-token') || '',
                    expires_in: 3600
                  },
                  isAuthenticated: true,
                  loading: false
                }
              });
              return true;
            } catch (refreshError) {
              set({ 
                auth: {
                  user: null,
                  tokens: null,
                  isAuthenticated: false,
                  loading: false
                }
              });
              return false;
            }
          }
        },

        // Deity Selection
        selectedDeity: null,
        setSelectedDeity: (deity: Deity | null) => set({ selectedDeity: deity }),

        // Collection Selection
        selectedCollection: null,
        setSelectedCollection: (collection: PoemCollection | null) => set({ selectedCollection: collection }),

        // Fortune Number Selection
        selectedFortuneNumber: null,
        setSelectedFortuneNumber: (number: number | null) => set({ selectedFortuneNumber: number }),

        // Consultation
        currentConsultation: null,
        setCurrentConsultation: (consultation: ConsultationResponse | null) => 
          set({ currentConsultation: consultation }),

        consultationHistory: [],
        setConsultationHistory: (history: ConsultationResponse[]) => 
          set({ consultationHistory: history }),

        // Reports
        reports: (mockReports as any[]).map((r) => ({...r, analysis: { LineByLineInterpretation: r?.analysis?.LineByLineInterpretation || '', OverallDevelopment: r?.analysis?.OverallDevelopment || '', PositiveFactors: r?.analysis?.PositiveFactors || '', Challenges: r?.analysis?.Challenges || '', SuggestedActions: r?.analysis?.SuggestedActions || '', SupplementaryNotes: r?.analysis?.SupplementaryNotes || '', Conclusion: r?.analysis?.Conclusion || '' }})),
        setReports: (reports: Report[]) => set({ reports }),

        selectedReport: null,
        setSelectedReport: (report: Report | null) => set({ selectedReport: report }),

        // Wallet State
        wallet: {
          balance: 0,
          available_balance: 0,
          pending_amount: 0,
          loading: false,
          error: null,
          last_updated: null
        } as {
          balance: number;
          available_balance: number;
          pending_amount: number;
          loading: boolean;
          error: string | null;
          last_updated: string | null;
        },

        // Purchase State
        purchase: {
          loading: false,
          error: null,
          currentSession: null,
          packages: []
        } as {
          loading: boolean;
          error: string | null;
          currentSession: PurchaseSession | null;
          packages: CoinPackage[];
        },

        // Wallet Actions
        setWallet: (walletUpdates: any) =>
          set((state) => ({
            wallet: { ...state.wallet, ...walletUpdates }
          })),

        setPurchase: (purchaseUpdates: any) =>
          set((state) => ({
            purchase: { ...state.purchase, ...purchaseUpdates }
          })),

        // Refresh wallet balance from API
        refreshWalletBalance: async () => {
          set((state) => ({
            wallet: { ...state.wallet, loading: true, error: null }
          }));

          try {
            const walletBalance = await purchaseService.getWalletBalance();
            set((state) => ({
              wallet: {
                ...state.wallet,
                balance: walletBalance.balance,
                available_balance: walletBalance.available_balance,
                pending_amount: walletBalance.pending_amount,
                last_updated: walletBalance.last_updated,
                loading: false,
                error: null
              }
            }));
          } catch (error: any) {
            console.error('Failed to refresh wallet balance:', error);
            set((state) => ({
              wallet: {
                ...state.wallet,
                loading: false,
                error: error.message || 'Failed to load wallet balance'
              }
            }));
          }
        },

        // Load coin packages
        loadCoinPackages: async () => {
          set((state) => ({
            purchase: { ...state.purchase, loading: true, error: null }
          }));

          try {
            const packagesResponse = await purchaseService.getPackages();
            // Developer aid: log packages API response for verification
            try {
              console.log('Packages API response:', {
                packages: packagesResponse.packages,
                currency: packagesResponse.currency,
                payment_methods: packagesResponse.payment_methods
              });
            } catch (_) {
              // no-op
            }
            set((state) => ({
              purchase: {
                ...state.purchase,
                packages: packagesResponse.packages,
                loading: false,
                error: null
              }
            }));
          } catch (error: any) {
            console.error('Failed to load coin packages:', error);
            set((state) => ({
              purchase: {
                ...state.purchase,
                loading: false,
                error: error.message || 'Failed to load coin packages'
              }
            }));
          }
        },

        // Initiate purchase
        initiatePurchase: async (packageId: string, paymentMethod: string) => {
          set((state) => ({
            purchase: { ...state.purchase, loading: true, error: null }
          }));

          try {
            const purchaseSession = await purchaseService.initiatePurchase(packageId, paymentMethod);
            set((state) => ({
              purchase: {
                ...state.purchase,
                currentSession: purchaseSession,
                loading: false,
                error: null
              }
            }));
            return purchaseSession;
          } catch (error: any) {
            console.error('Failed to initiate purchase:', error);
            set((state) => ({
              purchase: {
                ...state.purchase,
                loading: false,
                error: error.message || 'Failed to initiate purchase'
              }
            }));
            throw error;
          }
        },

        // Complete purchase
        completePurchase: async (purchaseId: string, paymentConfirmation: any = {}) => {
          set((state) => ({
            purchase: { ...state.purchase, loading: true, error: null }
          }));

          try {
            const completion = await purchaseService.completePurchase(purchaseId, paymentConfirmation);

            // Update wallet balance with new amount
            set((state) => ({
              wallet: {
                ...state.wallet,
                balance: completion.new_balance,
                available_balance: completion.new_balance
              },
              purchase: {
                ...state.purchase,
                loading: false,
                error: null,
                currentSession: null // Clear session after completion
              }
            }));

            return completion;
          } catch (error: any) {
            console.error('Failed to complete purchase:', error);
            set((state) => ({
              purchase: {
                ...state.purchase,
                loading: false,
                error: error.message || 'Failed to complete purchase'
              }
            }));
            throw error;
          }
        },

        // Legacy userCoins getter for backward compatibility
        get userCoins() {
          return get().wallet.available_balance;
        },

        // Legacy setUserCoins for backward compatibility
        setUserCoins: (coins: number) => {
          set((state) => ({
            wallet: {
              ...state.wallet,
              balance: coins,
              available_balance: coins
            }
          }));
        },
      }),
      {
        name: 'divine-whispers-store',
        partialize: (state) => ({
          currentLanguage: state.currentLanguage,
          auth: state.auth,
          consultationHistory: state.consultationHistory,
          selectedDeity: state.selectedDeity,
          selectedFortuneNumber: state.selectedFortuneNumber,
          selectedCollection: state.selectedCollection,
          wallet: {
            balance: state.wallet.balance,
            available_balance: state.wallet.available_balance,
            pending_amount: state.wallet.pending_amount,
            last_updated: state.wallet.last_updated
          },
        }),
      }
    ),
    { name: 'divine-whispers' }
  )
);

export default useAppStore;
