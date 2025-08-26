import React from 'react';

const ActivityFeedWidget = ({ data, config, onRefresh, refreshing }) => {
  const limit = config?.limit || 50;
  const showUserActions = config?.showUserActions !== false;

  const mockData = {
    activities: [
      {
        id: 'act_001',
        type: 'prediction',
        description: 'High-risk prediction for John Smith',
        user: 'Sarah Manager',
        timestamp: '2024-01-15T10:30:00Z',
        icon: '🔮'
      },
      {
        id: 'act_002',
        type: 'user_login',
        description: 'User logged in',
        user: 'Mike Davis',
        timestamp: '2024-01-15T09:15:00Z',
        icon: '🔑'
      },
      {
        id: 'act_003',
        type: 'model_training',
        description: 'Model retrained with new data',
        user: 'System',
        timestamp: '2024-01-15T08:00:00Z',
        icon: '🤖'
      }
    ]
  };

  const activityData = data || mockData;

  const getTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now - time) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  return (
    <div className="h-full">
      <h3 className="text-sm font-medium text-gray-900 mb-4">
        Activity Feed
      </h3>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {activityData.activities.slice(0, limit).map((activity) => (
          <div key={activity.id} className="flex items-start space-x-3 p-2 hover:bg-gray-50 rounded">
            <div className="flex-shrink-0 text-lg">
              {activity.icon}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900">
                {activity.description}
              </p>
              {showUserActions && (
                <p className="text-xs text-gray-500 mt-1">
                  by {activity.user} • {getTimeAgo(activity.timestamp)}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActivityFeedWidget;