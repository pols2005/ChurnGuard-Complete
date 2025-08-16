import React from 'react';
import { useSubscription } from '../contexts/SubscriptionContext';

const UsageDashboard = () => {
  const { currentTier, usage, getCurrentTierInfo } = useSubscription();
  const tierInfo = getCurrentTierInfo();

  const getUsagePercentage = (used, limit) => {
    if (limit === Infinity) return 0;
    return Math.min((used / limit) * 100, 100);
  };

  const getUsageColor = (percentage) => {
    if (percentage >= 90) return 'text-red-600 bg-red-100 dark:bg-red-900/20';
    if (percentage >= 75) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20';
    return 'text-green-600 bg-green-100 dark:bg-green-900/20';
  };

  const formatLimit = (limit) => {
    if (limit === Infinity) return 'Unlimited';
    return limit.toLocaleString();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Usage & Limits
        </h3>
        <div className="px-3 py-1 bg-primary/10 text-primary text-sm font-medium rounded-full capitalize">
          {currentTier} Plan
        </div>
      </div>

      <div className="space-y-4">
        {/* Users */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Users</span>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {usage.users} / {formatLimit(tierInfo.limits.users)}
            </span>
          </div>
          {tierInfo.limits.users !== Infinity && (
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-primary h-2 rounded-full transition-all duration-300" 
                style={{ width: `${getUsagePercentage(usage.users, tierInfo.limits.users)}%` }}
              />
            </div>
          )}
        </div>

        {/* Data Exports */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Data Exports (This Month)</span>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {usage.dataExports || 0}
            </span>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {tierInfo.limits.advancedAnalytics ? 'Unlimited exports available' : 'Upgrade to Professional for data export'}
          </div>
        </div>

        {/* Feature Status */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Available Features</h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Logo Upload</span>
              <div className={`px-2 py-1 rounded-full text-xs ${tierInfo.limits.logoUpload ? 'text-green-600 bg-green-100 dark:bg-green-900/20' : 'text-gray-500 bg-gray-100 dark:bg-gray-700'}`}>
                {tierInfo.limits.logoUpload ? 'Available' : 'Locked'}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Custom Colors</span>
              <div className={`px-2 py-1 rounded-full text-xs ${tierInfo.limits.customColors ? 'text-green-600 bg-green-100 dark:bg-green-900/20' : 'text-gray-500 bg-gray-100 dark:bg-gray-700'}`}>
                {tierInfo.limits.customColors ? 'Available' : 'Locked'}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Custom CSS</span>
              <div className={`px-2 py-1 rounded-full text-xs ${tierInfo.limits.customCss ? 'text-green-600 bg-green-100 dark:bg-green-900/20' : 'text-gray-500 bg-gray-100 dark:bg-gray-700'}`}>
                {tierInfo.limits.customCss ? 'Available' : 'Locked'}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Advanced Analytics</span>
              <div className={`px-2 py-1 rounded-full text-xs ${tierInfo.limits.advancedAnalytics ? 'text-green-600 bg-green-100 dark:bg-green-900/20' : 'text-gray-500 bg-gray-100 dark:bg-gray-700'}`}>
                {tierInfo.limits.advancedAnalytics ? 'Available' : 'Locked'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UsageDashboard;