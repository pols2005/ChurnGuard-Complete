import React, { createContext, useContext, useEffect, useState } from 'react';

const SubscriptionContext = createContext();

export const useSubscription = () => {
  const context = useContext(SubscriptionContext);
  if (!context) {
    throw new Error('useSubscription must be used within a SubscriptionProvider');
  }
  return context;
};

export const SUBSCRIPTION_TIERS = {
  starter: {
    name: 'Starter',
    price: '$29/month',
    features: [
      'Basic theme switching',
      'Organization name display',
      'Standard support',
      'Up to 5 users',
      'Basic analytics'
    ],
    limits: {
      users: 5,
      customColors: false,
      logoUpload: false,
      customCss: false,
      removeChurnGuardBranding: false,
      advancedAnalytics: false
    }
  },
  professional: {
    name: 'Professional',
    price: '$99/month',
    features: [
      'Full theme customization',
      'Logo upload',
      'Custom primary colors',
      'Priority support',
      'Up to 25 users',
      'Advanced analytics',
      'Data export'
    ],
    limits: {
      users: 25,
      customColors: true,
      logoUpload: true,
      customCss: false,
      removeChurnGuardBranding: true,
      advancedAnalytics: true
    }
  },
  enterprise: {
    name: 'Enterprise',
    price: '$299/month',
    features: [
      'Complete white-labeling',
      'Custom CSS injection',
      'Custom domain support',
      'Dedicated support',
      'Unlimited users',
      'API access',
      'Custom integrations'
    ],
    limits: {
      users: Infinity,
      customColors: true,
      logoUpload: true,
      customCss: true,
      removeChurnGuardBranding: true,
      advancedAnalytics: true
    }
  }
};

export const SubscriptionProvider = ({ children }) => {
  const [currentTier, setCurrentTier] = useState('starter');
  const [usage, setUsage] = useState({
    users: 1,
    dataExports: 0,
    apiCalls: 0
  });

  useEffect(() => {
    // Load subscription data from localStorage or API
    const storedTier = localStorage.getItem('churnguard-subscription-tier');
    const storedUsage = localStorage.getItem('churnguard-usage');
    
    if (storedTier && SUBSCRIPTION_TIERS[storedTier]) {
      setCurrentTier(storedTier);
    }
    
    if (storedUsage) {
      try {
        const parsedUsage = JSON.parse(storedUsage);
        setUsage(prev => ({ ...prev, ...parsedUsage }));
      } catch (error) {
        console.error('Failed to parse usage data:', error);
      }
    }
  }, []);

  const hasFeature = (feature) => {
    return SUBSCRIPTION_TIERS[currentTier]?.limits[feature] === true;
  };

  const canUse = (feature, count = 1) => {
    const limit = SUBSCRIPTION_TIERS[currentTier]?.limits[feature];
    if (typeof limit === 'boolean') return limit;
    if (typeof limit === 'number') return usage[feature] + count <= limit;
    return false;
  };

  const incrementUsage = (feature, amount = 1) => {
    setUsage(prev => {
      const newUsage = { ...prev, [feature]: (prev[feature] || 0) + amount };
      localStorage.setItem('churnguard-usage', JSON.stringify(newUsage));
      return newUsage;
    });
  };

  const upgradeTo = (tier) => {
    if (SUBSCRIPTION_TIERS[tier]) {
      setCurrentTier(tier);
      localStorage.setItem('churnguard-subscription-tier', tier);
    }
  };

  const getCurrentTierInfo = () => {
    return SUBSCRIPTION_TIERS[currentTier];
  };

  const getUpgradeOptions = () => {
    const tiers = Object.keys(SUBSCRIPTION_TIERS);
    const currentIndex = tiers.indexOf(currentTier);
    return tiers.slice(currentIndex + 1).map(tier => ({
      tier,
      ...SUBSCRIPTION_TIERS[tier]
    }));
  };

  return (
    <SubscriptionContext.Provider value={{
      currentTier,
      usage,
      hasFeature,
      canUse,
      incrementUsage,
      upgradeTo,
      getCurrentTierInfo,
      getUpgradeOptions,
      SUBSCRIPTION_TIERS
    }}>
      {children}
    </SubscriptionContext.Provider>
  );
};