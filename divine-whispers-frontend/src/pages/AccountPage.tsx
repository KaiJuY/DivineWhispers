import React, { useState } from 'react';
import styled from 'styled-components';
import { colors, gradients, media } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import useAppStore from '../stores/appStore';

interface PurchaseRecord {
  id: string;
  title: string;
  subtitle: string;
  amount: string;
  date: string;
  status: 'Completed' | 'Pending';
}

interface AnalysisReport {
  id: string;
  title: string;
  subtitle: string;
  meta: string;
}

const purchaseRecords: PurchaseRecord[] = [
  {
    id: '1',
    title: 'Premium Coin Package',
    subtitle: '50 Divine Coins',
    amount: '$19.99',
    date: 'Dec 28, 2024',
    status: 'Completed'
  },
  {
    id: '2',
    title: 'Standard Coin Package',
    subtitle: '25 Divine Coins',
    amount: '$9.99',
    date: 'Dec 15, 2024',
    status: 'Completed'
  },
  {
    id: '3',
    title: 'Basic Coin Package',
    subtitle: '10 Divine Coins',
    amount: '$4.99',
    date: 'Dec 08, 2024',
    status: 'Completed'
  },
  {
    id: '4',
    title: 'Premium Coin Package',
    subtitle: '50 Divine Coins',
    amount: '$19.99',
    date: 'Nov 30, 2024',
    status: 'Completed'
  },
  {
    id: '5',
    title: 'Standard Coin Package',
    subtitle: '25 Divine Coins',
    amount: '$9.99',
    date: 'Nov 22, 2024',
    status: 'Completed'
  }
];

const analysisReports: AnalysisReport[] = [
  {
    id: '1',
    title: 'Guan Yin Divine Guidance - Fortune #27',
    subtitle: '"天道酬勤志不移，福星高照事如意" - Career & Life Path Analysis',
    meta: 'Generated on Dec 28, 2024 • 2,340 words • Deep Analysis'
  },
  {
    id: '2',
    title: 'Mazu Sea Goddess - Fortune #83',
    subtitle: '"風平浪靜渡難關，順水推舟到彼岸" - Relationship & Emotional Guidance',
    meta: 'Generated on Dec 20, 2024 • 1,890 words • Deep Analysis'
  },
  {
    id: '3',
    title: 'Guan Yu War God - Fortune #42',
    subtitle: '"刀山火海不足懼，勇者無敵立功名" - Business & Financial Analysis',
    meta: 'Generated on Dec 15, 2024 • 2,120 words • Deep Analysis'
  },
  {
    id: '4',
    title: 'Yue Lao Marriage God - Fortune #91',
    subtitle: '"紅線牽動有緣人，月老祝福結良緣" - Love & Marriage Guidance',
    meta: 'Generated on Dec 10, 2024 • 1,650 words • Deep Analysis'
  },
  {
    id: '5',
    title: 'Asakusa Buddhist Temple - Fortune #18',
    subtitle: '"佛光普照眾生心，慈悲為懷渡有情" - Spiritual & Personal Growth',
    meta: 'Generated on Dec 5, 2024 • 2,050 words • Deep Analysis'
  }
];

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
const ProfileAvatar = styled.div`
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 40px;
  padding-bottom: 30px;
  border-bottom: 1px solid rgba(212, 175, 55, 0.2);

  ${media.mobile} {
    flex-direction: column;
    gap: 15px;
    margin-bottom: 30px;
    padding-bottom: 20px;
  }
`;

const AvatarCircle = styled.div`
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #d4af37 0%, #f4e99b 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
`;

const AvatarText = styled.div`
  color: #000;
  font-size: 1.5rem;
  font-weight: bold;
`;

const EditAvatarBtn = styled.button`
  background: rgba(212, 175, 55, 0.2);
  border: 1px solid rgba(212, 175, 55, 0.4);
  color: ${colors.primary};
  padding: 8px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;

  &:hover {
    background: rgba(212, 175, 55, 0.3);
    transform: translateY(-2px);
  }
`;

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
  padding-right: 40px;
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
`;

const ProfileSelect = styled.select`
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 8px;
  padding: 12px;
  padding-right: 40px;
  color: #fff;
  font-size: 1rem;
  transition: all 0.3s ease;

  &:focus {
    border-color: ${colors.primary};
    outline: none;
    box-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
  }

  option {
    background: #1e2749;
    color: #fff;
  }
`;

const EditBtn = styled.button`
  position: absolute;
  right: 10px;
  top: 32px;
  background: none;
  border: none;
  color: ${colors.primary};
  cursor: pointer;
  font-size: 16px;
  padding: 5px;
  border-radius: 4px;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(212, 175, 55, 0.2);
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

const AccountPage: React.FC = () => {
  const { reports, userCoins, setSelectedReport, setCurrentPage } = useAppStore();
  const [editingFields, setEditingFields] = useState<string[]>([]);
  const [profileData, setProfileData] = useState({
    username: 'DivineSeeker2024',
    email: 'john.dao@example.com',
    birthDate: '1990-03-15',
    gender: 'Male',
    location: 'San Francisco, CA, USA'
  });

  const toggleEdit = (field: string) => {
    setEditingFields(prev => 
      prev.includes(field) 
        ? prev.filter(f => f !== field)
        : [...prev, field]
    );
  };

  const handleInputChange = (field: string, value: string) => {
    setProfileData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSaveChanges = () => {
    console.log('Saving changes:', profileData);
    setEditingFields([]);
    alert('Profile updated successfully!');
  };

  const handleChangePassword = () => {
    console.log('Change password requested');
    alert('Password change functionality would be implemented here.');
  };

  const handleLogOut = () => {
    console.log('Logging out...');
    alert('Logout functionality would be implemented here.');
  };

  const handleViewReport = (reportId: string) => {
    const report = reports.find(r => r.id === reportId);
    if (report) {
      setSelectedReport(report);
      setCurrentPage('report');
    }
  };

  return (
    <Layout>
      <AccountContainer>
        <AccountSection>
          <AccountContent>
            <AccountTitle>My Account</AccountTitle>

            {/* Profile Information */}
            <AccountCard>
              <CardTitle>Profile Information</CardTitle>
              
              <ProfileAvatar>
                <AvatarCircle>
                  <AvatarText>JD</AvatarText>
                </AvatarCircle>
                <EditAvatarBtn>Change Avatar</EditAvatarBtn>
              </ProfileAvatar>

              <ProfileFields>
                <FieldGroup>
                  <FieldLabel>Username</FieldLabel>
                  <ProfileInput
                    type="text"
                    value={profileData.username}
                    disabled={!editingFields.includes('username')}
                    onChange={(e) => handleInputChange('username', e.target.value)}
                  />
                  <EditBtn onClick={() => toggleEdit('username')}>✏️</EditBtn>
                </FieldGroup>

                <FieldGroup>
                  <FieldLabel>Email</FieldLabel>
                  <ProfileInput
                    type="email"
                    value={profileData.email}
                    disabled={!editingFields.includes('email')}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                  />
                  <EditBtn onClick={() => toggleEdit('email')}>✏️</EditBtn>
                </FieldGroup>

                <FieldRow>
                  <FieldGroup>
                    <FieldLabel>Birth Date</FieldLabel>
                    <ProfileInput
                      type="date"
                      value={profileData.birthDate}
                      disabled={!editingFields.includes('birthDate')}
                      onChange={(e) => handleInputChange('birthDate', e.target.value)}
                    />
                    <EditBtn onClick={() => toggleEdit('birthDate')}>✏️</EditBtn>
                  </FieldGroup>

                  <FieldGroup>
                    <FieldLabel>Gender</FieldLabel>
                    <ProfileSelect
                      value={profileData.gender}
                      disabled={!editingFields.includes('gender')}
                      onChange={(e) => handleInputChange('gender', e.target.value)}
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Non-binary">Non-binary</option>
                      <option value="Prefer not to say">Prefer not to say</option>
                    </ProfileSelect>
                    <EditBtn onClick={() => toggleEdit('gender')}>✏️</EditBtn>
                  </FieldGroup>
                </FieldRow>

                <FieldGroup fullWidth>
                  <FieldLabel>Location</FieldLabel>
                  <ProfileInput
                    type="text"
                    value={profileData.location}
                    disabled={!editingFields.includes('location')}
                    onChange={(e) => handleInputChange('location', e.target.value)}
                  />
                  <EditBtn onClick={() => toggleEdit('location')}>✏️</EditBtn>
                </FieldGroup>
              </ProfileFields>
            </AccountCard>

            {/* Account Status */}
            <AccountCard>
              <CardTitle>Account Status</CardTitle>
              <StatusInfo>
                <StatusItem>
                  <StatusLabel>Current Balance</StatusLabel>
                  <StatusValue highlight>{userCoins} Coins</StatusValue>
                </StatusItem>
                <StatusItem>
                  <StatusLabel>Membership</StatusLabel>
                  <StatusValue highlight>Premium Member</StatusValue>
                </StatusItem>
                <StatusItem>
                  <StatusLabel>Member Since</StatusLabel>
                  <StatusValue>January 2024</StatusValue>
                </StatusItem>
              </StatusInfo>
            </AccountCard>

            {/* Recent Purchase Records */}
            <AccountCard>
              <CardTitle>Recent Purchase Records</CardTitle>
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
            </AccountCard>

            {/* My Analysis Reports */}
            <AccountCard>
              <CardTitle>Report History ({reports.length})</CardTitle>
              {reports.length === 0 ? (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '40px', 
                  color: 'rgba(255, 255, 255, 0.6)' 
                }}>
                  No reports generated yet. Start a conversation on the fortune analysis page to generate your first report!
                </div>
              ) : (
                reports.map((report) => (
                  <AnalysisItem 
                    key={report.id}
                    onClick={() => handleViewReport(report.id)}
                  >
                    <AnalysisInfo>
                      <AnalysisTitle>{report.title} - {report.deity_name}</AnalysisTitle>
                      <AnalysisSubtitle>"{report.question}" • Fortune #{report.fortune_number}</AnalysisSubtitle>
                      <AnalysisMeta>
                        Generated on {new Date(report.created_at).toLocaleDateString()} • 
                        Cost: {report.cost} coins • 
                        Status: {report.status === 'completed' ? 'Completed' : 'Generating...'}
                      </AnalysisMeta>
                    </AnalysisInfo>
                    <AnalysisAction>View Report</AnalysisAction>
                  </AnalysisItem>
                ))
              )}
            </AccountCard>

            {/* Action Buttons */}
            <AccountActions>
              <ActionButton variant="primary" onClick={handleSaveChanges}>
                Save Changes
              </ActionButton>
              <ActionButton variant="secondary" onClick={handleChangePassword}>
                Change Password
              </ActionButton>
              <ActionButton variant="danger" onClick={handleLogOut}>
                Log Out
              </ActionButton>
            </AccountActions>
          </AccountContent>
        </AccountSection>
      </AccountContainer>
    </Layout>
  );
};

export default AccountPage;