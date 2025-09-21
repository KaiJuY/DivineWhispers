import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { colors, gradients, media } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import adminService, { DashboardOverview, Customer as ApiCustomer, FAQ as ApiFAQ } from '../services/adminService';
import apiClient from '../services/apiClient';

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

const Modal = styled.div<{ show: boolean }>`
  display: ${props => props.show ? 'flex' : 'none'};
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  z-index: 1000;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(5px);
`;

const ModalContent = styled.div`
  background: linear-gradient(135deg, rgba(13, 13, 32, 0.95), rgba(20, 20, 40, 0.95));
  backdrop-filter: blur(10px);
  border: 1px solid rgba(212, 175, 55, 0.5);
  border-radius: 12px;
  padding: 2rem;
  max-width: 900px;
  width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  color: ${colors.white};
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.7);
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid rgba(212, 175, 55, 0.3);
  padding-bottom: 1rem;
`;

const ModalTitle = styled.h2`
  color: ${colors.primary};
  margin: 0;
  font-size: 1.5rem;
`;

const CloseBtn = styled.button`
  background: none;
  border: none;
  color: ${colors.white};
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    color: ${colors.primary};
  }
`;

const ModalBody = styled.div`
  line-height: 1.6;

  .poem-section {
    margin-bottom: 1.5rem;

    h4 {
      color: ${colors.primary};
      margin-bottom: 0.5rem;
      font-size: 1.1rem;
    }

    .poem-text {
      background: rgba(255, 255, 255, 0.05);
      padding: 1rem;
      border-radius: 8px;
      border-left: 3px solid ${colors.primary};
      font-family: serif;
      line-height: 1.8;
    }

    .fortune-badge {
      display: inline-block;
      background: ${colors.primary};
      color: ${colors.black};
      padding: 0.25rem 0.75rem;
      border-radius: 20px;
      font-weight: 600;
      font-size: 0.9rem;
    }
  }
`;

// Pagination styled components
const PaginationContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  margin-top: 2rem;
  padding: 1rem;
`;

const PaginationButton = styled.button<{ active?: boolean; disabled?: boolean }>`
  padding: 0.5rem 0.75rem;
  background: ${props => props.active ? colors.primary : 'rgba(255,255,255,0.1)'};
  color: ${props => props.active ? colors.black : colors.white};
  border: 1px solid ${props => props.active ? colors.primary : 'rgba(255,255,255,0.2)'};
  border-radius: 6px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  font-weight: ${props => props.active ? '600' : '400'};
  opacity: ${props => props.disabled ? '0.5' : '1'};
  transition: all 0.3s ease;
  min-width: 40px;

  &:hover:not(:disabled) {
    background: ${props => props.active ? colors.primary : 'rgba(255,255,255,0.2)'};
    border-color: ${colors.primary};
  }
`;

const PaginationInfo = styled.div`
  color: rgba(255,255,255,0.7);
  font-size: 0.9rem;
  margin: 0 1rem;
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

// Pagination helper functions
const generatePageNumbers = (currentPage: number, totalPages: number) => {
  const pages: (number | string)[] = [];
  const showEllipsis = totalPages > 7;

  if (!showEllipsis) {
    // Show all pages if 7 or fewer
    for (let i = 1; i <= totalPages; i++) {
      pages.push(i);
    }
  } else {
    // Always show first page
    pages.push(1);

    if (currentPage > 4) {
      pages.push('...');
    }

    // Show pages around current page
    const start = Math.max(2, currentPage - 1);
    const end = Math.min(totalPages - 1, currentPage + 1);

    for (let i = start; i <= end; i++) {
      if (!pages.includes(i)) {
        pages.push(i);
      }
    }

    if (currentPage < totalPages - 3) {
      pages.push('...');
    }

    // Always show last page
    if (totalPages > 1) {
      pages.push(totalPages);
    }
  }

  return pages;
};

const AdminPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState('customers');
  const [dashboardData, setDashboardData] = useState<DashboardOverview | null>(null);
  const [customers, setCustomers] = useState<ApiCustomer[]>([]);
  const [faqs, setFaqs] = useState<ApiFAQ[]>([]);
  const [poems, setPoems] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [selectedPoem, setSelectedPoem] = useState<any>(null);
  const [showPoemModal, setShowPoemModal] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null);
  const [showEditCustomerModal, setShowEditCustomerModal] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);

  // Edit customer form state
  const [editFullName, setEditFullName] = useState('');
  const [editStatus, setEditStatus] = useState('');
  const [editWalletBalance, setEditWalletBalance] = useState(0);
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
  const [poemPage, setPoemPage] = useState(1);
  const [totalPoems, setTotalPoems] = useState(0);

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

  // Load customers function - accessible from anywhere
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

  // Load customers data
  useEffect(() => {
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
          page: poemPage,
          limit: 10,
          deity_filter: poemDeity || undefined,
          search: poemSearch || undefined
        });
        setPoems(response.poems);
        setTotalPoems(response.pagination?.total || 0);
      } catch (err) {
        console.error('Error loading poems:', err);
        setError('Failed to load poems');
      }
    };

    if (activeSection === 'poems') {
      loadPoems();
    }
  }, [activeSection, poemDeity, poemSearch, poemPage]);

  // Reset poem page when filters change
  useEffect(() => {
    setPoemPage(1);
  }, [poemDeity, poemSearch]);

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
      const customer = customers.find(c => c.user_id === userId);
      if (!customer) return;

      setSelectedCustomer(customer);

      if (action === 'edit') {
        // Initialize form state with current customer data
        setEditFullName(customer.full_name || '');
        setEditStatus(customer.status || 'active');
        setEditWalletBalance(customer.wallet_balance || 0);
        setShowEditCustomerModal(true);
      } else if (action === 'reset_password') {
        setShowResetPasswordModal(true);
      }
    } catch (err) {
      console.error(`Error performing ${action} on customer ${userId}:`, err);
      setError(`Failed to ${action} customer`);
    }
  };

  const handleSaveCustomerChanges = async () => {
    if (!selectedCustomer) return;

    try {
      setLoading(true);

      // Update profile (full_name) using apiClient directly
      if (editFullName !== selectedCustomer.full_name) {
        await apiClient.put(`/api/v1/admin/users/${selectedCustomer.user_id}/profile`, {
          full_name: editFullName
        });
      }

      // Update status if changed using adminService methods
      if (editStatus !== selectedCustomer.status) {
        if (editStatus === 'suspended') {
          await adminService.suspendUser(selectedCustomer.user_id, {
            target_user_id: selectedCustomer.user_id,
            reason: 'Status updated by admin'
          });
        } else if (editStatus === 'active' && selectedCustomer.status === 'suspended') {
          await adminService.activateUser(selectedCustomer.user_id, {
            target_user_id: selectedCustomer.user_id,
            reason: 'Status activated by admin'
          });
        }
      }

      // Update wallet balance if changed using adminService
      if (editWalletBalance !== selectedCustomer.wallet_balance) {
        const balanceDiff = editWalletBalance - selectedCustomer.wallet_balance;
        await adminService.adjustUserPoints(selectedCustomer.user_id, {
          target_user_id: selectedCustomer.user_id,
          amount: balanceDiff,
          reason: 'Balance adjusted by admin',
          adjustment_type: balanceDiff > 0 ? 'add' : 'deduct'
        });
      }

      // Refresh customer list
      await loadCustomers();

      // Close modal
      setShowEditCustomerModal(false);
      setSelectedCustomer(null);

      alert('Customer updated successfully!');
    } catch (error) {
      console.error('Error updating customer:', error);
      alert('Failed to update customer. Please try again.');
    } finally {
      setLoading(false);
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

  const handleViewPoem = async (poemId: string) => {
    try {
      const poemDetails = await adminService.getPoemById(poemId);
      setSelectedPoem(poemDetails);
      setShowPoemModal(true);
    } catch (err) {
      console.error('Error fetching poem details:', err);
      setError('Failed to load poem details');
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
                {/* Removed Add Poem and Bulk Update buttons as requested */}
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
                <option value="GuanYin100">Guan Yin (觀音一百籤)</option>
                <option value="Mazu">Mazu (媽祖六十甲子籤)</option>
                <option value="GuanYu">Guan Yu (關聖帝君一百籤)</option>
                <option value="YueLao">Yue Lao (月老聖籤一百籤)</option>
                <option value="Tianhou">Tianhou (天后宮一百籤)</option>
                <option value="Asakusa">Asakusa (日本淺草觀音寺一百籤)</option>
              </FilterSelect>
            </SearchFilterBar>

            <PoemsGrid>
              {poems.length > 0 ? poems.map((poem) => (
                <AdminCard key={poem.id}>
                  <CardHeader>
                    <CardTitle>{poem.title}</CardTitle>
                    <CardActions>
                      <CardBtn edit onClick={() => handleViewPoem(poem.id)}>✏️ View</CardBtn>
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

            {/* Poems Pagination */}
            {poems.length > 0 && (
              <PaginationContainer>
                <PaginationButton
                  disabled={poemPage === 1}
                  onClick={() => setPoemPage(1)}
                >
                  ««
                </PaginationButton>
                <PaginationButton
                  disabled={poemPage === 1}
                  onClick={() => setPoemPage(poemPage - 1)}
                >
                  ‹
                </PaginationButton>

                {generatePageNumbers(poemPage, Math.ceil(totalPoems / 10)).map((page, index) => (
                  <PaginationButton
                    key={index}
                    active={page === poemPage}
                    disabled={page === '...'}
                    onClick={() => typeof page === 'number' && setPoemPage(page)}
                  >
                    {page}
                  </PaginationButton>
                ))}

                <PaginationButton
                  disabled={poemPage >= Math.ceil(totalPoems / 10)}
                  onClick={() => setPoemPage(poemPage + 1)}
                >
                  ›
                </PaginationButton>
                <PaginationButton
                  disabled={poemPage >= Math.ceil(totalPoems / 10)}
                  onClick={() => setPoemPage(Math.ceil(totalPoems / 10))}
                >
                  »»
                </PaginationButton>

                <PaginationInfo>
                  Page {poemPage} of {Math.ceil(totalPoems / 10)} | {totalPoems} total poems
                </PaginationInfo>
              </PaginationContainer>
            )}
          </DashboardSection>

          {/* Poem Detail Modal */}
          <Modal show={showPoemModal}>
            <ModalContent>
              <ModalHeader>
                <ModalTitle>Poem Details</ModalTitle>
                <CloseBtn onClick={() => {
                  setShowPoemModal(false);
                  setSelectedPoem(null);
                }}>×</CloseBtn>
              </ModalHeader>
              {selectedPoem && (
                <ModalBody>
                  <div className="poem-section">
                    <h4>Title</h4>
                    <p>{selectedPoem.title}</p>
                  </div>

                  <div className="poem-section">
                    <h4>Deity</h4>
                    <p>{selectedPoem.deity}</p>
                  </div>

                  <div className="poem-section">
                    <h4>Chinese Poem</h4>
                    <div className="poem-text">
                      {selectedPoem.chinese || 'N/A'}
                    </div>
                  </div>

                  <div className="poem-section">
                    <h4>Fortune Level</h4>
                    <span className="fortune-badge">{selectedPoem.fortune || 'Unknown'}</span>
                  </div>

                  {selectedPoem.analysis && (
                    <div className="poem-section">
                      <h4>Analysis</h4>
                      <div className="poem-text">
                        {typeof selectedPoem.analysis === 'object'
                          ? JSON.stringify(selectedPoem.analysis, null, 2)
                          : selectedPoem.analysis}
                      </div>
                    </div>
                  )}

                  {selectedPoem.topics && selectedPoem.topics.length > 0 && (
                    <div className="poem-section">
                      <h4>Topics</h4>
                      <p>{selectedPoem.topics.join(', ')}</p>
                    </div>
                  )}

                  {selectedPoem.rag_analysis && (
                    <div className="poem-section">
                      <h4>RAG Analysis</h4>
                      <div className="poem-text">
                        {selectedPoem.rag_analysis}
                      </div>
                    </div>
                  )}

                  {selectedPoem.llm_meta && (
                    <div className="poem-section">
                      <h4>LLM Metadata</h4>
                      <div className="poem-text">
                        <p><strong>Model:</strong> {selectedPoem.llm_meta.model || 'N/A'}</p>
                        <p><strong>Timestamp:</strong> {selectedPoem.llm_meta.timestamp || 'N/A'}</p>
                        <p><strong>Source File:</strong> {selectedPoem.llm_meta.source_file || 'N/A'}</p>
                        {selectedPoem.llm_meta.raw_llm_response_preview && (
                          <div>
                            <strong>Response Preview:</strong>
                            <div style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.7)', marginTop: '0.5rem' }}>
                              {selectedPoem.llm_meta.raw_llm_response_preview.substring(0, 200)}...
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="poem-section">
                    <h4>Metadata</h4>
                    <p><strong>ID:</strong> {selectedPoem.id}</p>
                    <p><strong>Temple:</strong> {selectedPoem.metadata?.temple || 'N/A'}</p>
                    <p><strong>Poem ID:</strong> {selectedPoem.metadata?.poem_id || 'N/A'}</p>
                    <p><strong>Last Modified:</strong> {selectedPoem.metadata?.last_modified ? new Date(selectedPoem.metadata.last_modified).toLocaleString() : 'N/A'}</p>
                    <p><strong>Usage Count:</strong> {selectedPoem.metadata?.usage_count || 0}</p>
                  </div>
                </ModalBody>
              )}
            </ModalContent>
          </Modal>

          {/* Edit Customer Modal */}
          <Modal show={showEditCustomerModal}>
            <ModalContent>
              <ModalHeader>
                <ModalTitle>Edit Customer</ModalTitle>
                <CloseBtn onClick={() => {
                  setShowEditCustomerModal(false);
                  setSelectedCustomer(null);
                }}>×</CloseBtn>
              </ModalHeader>
              {selectedCustomer && (
                <ModalBody>
                  <div className="poem-section">
                    <h4>Customer ID</h4>
                    <p>DW{selectedCustomer.user_id.toString().padStart(3, '0')}</p>
                  </div>

                  <div className="poem-section">
                    <h4>Email</h4>
                    <p>{selectedCustomer.email}</p>
                  </div>

                  <div className="poem-section">
                    <h4>Full Name</h4>
                    <input
                      type="text"
                      value={editFullName}
                      onChange={(e) => setEditFullName(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        borderRadius: '4px',
                        border: '1px solid rgba(212, 175, 55, 0.3)',
                        background: 'rgba(0,0,0,0.3)',
                        color: 'white'
                      }}
                    />
                  </div>

                  <div className="poem-section">
                    <h4>Status</h4>
                    <select
                      value={editStatus}
                      onChange={(e) => setEditStatus(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        borderRadius: '4px',
                        border: '1px solid rgba(212, 175, 55, 0.3)',
                        background: 'rgba(0,0,0,0.3)',
                        color: 'white'
                      }}
                    >
                      <option value="active">Active</option>
                      <option value="suspended">Suspended</option>
                      <option value="banned">Banned</option>
                    </select>
                  </div>

                  <div className="poem-section">
                    <h4>Wallet Balance</h4>
                    <input
                      type="number"
                      value={editWalletBalance}
                      onChange={(e) => setEditWalletBalance(parseInt(e.target.value) || 0)}
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        borderRadius: '4px',
                        border: '1px solid rgba(212, 175, 55, 0.3)',
                        background: 'rgba(0,0,0,0.3)',
                        color: 'white'
                      }}
                    />
                  </div>

                  <div className="poem-section">
                    <h4>Member Since</h4>
                    <p>{new Date(selectedCustomer.created_at).toLocaleDateString()}</p>
                  </div>

                  <div style={{ marginTop: '2rem', textAlign: 'center' }}>
                    <AdminBtn onClick={handleSaveCustomerChanges}>
                      💾 Save Changes
                    </AdminBtn>
                  </div>
                </ModalBody>
              )}
            </ModalContent>
          </Modal>

          {/* Reset Password Modal */}
          <Modal show={showResetPasswordModal}>
            <ModalContent>
              <ModalHeader>
                <ModalTitle>Reset Password</ModalTitle>
                <CloseBtn onClick={() => {
                  setShowResetPasswordModal(false);
                  setSelectedCustomer(null);
                }}>×</CloseBtn>
              </ModalHeader>
              {selectedCustomer && (
                <ModalBody>
                  <div className="poem-section">
                    <h4>Customer</h4>
                    <p>DW{selectedCustomer.user_id.toString().padStart(3, '0')} - {selectedCustomer.email}</p>
                  </div>

                  <div className="poem-section">
                    <h4>New Password</h4>
                    <input
                      type="password"
                      placeholder="Enter new password"
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        borderRadius: '4px',
                        border: '1px solid rgba(212, 175, 55, 0.3)',
                        background: 'rgba(0,0,0,0.3)',
                        color: 'white'
                      }}
                    />
                  </div>

                  <div className="poem-section">
                    <h4>Confirm Password</h4>
                    <input
                      type="password"
                      placeholder="Confirm new password"
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        borderRadius: '4px',
                        border: '1px solid rgba(212, 175, 55, 0.3)',
                        background: 'rgba(0,0,0,0.3)',
                        color: 'white'
                      }}
                    />
                  </div>

                  <div className="poem-section">
                    <h4>Reset Reason</h4>
                    <textarea
                      placeholder="Enter reason for password reset..."
                      style={{
                        width: '100%',
                        height: '80px',
                        padding: '0.5rem',
                        borderRadius: '4px',
                        border: '1px solid rgba(212, 175, 55, 0.3)',
                        background: 'rgba(0,0,0,0.3)',
                        color: 'white',
                        resize: 'vertical'
                      }}
                    />
                  </div>

                  <div style={{ marginTop: '2rem', textAlign: 'center' }}>
                    <AdminBtn onClick={() => console.log('Reset password')}>
                      🔑 Reset Password
                    </AdminBtn>
                  </div>
                </ModalBody>
              )}
            </ModalContent>
          </Modal>

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