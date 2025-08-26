import React from 'react';

const KPICardsWidget = ({ data, config, onRefresh, refreshing }) => {
  // Default KPI configuration
  const defaultCards = ['total_customers', 'churn_rate', 'high_risk', 'model_accuracy'];
  const activeCards = config?.cards || defaultCards;

  // Mock data structure - in production this would come from the API
  const defaultData = {
    total_customers: { value: 1250, change: 12, trend: 'up' },
    churn_rate: { value: 18.5, change: -2.3, trend: 'down' },
    high_risk: { value: 89, change: 5, trend: 'up' },
    model_accuracy: { value: 94.2, change: 1.1, trend: 'up' },
    predictions_made: { value: 542, change: 23, trend: 'up' },
    active_users: { value: 45, change: 3, trend: 'up' },
    revenue_at_risk: { value: 125000, change: -8000, trend: 'down' },
    avg_customer_value: { value: 2850, change: 120, trend: 'up' }
  };

  const kpiData = data || defaultData;

  const getKPIConfig = (cardType) => {
    const configs = {
      total_customers: {
        label: 'Total Customers',
        icon: '👥',
        format: 'number',
        suffix: '',
        color: 'blue'
      },
      churn_rate: {
        label: 'Churn Rate',
        icon: '📉',
        format: 'percentage',
        suffix: '%',
        color: 'red'
      },
      high_risk: {
        label: 'High Risk',
        icon: '⚠️',
        format: 'number',
        suffix: ' customers',
        color: 'orange'
      },
      model_accuracy: {
        label: 'Model Accuracy',
        icon: '🎯',
        format: 'percentage',
        suffix: '%',
        color: 'green'
      },
      predictions_made: {
        label: 'Predictions Made',
        icon: '🔮',
        format: 'number',
        suffix: '',
        color: 'purple'
      },
      active_users: {
        label: 'Active Users',
        icon: '👤',
        format: 'number',
        suffix: '',
        color: 'indigo'
      },
      revenue_at_risk: {
        label: 'Revenue at Risk',
        icon: '💰',
        format: 'currency',
        suffix: '',
        color: 'red'
      },
      avg_customer_value: {
        label: 'Avg Customer Value',
        icon: '💎',
        format: 'currency',
        suffix: '',
        color: 'green'
      }
    };
    
    return configs[cardType] || configs.total_customers;
  };

  const formatValue = (value, format) => {
    if (value === null || value === undefined) return '--';
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(value);
      case 'percentage':
        return value.toFixed(1);
      case 'number':
        return new Intl.NumberFormat('en-US').format(value);
      default:
        return value;
    }
  };

  const getColorClasses = (color) => {
    const colors = {
      blue: 'bg-blue-50 text-blue-600',
      red: 'bg-red-50 text-red-600',
      green: 'bg-green-50 text-green-600',
      orange: 'bg-orange-50 text-orange-600',
      purple: 'bg-purple-50 text-purple-600',
      indigo: 'bg-indigo-50 text-indigo-600'
    };
    return colors[color] || colors.blue;
  };

  const getTrendIcon = (trend, change) => {
    if (change === 0) {
      return <span className="text-gray-400">→</span>;
    }
    
    if (trend === 'up') {
      return (
        <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l9.2-9.2M17 17V7H7" />
        </svg>
      );
    } else {
      return (
        <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-9.2 9.2M7 7v10h10" />
        </svg>
      );
    }
  };

  const getTrendColor = (trend) => {
    return trend === 'up' ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className="h-full">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 h-full">
        {activeCards.map((cardType) => {
          const cardConfig = getKPIConfig(cardType);
          const cardData = kpiData[cardType] || { value: 0, change: 0, trend: 'up' };
          
          return (
            <div
              key={cardType}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className={`inline-flex items-center justify-center p-2 rounded-lg ${getColorClasses(cardConfig.color)}`}>
                  <span className="text-lg">{cardConfig.icon}</span>
                </div>
                <div className="flex items-center space-x-1">
                  {getTrendIcon(cardData.trend, cardData.change)}
                </div>
              </div>

              {/* Value */}
              <div className="mt-4">
                <div className="flex items-baseline">
                  <span className="text-2xl font-bold text-gray-900">
                    {formatValue(cardData.value, cardConfig.format)}
                  </span>
                  <span className="text-sm text-gray-500 ml-1">
                    {cardConfig.suffix}
                  </span>
                </div>
                
                {/* Change */}
                {cardData.change !== 0 && (
                  <div className={`flex items-center mt-1 text-sm ${getTrendColor(cardData.trend)}`}>
                    <span>
                      {cardData.change > 0 ? '+' : ''}{formatValue(Math.abs(cardData.change), cardConfig.format)}
                      {cardConfig.format === 'percentage' ? '%' : ''}
                    </span>
                    <span className="text-gray-500 ml-1">vs last period</span>
                  </div>
                )}
              </div>

              {/* Label */}
              <div className="mt-2">
                <p className="text-sm font-medium text-gray-600">
                  {cardConfig.label}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Additional Stats Row (if space allows) */}
      {activeCards.length <= 4 && (
        <div className="mt-4 grid grid-cols-1 lg:grid-cols-3 gap-4 text-sm text-gray-600">
          <div className="flex justify-between">
            <span>Last updated:</span>
            <span>
              {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Data source:</span>
            <span>ML Pipeline</span>
          </div>
          <div className="flex justify-between">
            <span>Refresh rate:</span>
            <span>5 minutes</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default KPICardsWidget;