import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { AppStore, AuthState, Deity, PoemCollection, ConsultationResponse, PageType, Report, Language, LoginCredentials, RegisterCredentials } from '../types';
import { mockReports } from '../utils/mockData';
import authService from '../services/authService';

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
        // Navigation
        currentPage: 'landing' as PageType,
        setCurrentPage: (page: PageType) => set({ currentPage: page }),

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
            const user = await authService.getCurrentUser();
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
          } catch (error) {
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
        reports: mockReports,
        setReports: (reports: Report[]) => set({ reports }),

        selectedReport: null,
        setSelectedReport: (report: Report | null) => set({ selectedReport: report }),

        // User Coins
        userCoins: 50, // Start with 50 coins for demo
        setUserCoins: (coins: number) => set({ userCoins: coins }),
      }),
      {
        name: 'divine-whispers-store',
        partialize: (state) => ({
          currentLanguage: state.currentLanguage,
          auth: state.auth,
          consultationHistory: state.consultationHistory,
        }),
      }
    ),
    { name: 'divine-whispers' }
  )
);

export default useAppStore;