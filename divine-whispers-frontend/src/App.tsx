import React from 'react';
import { ThemeProvider } from 'styled-components';
import { Routes, Route, Navigate } from 'react-router-dom';
import { GlobalStyle } from './assets/styles/globalStyles';
import RouterProvider from './contexts/RouterContext';
import useAppStore from './stores/appStore';
import './i18n/config'; // Initialize i18n
import LandingPage from './pages/LandingPage';
import HomePage from './pages/HomePage';
import DeitiesPage from './pages/DeitiesPage';
import FortuneSelectionPage from './pages/FortuneSelectionPage';
import FortuneAnalysisPage from './pages/FortuneAnalysisPage';
import ContactPage from './pages/ContactPage';
import PurchasePage from './pages/PurchasePage';
import AccountPage from './pages/AccountPage';
import AdminPage from './pages/AdminPage';
import ReportPage from './pages/ReportPage';
import AuthTestPage from './pages/AuthTestPage';

// Theme object for styled-components
const theme = {
  colors: {
    primary: '#d4af37',
    primaryLight: '#f4e99b',
    primaryDark: '#b8941f',
    white: '#ffffff',
    black: '#000000',
    darkBlue: '#0a1128',
    mediumBlue: '#1e2749',
    lightBlue: '#2d3748',
  },
  gradients: {
    primary: 'linear-gradient(135deg, #d4af37 0%, #f4e99b 100%)',
    background: 'linear-gradient(135deg, #0a1128 0%, #1e2749 50%, #2d3748 100%)',
  },
  breakpoints: {
    mobile: '480px',
    tablet: '768px',
    desktop: '1024px',
    large: '1400px',
  },
};

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <RouterProvider>
        <GlobalStyle />
        <Routes>
          {/* Landing/Home Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/home" element={<HomePage />} />

          {/* Fortune Telling Flow */}
          <Route path="/deities" element={<DeitiesPage />} />
          <Route path="/deity-selection" element={<DeitiesPage />} />
          <Route path="/fortune-selection" element={<FortuneSelectionPage />} />
          <Route path="/fortune-analysis" element={<FortuneAnalysisPage />} />
          <Route path="/poem" element={<DeitiesPage />} />
          <Route path="/poem/:deity" element={<FortuneSelectionPage />} />
          <Route path="/poem/:deity/:number" element={<FortuneAnalysisPage />} />

          {/* Other Pages */}
          <Route path="/purchase" element={<PurchasePage />} />
          <Route path="/account" element={<AccountPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/report" element={<ReportPage />} />

          {/* Admin Routes */}
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/auth-test" element={<AuthTestPage />} />

          {/* Catch-all redirect to landing */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </RouterProvider>
    </ThemeProvider>
  );
};

export default App;
