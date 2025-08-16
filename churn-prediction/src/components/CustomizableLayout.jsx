import React, { useState, useEffect } from 'react';
import FeatureGate from './FeatureGate';
import { useSubscription } from '../contexts/SubscriptionContext';

const CustomizableLayout = ({ children }) => {
  const { hasFeature } = useSubscription();
  const [layoutConfig, setLayoutConfig] = useState({
    columns: 2,
    widgetOrder: ['churn-meter', 'analytics', 'export', 'customer-form'],
    customWidgets: [],
    sidebar: {
      enabled: true,
      position: 'right', // left, right, top, bottom
      width: '300px'
    }
  });

  useEffect(() => {
    // Load layout config from localStorage
    const savedConfig = localStorage.getItem('churnguard-layout-config');
    if (savedConfig) {
      try {
        const parsedConfig = JSON.parse(savedConfig);
        setLayoutConfig(prev => ({ ...prev, ...parsedConfig }));
      } catch (error) {
        console.error('Failed to parse layout config:', error);
      }
    }
  }, []);

  const updateLayout = (newConfig) => {
    const updatedConfig = { ...layoutConfig, ...newConfig };
    setLayoutConfig(updatedConfig);
    localStorage.setItem('churnguard-layout-config', JSON.stringify(updatedConfig));
  };

  const LayoutCustomizer = () => (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 mb-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Layout Customization
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Column Configuration */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Grid Columns
          </label>
          <select
            value={layoutConfig.columns}
            onChange={(e) => updateLayout({ columns: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary focus:border-primary"
          >
            <option value={1}>1 Column</option>
            <option value={2}>2 Columns</option>
            <option value={3}>3 Columns</option>
            <option value={4}>4 Columns</option>
          </select>
        </div>

        {/* Sidebar Position */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Sidebar Position
          </label>
          <select
            value={layoutConfig.sidebar.position}
            onChange={(e) => updateLayout({ 
              sidebar: { ...layoutConfig.sidebar, position: e.target.value } 
            })}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary focus:border-primary"
          >
            <option value="left">Left</option>
            <option value="right">Right</option>
            <option value="top">Top</option>
            <option value="bottom">Bottom</option>
          </select>
        </div>

        {/* Sidebar Toggle */}
        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="sidebar-enabled"
            checked={layoutConfig.sidebar.enabled}
            onChange={(e) => updateLayout({ 
              sidebar: { ...layoutConfig.sidebar, enabled: e.target.checked } 
            })}
            className="w-4 h-4 text-primary focus:ring-primary focus:ring-2"
          />
          <label htmlFor="sidebar-enabled" className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Enable Sidebar
          </label>
        </div>
      </div>

      {/* Layout Preview */}
      <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">Layout Preview:</div>
        <div className="flex items-center space-x-2">
          <div className={`grid gap-1 flex-1`} style={{ gridTemplateColumns: `repeat(${layoutConfig.columns}, minmax(0, 1fr))` }}>
            {Array.from({ length: layoutConfig.columns }).map((_, i) => (
              <div key={i} className="h-4 bg-primary/20 rounded"></div>
            ))}
          </div>
          {layoutConfig.sidebar.enabled && (
            <div className="w-8 h-4 bg-secondary/20 rounded"></div>
          )}
        </div>
      </div>
    </div>
  );

  const EnterpriseLayoutWrapper = ({ children }) => {
    const sidebarClasses = {
      left: 'flex-row',
      right: 'flex-row-reverse',
      top: 'flex-col',
      bottom: 'flex-col-reverse'
    };

    return (
      <div className="w-full">
        <LayoutCustomizer />
        <div className={`flex ${sidebarClasses[layoutConfig.sidebar.position]} gap-6`}>
          <div className={`grid gap-6 flex-1`} style={{ 
            gridTemplateColumns: `repeat(${layoutConfig.columns}, minmax(0, 1fr))` 
          }}>
            {children}
          </div>
          
          {layoutConfig.sidebar.enabled && (
            <div 
              className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700"
              style={{ 
                width: ['left', 'right'].includes(layoutConfig.sidebar.position) 
                  ? layoutConfig.sidebar.width 
                  : '100%',
                height: ['top', 'bottom'].includes(layoutConfig.sidebar.position) 
                  ? '200px' 
                  : 'fit-content'
              }}
            >
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Quick Actions
              </h4>
              <div className="space-y-2">
                <button className="w-full text-left px-3 py-2 text-sm bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors">
                  Export Report
                </button>
                <button className="w-full text-left px-3 py-2 text-sm bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors">
                  Schedule Analysis
                </button>
                <button className="w-full text-left px-3 py-2 text-sm bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors">
                  Customer Alerts
                </button>
                <button className="w-full text-left px-3 py-2 text-sm bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors">
                  API Settings
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const BasicLayoutWrapper = ({ children }) => (
    <div className="space-y-6">
      {children}
    </div>
  );

  return (
    <FeatureGate 
      feature="customCss" 
      requiredTier="enterprise"
      fallback={<BasicLayoutWrapper>{children}</BasicLayoutWrapper>}
    >
      <EnterpriseLayoutWrapper>{children}</EnterpriseLayoutWrapper>
    </FeatureGate>
  );
};

export default CustomizableLayout;