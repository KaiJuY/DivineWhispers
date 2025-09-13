import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { colors, gradients } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import LoginForm from '../components/auth/LoginForm';
import useAppStore from '../stores/appStore';
import authService from '../services/authService';

const Container = styled.div`
  min-height: 100vh;
  background: ${gradients.background};
  padding: 2rem;
`;

const Content = styled.div`
  max-width: 800px;
  margin: 0 auto;
`;

const Title = styled.h1`
  color: ${colors.primary};
  text-align: center;
  margin-bottom: 2rem;
  font-size: 2rem;
`;

const StatusCard = styled.div`
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(212, 175, 55, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  backdrop-filter: blur(15px);
`;

const StatusTitle = styled.h3`
  color: ${colors.primary};
  margin-bottom: 1rem;
  font-size: 1.2rem;
`;

const StatusItem = styled.div`
  color: ${colors.white};
  margin-bottom: 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const StatusValue = styled.span<{ isGood?: boolean }>`
  color: ${props => props.isGood ? '#51cf66' : '#ff6b6b'};
  font-weight: 600;
`;

const UserInfo = styled.div`
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(212, 175, 55, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  backdrop-filter: blur(15px);
`;

const Button = styled.button`
  background: linear-gradient(135deg, #d4af37 0%, #f4e99b 100%);
  color: ${colors.black};
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-left: 1rem;

  &:hover {
    transform: translateY(-2px);
  }
`;

const BackButton = styled.button`
  background: rgba(212, 175, 55, 0.1);
  border: 2px solid rgba(212, 175, 55, 0.3);
  color: ${colors.primary};
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  margin-bottom: 2rem;

  &:hover {
    background: rgba(212, 175, 55, 0.2);
    border-color: ${colors.primary};
  }
`;

const AuthTestPage: React.FC = () => {
  const { auth, logout, verifyAuth, setCurrentPage } = useAppStore();
  const [backendHealth, setBackendHealth] = useState<boolean | null>(null);

  useEffect(() => {
    checkBackendHealth();
    // Try to verify existing authentication
    if (!auth.isAuthenticated && authService.hasValidSession()) {
      verifyAuth();
    }
  }, []);

  const checkBackendHealth = async () => {
    const isHealthy = await authService.healthCheck();
    setBackendHealth(isHealthy);
  };

  const handleLogout = async () => {
    await logout();
  };

  const handleLoginSuccess = () => {
    // Auto-verify auth after successful login
    verifyAuth();
  };

  return (
    <Layout>
      <Container>
        <Content>
          <BackButton onClick={() => setCurrentPage('home')}>
            ← Back to Home
          </BackButton>

          <Title>Authentication System Test</Title>

          <StatusCard>
            <StatusTitle>Backend Connection Status</StatusTitle>
            <StatusItem>
              <span>Backend API Health:</span>
              <StatusValue isGood={backendHealth === true}>
                {backendHealth === null ? 'Checking...' : backendHealth ? 'Connected ✓' : 'Disconnected ✗'}
              </StatusValue>
              <Button onClick={checkBackendHealth}>Refresh</Button>
            </StatusItem>
            <StatusItem>
              <span>API Base URL:</span>
              <span style={{ color: colors.white, fontSize: '0.8rem' }}>
                {process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}
              </span>
            </StatusItem>
          </StatusCard>

          {auth.isAuthenticated ? (
            <UserInfo>
              <StatusTitle>Authenticated User</StatusTitle>
              <StatusItem>
                <span>Username:</span>
                <StatusValue isGood>{auth.user?.username}</StatusValue>
              </StatusItem>
              <StatusItem>
                <span>Email:</span>
                <StatusValue isGood>{auth.user?.email}</StatusValue>
              </StatusItem>
              <StatusItem>
                <span>Role:</span>
                <StatusValue isGood>{auth.user?.role}</StatusValue>
              </StatusItem>
              <StatusItem>
                <span>Points Balance:</span>
                <StatusValue isGood>{auth.user?.points_balance}</StatusValue>
              </StatusItem>
              <StatusItem>
                <span>Member Since:</span>
                <span style={{ color: colors.white }}>
                  {auth.user?.created_at ? new Date(auth.user.created_at).toLocaleDateString() : 'N/A'}
                </span>
              </StatusItem>
              <StatusItem>
                <span>Actions:</span>
                <Button onClick={handleLogout}>
                  {auth.loading ? 'Logging out...' : 'Logout'}
                </Button>
              </StatusItem>
            </UserInfo>
          ) : (
            <LoginForm onSuccess={handleLoginSuccess} />
          )}

          <StatusCard>
            <StatusTitle>Authentication Status</StatusTitle>
            <StatusItem>
              <span>Is Authenticated:</span>
              <StatusValue isGood={auth.isAuthenticated}>
                {auth.isAuthenticated ? 'Yes ✓' : 'No ✗'}
              </StatusValue>
            </StatusItem>
            <StatusItem>
              <span>Has Access Token:</span>
              <StatusValue isGood={!!auth.tokens?.access_token}>
                {auth.tokens?.access_token ? 'Yes ✓' : 'No ✗'}
              </StatusValue>
            </StatusItem>
            <StatusItem>
              <span>Loading State:</span>
              <StatusValue isGood={!auth.loading}>
                {auth.loading ? 'Loading...' : 'Ready'}
              </StatusValue>
            </StatusItem>
          </StatusCard>
        </Content>
      </Container>
    </Layout>
  );
};

export default AuthTestPage;