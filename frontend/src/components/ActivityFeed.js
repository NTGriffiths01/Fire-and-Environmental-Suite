import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ActivityFeed = ({ facilityId, limit = 20 }) => {
  const [isVisible, setIsVisible] = useState(false);

  // Fetch activity feed
  const { data: activities, isLoading } = useQuery({
    queryKey: ['activity-feed', facilityId, limit],
    queryFn: async () => {
      const url = `${BACKEND_URL}/api/compliance/activity-feed?${facilityId ? `facility_id=${facilityId}&` : ''}limit=${limit}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch activity feed');
      return response.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const getActivityIcon = (activityType) => {
    switch (activityType) {
      case 'completed':
        return '✅';
      case 'updated':
        return '📝';
      case 'assigned':
        return '👤';
      case 'comment':
        return '💬';
      default:
        return '📋';
    }
  };

  const getActivityColor = (activityType) => {
    switch (activityType) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'updated':
        return 'bg-blue-50 border-blue-200';
      case 'assigned':
        return 'bg-purple-50 border-purple-200';
      case 'comment':
        return 'bg-yellow-50 border-yellow-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const activityTime = new Date(timestamp);
    const diffInMinutes = Math.floor((now - activityTime) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    
    return activityTime.toLocaleDateString();
  };

  return (
    <div className="relative">
      {/* Activity Feed Toggle Button */}
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="p-2 bg-white rounded-full shadow-md hover:shadow-lg transition-shadow"
      >
        <div className="w-6 h-6 text-gray-600">
          📊
        </div>
      </button>

      {/* Activity Feed Panel */}
      {isVisible && (
        <div className="absolute right-0 top-12 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
              <button
                onClick={() => setIsVisible(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              {facilityId ? 'Facility activity' : 'System-wide activity'}
            </p>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="flex justify-center items-center p-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-900"></div>
                <span className="ml-2 text-gray-600">Loading...</span>
              </div>
            ) : activities && activities.length > 0 ? (
              <div className="p-2 space-y-2">
                {activities.map((activity) => (
                  <div
                    key={activity.record_id}
                    className={`p-3 rounded-lg border ${getActivityColor(activity.activity_type)}`}
                  >
                    <div className="flex items-start space-x-3">
                      <span className="text-lg">{getActivityIcon(activity.activity_type)}</span>
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 text-sm">
                          {activity.function_name}
                        </div>
                        <div className="text-xs text-gray-600 mb-1">
                          {activity.facility_name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {activity.activity_type === 'completed' && activity.completed_by && (
                            <span>Completed by {activity.completed_by}</span>
                          )}
                          {activity.activity_type === 'updated' && (
                            <span>Status: {activity.status}</span>
                          )}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {formatTimeAgo(activity.updated_at)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">📋</div>
                <p>No recent activity</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ActivityFeed;