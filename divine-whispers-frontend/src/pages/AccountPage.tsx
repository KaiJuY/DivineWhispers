import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { colors, gradients, media } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import useAppStore from '../stores/appStore';
import { usePagesTranslation } from '../hooks/useTranslation';
import { profileService, UserProfile, UserReport, PurchaseRecord as APIPurchaseRecord } from '../services/profileService';

interface PurchaseRecord {
  id: string;
  title: string;
  subtitle: string;
  amount: string;
  date: string;
  status: 'Completed' | 'Pending';
}

const AccountContainer = styled.div`
  width: 100%;
  min-height: 100vh;
`;

const AccountSection = styled.section`
  padding: 120px 40px 80px;
  background: ${gradients.heroSection};
  min-height: 100vh;

  ${media.tablet} {
    padding: 100px 20px 60px;
  }

  ${media.mobile} {
    padding: 80px 20px 40px;
  }
`;

const AccountContent = styled.div`
  max-width: 1000px;
  margin: 0 auto;
`;

const AccountTitle = styled.h1`
  color: ${colors.primary};
  font-size: 2.5rem;
  text-align: center;
  margin-bottom: 50px;
  font-weight: bold;

  ${media.mobile} {
    font-size: 2rem;
    margin-bottom: 30px;
  }
`;

const AccountCard = styled.div`
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(212, 175, 55, 0.05) 100%);
  border: 2px solid rgba(212, 175, 55, 0.3);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 30px;
  backdrop-filter: blur(15px);

  ${media.mobile} {
    padding: 30px 20px;
    margin-bottom: 20px;
  }
`;

const CardTitle = styled.h3`
  color: ${colors.primary};
  font-size: 1.5rem;
  margin-bottom: 30px;
  font-weight: bold;

  ${media.mobile} {
    font-size: 1.3rem;
    margin-bottom: 20px;
  }
`;

// Profile Information Styles
const ProfileFields = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const FieldRow = styled.div`
  display: flex;
  gap: 20px;

  ${media.mobile} {
    flex-direction: column;
    gap: 15px;
  }
`;

const FieldGroup = styled.div<{ fullWidth?: boolean }>`
  flex: ${props => props.fullWidth ? '2' : '1'};
  display: flex;
  flex-direction: column;
  position: relative;
`;

const FieldLabel = styled.label`
  color: ${colors.primary};
  font-size: 0.9rem;
  margin-bottom: 8px;
  font-weight: 600;
`;

const ProfileInput = styled.input`
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 8px;
  padding: 12px;
  color: #fff;
  font-size: 1rem;
  transition: all 0.3s ease;

  &:focus {
    border-color: ${colors.primary};
    outline: none;
    box-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }

  /* Enhanced styling for date input */
  &[type="date"] {
    position: relative;
    color: #fff;

    &::-webkit-calendar-picker-indicator {
      background-color: ${colors.primary};
      border-radius: 4px;
      padding: 4px;
      cursor: pointer;
      filter: invert(0);
      margin-left: 8px;
    }

    &::-webkit-datetime-edit {
      color: #fff;
      padding: 2px;
    }

    &::-webkit-datetime-edit-text {
      color: rgba(255, 255, 255, 0.7);
      padding: 0 2px;
    }

    &::-webkit-datetime-edit-month-field,
    &::-webkit-datetime-edit-day-field,
    &::-webkit-datetime-edit-year-field {
      color: #fff;
      background: transparent;
      border-radius: 3px;
      padding: 2px 4px;

      &:hover {
        background: rgba(212, 175, 55, 0.2);
      }

      &:focus {
        background: rgba(212, 175, 55, 0.3);
        outline: none;
      }
    }

    /* Style the calendar popup when it opens */
    &::-webkit-calendar-picker-indicator:hover {
      background-color: #f4e99b;
      transform: scale(1.1);
    }
  }
`;

const ProfileSelect = styled.select`
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 8px;
  padding: 12px;
  color: #fff;
  font-size: 1rem;
  transition: all 0.3s ease;
  cursor: pointer;
  appearance: none;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="8" viewBox="0 0 12 8"><path fill="%23d4af37" d="M6 8L0 0h12z"/></svg>');
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 40px;
  background-size: 12px 8px;

  &:focus {
    border-color: ${colors.primary};
    outline: none;
    box-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
    background-color: rgba(0, 0, 0, 0.5);

    /* Rotate arrow when focused/opened */
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="8" viewBox="0 0 12 8"><path fill="%23f4e99b" d="M0 8L12 8L6 0z"/></svg>');
  }

  &:hover {
    border-color: rgba(212, 175, 55, 0.5);
    background-color: rgba(212, 175, 55, 0.05);
  }

  /* Enhanced option styling */
  option {
    background: #1e2749;
    color: #fff;
    padding: 12px 16px;
    border: none;
    font-size: 1rem;

    /* Add some spacing between options */
    &:not(:last-child) {
      border-bottom: 1px solid rgba(212, 175, 55, 0.1);
    }
  }

  option:checked {
    background: linear-gradient(135deg, ${colors.primary} 0%, #f4e99b 100%);
    color: #000;
    font-weight: 600;
  }

  option:hover {
    background: rgba(212, 175, 55, 0.2);
    color: ${colors.primary};
  }

  /* Style the dropdown when it's opened */
  &:focus option {
    background: #1e2749;
    color: #fff;
  }

  &:focus option:checked {
    background: linear-gradient(135deg, ${colors.primary} 0%, #f4e99b 100%);
    color: #000;
  }

  &:focus option:hover {
    background: rgba(212, 175, 55, 0.3);
    color: #fff;
  }
`;

// Account Status Styles
const StatusInfo = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;

  ${media.mobile} {
    grid-template-columns: 1fr;
    gap: 15px;
  }
`;

const StatusItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  border: 1px solid rgba(212, 175, 55, 0.2);
`;

const StatusLabel = styled.div`
  color: #ccc;
  font-size: 0.9rem;
`;

const StatusValue = styled.div<{ highlight?: boolean }>`
  color: ${props => props.highlight ? colors.primary : '#fff'};
  font-weight: bold;
  font-size: ${props => props.highlight ? '1.2rem' : '1rem'};
`;

// Records List Styles
const RecordsList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(212, 175, 55, 0.3);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: rgba(212, 175, 55, 0.5);
  }
`;

const RecordItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  border: 1px solid rgba(212, 175, 55, 0.2);
  transition: all 0.3s ease;

  &:hover {
    background: rgba(212, 175, 55, 0.1);
    border-color: rgba(212, 175, 55, 0.3);
  }

  ${media.mobile} {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
`;

const RecordLeft = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
`;

const RecordTitle = styled.div`
  color: #fff;
  font-weight: 600;
  font-size: 0.95rem;
`;

const RecordSubtitle = styled.div`
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
`;

const RecordRight = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;

  ${media.mobile} {
    align-items: flex-start;
    flex-direction: row;
    justify-content: space-between;
    width: 100%;
  }
`;

const RecordAmount = styled.div`
  color: ${colors.primary};
  font-weight: bold;
  font-size: 0.95rem;
`;

const RecordDate = styled.div`
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.8rem;
`;

const RecordStatus = styled.div<{ status: string }>`
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: bold;
  background: ${props => props.status === 'Completed' ? 'rgba(52, 199, 89, 0.2)' : 'rgba(255, 149, 0, 0.2)'};
  color: ${props => props.status === 'Completed' ? '#34c759' : '#ff9500'};
  border: 1px solid ${props => props.status === 'Completed' ? 'rgba(52, 199, 89, 0.3)' : 'rgba(255, 149, 0, 0.3)'};
`;

// Analysis Reports Styles
const AnalysisItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  border: 1px solid rgba(212, 175, 55, 0.2);
  transition: all 0.3s ease;
  cursor: pointer;
  margin-bottom: 12px;

  &:hover {
    background: rgba(212, 175, 55, 0.1);
    border-color: rgba(212, 175, 55, 0.3);
    transform: translateY(-2px);
  }

  ${media.mobile} {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
`;

const AnalysisInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
`;

const AnalysisTitle = styled.div`
  color: ${colors.primary};
  font-weight: 600;
  font-size: 1rem;
`;

const AnalysisSubtitle = styled.div`
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.85rem;
`;

const AnalysisMeta = styled.div`
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.8rem;
`;

const AnalysisAction = styled.div`
  color: ${colors.primary};
  font-size: 0.9rem;
  font-weight: 600;
  padding: 8px 16px;
  border: 1px solid rgba(212, 175, 55, 0.4);
  border-radius: 8px;
  background: rgba(212, 175, 55, 0.1);
  transition: all 0.3s ease;

  &:hover {
    background: rgba(212, 175, 55, 0.2);
    transform: translateY(-1px);
  }

  ${media.mobile} {
    align-self: flex-end;
  }
`;

// Action Buttons
const AccountActions = styled.div`
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 40px;

  ${media.mobile} {
    flex-direction: column;
    gap: 15px;
  }
`;

const ActionButton = styled.button<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 15px 30px;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;

  ${props => {
    switch (props.variant) {
      case 'primary':
        return `
          background: linear-gradient(135deg, ${colors.primary} 0%, #f4e99b 100%);
          color: #000;
          box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);

          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(212, 175, 55, 0.4);
          }
        `;
      case 'danger':
        return `
          background: rgba(220, 53, 69, 0.2);
          border: 1px solid rgba(220, 53, 69, 0.4);
          color: #dc3545;

          &:hover {
            background: rgba(220, 53, 69, 0.3);
            transform: translateY(-2px);
          }
        `;
      default:
        return `
          background: rgba(212, 175, 55, 0.2);
          border: 1px solid rgba(212, 175, 55, 0.4);
          color: ${colors.primary};

          &:hover {
            background: rgba(212, 175, 55, 0.3);
            transform: translateY(-2px);
          }
        `;
    }
  }}
`;

// Change Password Modal Styled Components
const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
`;

const ModalContainer = styled.div`
  background: ${gradients.heroSection};
  border-radius: 20px;
  padding: 40px;
  width: 90%;
  max-width: 500px;
  border: 1px solid rgba(212, 175, 55, 0.3);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  position: relative;
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
`;

const ModalTitle = styled.h2`
  color: ${colors.primary};
  font-size: 1.5rem;
  font-weight: bold;
  margin: 0;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  width: 35px;
  height: 35px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
  }
`;

const PasswordForm = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const PasswordField = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const PasswordLabel = styled.label`
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  font-weight: 500;
`;

const PasswordInput = styled.input`
  padding: 15px;
  border-radius: 10px;
  border: 1px solid rgba(212, 175, 55, 0.3);
  background: rgba(0, 0, 0, 0.3);
  color: #fff;
  font-size: 1rem;
  transition: all 0.3s ease;

  &:focus {
    outline: none;
    border-color: ${colors.primary};
    box-shadow: 0 0 15px rgba(212, 175, 55, 0.2);
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
`;

const ErrorMessage = styled.div`
  color: #ff6b6b;
  font-size: 0.9rem;
  text-align: center;
  padding: 10px;
  background: rgba(255, 107, 107, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(255, 107, 107, 0.3);
`;

const ModalActions = styled.div`
  display: flex;
  gap: 15px;
  margin-top: 30px;
`;

const ModalButton = styled.button<{ variant?: 'primary' | 'secondary' }>`
  flex: 1;
  padding: 15px;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;

  ${props => props.variant === 'primary' ? `
    background: linear-gradient(135deg, ${colors.primary} 0%, #f4e99b 100%);
    color: #000;
    box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(212, 175, 55, 0.4);
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  ` : `
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: #fff;

    &:hover {
      background: rgba(255, 255, 255, 0.2);
      transform: translateY(-2px);
    }
  `}
`;

const AccountPage: React.FC = () => {
  const { auth } = useAppStore();
  const { t } = usePagesTranslation();

  // State for user profile data
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [userReports, setUserReports] = useState<UserReport[]>([]);
  const [purchaseRecords, setPurchaseRecords] = useState<PurchaseRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State for Change Password modal
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  // Derived profile data for form fields
  type ProfileData = {
    username: string;
    email: string;
    birthDate: string;
    gender: string;
    location: string;
  };

  const [profileData, setProfileData] = useState<ProfileData>({
    username: '',
    email: '',
    birthDate: '',
    gender: 'Male',
    location: ''
  });

  // Load user data on component mount
  useEffect(() => {
    const loadUserData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch user profile
        const profile = await profileService.getUserProfile();
        setUserProfile(profile);

        // Update form data
        setProfileData({
          username: profile.full_name || '',
          email: profile.email,
          birthDate: profile.birth_date || '',
          gender: 'Male', // Default since backend doesn't have gender field
          location: profile.location || ''
        });

        // Fetch user reports
        const reportsData = await profileService.getUserReports();
        setUserReports(reportsData.reports);

        // Fetch purchase history and convert to display format
        try {
          const purchaseData = await profileService.getPurchaseHistory(5); // Recent 5 purchases
          const convertedPurchases: PurchaseRecord[] = purchaseData.purchases.map(purchase => ({
            id: purchase.purchase_id,
            title: purchase.description,
            subtitle: purchase.package_type,
            amount: `${purchase.amount} coins`,
            date: new Date(purchase.created_at).toLocaleDateString(),
            status: purchase.status === 'completed' ? 'Completed' : 'Pending'
          }));
          setPurchaseRecords(convertedPurchases);
        } catch (purchaseError) {
          console.warn('Failed to load purchase history:', purchaseError);
          // Keep empty array if purchase history fails to load
          setPurchaseRecords([]);
        }

      } catch (err: any) {
        console.error('Failed to load user data:', err);
        setError(err.message || 'Failed to load user data');
      } finally {
        setLoading(false);
      }
    };

    if (auth.isAuthenticated) {
      loadUserData();
    }
  }, [auth.isAuthenticated]);

  // Handle input changes
  const handleInputChange = (field: keyof ProfileData, value: string) => {
    setProfileData(prev => ({
      ...prev,
      [field]: value
    }));
  };


  const handleSaveChanges = async () => {
    if (!userProfile) return;

    try {
      console.log('Saving changes:', profileData);

      const updateData = {
        full_name: profileData.username,
        birth_date: profileData.birthDate,
        location: profileData.location,
        preferred_language: 'zh' // Default to Chinese
      };

      const updatedProfile = await profileService.updateUserProfile(updateData);
      setUserProfile(updatedProfile);
      alert(t('account.profileUpdated'));

    } catch (err: any) {
      console.error('Failed to update profile:', err);
      alert(`Failed to update profile: ${err.message}`);
    }
  };

  const handleChangePassword = () => {
    console.log('Change password requested');
    setShowPasswordModal(true);
    setPasswordError(null);
    setPasswordForm({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
  };

  const handlePasswordFormChange = (field: string, value: string) => {
    setPasswordForm(prev => ({
      ...prev,
      [field]: value
    }));
    setPasswordError(null);
  };

  const handlePasswordSubmit = async () => {
    const { currentPassword, newPassword, confirmPassword } = passwordForm;

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError('All fields are required');
      return;
    }

    if (newPassword.length < 6) {
      setPasswordError('New password must be at least 6 characters long');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('New password and confirmation do not match');
      return;
    }

    try {
      setIsChangingPassword(true);
      await profileService.changePassword(currentPassword, newPassword);
      setShowPasswordModal(false);
      alert('Password changed successfully!');
    } catch (err: any) {
      console.error('Password change failed:', err);

      // Extract meaningful error message from different error formats
      let errorMessage = 'Failed to change password';

      if (typeof err === 'string') {
        errorMessage = err;
      } else if (err?.message) {
        errorMessage = err.message;
      } else if (err?.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err?.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err?.detail) {
        errorMessage = err.detail;
      } else if (err?.error) {
        errorMessage = typeof err.error === 'string' ? err.error : err.error.message || 'Unknown error';
      }

      setPasswordError(errorMessage);
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handlePasswordModalClose = () => {
    setShowPasswordModal(false);
    setPasswordError(null);
    setPasswordForm({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
  };

  const handleLogOut = async () => {
    console.log('Logging out...');
    const confirmLogout = window.confirm('確定要登出嗎？');
    if (confirmLogout) {
      try {
        await profileService.logoutUser();
        // Navigate to home page
        window.location.href = '/';
      } catch (err: any) {
        console.error('Logout error:', err);
        // Still redirect even if API fails
        window.location.href = '/';
      }
    }
  };

  const handleViewReport = (reportId: string) => {
    console.log('Report view requested for:', reportId);

    // Find the report in the fetched data
    const report = userReports.find(r => r.id === reportId);

    if (report) {
      // For now, show a summary since full report viewing might need more implementation
      alert(`報告: ${report.title}\n\n摘要: ${report.summary}\n\n狀態: ${report.status}\n創建時間: ${new Date(report.created_at).toLocaleString()}`);
    } else {
      alert('報告未找到，請重試。\n\nReport not found, please try again.');
    }
  };


  // Show loading state
  if (loading) {
    return (
      <Layout>
        <AccountContainer>
          <AccountSection>
            <AccountContent>
              <AccountTitle>{t('account.title')}</AccountTitle>
              <div style={{ textAlign: 'center', color: '#fff', padding: '40px' }}>
                Loading...
              </div>
            </AccountContent>
          </AccountSection>
        </AccountContainer>
      </Layout>
    );
  }

  // Show error state
  if (error) {
    return (
      <Layout>
        <AccountContainer>
          <AccountSection>
            <AccountContent>
              <AccountTitle>{t('account.title')}</AccountTitle>
              <div style={{ textAlign: 'center', color: '#ff6b6b', padding: '40px' }}>
                Error: {error}
              </div>
            </AccountContent>
          </AccountSection>
        </AccountContainer>
      </Layout>
    );
  }

  // Show login required state
  if (!auth.isAuthenticated) {
    return (
      <Layout>
        <AccountContainer>
          <AccountSection>
            <AccountContent>
              <AccountTitle>{t('account.title')}</AccountTitle>
              <div style={{ textAlign: 'center', color: '#fff', padding: '40px' }}>
                Please login to view your account.
              </div>
            </AccountContent>
          </AccountSection>
        </AccountContainer>
      </Layout>
    );
  }

  return (
    <Layout>
      <AccountContainer>
        <AccountSection>
          <AccountContent>
            <AccountTitle>{t('account.title')}</AccountTitle>

            {/* Profile Information */}
            <AccountCard>
              <CardTitle>{t('account.profileInfo')}</CardTitle>


              <ProfileFields>
                <FieldGroup>
                  <FieldLabel>{t('account.username')}</FieldLabel>
                  <ProfileInput
                    type="text"
                    value={profileData.username}
                    onChange={(e) => handleInputChange('username', e.target.value)}
                  />
                </FieldGroup>

                <FieldGroup>
                  <FieldLabel>{t('account.email')}</FieldLabel>
                  <ProfileInput
                    type="email"
                    value={profileData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    disabled // Email should not be editable
                    style={{ opacity: 0.7 }}
                  />
                </FieldGroup>

                <FieldRow>
                  <FieldGroup>
                    <FieldLabel>{t('account.birthDate')}</FieldLabel>
                    <ProfileInput
                      type="date"
                      value={profileData.birthDate}
                      onChange={(e) => handleInputChange('birthDate', e.target.value)}
                    />
                  </FieldGroup>

                  <FieldGroup>
                    <FieldLabel>{t('account.gender')}</FieldLabel>
                    <ProfileSelect
                      value={profileData.gender}
                      onChange={(e) => handleInputChange('gender', e.target.value)}
                    >
                      <option value="Male">{t('account.genderOptions.male')}</option>
                      <option value="Female">{t('account.genderOptions.female')}</option>
                      <option value="Non-binary">{t('account.genderOptions.nonBinary')}</option>
                      <option value="Prefer not to say">{t('account.genderOptions.preferNotToSay')}</option>
                    </ProfileSelect>
                  </FieldGroup>
                </FieldRow>

                <FieldGroup fullWidth>
                  <FieldLabel>{t('account.location')}</FieldLabel>
                  <ProfileInput
                    type="text"
                    value={profileData.location}
                    onChange={(e) => handleInputChange('location', e.target.value)}
                  />
                </FieldGroup>
              </ProfileFields>
            </AccountCard>

            {/* Account Status */}
            <AccountCard>
              <CardTitle>{t('account.accountStatus')}</CardTitle>
              <StatusInfo>
                <StatusItem>
                  <StatusLabel>{t('account.currentBalance')}</StatusLabel>
                  <StatusValue highlight>{userProfile?.points_balance || 0} {t('account.coins')}</StatusValue>
                </StatusItem>
                <StatusItem>
                  <StatusLabel>{t('account.membership')}</StatusLabel>
                  <StatusValue highlight>
                    {userProfile?.role === 'admin' ? 'Admin' :
                     userProfile?.role === 'moderator' ? 'Moderator' :
                     userProfile?.role === 'user' ? 'User' : 'User'}
                  </StatusValue>
                </StatusItem>
                <StatusItem>
                  <StatusLabel>{t('account.memberSince')}</StatusLabel>
                  <StatusValue>{userProfile ? new Date(userProfile.created_at).toLocaleDateString() : 'N/A'}</StatusValue>
                </StatusItem>
              </StatusInfo>
            </AccountCard>

            {/* Recent Purchase Records */}
            <AccountCard>
              <CardTitle>{t('account.purchaseRecords')}</CardTitle>
              {purchaseRecords.length === 0 ? (
                <div style={{
                  textAlign: 'center',
                  padding: '40px',
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontSize: '16px'
                }}>
                  No purchase records available
                </div>
              ) : (
                <RecordsList>
                  {purchaseRecords.map((record) => (
                    <RecordItem key={record.id}>
                      <RecordLeft>
                        <RecordTitle>{record.title}</RecordTitle>
                        <RecordSubtitle>{record.subtitle}</RecordSubtitle>
                      </RecordLeft>
                      <RecordRight>
                        <RecordAmount>{record.amount}</RecordAmount>
                        <RecordDate>{record.date}</RecordDate>
                        <RecordStatus status={record.status}>
                          {record.status}
                        </RecordStatus>
                      </RecordRight>
                    </RecordItem>
                  ))}
                </RecordsList>
              )}
            </AccountCard>

            {/* My Analysis Reports */}
            <AccountCard>
              <CardTitle>{t('account.reportHistory', { count: userReports.length })}</CardTitle>
              {userReports.length === 0 ? (
                <div style={{
                  textAlign: 'center',
                  padding: '40px',
                  color: 'rgba(255, 255, 255, 0.6)'
                }}>
                  {t('account.noReports')}
                </div>
              ) : (
                userReports.map((report) => (
                  <AnalysisItem
                    key={report.id}
                    onClick={() => handleViewReport(report.id)}
                  >
                    <AnalysisInfo>
                      <AnalysisTitle>{report.title}</AnalysisTitle>
                      <AnalysisSubtitle>{report.summary}</AnalysisSubtitle>
                      <AnalysisMeta>
                        Generated on {new Date(report.created_at).toLocaleDateString()} •
                        Type: {report.type} •
                        Status: {report.status}
                      </AnalysisMeta>
                    </AnalysisInfo>
                    <AnalysisAction>{t('account.viewReport')}</AnalysisAction>
                  </AnalysisItem>
                ))
              )}
            </AccountCard>

            {/* Action Buttons */}
            <AccountActions>
              <ActionButton variant="primary" onClick={handleSaveChanges}>
                {t('account.saveChanges')}
              </ActionButton>
              <ActionButton variant="secondary" onClick={handleChangePassword}>
                {t('account.changePassword')}
              </ActionButton>
              <ActionButton variant="danger" onClick={handleLogOut}>
                {t('account.logOut')}
              </ActionButton>
            </AccountActions>
          </AccountContent>
        </AccountSection>
      </AccountContainer>

      {/* Change Password Modal */}
      {showPasswordModal && (
        <ModalOverlay onClick={handlePasswordModalClose}>
          <ModalContainer onClick={(e) => e.stopPropagation()}>
            <ModalHeader>
              <ModalTitle>Change Password</ModalTitle>
              <CloseButton onClick={handlePasswordModalClose}>
                ×
              </CloseButton>
            </ModalHeader>

            <PasswordForm>
              <PasswordField>
                <PasswordLabel>Current Password</PasswordLabel>
                <PasswordInput
                  type="password"
                  placeholder="Enter your current password"
                  value={passwordForm.currentPassword}
                  onChange={(e) => handlePasswordFormChange('currentPassword', e.target.value)}
                />
              </PasswordField>

              <PasswordField>
                <PasswordLabel>New Password</PasswordLabel>
                <PasswordInput
                  type="password"
                  placeholder="Enter your new password (min 6 characters)"
                  value={passwordForm.newPassword}
                  onChange={(e) => handlePasswordFormChange('newPassword', e.target.value)}
                />
              </PasswordField>

              <PasswordField>
                <PasswordLabel>Confirm New Password</PasswordLabel>
                <PasswordInput
                  type="password"
                  placeholder="Confirm your new password"
                  value={passwordForm.confirmPassword}
                  onChange={(e) => handlePasswordFormChange('confirmPassword', e.target.value)}
                />
              </PasswordField>

              {passwordError && (
                <ErrorMessage>{passwordError}</ErrorMessage>
              )}

              <ModalActions>
                <ModalButton variant="secondary" onClick={handlePasswordModalClose}>
                  Cancel
                </ModalButton>
                <ModalButton
                  variant="primary"
                  onClick={handlePasswordSubmit}
                  disabled={isChangingPassword}
                >
                  {isChangingPassword ? 'Changing...' : 'Change Password'}
                </ModalButton>
              </ModalActions>
            </PasswordForm>
          </ModalContainer>
        </ModalOverlay>
      )}
    </Layout>
  );
};

export default AccountPage;