// Divine Whispers Frontend Mock Data
// Based on FRONTEND_BACKEND_INTEGRATION_SPEC_UPDATED.md

// Authentication & User Data
export const mockAuth = {
  user: {
    user_id: 123,
    email: "john.dao@example.com",
    username: "DivineSeeker2024",
    role: "user",
    points_balance: 47,
    created_at: "2024-01-15T10:30:00Z",
    birth_date: "1990-03-15",
    gender: "Male",
    location: "San Francisco, CA, USA"
  },
  
  tokens: {
    access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    refresh_token: "refresh_token_here",
    expires_in: 3600
  },

  isAuthenticated: true,
  loading: false
};

// Deities Data
export const mockDeities = [
  {
    id: "guan_yin",
    name: "Guan Yin",
    description: ["The Goddess", "of", "Mercy"],
    templateMapping: "GuanYin100",
    imageUrl: "/GuanYin.jpg",
    isActive: true,
    totalPoems: 100,
    collections: [
      {
        id: "guanyin_standard",
        name: "Standard Collection",
        description: "Traditional 100 fortune poems",
        maxNumber: 100,
        templateMapping: "GuanYin100",
        numberRange: { start: 1, end: 100 }
      }
    ]
  },
  {
    id: "mazu",
    name: "Mazu",
    description: ["The Goddess", "of", "The sea"],
    templateMapping: "Mazu",
    imageUrl: "/Mazu.png",
    isActive: true,
    totalPoems: 163,
    collections: [
      {
        id: "mazu_classic",
        name: "Classic Collection",
        description: "Traditional 63 fortune poems",
        maxNumber: 63,
        templateMapping: "MazuClassic",
        numberRange: { start: 1, end: 63 }
      },
      {
        id: "mazu_extended",
        name: "Extended Collection",
        description: "Extended 100 fortune poems",
        maxNumber: 100,
        templateMapping: "MazuExtended",
        numberRange: { start: 1, end: 100 }
      }
    ]
  },
  {
    id: "guan_yu",
    name: "Guan Yu",
    description: ["The God", "of", "War and Wealth"],
    templateMapping: "GuanYu",
    imageUrl: "/GuanYu.jpg",
    isActive: true,
    totalPoems: 100,
    collections: [
      {
        id: "guanyu_standard",
        name: "Standard Collection",
        description: "Traditional 100 fortune poems",
        maxNumber: 100,
        templateMapping: "GuanYu",
        numberRange: { start: 1, end: 100 }
      }
    ]
  },
  {
    id: "yue_lao",
    name: "Yue Lao",
    description: ["The God", "of", "Marriage"],
    templateMapping: "YueLao",
    imageUrl: "/YueLao.png",
    isActive: true,
    totalPoems: 100,
    collections: [
      {
        id: "yuelao_standard",
        name: "Standard Collection",
        description: "Traditional 100 fortune poems",
        maxNumber: 100,
        templateMapping: "YueLao",
        numberRange: { start: 1, end: 100 }
      }
    ]
  },
  {
    id: "zhusheng",
    name: "Zhu sheng",
    description: ["The Goddess", "of", "Child Birth"],
    templateMapping: "ZhuSheng",
    imageUrl: "/TheGoddessofChildBirth.jpg",
    isActive: true,
    totalPoems: 100,
    collections: [
      {
        id: "zhusheng_standard",
        name: "Standard Collection",
        description: "Traditional 100 fortune poems",
        maxNumber: 100,
        templateMapping: "ZhuSheng",
        numberRange: { start: 1, end: 100 }
      }
    ]
  },
  {
    id: "asakusa",
    name: "Asakusa Kannon",
    description: ["Buddhist Temple"],
    templateMapping: "Asakusa",
    imageUrl: "/Asakusa.jpg",
    isActive: true,
    totalPoems: 100,
    collections: [
      {
        id: "asakusa_standard",
        name: "Standard Collection",
        description: "Traditional 100 fortune poems",
        maxNumber: 100,
        templateMapping: "Asakusa",
        numberRange: { start: 1, end: 100 }
      }
    ]
  },
  {
    id: "erawan",
    name: "Erawan Shrine",
    description: ["Buddhist Temple"],
    templateMapping: "ErawanShrine",
    imageUrl: "/ErawanShrine.jpg",
    isActive: true,
    totalPoems: 100,
    collections: [
      {
        id: "erawan_standard",
        name: "Standard Collection",
        description: "Traditional 100 fortune poems",
        maxNumber: 100,
        templateMapping: "ErawanShrine",
        numberRange: { start: 1, end: 100 }
      }
    ]
  }
];

// Fortune Numbers per Deity
export const mockFortuneNumbers = {
  deityId: "guan_yin",
  deityName: "Guan Yin",
  availableNumbers: Array.from({length: 100}, (_, i) => i + 1),
  totalCount: 100
};

// Sample Fortune Poems
export const mockFortunes = {
  "guan_yin_7": {
    id: "guan_yin_7",
    deity: {
      id: "guan_yin",
      name: "Guan Yin"
    },
    number: 7,
    title: "第7首",
    fortuneLevel: "大吉",
    poem: "一帆風順年年好\n萬事如意步步高\n家和萬事興旺盛\n財源廣進樂逍遙",
    analysis: "This fortune speaks of harmony and prosperity in all aspects of life. The winds are favorable, and success comes naturally. Family harmony brings abundance, and financial prosperity follows. This is an auspicious time for new ventures and important decisions."
  },
  "mazu_15": {
    id: "mazu_15",
    deity: {
      id: "mazu",
      name: "Mazu"
    },
    number: 15,
    title: "第15首",
    fortuneLevel: "中吉",
    poem: "海天一色浪滔滔\n船行萬里不辭勞\n媽祖護佑平安歸\n滿載而歸樂陶陶",
    analysis: "Under Mazu's protection, your journey across turbulent waters will be safe. Though the path may be long and challenging, divine guidance ensures safe passage. Persistence in your endeavors will bring abundant rewards."
  },
  "guan_yu_3": {
    id: "guan_yu_3",
    deity: {
      id: "guan_yu",
      name: "Guan Yu"
    },
    number: 3,
    title: "第3首",
    fortuneLevel: "大吉",
    poem: "義氣千秋照日月\n忠心不二護家邦\n刀光劍影皆退散\n正道光明永流傳",
    analysis: "Righteousness and loyalty are your guiding principles. Like Guan Yu's unwavering dedication, your moral strength will overcome all obstacles. Trust in justice and maintain your integrity - success will follow naturally."
  }
};

// Daily Fortune
export const mockDailyFortune = {
  poem: {
    id: "guan_yin_7",
    temple: "Guan Yin",
    title: "第7首",
    fortune: "大吉",
    poem: "天道酬勤志不移\n心正身修德自齊\n福祿雙全家業盛\n子孫滿堂樂融融",
    analysis: {
      "en": "Heaven rewards the diligent and those with unwavering determination. With a righteous heart and cultivated virtue, blessings naturally align. Both fortune and prosperity will flourish in your household, bringing joy and harmony to generations.",
      "zh": "天道酬勤的含義在於堅持不懈的努力必得回報。心地善良，品德修養自然齊備。福祿雙收，家業興旺，子孫滿堂，其樂融融。",
      "jp": "天が勤勉な者を報いるという意味で、不屈の意志を持つ者に幸運が訪れる。正しい心と徳を積めば、自然と福が訪れる。家業は栄え、子孫繁栄で喜びに満ちる。"
    }
  }
};

// Wallet & Purchase Data
export const mockWallet = {
  wallet_id: 123,
  user_id: 456,
  balance: 47,
  available_balance: 47,
  pending_amount: 0
};

export const mockCoinPackages = [
  {
    id: "package_5",
    coinAmount: 5,
    price: 1.00,
    pricePerCoin: 0.20,
    badge: "Perfect for trying",
    popular: false
  },
  {
    id: "package_25",
    coinAmount: 25,
    price: 4.00,
    pricePerCoin: 0.16,
    badge: "Most popular",
    popular: true
  },
  {
    id: "package_100",
    coinAmount: 100,
    price: 10.00,
    pricePerCoin: 0.10,
    badge: "Best value",
    popular: false
  },
  {
    id: "package_250",
    coinAmount: 250,
    price: 20.00,
    pricePerCoin: 0.08,
    badge: "Premium choice",
    popular: false
  }
];

// Transaction History
export const mockTransactions = {
  transactions: [
    {
      id: "txn_001",
      type: "deposit",
      amount: 25,
      description: "25 Divine Coins purchase",
      reference_id: "stripe_payment_123",
      status: "completed",
      created_at: "2024-12-28T14:30:00Z"
    },
    {
      id: "txn_002",
      type: "spend",
      amount: -10,
      description: "Fortune reading - Guan Yin #7",
      reference_id: "job_abc123",
      status: "completed",
      created_at: "2024-12-28T15:45:00Z"
    },
    {
      id: "txn_003",
      type: "spend",
      amount: -5,
      description: "Fortune reading - Mazu #15",
      reference_id: "job_def456",
      status: "completed",
      created_at: "2024-12-27T11:20:00Z"
    }
  ],
  total_count: 25,
  has_more: true
};

// Fortune History
export const mockFortuneHistory = {
  entries: [
    {
      job_id: "job_123",
      poem_id: "guan_yin_7",
      question: "Career guidance - should I take the new job offer?",
      created_at: "2024-12-28T10:30:00Z",
      status: "completed",
      points_cost: 10,
      deity_name: "Guan Yin",
      fortune_number: 7,
      fortune_level: "大吉"
    },
    {
      job_id: "job_456",
      poem_id: "mazu_15",
      question: "Travel safety for upcoming business trip",
      created_at: "2024-12-27T16:45:00Z",
      status: "completed",
      points_cost: 10,
      deity_name: "Mazu",
      fortune_number: 15,
      fortune_level: "中吉"
    },
    {
      job_id: "job_789",
      poem_id: "yue_lao_33",
      question: "Relationship advice about my current partner",
      created_at: "2024-12-26T14:20:00Z",
      status: "completed",
      points_cost: 10,
      deity_name: "Yue Lao",
      fortune_number: 33,
      fortune_level: "小吉"
    }
  ],
  total_count: 15,
  has_more: true
};

// Analysis Reports
export const mockAnalysisReports = [
  {
    id: "report_789",
    title: "Guan Yin Divine Guidance - Fortune #27",
    subtitle: "Career & Life Path Analysis",
    generated_date: "2024-12-28",
    word_count: 2340,
    deity: "Guan Yin",
    fortune_number: 27,
    preview: "Your career path shows promising developments ahead. The divine guidance suggests that patience and persistence will be rewarded..."
  },
  {
    id: "report_790",
    title: "Mazu Ocean Blessing - Fortune #8",
    subtitle: "Travel & Protection Reading",
    generated_date: "2024-12-27",
    word_count: 1850,
    deity: "Mazu",
    fortune_number: 8,
    preview: "Under Mazu's protective embrace, your journeys will be safe and prosperous. The ocean's wisdom speaks of new horizons..."
  },
  {
    id: "report_791",
    title: "Yue Lao Love Destiny - Fortune #42",
    subtitle: "Romantic Relationship Insight",
    generated_date: "2024-12-25",
    word_count: 1960,
    deity: "Yue Lao",
    fortune_number: 42,
    preview: "The red thread of destiny weaves through your love story. Yue Lao reveals that true connection requires both patience and courage..."
  }
];

// Chat Messages for Fortune Analysis
export const mockChatMessages = [
  {
    id: "msg_001",
    type: "user",
    message: "What does this fortune mean for my career?",
    timestamp: "2024-12-28T15:30:00Z"
  },
  {
    id: "msg_002",
    type: "assistant",
    message: "Your question touches the heart of this divination. The fortune speaks of 'Heaven rewards the diligent' - this is particularly auspicious for career matters. The poem suggests that your hard work and unwavering determination will soon be recognized and rewarded. Consider this a sign that any career moves you're contemplating are divinely supported.",
    timestamp: "2024-12-28T15:30:15Z"
  },
  {
    id: "msg_003",
    type: "user",
    message: "Should I take the job offer I received?",
    timestamp: "2024-12-28T15:32:00Z"
  },
  {
    id: "msg_004",
    type: "assistant",
    message: "The fortune's emphasis on 'righteousness of heart and cultivation of virtue' suggests you should evaluate this opportunity not just for monetary gain, but for alignment with your values. The line about 'prosperity flourishing in your household' indicates this change could bring stability and growth. Trust your instincts - if the opportunity feels right morally and professionally, the divine signs are favorable.",
    timestamp: "2024-12-28T15:32:25Z"
  }
];

// Admin Dashboard Data
export const mockAdminStats = {
  total_users: 1247,
  role_distribution: [
    { role: "user", count: 1180 },
    { role: "premium", count: 45 },
    { role: "moderator", count: 12 },
    { role: "admin", count: 10 }
  ],
  recent_role_changes: 15,
  recent_suspensions: 3,
  total_revenue: 15650.00,
  monthly_active_users: 892,
  total_fortune_readings: 8934,
  average_session_duration: "12:45"
};

export const mockAdminUsers = {
  users: [
    {
      id: 1,
      email: "john.doe@example.com",
      username: "JohnDoe",
      role: "user",
      status: "active",
      points_balance: 25,
      created_at: "2024-01-15T10:30:00Z",
      last_login: "2024-12-28T14:20:00Z",
      total_readings: 15
    },
    {
      id: 2,
      email: "jane.smith@example.com",
      username: "JaneSmith",
      role: "premium",
      status: "active",
      points_balance: 150,
      created_at: "2023-11-20T09:15:00Z",
      last_login: "2024-12-28T16:45:00Z",
      total_readings: 87
    },
    {
      id: 3,
      email: "bob.wilson@example.com",
      username: "BobWilson",
      role: "user",
      status: "suspended",
      points_balance: 5,
      created_at: "2024-02-10T13:22:00Z",
      last_login: "2024-12-25T11:30:00Z",
      total_readings: 3
    }
  ],
  total: 1247,
  page: 1,
  total_pages: 125,
  per_page: 10
};

// FAQ Data
export const mockFAQs = {
  public: [
    {
      id: "faq_001",
      question: "How do I start my first fortune reading?",
      answer: "To begin your fortune reading journey, simply select a deity that resonates with you, choose a number from 1-100, and ask your question. Each reading costs 10 Divine Coins.",
      category: "getting-started",
      order: 1,
      is_active: true
    },
    {
      id: "faq_002",
      question: "What are Divine Coins and how do I get them?",
      answer: "Divine Coins are our virtual currency used for fortune readings. You can purchase them in packages ranging from 5 coins ($1) to 250 coins ($20). Check our Purchase page for current packages.",
      category: "coins",
      order: 2,
      is_active: true
    },
    {
      id: "faq_003",
      question: "How accurate are the fortune readings?",
      answer: "Our fortune readings are based on traditional Chinese temple poems with AI-powered interpretations. They are meant for guidance and reflection, not as absolute predictions. Use them as tools for self-reflection and decision-making.",
      category: "accuracy",
      order: 3,
      is_active: true
    }
  ],
  pending: [
    {
      id: "faq_pending_001",
      question: "Can I get a refund for unused Divine Coins?",
      answer: "We offer refunds within 30 days of purchase for unused Divine Coins, minus any processing fees.",
      category: "refunds",
      submitted_by: "user@example.com",
      submitted_at: "2024-12-28T10:00:00Z",
      status: "pending_review"
    }
  ]
};

// Contact Form Data
export const mockContactSubmissions = [
  {
    id: "contact_001",
    name: "Sarah Johnson",
    email: "sarah@example.com",
    subject: "Question about premium features",
    message: "I'm interested in learning more about premium features. Do premium users get better fortune interpretations?",
    status: "new",
    created_at: "2024-12-28T14:30:00Z",
    ticket_id: "ticket_789"
  },
  {
    id: "contact_002",
    name: "Mike Chen",
    email: "mike.chen@example.com",
    subject: "Technical issue with payment",
    message: "I tried to purchase 25 Divine Coins but the payment failed. Can you help me troubleshoot this issue?",
    status: "in_progress",
    created_at: "2024-12-27T16:20:00Z",
    ticket_id: "ticket_790",
    assigned_to: "support@divinewhispers.com"
  }
];

// WebSocket Mock Events
export const mockWebSocketEvents = {
  fortune_chat_message: {
    type: "fortune_chat_message",
    data: {
      sessionId: "session_123",
      message: "What does this mean for my relationships?",
      timestamp: "2024-12-28T15:30:00Z"
    }
  },
  
  fortune_chat_response: {
    type: "fortune_chat_response",
    data: {
      sessionId: "session_123",
      response: "In matters of the heart, this fortune suggests...",
      timestamp: "2024-12-28T15:30:15Z"
    }
  },
  
  typing_indicator: {
    type: "typing_indicator",
    data: {
      sessionId: "session_123",
      isTyping: true
    }
  }
};

// Job Status for Async Operations
export const mockJobStatus = {
  processing: {
    job_id: "job_abc123",
    status: "processing",
    estimated_completion_time: 30,
    points_charged: 10,
    progress_percentage: 65
  },
  
  completed: {
    job_id: "job_abc123",
    status: "completed",
    result_data: {
      poem: mockFortunes["guan_yin_7"],
      interpretation: "Your fortune reveals a time of great potential and positive energy. The divine guidance suggests that your current path is aligned with cosmic harmony...",
      confidence: 0.95,
      additional_insights: [
        "Focus on maintaining balance in all aspects of life",
        "Trust your intuition when making important decisions",
        "Positive changes are approaching - be prepared to embrace them"
      ]
    }
  }
};

// Error States
export const mockErrors = {
  authentication: {
    code: "AUTH_FAILED",
    message: "Invalid email or password",
    details: "Please check your credentials and try again"
  },
  
  insufficient_balance: {
    code: "INSUFFICIENT_BALANCE",
    message: "Not enough Divine Coins",
    details: "You need 10 Divine Coins for a fortune reading. Current balance: 5 coins",
    required_amount: 10,
    current_balance: 5
  },
  
  server_error: {
    code: "SERVER_ERROR",
    message: "Something went wrong",
    details: "Our servers are experiencing issues. Please try again later."
  }
};

// Loading States
export const mockLoadingStates = {
  auth: { loading: true, error: null },
  fortune: { loading: false, error: null },
  wallet: { loading: false, error: null },
  admin: { loading: false, error: null }
};

// Today's Whisper Data
export const mockTodaysWhisper = {
  preview: "A gentle reminder from the universe awaits you... ▾",
  poem: {
    chinese: "月圓花好事如意，心靜自然福氣來。\n修德行善積陰功，前程似錦樂開懷。",
    english: "When moon is full and flowers bloom fair,\nA peaceful heart brings fortune everywhere.\nCultivate virtue and do good deeds,\nA bright future fulfills all your needs."
  },
  interpretation: {
    overview: "Today's divine message speaks of harmony and inner peace. The cosmos suggests that maintaining tranquility in your heart will attract positive energy and opportunities.",
    advice: "Focus on cultivating inner peace and performing acts of kindness. Your future prospects are bright when you align with virtue.",
    lucky_elements: ["Water", "Silver", "North Direction"],
    favorable_time: "Early morning hours (6-8 AM)"
  }
};

// Demo Report for showcasing report style
export const mockDemoReport = {
  id: "demo_report",
  title: "Divine Guidance Demo Report",
  question: "What does the future hold for my personal growth and happiness?",
  deity_id: "guan_yin",
  deity_name: "Guan Yin",
  fortune_number: 88,
  cost: 5,
  status: "completed" as const,
  created_at: "2024-12-28T10:00:00Z",
  analysis: {
    overview: "The goddess of mercy, Guan Yin, reveals that your path toward personal growth is illuminated with divine blessing. Your sincere desire for self-improvement and genuine happiness resonates with the cosmic energies. This fortune speaks of transformation, inner wisdom, and the blossoming of your true potential.",
    career_analysis: "Your professional journey is entering a phase of remarkable growth. The divine energies suggest that your authentic self-expression and compassionate approach will open new doors. Consider roles that allow you to help others while fulfilling your own aspirations. Leadership opportunities may present themselves in the coming months.",
    relationship_analysis: "Harmony in relationships flows from inner peace. Your growing self-awareness will naturally improve your connections with others. Be open to deep, meaningful conversations that can heal old wounds and strengthen bonds. A significant relationship may undergo positive transformation.",
    health_analysis: "Balance is key to your wellbeing. Pay attention to both physical and mental health through mindful practices. Regular meditation, gentle exercise, and connecting with nature will support your energy levels. Listen to your body's wisdom and honor its needs for rest and nourishment.",
    lucky_elements: ["Lotus", "White Light", "Morning Dew", "Gentle Breeze", "Compassionate Heart"],
    cautions: ["Avoid self-doubt", "Don't rush major decisions", "Be patient with change", "Trust your intuition"],
    advice: "Like a lotus blooming from muddy waters, your greatest growth often comes through challenges. Trust in your inherent wisdom and the divine support that surrounds you. Your journey toward happiness is not a destination but a beautiful unfolding of your soul's purpose."
  }
};

// Reports Mock Data
export const mockReports = [
  {
    id: "report_001",
    title: "Career Path Analysis",
    question: "What should I focus on in my career development?",
    deity_id: "guan_yin",
    deity_name: "Guan Yin",
    fortune_number: 42,
    cost: 5,
    status: "completed" as const,
    created_at: "2024-12-28T14:30:00Z",
    analysis: {
      overview: "Your career path shows promising developments ahead. The divine guidance suggests focusing on collaboration and building meaningful professional relationships. You are at a crossroads in your professional journey, with multiple opportunities presenting themselves.",
      career_analysis: "Your professional endeavors are blessed with strong communication skills and natural leadership qualities. Focus on networking and building genuine professional relationships. Consider taking on mentorship roles to develop leadership skills further. The next 3-6 months are particularly favorable for career advancement.",
      relationship_analysis: "Professional relationships will be key to your success. Your ability to inspire others will open new doors and create valuable connections in your field.",
      health_analysis: "Balance between ambition and patience is crucial. Don't neglect work-life balance as you pursue career goals. Regular breaks and stress management will support your professional journey.",
      lucky_elements: ["Metal", "White", "West Direction"],
      cautions: ["Avoid rushing major decisions", "Be patient with slow progress", "Don't neglect work-life balance"],
      advice: "Trust your instincts when making career decisions. Seek opportunities that align with your values and long-term goals. Your natural leadership qualities will guide you to success."
    }
  },
  {
    id: "report_002", 
    title: "Relationship Insights",
    question: "How can I improve my relationships with family?",
    deity_id: "mazu",
    deity_name: "Mazu",
    fortune_number: 18,
    cost: 5,
    status: "completed" as const,
    created_at: "2024-12-27T16:45:00Z",
    analysis: {
      overview: "Family relationships require patience and understanding. The sea goddess Mazu advises flowing like water - adapting while maintaining your core values. There are some underlying tensions that need gentle attention and care to resolve.",
      career_analysis: "Your strong sense of responsibility and willingness to make sacrifices will be valued in professional settings. These family relationship skills will enhance your workplace collaborations.",
      relationship_analysis: "Practice active listening without immediately offering solutions. Express appreciation for family members more frequently. Create regular family gathering opportunities and address conflicts with compassion rather than defensiveness. Family harmony will improve significantly in the coming months with consistent effort.",
      health_analysis: "Emotional well-being through improved family relationships will positively impact your overall health. Reduced family stress will lead to better sleep and mental clarity.",
      lucky_elements: ["Water", "Blue", "North Direction"],
      cautions: ["Don't try to control others", "Avoid bringing up past grievances", "Be patient with change"],
      advice: "Flow like water in your relationships - be flexible while maintaining your core values. Deep love for family and willingness to make sacrifices are your greatest strengths in healing these bonds."
    }
  },
  {
    id: "report_003",
    title: "Health & Wellness Guide", 
    question: "What should I focus on for better health?",
    deity_id: "guan_yu",
    deity_name: "Guan Yu",
    fortune_number: 73,
    cost: 5,
    status: "completed" as const,
    created_at: "2024-12-26T11:20:00Z",
    analysis: {
      overview: "Your health requires a balanced approach combining physical activity, mental wellness, and spiritual practices. The warrior god emphasizes discipline and consistency. Your body and mind need more attention and care, as there are signs of stress that should be addressed.",
      career_analysis: "Your strong willpower and ability to maintain routines will serve you well in establishing healthy work habits. Better health will significantly improve your professional performance and decision-making abilities.",
      relationship_analysis: "Improved health and reduced stress will enhance your relationships. When you feel better physically, you'll have more patience and energy for meaningful connections with others.",
      health_analysis: "Establish a consistent sleep schedule of 7-8 hours nightly. Incorporate regular physical exercise, even light walking. Practice stress-reduction techniques like meditation or deep breathing. Focus on nutritious, balanced meals rather than quick fixes. Health improvements will be noticeable within 30-60 days of consistent practice.",
      lucky_elements: ["Fire", "Red", "South Direction"],
      cautions: ["Don't overexert yourself initially", "Avoid extreme diet changes", "Listen to your body's signals"],
      advice: "Like a disciplined warrior, approach your health with consistency and determination. Your strong willpower and awareness of health's importance are your greatest assets in this journey toward wellness."
    }
  }
];

// Export all mock data as default
export default {
  mockAuth,
  mockDeities,
  mockFortuneNumbers,
  mockFortunes,
  mockDailyFortune,
  mockWallet,
  mockCoinPackages,
  mockTransactions,
  mockFortuneHistory,
  mockAnalysisReports,
  mockReports,
  mockDemoReport,
  mockChatMessages,
  mockAdminStats,
  mockAdminUsers,
  mockFAQs,
  mockContactSubmissions,
  mockWebSocketEvents,
  mockJobStatus,
  mockErrors,
  mockLoadingStates
};