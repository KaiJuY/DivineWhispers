import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { colors, gradients, media } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import adminService, { DashboardOverview, Customer as ApiCustomer, FAQ as ApiFAQ } from '../services/adminService';

const AdminContainer = styled.div`
  width: 100%;
  min-height: 100vh;
`;

const AdminSection = styled.section`
  padding: 40px;
  background: ${gradients.heroSection};
  min-height: calc(100vh - 80px);
  
  ${media.tablet} {
    padding: 30px 20px;
  }
  
  ${media.mobile} {
    padding: 20px;
  }
`;

const PageContent = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  color: ${colors.white};
`;

const DashboardHeader = styled.div`
  margin-bottom: 2rem;
`;

const DashboardTitle = styled.div`
  font-size: 2.5rem;
  font-weight: bold;
  color: ${colors.primary};
  text-shadow: 0 0 20px rgba(212, 175, 55, 0.3);
  margin-bottom: 1.5rem;
  text-align: center;
  
  ${media.tablet} {
    font-size: 2rem;
  }
  
  ${media.mobile} {
    font-size: 1.8rem;
  }
`;

const DashboardStats = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
  
  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const StatItem = styled.div`
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 12px;
  padding: 1rem;
  text-align: center;
  backdrop-filter: blur(10px);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(212, 175, 55, 0.2);
  }
`;

const StatValue = styled.span`
  display: block;
  font-size: 1.8rem;
  font-weight: bold;
  color: ${colors.primary};
  margin-bottom: 0.5rem;
`;

const StatLabel = styled.div`
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
`;

const DashboardNav = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
  
  &::-webkit-scrollbar {
    height: 4px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: ${colors.primary};
    border-radius: 2px;
  }
`;

const DashboardNavItem = styled.div<{ active?: boolean }>`
  padding: 1rem 1.5rem;
  background: ${props => props.active ? colors.primary : 'rgba(255, 255, 255, 0.1)'};
  color: ${props => props.active ? colors.black : colors.white};
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.3s ease;
  font-weight: ${props => props.active ? 'bold' : 'normal'};
  border: 1px solid ${props => props.active ? colors.primary : 'rgba(212, 175, 55, 0.3)'};
  
  &:hover {
    background: ${props => props.active ? colors.primary : 'rgba(212, 175, 55, 0.2)'};
    transform: translateY(-1px);
  }
`;

const DashboardContent = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 12px;
  padding: 2rem;
  backdrop-filter: blur(10px);
`;

const DashboardSection = styled.div<{ active?: boolean }>`
  display: ${props => props.active ? 'block' : 'none'};
`;

const SectionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
`;

const SectionTitle = styled.h2`
  font-size: 1.8rem;
  color: ${colors.primary};
  margin: 0;
`;

const SectionActions = styled.div`
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
`;

const AdminBtn = styled.button<{ secondary?: boolean; danger?: boolean }>`
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  background: ${props => 
    props.danger ? '#dc3545' : 
    props.secondary ? 'rgba(255, 255, 255, 0.2)' : 
    colors.primary
  };
  color: ${props => 
    props.secondary ? colors.white : 
    colors.black
  };
  
  &:hover {
    background: ${props => 
      props.danger ? '#c82333' : 
      props.secondary ? 'rgba(255, 255, 255, 0.3)' : 
      colors.primaryDark
    };
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
  }
`;

const SearchFilterBar = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
`;

const SearchInput = styled.input`
  flex: 1;
  min-width: 300px;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 8px;
  color: ${colors.white};
  font-size: 1rem;
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.6);
  }
  
  &:focus {
    outline: none;
    border-color: ${colors.primary};
    box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.2);
  }
`;

const FilterSelect = styled.select`
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 8px;
  color: ${colors.white};
  cursor: pointer;
  
  &:focus {
    outline: none;
    border-color: ${colors.primary};
  }
  
  option {
    background: #1a237e;
    color: ${colors.white};
  }
`;

const AdminTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  overflow: hidden;
  
  thead {
    background: rgba(212, 175, 55, 0.2);
  }
  
  th, td {
    padding: 1rem;
    text-align: left;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  th {
    font-weight: 600;
    color: ${colors.primary};
  }
  
  tbody tr:hover {
    background: rgba(255, 255, 255, 0.05);
  }
`;

const StatusBadge = styled.span<{ status: string }>`
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  background: ${props => {
    switch (props.status) {
      case 'active':
      case 'completed':
        return '#28a745';
      case 'premium':
        return colors.primary;
      case 'inactive':
        return '#6c757d';
      case 'pending':
        return '#ffc107';
      case 'refunded':
        return '#dc3545';
      default:
        return '#6c757d';
    }
  }};
  color: ${props => props.status === 'premium' || props.status === 'pending' ? colors.black : colors.white};
`;

const CardBtn = styled.button<{ edit?: boolean; delete?: boolean }>`
  padding: 0.5rem 1rem;
  margin-right: 0.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  background: ${props => props.delete ? '#dc3545' : props.edit ? colors.primary : '#6c757d'};
  color: ${props => props.edit ? colors.black : colors.white};
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
`;

const AdminCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.08);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2);
  }
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  gap: 1rem;
`;

const CardTitle = styled.div`
  font-weight: 600;
  color: ${colors.primary};
  font-size: 1.1rem;
`;

const CardActions = styled.div`
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
`;

const PoemsGrid = styled.div`
  display: grid;
  gap: 1rem;
`;

const ChartPlaceholder = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border: 2px dashed rgba(212, 175, 55, 0.3);
  border-radius: 8px;
  padding: 3rem;
  text-align: center;
  margin-bottom: 2rem;
  
  .chart-text {
    font-size: 1.2rem;
    color: ${colors.primary};
    margin-bottom: 0.5rem;
  }
  
  .chart-note {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.9rem;
  }
`;

// Legacy interfaces for mock data - keeping for orders only
interface Order {
  id: string;
  customer: string;
  package: string;
  amount: string;
  status: 'completed' | 'pending' | 'refunded';
  date: string;
}

// interface Report {
//   id: string;
//   title: string;
//   customer: string;
//   source: string;
//   question: string;
//   generated: string;
//   wordCount: number;
// }

interface PendingFAQ {
  id: string;
  question: string;
  userQuestion: string;
  userEmail: string;
  received: string;
  category: string;
}

const AdminPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState('customers');
  const [dashboardData, setDashboardData] = useState<DashboardOverview | null>(null);
  const [customers, setCustomers] = useState<ApiCustomer[]>([]);
  const [faqs, setFaqs] = useState<ApiFAQ[]>([]);
  const [poems, setPoems] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Pagination and filters
  const [customerPage, setCustomerPage] = useState(1);
  const [customerSearch, setCustomerSearch] = useState('');
  const [customerStatus, setCustomerStatus] = useState('');
  const [faqCategory, setFaqCategory] = useState('');
  const [poemDeity, setPoemDeity] = useState('');
  const [poemSearch, setPoemSearch] = useState('');
  const [reportSearch, setReportSearch] = useState('');
  const [reportDeity, setReportDeity] = useState('');
  const [reportDate, setReportDate] = useState('');

  // Load dashboard data
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        const data = await adminService.getDashboardOverview();
        setDashboardData(data);
      } catch (err) {
        console.error('Error loading dashboard data:', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  // Load customers data
  useEffect(() => {
    const loadCustomers = async () => {
      try {
        const response = await adminService.getCustomers({
          page: customerPage,
          limit: 20,
          search: customerSearch || undefined,
          status_filter: customerStatus || undefined,
          sort_by: 'created_at',
          sort_order: 'desc'
        });
        setCustomers(response.customers);
      } catch (err) {
        console.error('Error loading customers:', err);
        setError('Failed to load customers');
      }
    };

    if (activeSection === 'customers') {
      loadCustomers();
    }
  }, [activeSection, customerPage, customerSearch, customerStatus]);

  // Load FAQs data
  useEffect(() => {
    const loadFAQs = async () => {
      try {
        const response = await adminService.getFAQs({
          category: faqCategory || undefined,
          page: 1,
          limit: 50
        });
        setFaqs(response.faqs);
      } catch (err) {
        console.error('Error loading FAQs:', err);
        setError('Failed to load FAQs');
      }
    };

    if (activeSection === 'faqs') {
      loadFAQs();
    }
  }, [activeSection, faqCategory]);

  // Load poems data
  useEffect(() => {
    const loadPoems = async () => {
      try {
        const response = await adminService.getPoems({
          page: 1,
          limit: 20,
          deity_filter: poemDeity || undefined,
          search: poemSearch || undefined
        });
        setPoems(response.poems);
      } catch (err) {
        console.error('Error loading poems:', err);
        setError('Failed to load poems');
      }
    };

    if (activeSection === 'poems') {
      loadPoems();
    }
  }, [activeSection, poemDeity, poemSearch]);

  // Load reports data
  useEffect(() => {
    const loadReports = async () => {
      try {
        const response = await adminService.getReports({
          page: 1,
          limit: 20,
          user_search: reportSearch || undefined,
          deity_filter: reportDeity || undefined,
          date_filter: reportDate || undefined
        });
        setReports(response.reports);
      } catch (err) {
        console.error('Error loading reports:', err);
        setError('Failed to load reports');
      }
    };

    if (activeSection === 'reports') {
      loadReports();
    }
  }, [activeSection, reportSearch, reportDeity, reportDate]);

  // Mock data for sections not yet fully implemented

  const mockOrders: Order[] = [
    {
      id: 'ORD001',
      customer: 'John Dao',
      package: 'Premium Coin Package (50 Coins)',
      amount: '$19.99',
      status: 'completed',
      date: '2024-12-28'
    },
    {
      id: 'ORD002',
      customer: 'Sarah Chen',
      package: 'Standard Coin Package (25 Coins)',
      amount: '$9.99',
      status: 'pending',
      date: '2024-12-29'
    }
  ];


  const mockPendingFAQs: PendingFAQ[] = [
    {
      id: 'PFAQ001',
      question: 'How accurate are the fortune readings?',
      userQuestion: 'I\'m wondering about the accuracy of these readings. Are they based on real traditional methods or just random generated content?',
      userEmail: 'john.dao@example.com',
      received: '2024-12-29 10:30',
      category: 'General'
    },
    {
      id: 'PFAQ002',
      question: 'Can I get a refund for divine coins?',
      userQuestion: 'I purchased coins but haven\'t used them yet. Is it possible to get a refund if I change my mind?',
      userEmail: 'sarah.chen@example.com',
      received: '2024-12-29 15:45',
      category: 'Payment'
    },
    {
      id: 'PFAQ003',
      question: 'How do I interpret the Chinese poems?',
      userQuestion: 'The poems are beautiful but I don\'t understand Chinese. Will there always be English translations and explanations?',
      userEmail: 'mike.j@example.com',
      received: '2024-12-28 20:12',
      category: 'Usage'
    }
  ];

  const navItems = [
    { key: 'customers', label: '👥 Customer Management' },
    { key: 'poems', label: '📝 Poems Analysis' },
    { key: 'purchases', label: '💰 Purchase Management' },
    { key: 'reports', label: '📊 Reports Storage' },
    { key: 'faqs', label: '❓ FAQ Management' }
  ];

  const handleNavClick = (sectionKey: string) => {
    setActiveSection(sectionKey);
  };

  const handleCustomerAction = async (userId: number, action: string) => {
    try {
      if (action === 'edit') {
        // Navigate to edit page or open modal
        console.log('Edit customer:', userId);
      } else {
        const reason = prompt(`Enter reason for ${action}:`);
        if (reason) {
          await adminService.performCustomerAction(userId, action, reason);
          // Reload customers data
          const response = await adminService.getCustomers({
            page: customerPage,
            limit: 20,
            search: customerSearch || undefined,
            status_filter: customerStatus || undefined,
            sort_by: 'created_at',
            sort_order: 'desc'
          });
          setCustomers(response.customers);
        }
      }
    } catch (err) {
      console.error(`Error performing ${action} on customer ${userId}:`, err);
      setError(`Failed to ${action} customer`);
    }
  };

  const handleFAQAction = async (faqId: number | string, action: string) => {
    try {
      if (action === 'edit') {
        // Open FAQ edit modal or navigate to edit page
        console.log('Edit FAQ:', faqId);
      } else if (action === 'delete') {
        const confirm = window.confirm('Are you sure you want to delete this FAQ?');
        if (confirm) {
          await adminService.deleteFAQ(Number(faqId));
          // Reload FAQs
          const response = await adminService.getFAQs({
            category: faqCategory || undefined,
            page: 1,
            limit: 50
          });
          setFaqs(response.faqs);
        }
      }
    } catch (err) {
      console.error(`Error performing ${action} on FAQ ${faqId}:`, err);
      setError(`Failed to ${action} FAQ`);
    }
  };

  const handleReportAction = async (reportId: string, action: string) => {
    try {
      if (action === 'delete') {
        const confirm = window.confirm('Are you sure you want to delete this report?');
        if (confirm) {
          await adminService.deleteReport(reportId);
          // Reload reports
          const response = await adminService.getReports({
            page: 1,
            limit: 20,
            user_search: reportSearch || undefined,
            deity_filter: reportDeity || undefined,
            date_filter: reportDate || undefined
          });
          setReports(response.reports);
        }
      }
    } catch (err) {
      console.error(`Error performing ${action} on report ${reportId}:`, err);
      setError(`Failed to ${action} report`);
    }
  };

  return (
    <Layout>
      <AdminContainer>
        <AdminSection>
          <PageContent>
          <DashboardHeader>
            <DashboardTitle>🛠️ Admin Dashboard</DashboardTitle>
            {error && (
              <div style={{
                color: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                padding: '0.75rem 1rem',
                borderRadius: '4px',
                marginTop: '1rem',
                border: '1px solid rgba(220, 53, 69, 0.3)'
              }}>
                ⚠️ {error}
              </div>
            )}
          </DashboardHeader>
          
          <DashboardStats>
            <StatItem>
              <StatValue>{dashboardData?.users?.total?.toLocaleString() || '...'}</StatValue>
              <StatLabel>Total Users</StatLabel>
            </StatItem>
            <StatItem>
              <StatValue>{dashboardData?.revenue?.total_transactions?.toLocaleString() || '...'}</StatValue>
              <StatLabel>Total Transactions</StatLabel>
            </StatItem>
            <StatItem>
              <StatValue>{dashboardData?.engagement?.fortune_readings?.toLocaleString() || '...'}</StatValue>
              <StatLabel>Fortune Readings</StatLabel>
            </StatItem>
            <StatItem>
              <StatValue>{dashboardData?.engagement?.chat_sessions?.toLocaleString() || '...'}</StatValue>
              <StatLabel>Chat Sessions</StatLabel>
            </StatItem>
          </DashboardStats>

        <DashboardNav>
          {navItems.map((item) => (
            <DashboardNavItem
              key={item.key}
              active={activeSection === item.key}
              onClick={() => handleNavClick(item.key)}
            >
              {item.label}
            </DashboardNavItem>
          ))}
        </DashboardNav>

        <DashboardContent>
          {/* Customer Management Section */}
          <DashboardSection active={activeSection === 'customers'}>
            <SectionHeader>
              <SectionTitle>Customer Management</SectionTitle>
              <SectionActions>
                <AdminBtn onClick={() => console.log('Add customer')}>➕ Add Customer</AdminBtn>
                <AdminBtn secondary onClick={() => console.log('Export data')}>📤 Export Data</AdminBtn>
              </SectionActions>
            </SectionHeader>

            <SearchFilterBar>
              <SearchInput
                placeholder="🔍 Search customers by name, email, or ID..."
                value={customerSearch}
                onChange={(e) => setCustomerSearch(e.target.value)}
              />
              <FilterSelect
                value={customerStatus}
                onChange={(e) => setCustomerStatus(e.target.value)}
              >
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="suspended">Suspended</option>
                <option value="banned">Banned</option>
              </FilterSelect>
              <FilterSelect>
                <option value="">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
              </FilterSelect>
            </SearchFilterBar>

            <AdminTable>
              <thead>
                <tr>
                  <th>Customer ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Status</th>
                  <th>Balance</th>
                  <th>Join Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {customers.length > 0 ? customers.map((customer) => (
                  <tr key={customer.user_id}>
                    <td>DW{customer.user_id.toString().padStart(3, '0')}</td>
                    <td>{customer.full_name || customer.email.split('@')[0]}</td>
                    <td>{customer.email}</td>
                    <td>
                      <StatusBadge status={customer.status}>
                        {customer.status.charAt(0).toUpperCase() + customer.status.slice(1)}
                      </StatusBadge>
                    </td>
                    <td>{customer.wallet_balance} Coins</td>
                    <td>{new Date(customer.created_at).toLocaleDateString()}</td>
                    <td>
                      <CardBtn edit onClick={() => handleCustomerAction(customer.user_id, 'edit')}>✏️ Edit</CardBtn>
                      <CardBtn onClick={() => handleCustomerAction(customer.user_id, 'reset_password')}>🔑 Reset PWD</CardBtn>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'rgba(255,255,255,0.6)' }}>
                      {loading ? 'Loading customers...' : 'No customers found'}
                    </td>
                  </tr>
                )}
              </tbody>
            </AdminTable>
          </DashboardSection>

          {/* Poems Analysis Section */}
          <DashboardSection active={activeSection === 'poems'}>
            <SectionHeader>
              <SectionTitle>Poems Analysis Management</SectionTitle>
              <SectionActions>
                <AdminBtn onClick={() => console.log('Add poem')}>➕ Add Poem</AdminBtn>
                <AdminBtn secondary onClick={() => console.log('Bulk update')}>🔄 Bulk Update</AdminBtn>
              </SectionActions>
            </SectionHeader>

            <SearchFilterBar>
              <SearchInput
                placeholder="🔍 Search poems by title, deity, or fortune number..."
                value={poemSearch}
                onChange={(e) => setPoemSearch(e.target.value)}
              />
              <FilterSelect
                value={poemDeity}
                onChange={(e) => setPoemDeity(e.target.value)}
              >
                <option value="">All Deities</option>
                <option value="GuanYin">Guan Yin</option>
                <option value="Mazu">Mazu</option>
                <option value="GuanYu">Guan Yu</option>
                <option value="YueLao">Yue Lao</option>
                <option value="Asakusa">Asakusa</option>
              </FilterSelect>
            </SearchFilterBar>

            <PoemsGrid>
              {poems.length > 0 ? poems.map((poem) => (
                <AdminCard key={poem.id}>
                  <CardHeader>
                    <CardTitle>{poem.title}</CardTitle>
                    <CardActions>
                      <CardBtn edit onClick={() => console.log('Edit poem', poem.id)}>✏️ View</CardBtn>
                      <CardBtn onClick={() => console.log('Analyze poem', poem.id)}>📊 Analyze</CardBtn>
                    </CardActions>
                  </CardHeader>
                  <div style={{ color: 'rgba(255,255,255,0.8)', lineHeight: 1.5 }}>
                    <strong>Deity:</strong> {poem.deity}<br />
                    <strong>Chinese:</strong> {poem.chinese || 'N/A'}<br />
                    <strong>User Question:</strong> {poem.user_question || 'N/A'}<br />
                    <strong>Last Modified:</strong> {new Date(poem.last_modified).toLocaleDateString()}<br />
                    <strong>Status:</strong> <StatusBadge status={poem.status}>{poem.status}</StatusBadge>
                  </div>
                </AdminCard>
              )) : (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'rgba(255,255,255,0.6)' }}>
                  {loading ? 'Loading poems...' : 'No poems found'}
                </div>
              )}
            </PoemsGrid>
          </DashboardSection>

          {/* Purchase Management Section */}
          <DashboardSection active={activeSection === 'purchases'}>
            <SectionHeader>
              <SectionTitle>Purchase Management</SectionTitle>
              <SectionActions>
                <AdminBtn onClick={() => console.log('Generate report')}>📈 Generate Report</AdminBtn>
                <AdminBtn secondary onClick={() => console.log('Process refund')}>💸 Process Refund</AdminBtn>
              </SectionActions>
            </SectionHeader>

            <ChartPlaceholder>
              <div className="chart-text">📊 Sales Chart Placeholder</div>
              <div className="chart-note">Integration with Chart.js or similar library needed</div>
            </ChartPlaceholder>

            <SearchFilterBar>
              <SearchInput placeholder="🔍 Search orders by ID, customer, or amount..." />
              <FilterSelect>
                <option value="">All Status</option>
                <option value="completed">Completed</option>
                <option value="pending">Pending</option>
                <option value="refunded">Refunded</option>
              </FilterSelect>
            </SearchFilterBar>

            <AdminTable>
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Customer</th>
                  <th>Package</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {mockOrders.map((order) => (
                  <tr key={order.id}>
                    <td>{order.id}</td>
                    <td>{order.customer}</td>
                    <td>{order.package}</td>
                    <td>{order.amount}</td>
                    <td>
                      <StatusBadge status={order.status}>
                        {order.status === 'completed' ? 'Completed' : 
                         order.status === 'pending' ? 'Pending' : 'Refunded'}
                      </StatusBadge>
                    </td>
                    <td>{order.date}</td>
                    <td>
                      <CardBtn edit onClick={() => console.log('Edit order', order.id)}>✏️ Edit</CardBtn>
                      <CardBtn delete onClick={() => console.log('Refund order', order.id)}>↩️ Refund</CardBtn>
                    </td>
                  </tr>
                ))}
              </tbody>
            </AdminTable>
          </DashboardSection>

          {/* Reports Storage Section */}
          <DashboardSection active={activeSection === 'reports'}>
            <SectionHeader>
              <SectionTitle>Reports Storage Manager</SectionTitle>
              <SectionActions>
                <AdminBtn onClick={() => console.log('Bulk export')}>📦 Bulk Export</AdminBtn>
                <AdminBtn secondary onClick={() => console.log('Cleanup old')}>🧹 Cleanup Old</AdminBtn>
              </SectionActions>
            </SectionHeader>

            <SearchFilterBar>
              <SearchInput
                placeholder="🔍 Search reports by customer, deity, or keywords..."
                value={reportSearch}
                onChange={(e) => setReportSearch(e.target.value)}
              />
              <FilterSelect
                value={reportDeity}
                onChange={(e) => setReportDeity(e.target.value)}
              >
                <option value="">All Deities</option>
                <option value="GuanYin">Guan Yin</option>
                <option value="Mazu">Mazu</option>
                <option value="GuanYu">Guan Yu</option>
                <option value="YueLao">Yue Lao</option>
                <option value="Asakusa">Asakusa</option>
              </FilterSelect>
              <FilterSelect
                value={reportDate}
                onChange={(e) => setReportDate(e.target.value)}
              >
                <option value="">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
              </FilterSelect>
            </SearchFilterBar>

            <PoemsGrid>
              {reports.length > 0 ? reports.map((report) => (
                <AdminCard key={report.id}>
                  <CardHeader>
                    <CardTitle>{report.title}</CardTitle>
                    <CardActions>
                      <CardBtn onClick={() => console.log('View report', report.id)}>👁️ View</CardBtn>
                      <CardBtn edit onClick={() => console.log('Edit report', report.id)}>✏️ Edit</CardBtn>
                      <CardBtn delete onClick={() => handleReportAction(report.id, 'delete')}>🗑️ Delete</CardBtn>
                    </CardActions>
                  </CardHeader>
                  <div style={{ color: 'rgba(255,255,255,0.8)', lineHeight: 1.5 }}>
                    <strong>ID:</strong> {report.id}<br />
                    <strong>Customer:</strong> {report.customer}<br />
                    <strong>Source:</strong> {report.source}<br />
                    <strong>Question:</strong> {report.question?.substring(0, 100) || 'N/A'}{report.question?.length > 100 ? '...' : ''}<br />
                    <strong>Generated:</strong> {report.generated}<br />
                    <strong>Word Count:</strong> {report.word_count.toLocaleString()} words
                  </div>
                </AdminCard>
              )) : (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'rgba(255,255,255,0.6)' }}>
                  {loading ? 'Loading reports...' : 'No reports found'}
                </div>
              )}
            </PoemsGrid>
          </DashboardSection>

          {/* FAQ Management Section */}
          <DashboardSection active={activeSection === 'faqs'}>
            <SectionHeader>
              <SectionTitle>FAQ Management System</SectionTitle>
              <SectionActions>
                <AdminBtn onClick={() => console.log('Add FAQ')}>➕ Add FAQ</AdminBtn>
                <AdminBtn secondary onClick={() => console.log('Export FAQs')}>📤 Export FAQs</AdminBtn>
              </SectionActions>
            </SectionHeader>

            <h3 style={{ 
              color: 'rgba(255, 175, 55, 1)', 
              fontSize: '1.3rem', 
              marginBottom: '1.5rem',
              fontWeight: 'bold'
            }}>
              ⏳ Pending FAQ Queue
            </h3>
            
            <PoemsGrid style={{ marginBottom: '3rem' }}>
              {mockPendingFAQs.map((pendingFaq) => (
                <AdminCard key={pendingFaq.id}>
                  <CardHeader>
                    <CardTitle>{pendingFaq.question}</CardTitle>
                  </CardHeader>
                  <div style={{ color: 'rgba(255,255,255,0.8)', lineHeight: 1.5, marginBottom: '1rem' }}>
                    <strong>User Question:</strong> "{pendingFaq.userQuestion}"
                  </div>
                  <div style={{ 
                    display: 'flex', 
                    gap: '1rem', 
                    marginBottom: '1rem', 
                    fontSize: '0.9rem', 
                    color: 'rgba(255,255,255,0.7)' 
                  }}>
                    <div><strong>Asked by:</strong> {pendingFaq.userEmail}</div>
                    <div><strong>Received:</strong> {pendingFaq.received}</div>
                    <div><strong>Category:</strong> {pendingFaq.category}</div>
                  </div>
                  <CardActions>
                    <AdminBtn onClick={() => console.log('Approve FAQ', pendingFaq.id)}>✅ Approve & Add</AdminBtn>
                    <AdminBtn secondary onClick={() => console.log('Edit draft', pendingFaq.id)}>✏️ Edit Draft</AdminBtn>
                    <AdminBtn danger onClick={() => console.log('Reject FAQ', pendingFaq.id)}>❌ Reject</AdminBtn>
                  </CardActions>
                </AdminCard>
              ))}
            </PoemsGrid>

            <h3 style={{ 
              color: 'rgba(255, 175, 55, 1)', 
              fontSize: '1.3rem', 
              marginBottom: '1.5rem',
              fontWeight: 'bold'
            }}>
              ✅ Active FAQs
            </h3>

            <AdminTable>
              <thead>
                <tr>
                  <th>Question</th>
                  <th>Category</th>
                  <th>Views</th>
                  <th>Status</th>
                  <th>Last Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {faqs.length > 0 ? faqs.map((faq) => (
                  <tr key={faq.id}>
                    <td>{faq.question}</td>
                    <td>{faq.category}</td>
                    <td>{faq.view_count}</td>
                    <td>
                      <StatusBadge status={faq.is_published ? 'published' : 'draft'}>
                        {faq.is_published ? 'Published' : 'Draft'}
                      </StatusBadge>
                    </td>
                    <td>{new Date(faq.updated_at).toLocaleDateString()}</td>
                    <td>
                      <CardBtn edit onClick={() => handleFAQAction(faq.id, 'edit')}>✏️ Edit</CardBtn>
                      <CardBtn delete onClick={() => handleFAQAction(faq.id, 'delete')}>🗑️ Delete</CardBtn>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'rgba(255,255,255,0.6)' }}>
                      {loading ? 'Loading FAQs...' : 'No FAQs found'}
                    </td>
                  </tr>
                )}
              </tbody>
            </AdminTable>
          </DashboardSection>
        </DashboardContent>
          </PageContent>
        </AdminSection>
      </AdminContainer>
    </Layout>
  );
};

export default AdminPage;