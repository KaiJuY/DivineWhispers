import React, { ReactNode } from 'react';
import styled from 'styled-components';
import { gradients } from '../../assets/styles/globalStyles';
import Header from './Header';
import useAppStore from '../../stores/appStore';

interface LayoutProps {
  children: ReactNode;
  isLanding?: boolean;
}

const LayoutContainer = styled.div<{ isLanding: boolean }>`
  min-height: 100vh;
  background: ${props => props.isLanding ? '#000' : gradients.background};
  display: flex;
  flex-direction: column;
`;

const MainContent = styled.main<{ isLanding: boolean }>`
  flex: 1;
  padding-top: ${props => props.isLanding ? '0' : '80px'};
  width: 100%;
`;

const Layout: React.FC<LayoutProps> = ({ children, isLanding = false }) => {
  return (
    <LayoutContainer isLanding={isLanding}>
      <Header isLanding={isLanding} />
      <MainContent isLanding={isLanding}>
        {children}
      </MainContent>
    </LayoutContainer>
  );
};

export default Layout;