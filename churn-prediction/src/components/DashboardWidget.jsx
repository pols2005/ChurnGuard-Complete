import React, { useEffect, useState } from 'react';
import { useDashboard } from '../contexts/DashboardContext';
import { useAuth } from '../contexts/AuthContext';

// Import individual widget components
import ChurnSummaryWidget from './widgets/ChurnSummaryWidget';
import CustomerListWidget from './widgets/CustomerListWidget';
import ChurnTrendWidget from './widgets/ChurnTrendWidget';
import RiskDistributionWidget from './widgets/RiskDistributionWidget';
import ModelPerformanceWidget from './widgets/ModelPerformanceWidget';
import RecentPredictionsWidget from './widgets/RecentPredictionsWidget';
import KPICardsWidget from './widgets/KPICardsWidget';
import ActivityFeedWidget from './widgets/ActivityFeedWidget';
import ExportToolsWidget from './widgets/ExportToolsWidget';
import UserAnalyticsWidget from './widgets/UserAnalyticsWidget';

const DashboardWidget = ({ widget, isEditing, className = '' }) => {
  const { loadWidgetData, getWidgetData, WIDGET_TYPES } = useDashboard();
  const { organization } = useAuth();
  const [refreshing, setRefreshing] = useState(false);

  const widgetData = getWidgetData(widget.id);
  const widgetConfig = WIDGET_TYPES[widget.type];

  // Load data on mount and when config changes
  useEffect(() => {
    if (!isEditing) {
      loadWidgetData(widget.id, widget.type, widget.config);
    }
  }, [widget.id, widget.type, widget.config, isEditing, loadWidgetData]);

  // Handle manual refresh
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadWidgetData(widget.id, widget.type, widget.config);
    } finally {
      setRefreshing(false);
    }
  };

  // Get widget title (custom or default)
  const getWidgetTitle = () => {
    return widget.config?.title || widgetConfig?.name || 'Widget';
  };

  // Render appropriate widget component
  const renderWidgetContent = () => {
    if (isEditing) {
      return (
        <div className="flex items-center justify-center h-full bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg">
          <div className="text-center">
            <div className="text-3xl mb-2">{widgetConfig?.icon}</div>
            <p className="text-sm font-medium text-gray-600">{getWidgetTitle()}</p>
            <p className="text-xs text-gray-500 mt-1">
              {widgetConfig?.description}
            </p>
          </div>
        </div>
      );
    }

    if (widgetData.loading) {
      return <WidgetLoadingState />;
    }

    if (widgetData.error) {
      return (
        <WidgetErrorState 
          error={widgetData.error} 
          onRetry={handleRefresh}
        />
      );
    }

    const commonProps = {
      data: widgetData.data,
      config: widget.config,
      onRefresh: handleRefresh,
      refreshing: refreshing
    };

    switch (widget.type) {
      case 'churn_summary':
        return <ChurnSummaryWidget {...commonProps} />;
      case 'customer_list':
        return <CustomerListWidget {...commonProps} />;
      case 'churn_trend':
        return <ChurnTrendWidget {...commonProps} />;
      case 'risk_distribution':
        return <RiskDistributionWidget {...commonProps} />;
      case 'model_performance':
        return <ModelPerformanceWidget {...commonProps} />;
      case 'recent_predictions':
        return <RecentPredictionsWidget {...commonProps} />;
      case 'kpi_cards':
        return <KPICardsWidget {...commonProps} />;
      case 'activity_feed':
        return <ActivityFeedWidget {...commonProps} />;
      case 'export_tools':
        return <ExportToolsWidget {...commonProps} />;
      case 'user_analytics':
        return <UserAnalyticsWidget {...commonProps} />;
      default:
        return (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500">Unknown widget type: {widget.type}</p>
          </div>
        );
    }
  };

  return (
    <div className={`dashboard-widget bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden ${className}`}>
      {/* Widget Header */}
      {!isEditing && (
        <div className="widget-header px-4 py-3 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-lg">{widgetConfig?.icon}</span>
              <h3 className="text-sm font-medium text-gray-900">
                {getWidgetTitle()}
              </h3>
            </div>
            <div className="flex items-center space-x-1">
              {/* Refresh Button */}
              <button
                onClick={handleRefresh}
                disabled={refreshing || widgetData.loading}
                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 transition-colors"
                title="Refresh Widget"
              >
                <svg 
                  className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>

              {/* Last Updated */}
              {widgetData.lastUpdated && (
                <span className="text-xs text-gray-500">
                  {formatLastUpdated(widgetData.lastUpdated)}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Widget Content */}
      <div className="widget-content flex-1 p-4">
        {renderWidgetContent()}
      </div>

      {/* Widget Footer (if needed) */}
      {!isEditing && organization && (
        <div className="widget-footer px-4 py-2 border-t border-gray-100 bg-gray-50">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>
              Powered by {organization.name}
            </span>
            {widgetConfig?.category && (
              <span className="capitalize">
                {widgetConfig.category}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Loading State Component
const WidgetLoadingState = () => (
  <div className="flex items-center justify-center h-full">
    <div className="text-center">
      <svg className="animate-spin h-8 w-8 text-primary mx-auto" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p className="text-sm text-gray-500 mt-2">Loading widget data...</p>
    </div>
  </div>
);

// Error State Component
const WidgetErrorState = ({ error, onRetry }) => (
  <div className="flex items-center justify-center h-full">
    <div className="text-center">
      <svg className="h-8 w-8 text-red-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p className="text-sm text-gray-600 mt-2">Failed to load widget</p>
      <p className="text-xs text-gray-500 mt-1">{error}</p>
      <button
        onClick={onRetry}
        className="mt-3 px-3 py-1 text-xs bg-primary text-white rounded hover:bg-primary-dark transition-colors"
      >
        Try Again
      </button>
    </div>
  </div>
);

// Helper function to format last updated time
const formatLastUpdated = (timestamp) => {
  const now = new Date();
  const updated = new Date(timestamp);
  const diffInMinutes = Math.floor((now - updated) / (1000 * 60));

  if (diffInMinutes < 1) {
    return 'Just now';
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`;
  } else if (diffInMinutes < 1440) {
    const hours = Math.floor(diffInMinutes / 60);
    return `${hours}h ago`;
  } else {
    const days = Math.floor(diffInMinutes / 1440);
    return `${days}d ago`;
  }
};

export default DashboardWidget;