// Divine Whispers Type Definitions

export interface User {
  user_id: number;
  email: string;
  username: string;
  role: string;
  points_balance: number;
  created_at: string;
  birth_date: string;
  gender: string;
  location: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  loading: boolean;
}

export interface PoemCollection {
  id: string;
  name: string;
  description: string;
  maxNumber: number;
  templateMapping: string;
}

export interface Deity {
  id: string;
  name: string;
  description: string;
  templateMapping: string;
  imageUrl: string;
  isActive: boolean;
  totalPoems: number;
  collections: PoemCollection[];
}

export interface FortunePoem {
  id: number;
  title: string;
  fortune: string;
  poem: string;
  analysis: {
    zh: {
      overview: string;
      spiritual_aspect: string;
      career_aspect: string;
      relationship_aspect: string;
      health_aspect: string;
      financial_aspect: string;
    };
    en: {
      overview: string;
      spiritual_aspect: string;
      career_aspect: string;
      relationship_aspect: string;
      health_aspect: string;
      financial_aspect: string;
    };
    jp: {
      overview: string;
      spiritual_aspect: string;
      career_aspect: string;
      relationship_aspect: string;
      health_aspect: string;
      financial_aspect: string;
    };
  };
}

export interface ConsultationRequest {
  deity_id: string;
  question: string;
  birth_date?: string;
  gender?: string;
  location?: string;
}

export interface ConsultationResponse {
  id: string;
  deity_id: string;
  deity_name: string;
  question: string;
  selected_poem: FortunePoem;
  ai_interpretation: {
    summary: string;
    detailed_analysis: {
      spiritual: string;
      career: string;
      relationship: string;
      health: string;
      financial: string;
    };
    advice: string;
    lucky_elements: string[];
    cautions: string[];
  };
  created_at: string;
  status: 'active' | 'expired';
  expires_at?: string;
}

export interface PurchaseItem {
  type: 'consultation' | 'premium_reading' | 'points';
  name: string;
  description: string;
  price: number;
  currency: string;
  points_value?: number;
}

export interface Transaction {
  id: string;
  user_id: number;
  type: 'purchase' | 'consultation_cost' | 'refund';
  amount: number;
  currency: string;
  points_change: number;
  description: string;
  status: 'pending' | 'completed' | 'failed';
  created_at: string;
  payment_method?: string;
}

export interface FAQ {
  id: number;
  question: string;
  answer: string;
  category: string;
  is_featured: boolean;
  created_at: string;
}

export interface ContactMessage {
  name: string;
  email: string;
  subject: string;
  message: string;
}

// Navigation Types - Updated for all pages
export type PageType = 'landing' | 'home' | 'deities' | 'deity-selection' | 'fortune-selection' | 'fortune-analysis' | 'purchase' | 'account' | 'admin' | 'contact';

// Store Types
export interface AppStore {
  currentPage: PageType;
  setCurrentPage: (page: PageType) => void;
  auth: AuthState;
  setAuth: (auth: Partial<AuthState>) => void;
  selectedDeity: Deity | null;
  setSelectedDeity: (deity: Deity | null) => void;
  selectedCollection: PoemCollection | null;
  setSelectedCollection: (collection: PoemCollection | null) => void;
  selectedFortuneNumber: number | null;
  setSelectedFortuneNumber: (number: number | null) => void;
  currentConsultation: ConsultationResponse | null;
  setCurrentConsultation: (consultation: ConsultationResponse | null) => void;
  consultationHistory: ConsultationResponse[];
  setConsultationHistory: (history: ConsultationResponse[]) => void;
}