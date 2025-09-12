import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Define translations directly in TypeScript for better type safety and compilation
const enTranslations = {
  common: {
    appName: "Divine Whispers",
    navigation: {
      home: "Home",
      deities: "Deities",
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
      getStarted: "Get Started",
      learnMore: "Learn More"
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
      selectDeity: "Select This Deity",
      totalPoems: "{{count}} Fortune Poems"
    }
  },
  forms: {
    labels: {
      name: "Name",
      email: "Email Address",
      question: "Your Question"
    },
    validation: {
      required: "This field is required"
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
      deities: "神明",
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
      getStarted: "開始使用",
      learnMore: "了解更多"
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
      selectDeity: "選擇此神明",
      totalPoems: "{{count}} 首籤詩"
    }
  },
  forms: {
    labels: {
      name: "姓名",
      email: "電子郵件地址",
      question: "您的問題"
    },
    validation: {
      required: "此欄位為必填"
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
      deities: "神々",
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
      getStarted: "始める",
      learnMore: "詳細を見る"
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
      selectDeity: "この神を選択",
      totalPoems: "{{count}}の運勢詩"
    }
  },
  forms: {
    labels: {
      name: "お名前",
      email: "メールアドレス",
      question: "あなたの質問"
    },
    validation: {
      required: "この項目は必須です"
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