import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { AppStore, AuthState, Deity, PoemCollection, ConsultationResponse, PageType, Report, Language } from '../types';
import { mockAuth, mockReports } from '../utils/mockData';

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
        auth: mockAuth as AuthState,
        setAuth: (authUpdates: Partial<AuthState>) => 
          set((state) => ({ 
            auth: { ...state.auth, ...authUpdates } 
          })),

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