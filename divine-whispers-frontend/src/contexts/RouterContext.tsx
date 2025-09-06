import React, { createContext, useContext, ReactNode } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';

interface RouterContextProps {
  children: ReactNode;
}

const RouterContext = createContext({});

export const RouterProvider: React.FC<RouterContextProps> = ({ children }) => {
  return (
    <RouterContext.Provider value={{}}>
      <Router>
        {children}
      </Router>
    </RouterContext.Provider>
  );
};

export const useRouter = () => {
  const context = useContext(RouterContext);
  if (context === undefined) {
    throw new Error('useRouter must be used within a RouterProvider');
  }
  return context;
};

export default RouterProvider;