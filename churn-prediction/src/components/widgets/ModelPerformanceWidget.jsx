import React from 'react';

const ModelPerformanceWidget = ({ data, config, onRefresh, refreshing }) => {
  const metrics = config?.metrics || ['accuracy', 'precision', 'recall'];
  const timeRange = config?.timeRange || '30d';

  const mockData = {
    current: {
      accuracy: 0.942,
      precision: 0.889,
      recall: 0.876,
      f1_score: 0.882
    },
    trend: {
      accuracy: 0.011,
      precision: -0.003,
      recall: 0.008,
      f1_score: 0.002
    },
    model_info: {
      name: 'XGBoost Ensemble',
      version: 'v2.1.3',
      last_trained: '2024-01-10T14:30:00Z',
      training_samples: 15420
    }
  };

  const performanceData = data || mockData;

  const getMetricLabel = (metric) => {
    const labels = {
      accuracy: 'Accuracy',
      precision: 'Precision',
      recall: 'Recall',
      f1_score: 'F1 Score'
    };
    return labels[metric] || metric.charAt(0).toUpperCase() + metric.slice(1);
  };

  const getMetricColor = (value) => {
    if (value >= 0.9) return 'text-green-600 bg-green-100';
    if (value >= 0.8) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getTrendIcon = (change) => {
    if (Math.abs(change) < 0.001) {
      return <span className="text-gray-400">→</span>;
    }
    if (change > 0) {
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
      {/* Model Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-blue-900">
              {performanceData.model_info.name}
            </h3>
            <p className="text-xs text-blue-700">
              {performanceData.model_info.version} • Trained on {performanceData.model_info.training_samples} samples
            </p>
          </div>
          <div className="text-2xl">🤖</div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="space-y-3">
        {metrics.map((metric) => {
          const value = performanceData.current[metric];
          const trend = performanceData.trend[metric] || 0;
          
          return (
            <div key={metric} className="bg-white border border-gray-200 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getMetricColor(value)}`}>
                    {getMetricLabel(metric)}
                  </div>
                  <div className="text-lg font-bold text-gray-900">
                    {(value * 100).toFixed(1)}%
                  </div>
                </div>
                
                <div className="flex items-center space-x-1">
                  {getTrendIcon(trend)}
                  <span className="text-sm text-gray-600">
                    {trend > 0 ? '+' : ''}{(trend * 100).toFixed(2)}%
                  </span>
                </div>
              </div>
              
              {/* Progress Bar */}
              <div className="mt-2">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      value >= 0.9 ? 'bg-green-600' :
                      value >= 0.8 ? 'bg-yellow-600' : 'bg-red-600'
                    }`}
                    style={{ width: `${value * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Additional Info */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="font-medium text-gray-900">Last Updated</div>
          <div className="text-gray-600">
            {new Date(performanceData.model_info.last_trained).toLocaleDateString()}
          </div>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="font-medium text-gray-900">Eval Period</div>
          <div className="text-gray-600">{timeRange}</div>
        </div>
      </div>
    </div>
  );
};

export default ModelPerformanceWidget;