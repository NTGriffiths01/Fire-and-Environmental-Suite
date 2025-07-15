import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const NotificationPanel = ({ facilityId }) => {
  const [daysAhead, setDaysAhead] = useState(7);
  const [isVisible, setIsVisible] = useState(false);
  const queryClient = useQueryClient();

  // Fetch overdue notifications
  const { data: notifications, isLoading } = useQuery({
    queryKey: ['overdue-notifications', daysAhead],
    queryFn: async () => {
      const response = await fetch(`${BACKEND_URL}/api/compliance/notifications/overdue?days_ahead=${daysAhead}`);
      if (!response.ok) throw new Error('Failed to fetch notifications');
      return response.json();
    },
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  });

  // Send reminders mutation
  const sendRemindersMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${BACKEND_URL}/api/compliance/notifications/send-reminders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days_ahead: daysAhead }),
      });
      if (!response.ok) throw new Error('Failed to send reminders');
      return response.json();
    },
    onSuccess: (data) => {
      toast.success(`Sent ${data.emails_sent} reminder emails`);
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const getUrgencyColor = (urgency) => {
    switch (urgency) {
      case 'overdue':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'urgent':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'upcoming':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getUrgencyIcon = (urgency) => {
    switch (urgency) {
      case 'overdue':
        return '🚨';
      case 'urgent':
        return '⚠️';
      case 'upcoming':
        return '⏰';
      default:
        return '📅';
    }
  };

  const formatDaysText = (days) => {
    if (days < 0) return `${Math.abs(days)} days overdue`;
    if (days === 0) return 'Due today';
    if (days === 1) return 'Due tomorrow';
    return `Due in ${days} days`;
  };

  const filteredNotifications = facilityId 
    ? notifications?.filter(n => n.facility_id === facilityId) 
    : notifications;

  const overdueCount = filteredNotifications?.filter(n => n.urgency === 'overdue').length || 0;
  const urgentCount = filteredNotifications?.filter(n => n.urgency === 'urgent').length || 0;
  const upcomingCount = filteredNotifications?.filter(n => n.urgency === 'upcoming').length || 0;

  return (
    <div className="relative">
      {/* Notification Bell */}
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="relative p-2 bg-white rounded-full shadow-md hover:shadow-lg transition-shadow"
      >
        <div className="w-6 h-6 text-gray-600">
          🔔
        </div>
        {(overdueCount > 0 || urgentCount > 0) && (
          <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {overdueCount + urgentCount}
          </div>
        )}
      </button>

      {/* Notification Panel */}
      {isVisible && (
        <div className="absolute right-0 top-12 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900">Notifications</h3>
              <button
                onClick={() => setIsVisible(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="text-center p-2 bg-red-50 rounded-lg">
                <div className="text-lg font-bold text-red-800">{overdueCount}</div>
                <div className="text-xs text-red-600">Overdue</div>
              </div>
              <div className="text-center p-2 bg-orange-50 rounded-lg">
                <div className="text-lg font-bold text-orange-800">{urgentCount}</div>
                <div className="text-xs text-orange-600">Urgent</div>
              </div>
              <div className="text-center p-2 bg-yellow-50 rounded-lg">
                <div className="text-lg font-bold text-yellow-800">{upcomingCount}</div>
                <div className="text-xs text-yellow-600">Upcoming</div>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Days ahead:</label>
                <select
                  value={daysAhead}
                  onChange={(e) => setDaysAhead(parseInt(e.target.value))}
                  className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={3}>3 days</option>
                  <option value={7}>7 days</option>
                  <option value={14}>14 days</option>
                  <option value={30}>30 days</option>
                </select>
              </div>
              
              <button
                onClick={() => sendRemindersMutation.mutate()}
                disabled={sendRemindersMutation.isLoading}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {sendRemindersMutation.isLoading ? 'Sending...' : 'Send Reminders'}
              </button>
            </div>
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="flex justify-center items-center p-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-900"></div>
                <span className="ml-2 text-gray-600">Loading...</span>
              </div>
            ) : filteredNotifications && filteredNotifications.length > 0 ? (
              <div className="p-2 space-y-2">
                {filteredNotifications.map((notification) => (
                  <div
                    key={notification.record_id}
                    className={`p-3 rounded-lg border ${getUrgencyColor(notification.urgency)}`}
                  >
                    <div className="flex items-start space-x-3">
                      <span className="text-lg">{getUrgencyIcon(notification.urgency)}</span>
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 mb-1">
                          {notification.function_name}
                        </div>
                        <div className="text-sm text-gray-600 mb-1">
                          {notification.facility_name}
                        </div>
                        <div className="text-sm font-medium">
                          {formatDaysText(notification.days_until_due)}
                        </div>
                        {notification.assigned_to && (
                          <div className="text-xs text-gray-500 mt-1">
                            Assigned to: {notification.assigned_to}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">🎉</div>
                <p>No upcoming notifications</p>
                <p className="text-sm">All tasks are on track!</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationPanel;