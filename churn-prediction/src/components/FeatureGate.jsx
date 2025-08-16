import React, { useState } from 'react';
import { useSubscription } from '../contexts/SubscriptionContext';

const FeatureGate = ({ 
  feature, 
  children, 
  fallback, 
  showUpgradePrompt = true,
  requiredTier = null 
}) => {
  const { hasFeature, currentTier, getUpgradeOptions } = useSubscription();
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  
  const hasAccess = hasFeature(feature);
  const upgradeOptions = getUpgradeOptions();

  if (hasAccess) {
    return children;
  }

  if (fallback && !showUpgradePrompt) {
    return fallback;
  }

  const UpgradePrompt = () => (
    <div className="relative">
      <div className="absolute inset-0 bg-gradient-to-r from-gray-300/50 to-gray-400/50 dark:from-gray-700/50 dark:to-gray-800/50 backdrop-blur-sm rounded-lg flex items-center justify-center">
        <div className="text-center p-6">
          <div className="mb-3">
            <svg className="w-8 h-8 text-primary mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Premium Feature</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            Upgrade to {requiredTier || 'professional'} to unlock this feature
          </p>
          <button
            onClick={() => setShowUpgradeModal(true)}
            className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg text-sm font-medium transition-colors duration-200"
          >
            Upgrade Now
          </button>
        </div>
      </div>
      <div className="opacity-30 pointer-events-none">
        {fallback || children}
      </div>
      
      {showUpgradeModal && (
        <UpgradeModal 
          onClose={() => setShowUpgradeModal(false)}
          upgradeOptions={upgradeOptions}
          currentTier={currentTier}
        />
      )}
    </div>
  );

  return <UpgradePrompt />;
};

const UpgradeModal = ({ onClose, upgradeOptions, currentTier }) => {
  const { upgradeTo } = useSubscription();

  const handleUpgrade = (tier) => {
    upgradeTo(tier);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Upgrade Your Plan
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        <div className="p-6">
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            You're currently on the <span className="font-semibold capitalize">{currentTier}</span> plan. 
            Choose a plan below to unlock more features:
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {upgradeOptions.map((option) => (
              <div 
                key={option.tier} 
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:border-primary transition-colors duration-200"
              >
                <div className="text-center mb-4">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                    {option.name}
                  </h3>
                  <p className="text-3xl font-bold text-primary mb-1">
                    {option.price}
                  </p>
                </div>
                
                <ul className="space-y-2 mb-6">
                  {option.features.slice(0, 5).map((feature, index) => (
                    <li key={index} className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                      <svg className="w-4 h-4 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>
                
                <button
                  onClick={() => handleUpgrade(option.tier)}
                  className="w-full px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg font-medium transition-colors duration-200"
                >
                  Upgrade to {option.name}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeatureGate;