import { useTranslation as useReactI18next } from 'react-i18next';
import { useEffect } from 'react';
import useAppStore from '../stores/appStore';
import type { Language } from '../types';

// Extended type for translation namespaces
type TranslationNamespace = 'common' | 'pages' | 'forms' | 'errors';

export const useTranslation = (namespace: TranslationNamespace = 'common') => {
  const { t, i18n } = useReactI18next(namespace);
  const { currentLanguage, setCurrentLanguage } = useAppStore();

  // Sync i18next language with Zustand store
  useEffect(() => {
    if (i18n.language !== currentLanguage) {
      i18n.changeLanguage(currentLanguage);
    }
  }, [currentLanguage, i18n]);

  // Function to change language (updates both stores)
  const changeLanguage = (newLanguage: Language) => {
    setCurrentLanguage(newLanguage);
    i18n.changeLanguage(newLanguage);
  };

  // Helper function for translation with fallback
  const translate = (key: string, options?: any) => {
    const translation = t(key, options);
    
    // If translation is missing, return a clear indication
    if (translation === key && process.env.NODE_ENV === 'development') {
      console.warn(`Missing translation for key: ${namespace}.${key} in language: ${currentLanguage}`);
      return `[Missing: ${namespace}.${key}]`;
    }
    
    return translation;
  };

  return {
    t: translate,
    currentLanguage,
    changeLanguage,
    isReady: i18n.isInitialized,
  };
};

// Convenience hooks for specific namespaces
export const useCommonTranslation = () => useTranslation('common');
export const usePagesTranslation = () => useTranslation('pages');
export const useFormsTranslation = () => useTranslation('forms');
export const useErrorsTranslation = () => useTranslation('errors');

// Language display names
export const getLanguageDisplayName = (language: Language): string => {
  const displayNames: Record<Language, string> = {
    en: 'English',
    zh: '中文',
    jp: '日本語',
  };
  return displayNames[language];
};

// Available languages for language selector
export const availableLanguages: Array<{ code: Language; name: string; nativeName: string }> = [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'zh', name: 'Chinese', nativeName: '中文' },
  { code: 'jp', name: 'Japanese', nativeName: '日本語' },
];