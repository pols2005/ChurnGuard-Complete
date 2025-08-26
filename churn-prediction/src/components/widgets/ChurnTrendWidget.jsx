import React from 'react';

const ChurnTrendWidget = ({ data, config, onRefresh, refreshing }) => {
  const timeRange = config?.timeRange || '6m';
  const chartType = config?.chartType || 'line';
  const showPredictions = config?.showPredictions !== false;

  // Mock data for demonstration
  const mockData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    churnRate: [15.2, 18.1, 16.8, 19.5, 17.3, 18.5],
    predictions: [20.1, 19.8, 18.9, 18.2, 17.8, 17.5],
    customerCount: [1200, 1180, 1165, 1142, 1158, 1250]
  };

  const trendData = data || mockData;

  return (
    <div className="h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-900">
          Churn Trend - Last {timeRange}
        </h3>
        <div className="flex items-center space-x-2 text-xs text-gray-500">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-500 rounded-full mr-1"></div>
            <span>Actual</span>
          </div>
          {showPredictions && (
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-500 rounded-full mr-1"></div>
              <span>Predicted</span>
            </div>
          )}
        </div>
      </div>

      {/* Simple Chart Representation */}
      <div className="h-48 bg-gray-50 rounded-lg p-4 flex items-end justify-around">
        {trendData.labels.map((label, index) => (
          <div key={label} className="flex flex-col items-center space-y-2">
            <div className="flex items-end space-x-1">
              {/* Actual churn rate bar */}
              <div 
                className="bg-red-500 rounded-t w-6"
                style={{ height: `${(trendData.churnRate[index] / 25) * 120}px` }}
                title={`${label}: ${trendData.churnRate[index]}%`}
              ></div>
              
              {/* Predicted churn rate bar */}
              {showPredictions && (
                <div 
                  className="bg-blue-400 rounded-t w-6 opacity-70"
                  style={{ height: `${(trendData.predictions[index] / 25) * 120}px` }}
                  title={`${label} Predicted: ${trendData.predictions[index]}%`}
                ></div>
              )}
            </div>
            
            {/* Month label */}
            <span className="text-xs text-gray-600">{label}</span>
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div className="bg-white border border-gray-200 rounded p-3">
          <div className="text-lg font-bold text-red-600">
            {trendData.churnRate[trendData.churnRate.length - 1]}%
          </div>
          <div className="text-xs text-gray-600">Current Rate</div>
        </div>
        <div className="bg-white border border-gray-200 rounded p-3">
          <div className="text-lg font-bold text-blue-600">
            {(trendData.churnRate.reduce((a, b) => a + b, 0) / trendData.churnRate.length).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-600">Average</div>
        </div>
        <div className="bg-white border border-gray-200 rounded p-3">
          <div className="text-lg font-bold text-green-600">
            {showPredictions ? trendData.predictions[trendData.predictions.length - 1] + '%' : 'N/A'}
          </div>
          <div className="text-xs text-gray-600">Forecast</div>
        </div>
      </div>
    </div>
  );
};

export default ChurnTrendWidget;