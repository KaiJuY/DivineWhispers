import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import styled from 'styled-components';
import adminService from '../../services/adminService';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const ChartContainer = styled.div`
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
`;

const ChartHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

const ChartTitle = styled.h3`
  color: #2d3436;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
`;

const ChartControls = styled.div`
  display: flex;
  gap: 12px;
  align-items: center;
`;

const TimeRangeButton = styled.button<{ active?: boolean }>`
  padding: 8px 16px;
  border: 1px solid ${props => props.active ? '#6c5ce7' : '#ddd'};
  background: ${props => props.active ? '#6c5ce7' : 'white'};
  color: ${props => props.active ? 'white' : '#666'};
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;

  &:hover {
    border-color: #6c5ce7;
    color: ${props => props.active ? 'white' : '#6c5ce7'};
  }
`;

const ChartTypeToggle = styled.button`
  padding: 8px 16px;
  border: 1px solid #6c5ce7;
  background: white;
  color: #6c5ce7;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;

  &:hover {
    background: #6c5ce7;
    color: white;
  }
`;

const SummaryStats = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
`;

const StatCard = styled.div`
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #6c5ce7;
`;

const StatLabel = styled.div`
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
  text-transform: uppercase;
  font-weight: 500;
`;

const StatValue = styled.div`
  font-size: 24px;
  font-weight: bold;
  color: #2d3436;
`;

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
  color: #666;
`;

const ErrorContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
  color: #e74c3c;
  text-align: center;
`;

interface SalesData {
  date: string;
  amount: number;
  transactions: number;
}

interface SalesChartData {
  chart_data: SalesData[];
  summary: {
    total_revenue: number;
    total_transactions: number;
    avg_daily_revenue: number;
    date_range: {
      start: string;
      end: string;
      days: number;
    };
    peak_day: {
      date: string;
      amount: number;
      transactions: number;
    } | null;
  };
}

const SalesChart: React.FC = () => {
  const [chartData, setChartData] = useState<SalesChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDays, setSelectedDays] = useState(30);
  const [chartType, setChartType] = useState<'line' | 'bar'>('line');

  const timeRanges = [
    { days: 7, label: '7D' },
    { days: 30, label: '30D' },
    { days: 90, label: '90D' },
  ];

  useEffect(() => {
    loadSalesData();
  }, [selectedDays]);

  const loadSalesData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminService.getSalesChartData(selectedDays);
      setChartData(data);
    } catch (err) {
      setError('Failed to load sales data');
      console.error('Error loading sales data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getChartOptions = () => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const dataPoint = chartData?.chart_data[context.dataIndex];
            return [
              `Revenue: $${context.parsed.y.toFixed(2)}`,
              `Transactions: ${dataPoint?.transactions || 0}`
            ];
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date'
        },
        ticks: {
          maxTicksLimit: 10
        }
      },
      y: {
        title: {
          display: true,
          text: 'Revenue ($)'
        },
        ticks: {
          callback: function(value: any) {
            return '$' + value.toFixed(2);
          }
        }
      },
    },
  });

  const getChartDataConfig = () => {
    if (!chartData) {
      return {
        labels: [],
        datasets: [],
      };
    }

    return {
      labels: chartData.chart_data.map(item => {
        const date = new Date(item.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      }),
      datasets: [
        {
          label: 'Daily Revenue',
          data: chartData.chart_data.map(item => item.amount),
          borderColor: '#6c5ce7',
          backgroundColor: chartType === 'bar' ? 'rgba(108, 92, 231, 0.8)' : 'rgba(108, 92, 231, 0.1)',
          borderWidth: 2,
          fill: chartType === 'line' ? true : false,
          tension: 0.1,
        },
      ],
    };
  };

  if (loading) {
    return (
      <ChartContainer>
        <LoadingContainer>
          Loading sales data...
        </LoadingContainer>
      </ChartContainer>
    );
  }

  if (error) {
    return (
      <ChartContainer>
        <ErrorContainer>
          <div>
            <div>{error}</div>
            <button onClick={loadSalesData} style={{ marginTop: '12px', padding: '8px 16px', cursor: 'pointer' }}>
              Retry
            </button>
          </div>
        </ErrorContainer>
      </ChartContainer>
    );
  }

  return (
    <ChartContainer>
      <ChartHeader>
        <ChartTitle>Sales Overview</ChartTitle>
        <ChartControls>
          {timeRanges.map(range => (
            <TimeRangeButton
              key={range.days}
              active={selectedDays === range.days}
              onClick={() => setSelectedDays(range.days)}
            >
              {range.label}
            </TimeRangeButton>
          ))}
          <ChartTypeToggle onClick={() => setChartType(chartType === 'line' ? 'bar' : 'line')}>
            {chartType === 'line' ? 'Bar Chart' : 'Line Chart'}
          </ChartTypeToggle>
        </ChartControls>
      </ChartHeader>

      {chartData && (
        <SummaryStats>
          <StatCard>
            <StatLabel>Total Revenue</StatLabel>
            <StatValue>${chartData.summary.total_revenue.toFixed(2)}</StatValue>
          </StatCard>
          <StatCard>
            <StatLabel>Total Transactions</StatLabel>
            <StatValue>{chartData.summary.total_transactions}</StatValue>
          </StatCard>
          <StatCard>
            <StatLabel>Avg Daily Revenue</StatLabel>
            <StatValue>${chartData.summary.avg_daily_revenue.toFixed(2)}</StatValue>
          </StatCard>
          {chartData.summary.peak_day && (
            <StatCard>
              <StatLabel>Peak Day</StatLabel>
              <StatValue>
                ${chartData.summary.peak_day.amount.toFixed(2)}
                <div style={{ fontSize: '12px', color: '#666', fontWeight: 'normal' }}>
                  {new Date(chartData.summary.peak_day.date).toLocaleDateString()}
                </div>
              </StatValue>
            </StatCard>
          )}
        </SummaryStats>
      )}

      <div style={{ height: '300px' }}>
        {chartType === 'line' ? (
          <Line options={getChartOptions()} data={getChartDataConfig()} />
        ) : (
          <Bar options={getChartOptions()} data={getChartDataConfig()} />
        )}
      </div>
    </ChartContainer>
  );
};

export default SalesChart;