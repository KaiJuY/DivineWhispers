import React, { createContext, useContext, ReactNode } from 'react';
import { BrowserRouter as Router, useNavigate, useLocation, useParams } from 'react-router-dom';

interface RouterContextProps {
  children: ReactNode;
}

interface RouterContextValue {
  navigate: (path: string) => void;
  location: ReturnType<typeof useLocation>;
  params: ReturnType<typeof useParams>;
}

const RouterContext = createContext<RouterContextValue | undefined>(undefined);

// Inner component that has access to React Router hooks
const RouterContextProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const params = useParams();

  const value: RouterContextValue = {
    navigate,
    location,
    params,
  };

  return (
    <RouterContext.Provider value={value}>
      {children}
    </RouterContext.Provider>
  );
};

export const RouterProvider: React.FC<RouterContextProps> = ({ children }) => {
  return (
    <Router>
      <RouterContextProvider>
        {children}
      </RouterContextProvider>
    </Router>
  );
};

export const useRouter = () => {
  const context = useContext(RouterContext);
  if (context === undefined) {
    throw new Error('useRouter must be used within a RouterProvider');
  }
  return context;
};

// Convenience hooks that can be used directly
export const useAppNavigate = () => {
  const { navigate } = useRouter();
  return navigate;
};

export const useAppLocation = () => {
  const { location } = useRouter();
  return location;
};

export const useAppParams = () => {
  const { params } = useRouter();
  return params;
};

export default RouterProvider;