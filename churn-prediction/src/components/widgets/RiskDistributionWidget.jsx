import React from 'react';

const RiskDistributionWidget = ({ data, config, onRefresh, refreshing }) => {
  const chartType = config?.chartType || 'pie';
  const showPercentages = config?.showPercentages !== false;

  const mockData = {
    low: { count: 825, percentage: 66, color: '#10B981' },
    medium: { count: 336, percentage: 27, color: '#F59E0B' },
    high: { count: 89, percentage: 7, color: '#EF4444' }
  };

  const riskData = data || mockData;
  const total = Object.values(riskData).reduce((sum, item) => sum + item.count, 0);

  return (
    <div className="h-full">
      <h3 className="text-sm font-medium text-gray-900 mb-4">
        Risk Distribution
      </h3>

      {/* Simple Pie Chart Representation */}
      <div className="flex items-center justify-center mb-6">
        <div className="relative w-32 h-32">
          <svg className="w-32 h-32" viewBox="0 0 42 42">
            <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#e5e7eb" strokeWidth="3"/>
            <circle
              cx="21" cy="21" r="15.915"
              fill="transparent"
              stroke={riskData.low.color}
              strokeWidth="3"
              strokeDasharray={`${riskData.low.percentage} ${100 - riskData.low.percentage}`}
              strokeDashoffset="25"
            />
            <circle
              cx="21" cy="21" r="15.915"
              fill="transparent"
              stroke={riskData.medium.color}
              strokeWidth="3"
              strokeDasharray={`${riskData.medium.percentage} ${100 - riskData.medium.percentage}`}
              strokeDashoffset={`${25 - riskData.low.percentage}`}
            />
            <circle
              cx="21" cy="21" r="15.915"
              fill="transparent"
              stroke={riskData.high.color}
              strokeWidth="3"
              strokeDasharray={`${riskData.high.percentage} ${100 - riskData.high.percentage}`}
              strokeDashoffset={`${25 - riskData.low.percentage - riskData.medium.percentage}`}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-lg font-bold text-gray-900">{total}</div>
              <div className="text-xs text-gray-600">Total</div>
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="space-y-3">
        {Object.entries(riskData).map(([level, data]) => (
          <div key={level} className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: data.color }}
              ></div>
              <span className="text-sm font-medium text-gray-900 capitalize">
                {level} Risk
              </span>
            </div>
            <div className="text-right">
              <div className="text-sm font-bold text-gray-900">{data.count}</div>
              {showPercentages && (
                <div className="text-xs text-gray-600">{data.percentage}%</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RiskDistributionWidget;