import React, { useState } from 'react';
import FeatureGate from './FeatureGate';
import { useSubscription } from '../contexts/SubscriptionContext';

const ExportFeature = ({ data }) => {
  const [isExporting, setIsExporting] = useState(false);
  const { incrementUsage } = useSubscription();

  const handleExport = async (format) => {
    setIsExporting(true);
    
    // Simulate export process
    setTimeout(() => {
      const filename = `churn_analysis_${new Date().toISOString().split('T')[0]}.${format}`;
      const exportData = {
        timestamp: new Date().toISOString(),
        format: format,
        data: data || {
          totalCustomers: 6800,
          churnRate: 12.5,
          highRiskCustomers: 247,
          analysis: "Sample churn analysis data"
        }
      };
      
      // Create download
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
        type: format === 'json' ? 'application/json' : 'text/csv' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      // Track usage
      incrementUsage('dataExports', 1);
      setIsExporting(false);
    }, 2000);
  };

  const ExportInterface = () => (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Export Analysis Data
      </h3>
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        Download your churn analysis data in various formats for further processing.
      </p>
      
      <div className="space-y-3">
        <button
          onClick={() => handleExport('json')}
          disabled={isExporting}
          className="w-full flex items-center justify-center px-4 py-3 bg-primary hover:bg-primary/90 disabled:opacity-50 text-white rounded-lg font-medium transition-colors duration-200"
        >
          {isExporting ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"></circle>
                <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" className="opacity-75"></path>
              </svg>
              Exporting...
            </>
          ) : (
            <>
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export as JSON
            </>
          )}
        </button>
        
        <button
          onClick={() => handleExport('csv')}
          disabled={isExporting}
          className="w-full flex items-center justify-center px-4 py-3 border border-primary text-primary hover:bg-primary hover:text-white disabled:opacity-50 rounded-lg font-medium transition-colors duration-200"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export as CSV
        </button>
      </div>
    </div>
  );

  const BasicFallback = () => (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Data Export (Premium Feature)
      </h3>
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        Export your analysis data in multiple formats.
      </p>
      <div className="text-center py-8">
        <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-gray-400 text-sm">Available with Professional plan and above</p>
      </div>
    </div>
  );

  return (
    <div className="max-w-md">
      <FeatureGate 
        feature="advancedAnalytics" 
        requiredTier="professional"
        fallback={<BasicFallback />}
      >
        <ExportInterface />
      </FeatureGate>
    </div>
  );
};

export default ExportFeature;