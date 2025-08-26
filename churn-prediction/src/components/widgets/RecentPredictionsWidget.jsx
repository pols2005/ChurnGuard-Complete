import React from 'react';

const RecentPredictionsWidget = ({ data, config, onRefresh, refreshing }) => {
  const limit = config?.limit || 20;
  const showConfidence = config?.showConfidence !== false;

  const mockData = {
    predictions: [
      {
        id: 'pred_001',
        customer_name: 'John Smith',
        probability: 0.89,
        risk_level: 'high',
        predicted_at: '2024-01-15T10:30:00Z',
        model: 'XGBoost v2.1'
      },
      {
        id: 'pred_002',
        customer_name: 'Sarah Johnson',
        probability: 0.72,
        risk_level: 'high',
        predicted_at: '2024-01-15T09:15:00Z',
        model: 'XGBoost v2.1'
      },
      {
        id: 'pred_003',
        customer_name: 'Mike Davis',
        probability: 0.45,
        risk_level: 'medium',
        predicted_at: '2024-01-15T08:45:00Z',
        model: 'Ensemble v1.2'
      }
    ]
  };

  const predictionData = data || mockData;

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="h-full">
      <h3 className="text-sm font-medium text-gray-900 mb-4">
        Recent Predictions
      </h3>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {predictionData.predictions.slice(0, limit).map((prediction) => (
          <div key={prediction.id} className="bg-white border border-gray-200 rounded p-3">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">
                  {prediction.customer_name}
                </div>
                <div className="flex items-center space-x-2 mt-1">
                  <span className={`px-2 py-0.5 text-xs rounded-full ${getRiskColor(prediction.risk_level)}`}>
                    {prediction.risk_level}
                  </span>
                  <span className="text-xs text-gray-500">
                    {prediction.model}
                  </span>
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-lg font-bold text-gray-900">
                  {(prediction.probability * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500">
                  {formatTime(prediction.predicted_at)}
                </div>
              </div>
            </div>
            
            {showConfidence && (
              <div className="mt-2">
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span>Confidence</span>
                  <span>{(prediction.probability * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1">
                  <div
                    className="bg-primary rounded-full h-1"
                    style={{ width: `${prediction.probability * 100}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {predictionData.predictions.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <div className="text-2xl mb-2">🔮</div>
          <div className="text-sm">No recent predictions</div>
        </div>
      )}
    </div>
  );
};

export default RecentPredictionsWidget;