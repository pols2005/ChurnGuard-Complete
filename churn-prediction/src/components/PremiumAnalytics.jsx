import React from 'react';
import FeatureGate from './FeatureGate';

const PremiumAnalytics = ({ data }) => {
  const mockAdvancedData = {
    cohortAnalysis: [
      { month: 'Jan', retention: 95, churn: 5 },
      { month: 'Feb', retention: 92, churn: 8 },
      { month: 'Mar', retention: 89, churn: 11 },
      { month: 'Apr', retention: 87, churn: 13 },
      { month: 'May', retention: 85, churn: 15 },
      { month: 'Jun', retention: 83, churn: 17 }
    ],
    segmentAnalysis: [
      { segment: 'High Value', customers: 1250, churnRate: 8.2 },
      { segment: 'Medium Value', customers: 3450, churnRate: 12.5 },
      { segment: 'Low Value', customers: 2100, churnRate: 18.7 }
    ]
  };

  const BasicAnalytics = () => (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Basic Analytics
      </h3>
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="text-2xl font-bold text-primary">12.5%</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Overall Churn Rate</div>
        </div>
        <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="text-2xl font-bold text-secondary">6,800</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Total Customers</div>
        </div>
      </div>
    </div>
  );

  const AdvancedAnalytics = () => (
    <div className="space-y-6">
      {/* Cohort Analysis */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Cohort Retention Analysis
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-2 text-gray-600 dark:text-gray-400">Month</th>
                <th className="text-right py-2 text-gray-600 dark:text-gray-400">Retention %</th>
                <th className="text-right py-2 text-gray-600 dark:text-gray-400">Churn %</th>
              </tr>
            </thead>
            <tbody>
              {mockAdvancedData.cohortAnalysis.map((item, index) => (
                <tr key={index} className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 text-gray-900 dark:text-gray-100">{item.month}</td>
                  <td className="text-right py-2 text-green-600">{item.retention}%</td>
                  <td className="text-right py-2 text-red-600">{item.churn}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Customer Segmentation */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Customer Segmentation Analysis
        </h3>
        <div className="space-y-3">
          {mockAdvancedData.segmentAnalysis.map((segment, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div>
                <div className="font-medium text-gray-900 dark:text-gray-100">{segment.segment}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">{segment.customers.toLocaleString()} customers</div>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold" style={{ 
                  color: segment.churnRate < 10 ? '#10B981' : segment.churnRate < 15 ? '#F59E0B' : '#EF4444' 
                }}>
                  {segment.churnRate}%
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">churn rate</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Trend Analysis */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Churn Prediction Insights
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 rounded-lg">
            <div className="text-2xl font-bold text-red-600">247</div>
            <div className="text-sm text-red-700 dark:text-red-300">High Risk Customers</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">1,156</div>
            <div className="text-sm text-yellow-700 dark:text-yellow-300">Medium Risk Customers</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg">
            <div className="text-2xl font-bold text-green-600">5,397</div>
            <div className="text-sm text-green-700 dark:text-green-300">Low Risk Customers</div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-6xl w-full mx-auto mt-10">
      <FeatureGate 
        feature="advancedAnalytics" 
        requiredTier="professional"
        fallback={<BasicAnalytics />}
      >
        <AdvancedAnalytics />
      </FeatureGate>
    </div>
  );
};

export default PremiumAnalytics;