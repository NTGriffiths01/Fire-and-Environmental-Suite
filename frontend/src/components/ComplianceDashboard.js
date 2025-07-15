import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import DocumentUpload from './DocumentUpload';
import TaskAssignment from './TaskAssignment';
import CommentSystem from './CommentSystem';
import NotificationPanel from './NotificationPanel';
import ExportPanel from './ExportPanel';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Status color mapping
const getStatusColor = (status) => {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800 border-green-300';
    case 'overdue':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'pending':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
};

// Status icon mapping
const getStatusIcon = (status, hasDocuments) => {
  if (hasDocuments) {
    return '⬆️'; // Documentation uploaded
  }
  switch (status) {
    case 'completed':
      return '✅';
    case 'overdue':
      return '❌';
    case 'pending':
      return '⏳';
    default:
      return '⚪';
  }
};

// Calculate which months should show status based on frequency
const getScheduledMonths = (frequency, startMonth = 1) => {
  const months = [];
  
  switch (frequency) {
    case 'W': // Weekly - show every month (weekly tasks happen every month)
      for (let i = 1; i <= 12; i++) {
        months.push(i);
      }
      break;
    case 'M': // Monthly - show every month
      for (let i = 1; i <= 12; i++) {
        months.push(i);
      }
      break;
    case 'Q': // Quarterly - show every 3 months
      for (let i = startMonth; i <= 12; i += 3) {
        months.push(i);
      }
      break;
    case 'SA': // Semi-Annually - show every 6 months
      for (let i = startMonth; i <= 12; i += 6) {
        months.push(i);
      }
      break;
    case 'A': // Annually - show once per year
      months.push(startMonth);
      break;
    case '2y': // Every 2 years - show once per year (alternating years)
      if (new Date().getFullYear() % 2 === 0) {
        months.push(startMonth);
      }
      break;
    case '3y': // Every 3 years - show once per year (every 3rd year)
      if (new Date().getFullYear() % 3 === 0) {
        months.push(startMonth);
      }
      break;
    case '5y': // Every 5 years - show once per year (every 5th year)
      if (new Date().getFullYear() % 5 === 0) {
        months.push(startMonth);
      }
      break;
    default:
      months.push(startMonth);
  }
  
  return months;
};

// Month names
const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

// Quarter labels
const QUARTER_LABELS = ['Q1', 'Q2', 'Q3', 'Q4'];

export default function ComplianceDashboard() {
  const [selectedFacility, setSelectedFacility] = useState(null);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [activeModal, setActiveModal] = useState(null); // 'document', 'task', 'comment'

  // Fetch facilities
  const { data: facilities, isLoading: facilitiesLoading } = useQuery({
    queryKey: ['compliance-facilities'],
    queryFn: async () => {
      const response = await fetch(`${BACKEND_URL}/api/compliance/facilities`);
      if (!response.ok) throw new Error('Failed to fetch facilities');
      return response.json();
    },
  });

  // Fetch dashboard data
  const { data: dashboardData, isLoading: dashboardLoading, refetch: refetchDashboard } = useQuery({
    queryKey: ['compliance-dashboard', selectedFacility, selectedYear],
    queryFn: async () => {
      if (!selectedFacility) return null;
      const response = await fetch(
        `${BACKEND_URL}/api/compliance/facilities/${selectedFacility}/dashboard?year=${selectedYear}`
      );
      if (!response.ok) throw new Error('Failed to fetch dashboard data');
      return response.json();
    },
    enabled: !!selectedFacility,
  });

  // Fetch statistics
  const { data: statistics } = useQuery({
    queryKey: ['compliance-statistics', selectedFacility],
    queryFn: async () => {
      const url = selectedFacility 
        ? `${BACKEND_URL}/api/compliance/statistics?facility_id=${selectedFacility}`
        : `${BACKEND_URL}/api/compliance/statistics`;
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch statistics');
      return response.json();
    },
  });

  // Set default facility
  useEffect(() => {
    if (facilities && facilities.length > 0 && !selectedFacility) {
      setSelectedFacility(facilities[0].id);
    }
  }, [facilities, selectedFacility]);

  const toggleRowExpansion = (scheduleId) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(scheduleId)) {
      newExpanded.delete(scheduleId);
    } else {
      newExpanded.add(scheduleId);
    }
    setExpandedRows(newExpanded);
  };

  const handleCompleteRecord = async (recordId, completedBy) => {
    try {
      const formData = new FormData();
      formData.append('completed_by', completedBy);
      
      const response = await fetch(`${BACKEND_URL}/api/compliance/records/${recordId}/complete`, {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        toast.success('Record marked as completed');
        refetchDashboard();
      } else {
        toast.error('Failed to complete record');
      }
    } catch (error) {
      toast.error('Error completing record');
    }
  };

  // Process dashboard data to only show status for scheduled months
  const processedDashboardData = dashboardData ? {
    ...dashboardData,
    schedules: dashboardData.schedules.map(schedule => {
      const scheduledMonths = getScheduledMonths(schedule.frequency);
      const processedMonthlyStatus = {};
      
      // Initialize all months as empty
      for (let month = 1; month <= 12; month++) {
        processedMonthlyStatus[month] = {
          status: null,
          due_date: null,
          completed_date: null,
          has_documents: false,
          isScheduled: false
        };
      }
      
      // Only populate scheduled months
      scheduledMonths.forEach(month => {
        if (schedule.monthly_status[month]) {
          processedMonthlyStatus[month] = {
            ...schedule.monthly_status[month],
            isScheduled: true
          };
        } else {
          processedMonthlyStatus[month] = {
            status: 'pending',
            due_date: null,
            completed_date: null,
            has_documents: false,
            isScheduled: true
          };
        }
      });
      
      return {
        ...schedule,
        monthly_status: processedMonthlyStatus
      };
    })
  } : null;

  if (facilitiesLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-900"></div>
        <span className="ml-2 text-gray-600">Loading facilities...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-blue-900 mb-2">
              Compliance Tracking Dashboard
            </h2>
            <p className="text-gray-600">
              Environmental safety, inspections, and certification timeline tracking
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Facility Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select Facility
              </label>
              <select
                value={selectedFacility || ''}
                onChange={(e) => setSelectedFacility(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Choose a facility...</option>
                {facilities?.map((facility) => (
                  <option key={facility.id} value={facility.id}>
                    {facility.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Year Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Year
              </label>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                className="border border-gray-300 rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 2 + i).map(year => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Statistics */}
        {statistics && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-900">{statistics.total_records}</div>
              <div className="text-sm text-blue-600">Total Records</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-900">{statistics.completed_records}</div>
              <div className="text-sm text-green-600">Completed</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-yellow-900">{statistics.completion_rate.toFixed(1)}%</div>
              <div className="text-sm text-yellow-600">Completion Rate</div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-red-900">{statistics.overdue_records}</div>
              <div className="text-sm text-red-600">Overdue</div>
            </div>
          </div>
        )}
      </div>

      {/* Dashboard Matrix */}
      {dashboardLoading ? (
        <div className="flex justify-center items-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-900"></div>
          <span className="ml-2 text-gray-600">Loading dashboard...</span>
        </div>
      ) : processedDashboardData && processedDashboardData.schedules.length > 0 ? (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Matrix Header */}
          <div className="bg-gray-50 p-4 border-b">
            <h3 className="text-lg font-semibold text-gray-900">
              {processedDashboardData.facility_name} - {processedDashboardData.year}
            </h3>
            <p className="text-sm text-gray-600">
              Click on rows to expand details • Icons: ✅ Completed, ❌ Overdue, ⏳ Pending, ⬆️ Documents Uploaded
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Status indicators only appear for months when tasks are due based on their frequency
            </p>
          </div>

          {/* Matrix Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-64">
                    Function
                  </th>
                  <th className="px-2 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Freq.
                  </th>
                  {/* Quarter headers */}
                  {QUARTER_LABELS.map((quarter, qIndex) => (
                    <th key={quarter} className="px-1 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-l">
                      <div className="font-semibold">{quarter}</div>
                      <div className="grid grid-cols-3 gap-1 mt-1">
                        {MONTH_NAMES.slice(qIndex * 3, (qIndex + 1) * 3).map((month, mIndex) => (
                          <div key={month} className="text-xs">{month}</div>
                        ))}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {processedDashboardData.schedules.map((schedule) => (
                  <React.Fragment key={schedule.schedule_id}>
                    <tr 
                      className={`hover:bg-gray-50 cursor-pointer ${expandedRows.has(schedule.schedule_id) ? 'bg-blue-50' : ''}`}
                      onClick={() => toggleRowExpansion(schedule.schedule_id)}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 w-4 h-4 mr-2">
                            {expandedRows.has(schedule.schedule_id) ? '▼' : '▶'}
                          </div>
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {schedule.function_name}
                            </div>
                            <div className="text-xs text-gray-500">
                              {schedule.function_category}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-2 py-3 text-center">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {schedule.frequency}
                        </span>
                      </td>
                      {/* Monthly status cells grouped by quarters */}
                      {QUARTER_LABELS.map((quarter, qIndex) => (
                        <td key={quarter} className="px-1 py-3 border-l">
                          <div className="grid grid-cols-3 gap-1">
                            {Array.from({ length: 3 }, (_, mIndex) => {
                              const monthNum = qIndex * 3 + mIndex + 1;
                              const monthStatus = schedule.monthly_status[monthNum];
                              
                              // Only show status if this month is scheduled
                              if (!monthStatus.isScheduled) {
                                return (
                                  <div
                                    key={monthNum}
                                    className="h-8 w-8 rounded border-2 border-gray-200 bg-gray-50"
                                    title={`${MONTH_NAMES[monthNum - 1]} ${processedDashboardData.year}: Not scheduled`}
                                  >
                                  </div>
                                );
                              }
                              
                              return (
                                <div
                                  key={monthNum}
                                  className={`h-8 w-8 rounded border-2 flex items-center justify-center text-xs font-medium cursor-pointer ${getStatusColor(monthStatus.status)}`}
                                  title={`${MONTH_NAMES[monthNum - 1]} ${processedDashboardData.year}: ${monthStatus.status}`}
                                >
                                  {getStatusIcon(monthStatus.status, monthStatus.has_documents)}
                                </div>
                              );
                            })}
                          </div>
                        </td>
                      ))}
                    </tr>
                    
                    {/* Expanded Row Details */}
                    {expandedRows.has(schedule.schedule_id) && (
                      <tr className="bg-blue-50">
                        <td colSpan="6" className="px-4 py-4">
                          <div className="space-y-3">
                            <div className="text-sm">
                              <strong>Frequency:</strong> {schedule.frequency_display}
                            </div>
                            {schedule.citation_references.length > 0 && (
                              <div className="text-sm">
                                <strong>Citations:</strong> {schedule.citation_references.join(', ')}
                              </div>
                            )}
                            <div className="text-sm">
                              <strong>Scheduled Months:</strong>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
                              {Object.entries(schedule.monthly_status)
                                .filter(([month, status]) => status.isScheduled)
                                .map(([month, status]) => (
                                <div key={month} className="text-xs p-2 bg-white rounded border">
                                  <div className="font-medium">{MONTH_NAMES[parseInt(month) - 1]}</div>
                                  <div className={`capitalize ${status.status === 'completed' ? 'text-green-600' : status.status === 'overdue' ? 'text-red-600' : 'text-yellow-600'}`}>
                                    {status.status}
                                  </div>
                                  {status.due_date && (
                                    <div className="text-gray-500">Due: {new Date(status.due_date).toLocaleDateString()}</div>
                                  )}
                                  {status.completed_date && (
                                    <div className="text-gray-500">Completed: {new Date(status.completed_date).toLocaleDateString()}</div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : selectedFacility ? (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <div className="text-gray-500">
            <p className="text-lg mb-2">No compliance data available</p>
            <p className="text-sm">
              Compliance schedules will appear here once they are configured for this facility.
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <div className="text-gray-500">
            <p className="text-lg mb-2">Select a facility to view compliance dashboard</p>
            <p className="text-sm">
              Choose a facility from the dropdown above to see its compliance tracking matrix.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}