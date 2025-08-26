import React from 'react';

const UserAnalyticsWidget = ({ data, config, onRefresh, refreshing }) => {
  const timeRange = config?.timeRange || '7d';
  const metrics = config?.metrics || ['active_users', 'predictions_made', 'dashboards_viewed'];

  const mockData = {
    active_users: { current: 45, change: 3, trend: 'up' },
    predictions_made: { current: 542, change: 23, trend: 'up' },
    dashboards_viewed: { current: 1250, change: -15, trend: 'down' },
    avg_session_duration: { current: 18, change: 2, trend: 'up' },
    user_breakdown: {
      admin: 5,
      manager: 12,
      user: 28,
      viewer: 8
    }
  };

  const analyticsData = data || mockData;

  const getMetricLabel = (metric) => {
    const labels = {
      active_users: 'Active Users',
      predictions_made: 'Predictions Made',
      dashboards_viewed: 'Dashboard Views',
      avg_session_duration: 'Avg Session (min)'
    };
    return labels[metric] || metric;
  };

  const getTrendIcon = (trend) => {
    if (trend === 'up') {
      return (
        <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      );
    } else {
      return (
        <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
        </svg>
      );
    }
  };

  return (
    <div className="h-full space-y-4">
      <h3 className="text-sm font-medium text-gray-900">
        User Analytics - Last {timeRange}
      </h3>

      {/* Key Metrics */}
      <div className="space-y-3">
        {metrics.map((metric) => {
          const data = analyticsData[metric] || { current: 0, change: 0, trend: 'up' };
          
          return (
            <div key={metric} className="bg-white border border-gray-200 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {getMetricLabel(metric)}
                  </div>
                  <div className="text-2xl font-bold text-gray-900 mt-1">
                    {data.current.toLocaleString()}
                  </div>
                </div>
                
                <div className="flex items-center space-x-1">
                  {getTrendIcon(data.trend)}
                  <span className={`text-sm ${
                    data.trend === 'up' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {data.change > 0 ? '+' : ''}{data.change}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* User Role Breakdown */}
      <div className="bg-white border border-gray-200 rounded-lg p-3">
        <h4 className="text-sm font-medium text-gray-900 mb-3">User Roles</h4>
        <div className="space-y-2">
          {Object.entries(analyticsData.user_breakdown).map(([role, count]) => (
            <div key={role} className="flex items-center justify-between">
              <span className="text-sm text-gray-600 capitalize">{role}</span>
              <span className="text-sm font-medium text-gray-900">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default UserAnalyticsWidget;