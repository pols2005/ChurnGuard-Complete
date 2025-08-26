import React from 'react';

const ChurnSummaryWidget = ({ data, config, onRefresh, refreshing }) => {
  // Default configuration
  const showTrends = config?.showTrends !== false;
  const timeRange = config?.timeRange || '30d';
  const includeComparison = config?.includeComparison !== false;

  // Mock data - in production this would come from the API
  const defaultData = {
    summary: {
      total_customers: 1250,
      churned_customers: 231,
      churn_rate: 18.5,
      predicted_churn: 89,
      revenue_at_risk: 125000
    },
    risk_levels: {
      low: { count: 825, percentage: 66 },
      medium: { count: 336, percentage: 27 },
      high: { count: 89, percentage: 7 }
    },
    trends: {
      churn_rate_change: -2.3,
      high_risk_change: 5,
      revenue_change: -8000
    },
    comparison: {
      industry_avg: 22.1,
      vs_industry: -3.6
    },
    recent_activity: {
      predictions_today: 15,
      alerts_generated: 3,
      customers_saved: 7
    }
  };

  const summaryData = data || defaultData;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value, decimals = 1) => {
    return `${value.toFixed(decimals)}%`;
  };

  const getTrendIcon = (change) => {
    if (change > 0) {
      return (
        <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l9.2-9.2M17 17V7H7" />
        </svg>
      );
    } else if (change < 0) {
      return (
        <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-9.2 9.2M7 7v10h10" />
        </svg>
      );
    } else {
      return (
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
        </svg>
      );
    }
  };

  const getTrendColor = (change) => {
    if (change > 0) return 'text-red-600';
    if (change < 0) return 'text-green-600';
    return 'text-gray-600';
  };

  const getRiskLevelColor = (level) => {
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-red-100 text-red-800'
    };
    return colors[level] || colors.medium;
  };

  return (
    <div className="h-full space-y-6">
      {/* Main Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Churn Rate */}
        <div className="bg-gradient-to-r from-red-50 to-red-100 p-4 rounded-lg border border-red-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-600">Churn Rate</p>
              <p className="text-2xl font-bold text-red-900">
                {formatPercentage(summaryData.summary.churn_rate)}
              </p>
            </div>
            <div className="text-2xl">📉</div>
          </div>
          {showTrends && (
            <div className="flex items-center mt-2 text-sm">
              {getTrendIcon(summaryData.trends.churn_rate_change)}
              <span className={`ml-1 ${getTrendColor(summaryData.trends.churn_rate_change)}`}>
                {Math.abs(summaryData.trends.churn_rate_change)}% vs last {timeRange}
              </span>
            </div>
          )}
        </div>

        {/* Total Customers */}
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-600">Total Customers</p>
              <p className="text-2xl font-bold text-blue-900">
                {summaryData.summary.total_customers.toLocaleString()}
              </p>
            </div>
            <div className="text-2xl">👥</div>
          </div>
          <div className="mt-2 text-sm text-blue-700">
            {summaryData.summary.churned_customers} churned this period
          </div>
        </div>

        {/* High Risk Customers */}
        <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-4 rounded-lg border border-orange-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-orange-600">High Risk</p>
              <p className="text-2xl font-bold text-orange-900">
                {summaryData.summary.predicted_churn}
              </p>
            </div>
            <div className="text-2xl">⚠️</div>
          </div>
          {showTrends && (
            <div className="flex items-center mt-2 text-sm">
              {getTrendIcon(summaryData.trends.high_risk_change)}
              <span className={`ml-1 ${getTrendColor(summaryData.trends.high_risk_change)}`}>
                {Math.abs(summaryData.trends.high_risk_change)} vs last {timeRange}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Risk Distribution */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Risk Distribution</h4>
        <div className="space-y-3">
          {Object.entries(summaryData.risk_levels).map(([level, data]) => (
            <div key={level} className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRiskLevelColor(level)}`}>
                  {level.charAt(0).toUpperCase() + level.slice(1)} Risk
                </span>
                <span className="text-sm text-gray-600">
                  {data.count} customers
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      level === 'low' ? 'bg-green-600' :
                      level === 'medium' ? 'bg-yellow-600' : 'bg-red-600'
                    }`}
                    style={{ width: `${data.percentage}%` }}
                  ></div>
                </div>
                <span className="text-sm font-medium text-gray-900 w-8">
                  {data.percentage}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Revenue Impact & Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Revenue at Risk */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-900">Revenue at Risk</h4>
            <span className="text-xl">💰</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {formatCurrency(summaryData.summary.revenue_at_risk)}
          </p>
          {showTrends && (
            <div className="flex items-center mt-2 text-sm">
              {getTrendIcon(summaryData.trends.revenue_change)}
              <span className={`ml-1 ${getTrendColor(summaryData.trends.revenue_change)}`}>
                {formatCurrency(Math.abs(summaryData.trends.revenue_change))} vs last {timeRange}
              </span>
            </div>
          )}
        </div>

        {/* Industry Comparison */}
        {includeComparison && (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-900">Industry Comparison</h4>
              <span className="text-xl">📊</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Industry Average</span>
                <span className="font-medium">{formatPercentage(summaryData.comparison.industry_avg)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Your Performance</span>
                <span className={`font-medium ${summaryData.comparison.vs_industry < 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {summaryData.comparison.vs_industry < 0 ? '' : '+'}{formatPercentage(summaryData.comparison.vs_industry)} vs industry
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Recent Activity */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Today's Activity</h4>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-lg font-bold text-blue-600">{summaryData.recent_activity.predictions_today}</p>
            <p className="text-xs text-gray-600">Predictions Made</p>
          </div>
          <div>
            <p className="text-lg font-bold text-orange-600">{summaryData.recent_activity.alerts_generated}</p>
            <p className="text-xs text-gray-600">Alerts Generated</p>
          </div>
          <div>
            <p className="text-lg font-bold text-green-600">{summaryData.recent_activity.customers_saved}</p>
            <p className="text-xs text-gray-600">Customers Saved</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChurnSummaryWidget;