# Divine Whispers Frontend-Backend Integration Specification (Updated)

## Overview
This document provides the updated mapping between the Divine Whispers frontend mockup and the existing backend API architecture. This version aligns the SPEC with actual backend capabilities while noting required implementations.

**Update Status**: ✅ Aligned with existing backend as of January 2025

---

## 🏗️ Architecture Overview

### Frontend Stack Requirements
- **Framework**: React.js or Vue.js recommended
- **State Management**: Redux/Zustand (React) or Pinia (Vue)
- **Routing**: React Router or Vue Router
- **Styling**: CSS-in-JS or Tailwind CSS (current mockup uses CSS)
- **HTTP Client**: Axios or Fetch API
- **Real-time**: WebSocket for chat functionality

### Backend Architecture (Existing)
- **Base URL**: `/api/v1`
- **Authentication**: JWT tokens ✅ (Implemented)
- **Payment Processing**: Points-based wallet system ✅ (Implemented)
- **AI Integration**: Async job processing with ChromaDB ✅ (Implemented)
- **Admin System**: Comprehensive RBAC ✅ (Implemented)
- **Missing**: Deity mapping, FAQ system, Contact form

---

## 📱 Page-by-Page Analysis & Updated API Mapping

### 1. Landing Page ✅ READY
**Purpose**: User acquisition and initial engagement
**URL**: `/` (homepage)

#### Components & Interactions
| Component | Purpose | API Required | Status |
|-----------|---------|-------------|--------|
| Language Selector | Change language preference | None (Frontend state) | ✅ Ready |
| Learn More Button | Navigate to main website | Frontend routing | ✅ Ready |

**APIs Needed**: None (static page)

---

### 2. HOME Page ⚠️ NEEDS IMPLEMENTATION
**Purpose**: Main dashboard with daily fortune preview
**URL**: `/home`

#### Components & Interactions
| Component | Purpose | API Required | Status |
|-----------|---------|-------------|--------|
| Today's Whisper Card | Show daily fortune preview | `GET /api/v1/fortune/daily` | ❌ Needs Implementation |
| Try Reading Now Button | Navigate to fortune selection | Frontend routing | ✅ Ready |

**UPDATED API Contracts**:
```javascript
// Daily Fortune API - TO BE IMPLEMENTED
GET /api/v1/fortune/daily
Headers: {
  Authorization: "Bearer <jwt_token>"
}
Response: {
  poem: {
    id: "guan_yin_7",
    temple: "Guan Yin",
    title: "第7首",
    fortune: "大吉",
    poem: "天道酬勤志不移...",
    analysis: {
      "en": "Heaven rewards the diligent...",
      "zh": "天道酬勤的含义...",
      "jp": "天が勤勉な者を報いる..."
    }
  }
}
```

---

### 3. POEM Page (Fortune Reading Flow) ⚠️ PARTIAL / NEEDS MAPPING

#### 3.1 Deity Selection Sub-page - ❌ NEEDS IMPLEMENTATION
**Current Status**: Backend has temple-based system, needs deity mapping layer

**REQUIRED NEW API**:
```javascript
// Deity List API - TO BE IMPLEMENTED
GET /api/v1/deities
Response: [
  {
    id: "guan_yin",
    name: "Guan Yin", 
    description: "The Goddess of Mercy",
    templateMapping: "GuanYin100", // Maps to existing temple
    imageUrl: "/images/guan_yin.jpg",
    isActive: true,
    totalPoems: 100
  },
  {
    id: "mazu", 
    name: "Mazu",
    description: "The Goddess of The sea", 
    templateMapping: "Mazu",
    imageUrl: "/images/mazu.jpg",
    isActive: true,
    totalPoems: 100
  }
  // ... 5 more deities
]
```

#### 3.2 Fortune Number Selection - ❌ NEEDS IMPLEMENTATION
**Current Status**: Backend uses poem_id, needs number-based mapping

**REQUIRED NEW API**:
```javascript
// Available Numbers per Deity - TO BE IMPLEMENTED  
GET /api/v1/fortunes/{deityId}/numbers
Response: {
  deityId: "guan_yin",
  deityName: "Guan Yin",
  availableNumbers: [1, 2, 3, ..., 100],
  totalCount: 100
}
```

#### 3.3 Fortune Display & Analysis - ⚠️ PARTIALLY AVAILABLE
**Current Status**: Backend has async job system, needs synchronous mapping for UI

**EXISTING BACKEND API** (Async):
```javascript
// Current Backend - Async Job System
POST /api/v1/fortune/interpret/{poem_id}
Request: {
  poem_id: "guan_yin_7",
  question: "What does this fortune mean for my career?",
  language: "en"
}
Response: {
  job_id: "job_abc123",
  status: "processing", 
  estimated_completion_time: 30,
  points_charged: 10
}

// Get Job Status
GET /api/v1/fortune/jobs/{job_id}/status
Response: {
  job_id: "job_abc123",
  status: "completed",
  result_data: {
    poem: {...},
    interpretation: "...",
    confidence: 0.95
  }
}
```

**REQUIRED NEW API** (Synchronous for UI):
```javascript
// Direct Fortune Retrieval - TO BE IMPLEMENTED
GET /api/v1/fortunes/{deityId}/{number}
Headers: {
  Authorization: "Bearer <jwt_token>"
}
Response: {
  id: "guan_yin_7",
  deity: {
    id: "guan_yin", 
    name: "Guan Yin"
  },
  number: 7,
  title: "第7首",
  fortuneLevel: "大吉",
  poem: "一帆風順年年好\n萬事如意步步高\n家和萬事興旺盛\n財源廣進樂逍遙",
  analysis: "This fortune speaks of harmony and prosperity..."
}

// Chat Analysis - TO BE IMPLEMENTED
POST /api/v1/analysis/chat  
Request: {
  fortuneId: "guan_yin_7",
  message: "What does this mean for my career?",
  sessionId: "session_123"
}
Response: {
  reply: "Your question touches the heart of this divination...",
  sessionId: "session_123"
}
```

---

### 4. PURCHASE Page ✅ BACKEND READY - NEEDS MAPPING
**Purpose**: Divine coin purchase system  
**URL**: `/purchase`

**BACKEND STATUS**: ✅ Wallet system fully implemented, needs coin package mapping

**EXISTING WALLET APIs**:
```javascript
// Get Current Balance - READY
GET /api/v1/balance
Response: {
  wallet_id: 123,
  user_id: 456, 
  balance: 47,
  available_balance: 47,
  pending_amount: 0
}

// Deposit Points (Purchase) - READY
POST /api/v1/deposit
Request: {
  amount: 25,
  reference_id: "stripe_payment_123",
  description: "25 Divine Coins purchase"
}
Response: {
  transaction: {...},
  new_balance: 72,
  message: "Successfully deposited 25 points"
}
```

**REQUIRED MAPPING LAYER**:
```javascript
// Coin Packages - TO BE IMPLEMENTED (Frontend can define)
const COIN_PACKAGES = [
  {
    id: "package_5",
    coinAmount: 5, 
    price: 1.00,
    pricePerCoin: 0.20,
    badge: "Perfect for trying"
  },
  {
    id: "package_25",
    coinAmount: 25,
    price: 4.00, 
    pricePerCoin: 0.16,
    badge: "Most popular"
  },
  {
    id: "package_100", 
    coinAmount: 100,
    price: 10.00,
    pricePerCoin: 0.10,
    badge: "Best value"
  }
];
```

---

### 5. ACCOUNT Page ⚠️ PARTIALLY READY
**Purpose**: User profile and history management
**URL**: `/account`

**BACKEND STATUS**: ⚠️ Profile data available, needs aggregation endpoints

**EXISTING BACKEND APIs**:
```javascript
// User Profile - READY
GET /api/v1/auth/me
Response: {
  user_id: 123,
  email: "john.dao@example.com",
  role: "user",
  points_balance: 47,
  created_at: "2024-01-15T...",
  // Missing: username, birth_date, gender, location
}

// Transaction History - READY  
GET /api/v1/transactions?limit=10
Response: {
  transactions: [...],
  total_count: 25,
  has_more: true
}

// Fortune History - READY
GET /api/v1/fortune/history?limit=10
Response: {
  entries: [
    {
      job_id: "job_123",
      poem_id: "guan_yin_7", 
      question: "Career guidance",
      created_at: "2024-12-28T...",
      status: "completed",
      points_cost: 10
    }
  ]
}
```

**REQUIRED IMPLEMENTATIONS**:
```javascript
// Profile Update - TO BE IMPLEMENTED
PUT /api/v1/auth/profile
Request: {
  username: "DivineSeeker2024",
  birth_date: "1990-03-15",
  gender: "Male", 
  location: "San Francisco, CA, USA"
}

// Analysis Reports - TO BE IMPLEMENTED
GET /api/v1/analysis/reports?limit=10
Response: [
  {
    id: "report_789",
    title: "Guan Yin Divine Guidance - Fortune #27",
    subtitle: "Career & Life Path Analysis", 
    generated_date: "2024-12-28",
    word_count: 2340,
    deity: "Guan Yin",
    fortune_number: 27
  }
]
```

---

### 6. ADMIN Dashboard ✅ FULLY READY
**Purpose**: Administrative management interface
**URL**: `/admin`

**BACKEND STATUS**: ✅ Comprehensive admin system implemented

**EXISTING BACKEND APIs** (All Ready):
```javascript
// Dashboard Stats - READY
GET /api/v1/admin/stats
Response: {
  total_users: 1247,
  role_distribution: [...],
  recent_role_changes: 15,
  recent_suspensions: 3
}

// Customer Management - READY  
GET /api/v1/admin/users?page=1&per_page=10&search=john
Response: {
  users: [...],
  total: 1247,
  page: 1,
  total_pages: 125
}

// User Actions - ALL READY
PUT /api/v1/admin/users/{id}/role
PUT /api/v1/admin/users/{id}/suspend
PUT /api/v1/admin/users/{id}/points
DELETE /api/v1/admin/users/{id}
```

**MISSING: FAQ Management System**:
```javascript
// FAQ Management - TO BE IMPLEMENTED
GET /api/v1/admin/faqs/pending
POST /api/v1/admin/faqs/{id}/approve  
GET /api/v1/admin/faqs/active
DELETE /api/v1/admin/faqs/{id}

// Public FAQs - TO BE IMPLEMENTED
GET /api/v1/faqs/public
```

---

### 7. CONTACT Page ❌ NEEDS IMPLEMENTATION
**Purpose**: Customer support and communication
**URL**: `/contact`

**BACKEND STATUS**: ❌ Not implemented

**REQUIRED NEW API**:
```javascript
// Contact Form Submission - TO BE IMPLEMENTED
POST /api/v1/contact/submit
Request: {
  name: "Test User",
  email: "test@example.com",
  subject: "Testing contact form", 
  message: "This is a test message..."
}
Response: {
  success: true,
  message: "Thank you for your message. We'll get back to you within 24 hours.",
  ticket_id: "ticket_789"
}
```

---

## 🔐 Authentication & Authorization ✅ FULLY READY

### Authentication Flow (All Implemented)
```javascript
// Login API - READY
POST /api/v1/auth/login
Request: {
  email: "user@example.com", 
  password: "password123"
}
Response: {
  user: {...},
  tokens: {
    access_token: "jwt_token_here",
    refresh_token: "refresh_token_here", 
    expires_in: 3600
  }
}

// Register API - READY
POST /api/v1/auth/register
Request: {
  email: "new@example.com",
  password: "password123",
  confirm_password: "password123"  
}
Response: {
  user: {...},
  tokens: {...}
}

// Token Refresh - READY
POST /api/v1/auth/refresh
POST /api/v1/auth/logout  
GET /api/v1/auth/me
PUT /api/v1/auth/change-password
```

---

## 💡 Frontend State Management Requirements

### Global State Structure (Updated)
```javascript
{
  auth: {
    user: UserObject | null,
    isAuthenticated: boolean,
    loading: boolean
  },
  
  fortune: {
    selectedDeity: DeityObject | null,
    selectedNumber: number | null,
    currentFortune: FortuneObject | null,
    jobStatus: JobStatusObject | null // For async operations
  },
  
  wallet: { // Updated from 'purchase'
    balance: number,
    availableBalance: number,
    pendingAmount: number,
    selectedPackage: PackageObject | null
  },
  
  admin: {
    activeTab: 'customers' | 'faqs' | 'reports' | 'analytics',
    users: UserObject[],
    pendingFAQs: FAQObject[], // When implemented
    stats: StatsObject
  }
}
```

---

## 🚨 Implementation Priority & Status

### ✅ READY TO USE (No Implementation Needed)
1. **Authentication System** - Complete
2. **Admin User Management** - Complete  
3. **Wallet Operations** - Complete
4. **WebSocket Infrastructure** - Basic implementation ready

### ⚠️ NEEDS SIMPLE MAPPING (1-2 weeks)
5. **Deity System** - Map existing temples to deities
6. **Purchase Packages** - Define coin packages in frontend
7. **Profile Management** - Extend user model

### ❌ NEEDS FULL IMPLEMENTATION (2-4 weeks each)
8. **Interactive Chat System** - New chat API + WebSocket integration
9. **FAQ Management** - Complete admin system
10. **Contact Form** - Simple form processing  
11. **Synchronous Fortune APIs** - Alternative to async job system
12. **Daily Fortune** - Random poem selection

---

## 🔄 Real-time Features Status

### WebSocket System ✅ READY
```javascript
// Basic WebSocket - IMPLEMENTED
/ws/{user_id} - Basic connection ready

// Chat System - NEEDS IMPLEMENTATION  
Events needed:
- fortune_chat_message
- fortune_chat_response  
- typing_indicator
```

---

## 📊 Performance Requirements ✅ MOSTLY READY

### Backend Performance Features
- **Caching**: ChromaDB caching implemented ✅
- **Async Processing**: Job queue system ready ✅
- **Pagination**: Admin endpoints support pagination ✅  
- **Rate Limiting**: Can be added to existing endpoints ⚠️
- **Error Handling**: Comprehensive error responses ✅

---

## 🧪 Testing Requirements ✅ INFRASTRUCTURE READY

### Backend Testing
- **Database**: SQLAlchemy + Alembic migrations ✅
- **Authentication**: JWT token validation ✅  
- **Admin Permissions**: RBAC system with audit logs ✅
- **Payment Processing**: Transaction integrity checks ✅

---

## 📋 Updated Implementation Checklist

### Phase 1: Core Mapping (Week 1-2) 
- [ ] Implement deity-to-temple mapping API
- [ ] Add fortune number selection endpoints  
- [ ] Create daily fortune endpoint
- [ ] Extend user profile model
- [ ] Map coin packages to wallet deposits

### Phase 2: Interactive Features (Week 3-4)
- [ ] Build synchronous fortune retrieval API
- [ ] Implement chat analysis system
- [ ] Integrate real-time WebSocket chat
- [ ] Add purchase history aggregation

### Phase 3: Admin Extensions (Week 5-6)  
- [ ] Implement FAQ management system
- [ ] Add contact form processing
- [ ] Create analysis report storage
- [ ] Build admin FAQ moderation interface

### Phase 4: Testing & Polish (Week 7-8)
- [ ] Comprehensive API testing
- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] Frontend integration testing

---

## 🎯 Success Metrics (Updated)

### Technical Metrics
- API response times < 200ms (existing endpoints meet this) ✅
- Authentication success rate > 99% ✅  
- Admin operations complete without errors ✅
- Wallet transactions are atomic and consistent ✅

### Business Metrics  
- User registration conversion rate (tracking ready)
- Fortune reading completion rate (needs new tracking)
- Coin purchase conversion rate (wallet system ready)
- Admin task completion efficiency (audit logs ready)

---

## Summary

**Current Backend Readiness**: ~70%
- **Authentication & Admin**: 100% ready ✅
- **Wallet System**: 100% ready ✅  
- **Fortune System**: 40% ready (async jobs work, needs UI mapping) ⚠️
- **User Management**: 80% ready (needs profile extensions) ⚠️
- **FAQ & Contact**: 0% ready ❌

**Recommended Approach**:  
1. **Phase 1**: Quick mapping layer for deity/number selection (2 weeks)
2. **Phase 2**: Implement missing high-value features (chat, FAQ) (4 weeks)  
3. **Phase 3**: Polish and optimize (2 weeks)

**Total Development Time**: 8 weeks for full SPEC compliance with existing backend architecture.

---

*Updated SPEC Version: 2.0*  
*Backend Compatibility: Divine Whispers Backend v1.0.0*  
*Last Updated: January 2025*