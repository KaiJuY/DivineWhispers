import React from 'react';
import styled, { keyframes, css } from 'styled-components';
import { colors, gradients, media } from '../../assets/styles/globalStyles';
import useAppStore from '../../stores/appStore';

interface HeaderProps {
  isLanding?: boolean;
}

const HeaderContainer = styled.header<{ isLanding: boolean }>`
  position: ${props => props.isLanding ? 'absolute' : 'fixed'};
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  padding: ${props => props.isLanding ? '25px 40px' : '20px 40px'};
  background: ${props => props.isLanding ? 'transparent' : 'rgba(10, 17, 40, 0.95)'};
  backdrop-filter: ${props => props.isLanding ? 'none' : 'blur(15px)'};
  border-bottom: ${props => props.isLanding ? 'none' : '1px solid rgba(212, 175, 55, 0.2)'};
  transition: all 0.3s ease;

  ${media.tablet} {
    padding: ${props => props.isLanding ? '20px 20px' : '15px 20px'};
  }
`;

const NavContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 22px;
  font-weight: bold;
  color: ${colors.primary};
  letter-spacing: 1px;
  cursor: pointer;

  ${media.tablet} {
    font-size: 18px;
  }
`;

const LogoIcon = styled.div`
  width: 35px;
  height: 35px;
  background: ${gradients.primary};
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: ${colors.black};
  box-shadow: 0 0 15px rgba(212, 175, 55, 0.4);

  ${media.tablet} {
    width: 30px;
    height: 30px;
    font-size: 16px;
  }
`;

const HeaderLogo = styled.img`
  height: 60px;
  width: auto;
  object-fit: contain;
  filter: drop-shadow(0 2px 8px rgba(212, 175, 55, 0.3));

  ${media.tablet} {
    height: 50px;
  }
`;

const MainNav = styled.nav<{ isLanding: boolean }>`
  display: ${props => props.isLanding ? 'none' : 'flex'};
  gap: 40px;
  list-style: none;

  ${media.desktop} {
    gap: 30px;
  }

  ${media.tablet} {
    display: none; // Will implement mobile menu later
  }
`;

const shimmer = keyframes`
  0% {
    background-position: -468px 0;
  }
  100% {
    background-position: 468px 0;
  }
`;
const NavLink = styled.a<{ active?: boolean }>`
  color: ${props => props.active ? colors.primary : colors.white};
  text-decoration: none;
  font-size: 20px;
  font-weight: 500;
  transition: all 0.3s ease;
  cursor: pointer;
  padding: 8px 0;
  position: relative;

  ${props => props.active && css`
    background: linear-gradient(45deg, ${colors.primary}, #f2d06b, ${colors.primary});
    background-size: 200% 200%;
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: ${shimmer} 15s linear infinite;
  `}

  &::after {
    content: '';
    position: absolute;
    width: ${props => props.active ? '100%' : '0'};
    height: 2px;
    bottom: -5px;
    left: 50%;
    background: ${props => props.active ? 
      'linear-gradient(90deg, transparent, ' + colors.primary + ', transparent)' : 
      colors.primary};
    background-size: ${props => props.active ? '200% 100%' : 'auto'};
    transition: all 0.3s ease;
    transform: translateX(-50%);
    ${props => props.active && css`
      animation: ${shimmer} 15s linear infinite;
    `}
  }

  &:hover {
    color: ${colors.primary};
    background: linear-gradient(45deg, ${colors.primary}, #f2d06b, ${colors.primary});
    background-size: 200% 200%;
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: ${shimmer} 15s linear infinite;

    &::after {
      width: 100%;
      background: linear-gradient(90deg, transparent, ${colors.primary}, transparent);
      background-size: 200% 100%;
      animation: ${shimmer} 15s linear infinite;
    }
  }

  ${media.desktop} {
    font-size: 16px;
  }
`;

const AuthSection = styled.div`
  display: flex;
  align-items: center;
  gap: 15px;

  ${media.tablet} {
    gap: 10px;
  }
`;

const AuthButton = styled.button<{ secondary?: boolean }>`
  padding: 10px 20px;
  background: ${props => props.secondary ? 'transparent' : colors.primary};
  color: ${props => props.secondary ? colors.white : colors.black};
  border: ${props => props.secondary ? `1px solid ${colors.primary}` : 'none'};
  border-radius: 25px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;

  &:hover {
    background: ${props => props.secondary ? colors.primary : 'rgba(212, 175, 55, 0.9)'};
    color: ${colors.black};
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
  }

  ${media.tablet} {
    padding: 8px 15px;
    font-size: 12px;
  }
`;

const UserInfo = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
`;

const UserEmail = styled.span`
  color: ${colors.white};
  font-size: 14px;
  font-weight: 500;

  ${media.tablet} {
    font-size: 12px;
  }
`;

const UserRole = styled.span<{ isAdmin?: boolean }>`
  color: ${props => props.isAdmin ? colors.primary : 'rgba(255, 255, 255, 0.7)'};
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;

  ${media.tablet} {
    font-size: 10px;
  }
`;

const LanguageSelector = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: rgba(212, 175, 55, 0.15);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  &:hover {
    background: rgba(212, 175, 55, 0.25);
    border-color: rgba(212, 175, 55, 0.5);
    transform: translateY(-2px);
  }

  ${media.tablet} {
    padding: 8px 15px;
    font-size: 12px;
  }
`;

const Header: React.FC<HeaderProps> = ({ isLanding = false }) => {
  const { currentPage, setCurrentPage, auth, setAuth } = useAppStore();

  // Check user authentication and role
  const isAuthenticated = auth.isAuthenticated;
  const isAdmin = isAuthenticated && auth.user?.role === 'admin';
  const userEmail = auth.user?.email;

  const handleNavClick = (page: string) => {
    if (page === 'home') {
      setCurrentPage('home');
    } else if (page === 'landing') {
      setCurrentPage('landing');
    }
  };

  const handleLogin = () => {
    // For demo purposes, simulate different user types
    const userType = prompt('Login as:\n1. Regular user (enter "user")\n2. Admin (enter "admin")\n3. Cancel (press Cancel)');
    
    if (userType === 'user') {
      setAuth({
        user: {
          user_id: 123,
          email: "user@example.com",
          username: "RegularUser",
          role: "user",
          points_balance: 25,
          created_at: "2024-01-15T10:30:00Z",
          birth_date: "1990-03-15",
          gender: "Male",
          location: "San Francisco, CA, USA"
        },
        tokens: {
          access_token: "user_token_here",
          refresh_token: "user_refresh_token",
          expires_in: 3600
        },
        isAuthenticated: true,
        loading: false
      });
      alert('✅ Logged in as Regular User');
    } else if (userType === 'admin') {
      setAuth({
        user: {
          user_id: 1,
          email: "admin@divinewhispers.com",
          username: "AdminUser",
          role: "admin",
          points_balance: 999,
          created_at: "2024-01-01T00:00:00Z",
          birth_date: "1985-01-01",
          gender: "Admin",
          location: "Divine Realm"
        },
        tokens: {
          access_token: "admin_token_here",
          refresh_token: "admin_refresh_token",
          expires_in: 3600
        },
        isAuthenticated: true,
        loading: false
      });
      alert('✅ Logged in as Admin');
    }
  };

  const handleSignup = () => {
    // Navigate to a signup page or show signup modal
    alert('🚀 Signup functionality - would redirect to signup form');
    setCurrentPage('home');
  };

  const handleLogout = () => {
    setAuth({
      user: null,
      tokens: null,
      isAuthenticated: false,
      loading: false
    });
    // Redirect to home after logout
    setCurrentPage('home');
    alert('👋 Logged out successfully');
  };

  const handleLanguageChange = () => {
    // TODO: Implement language switching logic
    console.log('Language switch clicked');
  };

  return (
    <HeaderContainer isLanding={isLanding}>
      <NavContainer>
        <Logo onClick={() => handleNavClick('landing')}>
          <HeaderLogo src="/assets/divine whispers logo.png" alt="Divine Whispers" />
        </Logo>

        <MainNav isLanding={isLanding}>
          <NavLink 
            active={currentPage === 'home'} 
            onClick={() => handleNavClick('home')}
          >
            Home
          </NavLink>
          <NavLink 
            active={currentPage === 'deities'} 
            onClick={() => setCurrentPage('deities')}
          >
            Deities
          </NavLink>
          <NavLink 
            active={currentPage === 'purchase'} 
            onClick={() => setCurrentPage('purchase')}
          >
            Purchase
          </NavLink>
          
          {/* Show Account link only when user is logged in */}
          {isAuthenticated && (
            <NavLink 
              active={currentPage === 'account'} 
              onClick={() => setCurrentPage('account')}
            >
              Account
            </NavLink>
          )}
          
          <NavLink 
            active={currentPage === 'contact'} 
            onClick={() => setCurrentPage('contact')}
          >
            Contact
          </NavLink>
          
          {/* Show Admin link only for admin users */}
          {isAdmin && (
            <NavLink 
              active={currentPage === 'admin'} 
              onClick={() => setCurrentPage('admin')}
            >
              Admin
            </NavLink>
          )}
        </MainNav>

        {/* Auth Section - replaces language selector */}
        <AuthSection>
          {!isAuthenticated ? (
            // Show Login/Signup when not authenticated
            <>
              <AuthButton onClick={handleLogin}>
                Login
              </AuthButton>
              <AuthButton secondary onClick={handleSignup}>
                Sign Up
              </AuthButton>
            </>
          ) : (
            // Show user info and logout when authenticated
            <>
              <UserInfo>
                <UserEmail>{userEmail}</UserEmail>
                <UserRole isAdmin={isAdmin}>
                  {isAdmin ? '👑 Admin' : '👤 User'}
                </UserRole>
              </UserInfo>
              <AuthButton secondary onClick={handleLogout}>
                Logout
              </AuthButton>
            </>
          )}
          
          <LanguageSelector onClick={handleLanguageChange}>
            <span>🌐</span>
            <span>EN</span>
            <span>▾</span>
          </LanguageSelector>
        </AuthSection>
      </NavContainer>
    </HeaderContainer>
  );
};

export default Header;