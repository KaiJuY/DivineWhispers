import React from 'react';
import { ThemeProvider } from 'styled-components';
import { GlobalStyle } from './assets/styles/globalStyles';
import RouterProvider from './contexts/RouterContext';
import useAppStore from './stores/appStore';
import LandingPage from './pages/LandingPage';
import HomePage from './pages/HomePage';
import DeitiesPage from './pages/DeitiesPage';
import FortuneSelectionPage from './pages/FortuneSelectionPage';
import FortuneAnalysisPage from './pages/FortuneAnalysisPage';
import ContactPage from './pages/ContactPage';
import PurchasePage from './pages/PurchasePage';

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
  const { currentPage } = useAppStore();

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'landing':
        return <LandingPage />;
      case 'home':
        return <HomePage />;
      case 'deities':
      case 'deity-selection':
        return <DeitiesPage />;
      case 'fortune-selection':
        return <FortuneSelectionPage />;
      case 'fortune-analysis':
        return <FortuneAnalysisPage />;
      case 'purchase':
        return <PurchasePage />;
      case 'account':
        // TODO: Implement AccountPage
        return <HomePage />;
      case 'contact':
        return <ContactPage />;
      default:
        return <LandingPage />;
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <RouterProvider>
        <GlobalStyle />
        {renderCurrentPage()}
      </RouterProvider>
    </ThemeProvider>
  );
};

export default App;
