import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Define translations directly in TypeScript for better type safety and compilation
const enTranslations = {
  common: {
    appName: "Divine Whispers",
    navigation: {
      home: "Home",
      deities: "Poems",
      purchase: "Purchase",
      account: "Account",
      contact: "Contact",
      admin: "Admin"
    },
    auth: {
      login: "Login",
      signup: "Sign Up",
      logout: "Logout",
      userRole: "User",
      adminRole: "Admin"
    },
    buttons: {
      submit: "Submit",
      cancel: "Cancel",
      continue: "Continue",
      back: "Back",
      next: "Next",
      close: "Close",
      save: "Save",
      edit: "Edit",
      delete: "Delete",
      confirm: "Confirm"
    },
    language: {
      selector: "Language",
      english: "English",
      chinese: "中文",
      japanese: "日本語"
    },
    loading: "Loading...",
    error: "An error occurred",
    success: "Success"
  },
  pages: {
    landing: {
      title: "Divine Whispers",
      subtitle: "Discover Your Fortune Through Ancient Wisdom",
      heroTitle: "Hear the call of mystery guiding your true path",
      getStarted: "Get Started",
      learnMore: "Learn More",
      videoError: "Your browser does not support the video tag."
    },
    home: {
      todaysWhisper: "Today's Whisper",
      yourFortune: "Your Fortune",
      knowYourFate: "Know Your Fate",
      readWhisper: "Read Your Whisper",
      demoReport: "Demo Report",
      welcomeBack: "Welcome back, {{username}}",
      selectDeity: "Select a Deity to Begin"
    },
    deities: {
      title: "Choose Your Deity",
      subtitle: "Select a divine guide for your fortune reading",
      chooseYourBelief: "Choose your belief",
      selectDeity: "Select This Deity",
      totalPoems: "{{count}} Fortune Poems"
    },
    contact: {
      title: "Contact Us",
      subtitle: "Get in touch with our support team",
      thankYouMessage: "Thank you for your message! We'll get back to you soon.",
      getInTouch: "Get in Touch",
      haveQuestions: "Have questions about your fortune reading or need help with our services?",
      workingHours: "Working Hours: Monday - Friday, 9:00 AM - 6:00 PM (PST)",
      customerSupport: "Customer Support: Available during business hours",
      responseTime: "Response Time: We typically respond within 4-6 hours during business days",
      faqTitle: "Frequently Asked Questions",
      sendMessage: "Send Message",
      sending: "Sending..."
    },
    purchase: {
      title: "Buy Divine Coins",
      subtitle: "Every Divine Coin gets you one fortune telling divination.",
      selectedPackage: "Selected Package",
      totalPrice: "Total Price",
      pricePerCoin: "Price Per Coin",
      paymentMethod: "Choose Payment Method",
      purchaseWith: "Purchase with {{method}}",
      coin: "coin",
      coins: "Coins",
      perTime: "time",
      choosePaymentMethod: "Choose Payment Method",
      packages: {
        small: {
          badge: "Perfect for trying"
        },
        popular: {
          badge: "Most popular"
        },
        best: {
          badge: "Best value"
        }
      },
      summary: {
        coinsToReceive: "Coins to receive",
        coinsAfter: "Coins after",
        currentCoins: "Current coins",
        transactionCost: "Transaction cost",
        coinCurrencyRate: "Coin currency rate"
      },
      paymentMethods: {
        card: {
          name: "Credit/Debit Card",
          description: "Visa, Mastercard, American Express"
        },
        paypal: {
          name: "PayPal",
          description: "Pay with your PayPal account"
        },
        applePay: {
          name: "Apple Pay",
          description: "Touch ID or Face ID"
        },
        googlePay: {
          name: "Google Pay",
          description: "Google account payment"
        }
      },
      policy: {
        title: "Policy",
        text: "All coin purchases are final and non-refundable. Coins do not expire and can be used anytime for divine fortune readings. By purchasing, you agree to our terms of service."
      }
    },
    fortuneSelection: {
      title: "Choose Your Fortune Number",
      subtitle: "{{deityName}} - Select a number from the collections below",
      backToDeities: "← Back to Poems",
      chooseNumber: "Choose Your Fortune Number",
      numbersRange: "Numbers 1 - {{max}}"
    },
    fortuneAnalysis: {
      title: "Divine Fortune Reading",
      subtitle: "Fortune #{{number}} - {{fortuneLevel}}",
      backToNumbers: "← Back to Numbers",
      coinsDisplay: "🪙 {{coins}} Coins",
      poemTitle: "Fortune Poem",
      analysisTitle: "Divine Interpretation",
      chatTitle: "Ask for Guidance",
      chatSubtitle: "Discuss this fortune with divine wisdom",
      chatPlaceholder: "Ask about this fortune...",
      sendButton: "Send",
      reportGenerated: "📊 Report Generated",
      viewReportButton: "View Report",
      reportMessage: "Your personalized report has been generated successfully! Click below to view your detailed divine analysis.",
      generatingReport: "🔮 Generating your personalized report...",
      insufficientCoins: "⚠️ You need at least 5 coins to generate a detailed report. Please purchase more coins or ask a general question that doesn't require report generation."
    },
    account: {
      title: "My Account",
      profileInfo: "Profile Information",
      accountStatus: "Account Status",
      purchaseRecords: "Recent Purchase Records",
      reportHistory: "Report History ({{count}})",
      changeAvatar: "Change Avatar",
      username: "Username",
      email: "Email",
      birthDate: "Birth Date",
      gender: "Gender",
      location: "Location",
      currentBalance: "Current Balance",
      membership: "Membership",
      memberSince: "Member Since",
      premiumMember: "Premium Member",
      coins: "Coins",
      noReports: "No reports generated yet. Start a conversation on the fortune analysis page to generate your first report!",
      viewReport: "View Report",
      saveChanges: "Save Changes",
      changePassword: "Change Password",
      logOut: "Log Out",
      profileUpdated: "Profile updated successfully!",
      passwordChangePrompt: "Password change functionality would be implemented here.",
      logoutPrompt: "Logout functionality would be implemented here.",
      genderOptions: {
        male: "Male",
        female: "Female",
        nonBinary: "Non-binary",
        preferNotToSay: "Prefer not to say"
      },
      statusLabels: {
        completed: "Completed",
        generating: "Generating..."
      }
    },
    admin: {
      title: "🛠️ Admin Dashboard",
      stats: {
        totalUsers: "Total Users",
        totalOrders: "Total Orders", 
        activeReports: "Active Reports",
        pendingFaqs: "Pending FAQs"
      },
      sections: {
        customers: "👥 Customer Management",
        poems: "📝 Poems Analysis",
        purchases: "💰 Purchase Management",
        reports: "📊 Reports Storage",
        faqs: "❓ FAQ Management"
      },
      customers: {
        title: "Customer Management",
        addCustomer: "➕ Add Customer",
        exportData: "📤 Export Data",
        searchPlaceholder: "🔍 Search customers by name, email, or ID...",
        headers: {
          customerId: "Customer ID",
          name: "Name",
          email: "Email",
          status: "Status", 
          balance: "Balance",
          joinDate: "Join Date",
          actions: "Actions"
        },
        actions: {
          edit: "✏️ Edit",
          resetPassword: "🔑 Reset PWD"
        }
      },
      poems: {
        title: "Poems Analysis Management",
        addPoem: "➕ Add Poem",
        bulkUpdate: "🔄 Bulk Update",
        searchPlaceholder: "🔍 Search poems by title, deity, or fortune number...",
        chinese: "Chinese",
        analysisTopics: "Analysis Topics",
        lastModified: "Last Modified",
        usageCount: "Usage Count",
        times: "times"
      },
      purchases: {
        title: "Purchase Management",
        generateReport: "📈 Generate Report",
        processRefund: "💸 Process Refund",
        salesChart: "📊 Sales Chart Placeholder",
        chartNote: "Integration with Chart.js or similar library needed",
        searchPlaceholder: "🔍 Search orders by ID, customer, or amount...",
        headers: {
          orderId: "Order ID",
          customer: "Customer",
          package: "Package",
          amount: "Amount",
          status: "Status",
          date: "Date",
          actions: "Actions"
        },
        actions: {
          edit: "✏️ Edit",
          refund: "↩️ Refund"
        }
      },
      reports: {
        title: "Reports Storage Manager",
        bulkExport: "📦 Bulk Export",
        cleanupOld: "🧹 Cleanup Old",
        searchPlaceholder: "🔍 Search reports by customer, deity, or keywords...",
        id: "ID",
        source: "Source",
        question: "Question",
        generated: "Generated",
        wordCount: "Word Count",
        words: "words",
        actions: {
          view: "👁️ View",
          edit: "✏️ Edit",
          delete: "🗑️ Delete"
        }
      },
      faqs: {
        title: "FAQ Management System",
        addFaq: "➕ Add FAQ",
        exportFaqs: "📤 Export FAQs",
        pendingQueue: "⏳ Pending FAQ Queue",
        activeFaqs: "✅ Active FAQs",
        userQuestion: "User Question",
        askedBy: "Asked by",
        received: "Received",
        category: "Category",
        headers: {
          question: "Question",
          category: "Category",
          views: "Views",
          lastUpdated: "Last Updated",
          actions: "Actions"
        },
        actions: {
          approve: "✅ Approve & Add",
          editDraft: "✏️ Edit Draft",
          reject: "❌ Reject",
          edit: "✏️ Edit",
          deactivate: "🔒 Deactivate"
        }
      },
      filters: {
        allStatus: "All Status",
        active: "Active",
        premium: "Premium",
        inactive: "Inactive",
        allTime: "All Time",
        today: "Today",
        thisWeek: "This Week",
        thisMonth: "This Month",
        completed: "Completed",
        pending: "Pending",
        refunded: "Refunded",
        allDeities: "All Poems"
      }
    },
    report: {
      backToHome: "← Back to Home",
      backToAccount: "← Back to Account",
      yourQuestion: "Your Question",
      divineAnalysisOverview: "📊 Divine Analysis Overview",
      careerAnalysis: "💼 Career Analysis",
      relationshipAnalysis: "❤️ Relationship Analysis",
      healthAnalysis: "🌿 Health Analysis",
      luckyElements: "✨ Lucky Elements",
      cautions: "⚠️ Cautions",
      divineAdvice: "🌟 Divine Advice",
      fortuneNumber: "🔢 Fortune #{{number}}",
      deityName: "🏛️ {{deity}}",
      coinsCost: "💰 {{cost}} coins",
      date: "📅 {{date}}"
    }
  },
  forms: {
    labels: {
      name: "Name",
      email: "Email",
      subject: "Subject", 
      message: "Message",
      question: "Your Question"
    },
    placeholders: {
      name: "Your full name",
      email: "your.email@example.com",
      subject: "What can we help you with?",
      message: "Tell us more about your inquiry..."
    },
    validation: {
      required: "This field is required"
    },
    faq: {
      q1: "How accurate are the fortune readings?",
      a1: "Our fortune readings combine traditional Chinese divination methods with AI interpretation. While we strive for meaningful insights, remember that fortunes are guidance tools and should be considered alongside your own judgment.",
      q2: "How much does a fortune reading cost?",
      a2: "Basic fortune readings are free for registered users. Premium readings with detailed analysis and personalized insights are available through our points system. Check our Purchase page for current pricing.",
      q3: "Can I get multiple readings for the same question?",
      a3: "We recommend waiting at least 24 hours before asking the same question again. Traditional divination suggests that asking the same question repeatedly may lead to unclear or conflicting guidance.",
      q4: "Which deity should I choose for my reading?",
      a4: "Each deity specializes in different aspects of life. Guan Yin focuses on compassion and relationships, Guan Yu on courage and career, Mazu on protection and travel. Choose based on your question's nature or trust your intuition.",
      q5: "Is my personal information secure?",
      a5: "Yes, we take privacy seriously. Your personal information, questions, and readings are encrypted and stored securely. We never share your data with third parties without your explicit consent.",
      q6: "Can I save my reading results?",
      a6: "Yes! All your readings are automatically saved to your account history. You can access them anytime from your Account page to review past insights and track your spiritual journey."
    }
  },
  errors: {
    general: {
      somethingWentWrong: "Something went wrong. Please try again."
    }
  }
};

const zhTranslations = {
  common: {
    appName: "神明私語",
    navigation: {
      home: "首頁",
      deities: "籤詩",
      purchase: "購買",
      account: "帳戶",
      contact: "聯絡我們",
      admin: "管理員"
    },
    auth: {
      login: "登入",
      signup: "註冊",
      logout: "登出",
      userRole: "用戶",
      adminRole: "管理員"
    },
    buttons: {
      submit: "提交",
      cancel: "取消",
      continue: "繼續",
      back: "返回",
      next: "下一步",
      close: "關閉",
      save: "保存",
      edit: "編輯",
      delete: "刪除",
      confirm: "確認"
    },
    language: {
      selector: "語言",
      english: "English",
      chinese: "中文",
      japanese: "日本語"
    },
    loading: "載入中...",
    error: "發生錯誤",
    success: "成功"
  },
  pages: {
    landing: {
      title: "神明私語",
      subtitle: "透過古老智慧發現您的命運",
      heroTitle: "聆聽神秘的呼喚指引您的真實道路",
      getStarted: "開始使用",
      learnMore: "了解更多",
      videoError: "您的瀏覽器不支援視頻標籤。"
    },
    home: {
      todaysWhisper: "今日神諭",
      yourFortune: "您的運勢",
      knowYourFate: "了解您的命運",
      readWhisper: "讀取您的神諭",
      demoReport: "示範報告",
      welcomeBack: "歡迎回來，{{username}}",
      selectDeity: "選擇一位神明開始"
    },
    deities: {
      title: "選擇您的神明",
      subtitle: "選擇一位神聖嚮導為您解籤",
      chooseYourBelief: "選擇您的信仰",
      selectDeity: "選擇此神明",
      totalPoems: "{{count}} 首籤詩"
    },
    contact: {
      title: "聯絡我們",
      subtitle: "聯繫我們的客服團隊",
      thankYouMessage: "感謝您的訊息！我們會盡快回覆您。",
      getInTouch: "聯絡我們",
      haveQuestions: "對您的運勢解讀有疑問或需要我們服務方面的協助嗎？",
      workingHours: "工作時間：星期一至星期五，上午9:00 - 下午6:00 (PST)",
      customerSupport: "客服支援：營業時間內提供服務",
      responseTime: "回應時間：我們通常在營業日4-6小時內回覆",
      faqTitle: "常見問題",
      sendMessage: "發送訊息",
      sending: "發送中..."
    },
    purchase: {
      title: "購買神聖錢幣",
      subtitle: "每個神聖錢幣都能為您提供一次運勢占卜解讀。",
      selectedPackage: "選擇的套餐",
      totalPrice: "總價格",
      pricePerCoin: "每枚錢幣價格",
      paymentMethod: "選擇付款方式",
      purchaseWith: "使用 {{method}} 購買",
      coinsToReceive: "將收到的錢幣",
      coinsAfter: "購買後錢幣",
      currentCoins: "當前錢幣",
      transactionCost: "交易費用",
      coinCurrencyRate: "錢幣兌換率",
      coins: "錢幣",
      coin: "錢幣",
      perTime: "次",
      choosePaymentMethod: "選擇付款方式",
      processingPayment: "正在處理付款",
      demoNotice: "這是一個演示。",
      packages: {
        small: {
          badge: "適合嘗試"
        },
        popular: {
          badge: "最受歡迎"
        },
        best: {
          badge: "最超值"
        }
      },
      summary: {
        coinsToReceive: "將收到的錢幣",
        coinsAfter: "購買後錢幣",
        currentCoins: "當前錢幣",
        transactionCost: "交易費用",
        coinCurrencyRate: "錢幣兌換率"
      },
      paymentMethods: {
        card: {
          name: "信用卡/Debit Card",
          description: "Visa, Mastercard, American Express"
        },
        paypal: {
          name: "PayPal",
          description: "使用您的PayPal帳戶付款"
        },
        applePay: {
          name: "Apple Pay",
          description: "Touch ID 或 Face ID"
        },
        googlePay: {
          name: "Google Pay",
          description: "Google 帳戶付款"
        }
      },
      policy: {
        title: "政策",
        text: "所有錢幣購買均為最終交易，不可退款。錢幣不會過期，可隨時用於神聖運勢解讀。購買即表示您同意我們的服務條款。"
      }
    },
    fortuneSelection: {
      title: "選擇您的運勢號碼",
      subtitle: "{{deityName}} - 從下面的集合中選擇一個號碼",
      backToDeities: "← 返回籤詩",
      chooseNumber: "選擇您的運勢號碼",
      numbersRange: "號碼 1 - {{max}}"
    },
    fortuneAnalysis: {
      title: "神聖運勢解讀",
      subtitle: "運勢 #{{number}} - {{fortuneLevel}}",
      backToNumbers: "← 返回號碼",
      coinsDisplay: "🪙 {{coins}} 錢幣",
      poemTitle: "運勢詩",
      analysisTitle: "神聖解釋",
      chatTitle: "尋求指導",
      chatSubtitle: "與神聖智慧討論這個運勢",
      chatPlaceholder: "詢問關於這個運勢...",
      sendButton: "發送",
      reportGenerated: "📊 報告已生成",
      viewReportButton: "查看報告",
      reportMessage: "您的個人化報告已成功生成！點擊下方查看您的詳細神聖分析。",
      generatingReport: "🔮 正在生成您的個人化報告...",
      insufficientCoins: "⚠️ 您需要至少 5 個錢幣才能生成詳細報告。請購買更多錢幣或詢問不需要生成報告的一般問題。"
    },
    account: {
      title: "我的帳戶",
      profileInfo: "個人資料",
      accountStatus: "帳戶狀態",
      purchaseRecords: "最近購買記錄",
      reportHistory: "報告歷史 ({{count}})",
      changeAvatar: "更換頭像",
      username: "用戶名",
      email: "電子郵件",
      birthDate: "出生日期",
      gender: "性別",
      location: "位置",
      currentBalance: "當前餘額",
      membership: "會員身份",
      memberSince: "會員開始日期",
      premiumMember: "高級會員",
      coins: "錢幣",
      noReports: "尚未生成報告。在運勢分析頁面開始對話以生成您的第一個報告！",
      viewReport: "查看報告",
      saveChanges: "保存更改",
      changePassword: "更改密碼",
      logOut: "登出",
      profileUpdated: "個人資料更新成功！",
      passwordChangePrompt: "密碼更改功能將在此處實現。",
      logoutPrompt: "登出功能將在此處實現。",
      genderOptions: {
        male: "男性",
        female: "女性",
        nonBinary: "非二元性別",
        preferNotToSay: "不願透露"
      },
      statusLabels: {
        completed: "已完成",
        generating: "生成中..."
      }
    },
    report: {
      backToHome: "← 返回首頁",
      backToAccount: "← 返回帳戶",
      yourQuestion: "您的問題",
      divineAnalysisOverview: "📊 神聖分析概覽",
      careerAnalysis: "💼 事業分析",
      relationshipAnalysis: "❤️ 關係分析",
      healthAnalysis: "🌿 健康分析",
      luckyElements: "✨ 幸運元素",
      cautions: "⚠️ 注意事項",
      divineAdvice: "🌟 神聖建議",
      fortuneNumber: "🔢 運勢 #{{number}}",
      deityName: "🏛️ {{deity}}",
      coinsCost: "💰 {{cost}} 錢幣",
      date: "📅 {{date}}"
    }
  },
  forms: {
    labels: {
      name: "姓名",
      email: "電子郵件",
      subject: "主題",
      message: "訊息",
      question: "您的問題"
    },
    placeholders: {
      name: "請輸入您的姓名",
      email: "your.email@example.com",
      subject: "我們可以如何協助您？",
      message: "請告訴我們更多關於您的詢問..."
    },
    validation: {
      required: "此欄位為必填"
    },
    faq: {
      q1: "運勢解讀的準確度如何？",
      a1: "我們的運勢解讀結合了傳統中國占卜方法與AI解釋。雖然我們力求提供有意義的洞察，但請記住運勢是指導工具，應該結合您自己的判斷來考慮。",
      q2: "運勢解讀需要多少費用？",
      a2: "註冊用戶可免費獲得基本運勢解讀。詳細分析和個人化洞察的進階解讀可通過我們的點數系統獲得。請查看購買頁面了解目前價格。",
      q3: "我可以為同一個問題獲得多次解讀嗎？",
      a3: "我們建議在再次詢問同一個問題前至少等待24小時。傳統占卜認為重複詢問同一問題可能會導致不清楚或矛盾的指引。",
      q4: "我應該為解讀選擇哪位神明？",
      a4: "每位神明專精於生活的不同方面。觀音專注於慈悲和關係，關公專注於勇氣和事業，媽祖專注於保護和旅行。根據您問題的性質選擇或相信您的直覺。",
      q5: "我的個人資訊安全嗎？",
      a5: "是的，我們非常重視隱私。您的個人資訊、問題和解讀都經過加密並安全儲存。未經您明確同意，我們絕不會與第三方分享您的資料。",
      q6: "我可以儲存我的解讀結果嗎？",
      a6: "可以！您的所有解讀都會自動儲存到您的帳戶歷史記錄中。您可以隨時從帳戶頁面存取它們，回顧過去的洞察並追蹤您的靈性旅程。"
    }
  },
  errors: {
    general: {
      somethingWentWrong: "出現問題，請重試。"
    }
  }
};

const jpTranslations = {
  common: {
    appName: "神々の囁き",
    navigation: {
      home: "ホーム",
      deities: "おみくじ",
      purchase: "購入",
      account: "アカウント",
      contact: "お問い合わせ",
      admin: "管理者"
    },
    auth: {
      login: "ログイン",
      signup: "サインアップ",
      logout: "ログアウト",
      userRole: "ユーザー",
      adminRole: "管理者"
    },
    buttons: {
      submit: "送信",
      cancel: "キャンセル",
      continue: "続ける",
      back: "戻る",
      next: "次へ",
      close: "閉じる",
      save: "保存",
      edit: "編集",
      delete: "削除",
      confirm: "確認"
    },
    language: {
      selector: "言語",
      english: "English",
      chinese: "中文",
      japanese: "日本語"
    },
    loading: "読み込み中...",
    error: "エラーが発生しました",
    success: "成功"
  },
  pages: {
    landing: {
      title: "神々の囁き",
      subtitle: "古代の知恵からあなたの運命を発見",
      heroTitle: "神秘の呼び声があなたの真の道を導く",
      getStarted: "始める",
      learnMore: "詳細を見る",
      videoError: "お使いのブラウザはビデオタグをサポートしていません。"
    },
    home: {
      todaysWhisper: "今日の神託",
      yourFortune: "あなたの運勢",
      knowYourFate: "あなたの運命を知る",
      readWhisper: "神託を読む",
      demoReport: "デモレポート",
      welcomeBack: "おかえりなさい、{{username}}さん",
      selectDeity: "神を選んで始める"
    },
    deities: {
      title: "あなたの神を選択",
      subtitle: "運勢占いのための神聖な案内者を選択",
      chooseYourBelief: "あなたの信念を選択",
      selectDeity: "この神を選択",
      totalPoems: "{{count}}の運勢詩"
    },
    contact: {
      title: "お問い合わせ",
      subtitle: "サポートチームにご連絡ください",
      thankYouMessage: "メッセージをありがとうございます！すぐに返信いたします。",
      getInTouch: "お問い合わせ",
      haveQuestions: "運勢鑑定に関するご質問やサービスについてのヘルプが必要ですか？",
      workingHours: "営業時間：月曜日〜金曜日、午前9:00〜午後6:00（PST）",
      customerSupport: "カスタマーサポート：営業時間内に利用可能",
      responseTime: "応答時間：通常、営業日に4〜6時間以内に返信します",
      faqTitle: "よくある質問",
      sendMessage: "メッセージを送信",
      sending: "送信中..."
    },
    purchase: {
      title: "神聖コインを購入",
      subtitle: "神聖コイン1枚で運勢占い1回をご利用いただけます。",
      selectedPackage: "選択されたパッケージ",
      totalPrice: "総価格",
      pricePerCoin: "コインあたりの価格",
      paymentMethod: "支払い方法を選択",
      purchaseWith: "{{method}}で購入",
      coinsToReceive: "受け取るコイン",
      coinsAfter: "購入後のコイン",
      currentCoins: "現在のコイン",
      transactionCost: "取引費用",
      coinCurrencyRate: "コイン換算レート",
      coins: "コイン",
      coin: "コイン",
      perTime: "回",
      choosePaymentMethod: "支払い方法を選択",
      processingPayment: "支払いを処理中",
      demoNotice: "これはデモです。",
      packages: {
        small: {
          badge: "お試しに最適"
        },
        popular: {
          badge: "最も人気"
        },
        best: {
          badge: "最高の価値"
        }
      },
      summary: {
        coinsToReceive: "受け取るコイン",
        coinsAfter: "購入後のコイン",
        currentCoins: "現在のコイン",
        transactionCost: "取引費用",
        coinCurrencyRate: "コイン換算レート"
      },
      paymentMethods: {
        card: {
          name: "クレジット/Debit Card",
          description: "Visa, Mastercard, American Express"
        },
        paypal: {
          name: "PayPal",
          description: "PayPalアカウントでお支払い"
        },
        applePay: {
          name: "Apple Pay",
          description: "Touch ID または Face ID"
        },
        googlePay: {
          name: "Google Pay",
          description: "Googleアカウント決済"
        }
      },
      policy: {
        title: "ポリシー",
        text: "すべてのコイン購入は最終的なもので、返金不可です。コインに有効期限はなく、いつでも神聖な運勢鑑定にご利用いただけます。購入により、利用規約に同意したものとみなされます。"
      }
    },
    fortuneSelection: {
      title: "運勢番号を選択",
      subtitle: "{{deityName}} - 以下のコレクションから番号を選択してください",
      backToDeities: "← おみくじに戻る",
      chooseNumber: "運勢番号を選択",
      numbersRange: "番号 1 - {{max}}"
    },
    fortuneAnalysis: {
      title: "神聖な運勢鑑定",
      subtitle: "運勢 #{{number}} - {{fortuneLevel}}",
      backToNumbers: "← 番号に戻る",
      coinsDisplay: "🪙 {{coins}} コイン",
      poemTitle: "運勢詩",
      analysisTitle: "神聖な解釈",
      chatTitle: "指導を求める",
      chatSubtitle: "この運勢について神の知恵と相談",
      chatPlaceholder: "この運勢について質問する...",
      sendButton: "送信",
      reportGenerated: "📊 レポート生成完了",
      viewReportButton: "レポートを見る",
      reportMessage: "パーソナライズされたレポートが正常に生成されました！下のボタンをクリックして詳細な神聖分析をご覧ください。",
      generatingReport: "🔮 パーソナライズされたレポートを生成中...",
      insufficientCoins: "⚠️ 詳細レポートを生成するには最低5コインが必要です。コインを購入するか、レポート生成を必要としない一般的な質問をしてください。"
    },
    account: {
      title: "マイアカウント",
      profileInfo: "プロフィール情報",
      accountStatus: "アカウント状況",
      purchaseRecords: "最近の購入記録",
      reportHistory: "レポート履歴 ({{count}})",
      changeAvatar: "アバター変更",
      username: "ユーザー名",
      email: "メール",
      birthDate: "生年月日",
      gender: "性別",
      location: "居住地",
      currentBalance: "現在の残高",
      membership: "メンバーシップ",
      memberSince: "メンバー開始日",
      premiumMember: "プレミアムメンバー",
      coins: "コイン",
      noReports: "まだレポートが生成されていません。運勢分析ページで会話を始めて最初のレポートを生成しましょう！",
      viewReport: "レポートを見る",
      saveChanges: "変更を保存",
      changePassword: "パスワード変更",
      logOut: "ログアウト",
      profileUpdated: "プロフィールが正常に更新されました！",
      passwordChangePrompt: "パスワード変更機能はここで実装されます。",
      logoutPrompt: "ログアウト機能はここで実装されます。",
      genderOptions: {
        male: "男性",
        female: "女性",
        nonBinary: "ノンバイナリー",
        preferNotToSay: "回答しない"
      },
      statusLabels: {
        completed: "完了",
        generating: "生成中..."
      }
    },
    report: {
      backToHome: "← ホームに戻る",
      backToAccount: "← アカウントに戻る",
      yourQuestion: "あなたの質問",
      divineAnalysisOverview: "📊 神聖分析概要",
      careerAnalysis: "💼 キャリア分析",
      relationshipAnalysis: "❤️ 人間関係分析",
      healthAnalysis: "🌿 健康分析",
      luckyElements: "✨ 幸運の要素",
      cautions: "⚠️ 注意事項",
      divineAdvice: "🌟 神聖なアドバイス",
      fortuneNumber: "🔢 運勢 #{{number}}",
      deityName: "🏛️ {{deity}}",
      coinsCost: "💰 {{cost}} コイン",
      date: "📅 {{date}}"
    }
  },
  forms: {
    labels: {
      name: "お名前",
      email: "メール",
      subject: "件名",
      message: "メッセージ",
      question: "あなたの質問"
    },
    placeholders: {
      name: "お名前を入力してください",
      email: "your.email@example.com",
      subject: "どのようなことでお手伝いできますか？",
      message: "お問い合わせの詳細を教えてください..."
    },
    validation: {
      required: "この項目は必須です"
    },
    faq: {
      q1: "運勢鑑定の精度はどの程度ですか？",
      a1: "私たちの運勢鑑定は、伝統的な中国の占術とAI解釈を組み合わせています。意味のある洞察を提供するよう努めていますが、運勢は指針ツールであり、ご自身の判断と併せて考慮すべきであることを覚えておいてください。",
      q2: "運勢鑑定の料金はいくらですか？",
      a2: "登録ユーザーには基本的な運勢鑑定を無料で提供しています。詳細な分析と個人化された洞察を含むプレミアム鑑定は、ポイントシステムを通じて利用できます。現在の価格については購入ページをご確認ください。",
      q3: "同じ質問について複数回鑑定を受けることはできますか？",
      a3: "同じ質問を再び尋ねる前に、少なくとも24時間待つことをお勧めします。伝統的な占術では、同じ質問を繰り返し尋ねると不明確または矛盾した指針につながる可能性があるとされています。",
      q4: "鑑定にはどの神を選ぶべきですか？",
      a4: "それぞれの神は人生の異なる側面を専門としています。観音は慈悲と人間関係に、関羽は勇気とキャリアに、媽祖は保護と旅行に焦点を当てています。質問の性質に基づいて選ぶか、直感を信じてください。",
      q5: "私の個人情報は安全ですか？",
      a5: "はい、プライバシーを真剣に考えています。あなたの個人情報、質問、鑑定結果は暗号化され、安全に保存されています。明示的な同意なしに、第三者とデータを共有することはありません。",
      q6: "鑑定結果を保存できますか？",
      a6: "はい！すべての鑑定結果は自動的にアカウント履歴に保存されます。アカウントページからいつでもアクセスして、過去の洞察を振り返り、精神的な旅路を追跡できます。"
    }
  },
  errors: {
    general: {
      somethingWentWrong: "何かが間違っています。もう一度やり直してください。"
    }
  }
};

export const resources = {
  en: enTranslations,
  zh: zhTranslations,
  jp: jpTranslations,
};

export type Language = keyof typeof resources;
export type Namespace = keyof typeof resources.en;

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    defaultNS: 'common',
    
    // Language detection options
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      lookupLocalStorage: 'divine-whispers-language',
      caches: ['localStorage'],
    },

    interpolation: {
      escapeValue: false, // React already escapes values
    },

    // Development options
    debug: process.env.NODE_ENV === 'development',
    
    // Namespace configuration
    ns: ['common', 'pages', 'forms', 'errors'],
    
    // React specific options
    react: {
      useSuspense: false, // Disable suspense to avoid loading issues
    },
  });

export default i18n;