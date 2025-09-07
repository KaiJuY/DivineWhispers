import React, { useState } from 'react';
import styled from 'styled-components';
import { colors, gradients, media } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';

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

interface Customer {
  id: string;
  name: string;
  email: string;
  status: 'active' | 'premium' | 'inactive';
  balance: string;
  joinDate: string;
}

interface Poem {
  id: string;
  title: string;
  deity: string;
  chinese: string;
  topics: string;
  lastModified: string;
  usageCount: number;
}

interface Order {
  id: string;
  customer: string;
  package: string;
  amount: string;
  status: 'completed' | 'pending' | 'refunded';
  date: string;
}

interface Report {
  id: string;
  title: string;
  customer: string;
  source: string;
  question: string;
  generated: string;
  wordCount: number;
}

interface FAQ {
  id: string;
  question: string;
  category: string;
  status: 'published' | 'pending';
  views: number;
  lastUpdated: string;
  userEmail?: string;
  received?: string;
  userQuestion?: string;
}

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

  const mockCustomers: Customer[] = [
    {
      id: 'DW001',
      name: 'John Dao',
      email: 'john.dao@example.com',
      status: 'premium',
      balance: '47 Coins',
      joinDate: '2024-01-15'
    },
    {
      id: 'DW002',
      name: 'Sarah Chen',
      email: 'sarah.chen@example.com',
      status: 'active',
      balance: '23 Coins',
      joinDate: '2024-02-08'
    },
    {
      id: 'DW003',
      name: 'Mike Johnson',
      email: 'mike.j@example.com',
      status: 'inactive',
      balance: '0 Coins',
      joinDate: '2024-03-22'
    }
  ];

  const mockPoems: Poem[] = [
    {
      id: 'guan-yin-27',
      title: 'Guan Yin Fortune #27 - 天道酬勤志不移',
      deity: 'Guan Yin',
      chinese: '天道酬勤志不移，福星高照事如意',
      topics: 'Career & Life Path',
      lastModified: '2024-12-28',
      usageCount: 47
    },
    {
      id: 'mazu-83',
      title: 'Mazu Fortune #83 - 風平浪靜渡難關',
      deity: 'Mazu',
      chinese: '風平浪靜渡難關，順水推舟到彼岸',
      topics: 'Relationship & Emotional Guidance',
      lastModified: '2024-12-20',
      usageCount: 32
    }
  ];

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

  const mockReports: Report[] = [
    {
      id: 'RPT001',
      title: 'Career Guidance Report - John Dao',
      customer: 'John Dao',
      source: 'Guan Yin Fortune #27',
      question: '"I\'ve been feeling lost in my career path lately..."',
      generated: '2024-12-28 14:30',
      wordCount: 2340
    },
    {
      id: 'RPT002',
      title: 'Relationship Analysis - Sarah Chen',
      customer: 'Sarah Chen',
      source: 'Mazu Fortune #83',
      question: '"My relationship feels stagnant..."',
      generated: '2024-12-20 09:15',
      wordCount: 1890
    }
  ];

  const mockFAQs: FAQ[] = [
    {
      id: 'FAQ001',
      question: 'How do divine coins work?',
      category: 'General',
      status: 'published',
      views: 347,
      lastUpdated: '2024-12-15'
    },
    {
      id: 'FAQ002',
      question: 'Are readings accurate?',
      category: 'General',
      status: 'published',
      views: 289,
      lastUpdated: '2024-12-10'
    },
    {
      id: 'FAQ003',
      question: 'Can I get a refund?',
      category: 'Payment',
      status: 'published',
      views: 156,
      lastUpdated: '2024-12-08'
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

  return (
    <Layout>
      <AdminContainer>
        <AdminSection>
          <PageContent>
          <DashboardHeader>
            <DashboardTitle>🛠️ Admin Dashboard</DashboardTitle>
          </DashboardHeader>
          
          <DashboardStats>
            <StatItem>
              <StatValue>1,247</StatValue>
              <StatLabel>Total Users</StatLabel>
            </StatItem>
            <StatItem>
              <StatValue>3,892</StatValue>
              <StatLabel>Total Orders</StatLabel>
            </StatItem>
            <StatItem>
              <StatValue>156</StatValue>
              <StatLabel>Active Reports</StatLabel>
            </StatItem>
            <StatItem>
              <StatValue>23</StatValue>
              <StatLabel>Pending FAQs</StatLabel>
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
              <SearchInput placeholder="🔍 Search customers by name, email, or ID..." />
              <FilterSelect>
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="premium">Premium</option>
                <option value="inactive">Inactive</option>
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
                {mockCustomers.map((customer) => (
                  <tr key={customer.id}>
                    <td>{customer.id}</td>
                    <td>{customer.name}</td>
                    <td>{customer.email}</td>
                    <td>
                      <StatusBadge status={customer.status}>
                        {customer.status === 'premium' ? 'Premium' : 
                         customer.status === 'active' ? 'Active' : 'Inactive'}
                      </StatusBadge>
                    </td>
                    <td>{customer.balance}</td>
                    <td>{customer.joinDate}</td>
                    <td>
                      <CardBtn edit onClick={() => console.log('Edit customer', customer.id)}>✏️ Edit</CardBtn>
                      <CardBtn delete onClick={() => console.log('Reset password', customer.id)}>🔑 Reset PWD</CardBtn>
                    </td>
                  </tr>
                ))}
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
              <SearchInput placeholder="🔍 Search poems by title, deity, or fortune number..." />
              <FilterSelect>
                <option value="">All Deities</option>
                <option value="guanyin">Guan Yin</option>
                <option value="mazu">Mazu</option>
                <option value="guanyu">Guan Yu</option>
                <option value="yuelao">Yue Lao</option>
                <option value="asakusa">Asakusa</option>
              </FilterSelect>
            </SearchFilterBar>

            <PoemsGrid>
              {mockPoems.map((poem) => (
                <AdminCard key={poem.id}>
                  <CardHeader>
                    <CardTitle>{poem.title}</CardTitle>
                    <CardActions>
                      <CardBtn edit onClick={() => console.log('Edit poem', poem.id)}>✏️ Edit</CardBtn>
                      <CardBtn delete onClick={() => console.log('Delete poem', poem.id)}>🗑️ Delete</CardBtn>
                    </CardActions>
                  </CardHeader>
                  <div style={{ color: 'rgba(255,255,255,0.8)', lineHeight: 1.5 }}>
                    <strong>Chinese:</strong> {poem.chinese}<br />
                    <strong>Analysis Topics:</strong> {poem.topics}<br />
                    <strong>Last Modified:</strong> {poem.lastModified}<br />
                    <strong>Usage Count:</strong> {poem.usageCount} times
                  </div>
                </AdminCard>
              ))}
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
              <SearchInput placeholder="🔍 Search reports by customer, deity, or keywords..." />
              <FilterSelect>
                <option value="">All Deities</option>
                <option value="guanyin">Guan Yin</option>
                <option value="mazu">Mazu</option>
                <option value="guanyu">Guan Yu</option>
                <option value="yuelao">Yue Lao</option>
              </FilterSelect>
              <FilterSelect>
                <option value="">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
              </FilterSelect>
            </SearchFilterBar>

            <PoemsGrid>
              {mockReports.map((report) => (
                <AdminCard key={report.id}>
                  <CardHeader>
                    <CardTitle>{report.title}</CardTitle>
                    <CardActions>
                      <CardBtn onClick={() => console.log('View report', report.id)}>👁️ View</CardBtn>
                      <CardBtn edit onClick={() => console.log('Edit report', report.id)}>✏️ Edit</CardBtn>
                      <CardBtn delete onClick={() => console.log('Delete report', report.id)}>🗑️ Delete</CardBtn>
                    </CardActions>
                  </CardHeader>
                  <div style={{ color: 'rgba(255,255,255,0.8)', lineHeight: 1.5 }}>
                    <strong>ID:</strong> {report.id}<br />
                    <strong>Source:</strong> {report.source}<br />
                    <strong>Question:</strong> {report.question}<br />
                    <strong>Generated:</strong> {report.generated}<br />
                    <strong>Word Count:</strong> {report.wordCount.toLocaleString()} words
                  </div>
                </AdminCard>
              ))}
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
                  <th>Last Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {mockFAQs.map((faq) => (
                  <tr key={faq.id}>
                    <td>{faq.question}</td>
                    <td>{faq.category}</td>
                    <td>{faq.views}</td>
                    <td>{faq.lastUpdated}</td>
                    <td>
                      <CardBtn edit onClick={() => console.log('Edit FAQ', faq.id)}>✏️ Edit</CardBtn>
                      <CardBtn delete onClick={() => console.log('Deactivate FAQ', faq.id)}>🔒 Deactivate</CardBtn>
                    </td>
                  </tr>
                ))}
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