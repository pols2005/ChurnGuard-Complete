import React, { useState, useEffect } from 'react';

const PerformanceMonitor = () => {
  const [metrics, setMetrics] = useState({
    loadTime: 0,
    renderTime: 0,
    memoryUsage: 0,
    apiResponseTime: 0,
    themeSwitch: 0,
    fps: 0
  });

  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Monitor performance metrics
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'navigation') {
          setMetrics(prev => ({
            ...prev,
            loadTime: entry.loadEventEnd - entry.loadEventStart
          }));
        }
        
        if (entry.entryType === 'measure') {
          if (entry.name.includes('theme-switch')) {
            setMetrics(prev => ({
              ...prev,
              themeSwitch: entry.duration
            }));
          }
        }
      }
    });

    try {
      observer.observe({ entryTypes: ['navigation', 'measure'] });
    } catch (e) {
      // Fallback for browsers that don't support all entry types
      console.log('Performance Observer not fully supported');
    }

    // Mock some performance data
    const updateMetrics = () => {
      setMetrics(prev => ({
        ...prev,
        renderTime: performance.now() % 100,
        memoryUsage: (performance.memory?.usedJSHeapSize || Math.random() * 50000000) / 1048576, // Convert to MB
        apiResponseTime: 150 + Math.random() * 100,
        fps: 55 + Math.random() * 5
      }));
    };

    const interval = setInterval(updateMetrics, 2000);
    updateMetrics();

    return () => {
      clearInterval(interval);
      observer.disconnect();
    };
  }, []);

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className="fixed bottom-4 right-4 z-40 p-2 bg-primary hover:bg-primary/90 text-white rounded-full shadow-lg transition-colors duration-200"
        title="Show Performance Monitor"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 00-2-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      </button>
    );
  }

  const getMetricColor = (value, thresholds) => {
    if (value <= thresholds.good) return 'text-green-600';
    if (value <= thresholds.warning) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="fixed bottom-4 right-4 z-40 bg-white dark:bg-gray-800 rounded-lg p-4 shadow-2xl border border-gray-200 dark:border-gray-700 min-w-80">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Performance Monitor
        </h3>
        <button
          onClick={() => setIsVisible(false)}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div className="space-y-2">
        {/* Load Time */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Load Time:</span>
          <span className={`text-xs font-mono ${getMetricColor(metrics.loadTime, { good: 100, warning: 300 })}`}>
            {metrics.loadTime.toFixed(1)}ms
          </span>
        </div>
        
        {/* Theme Switch Performance */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Theme Switch:</span>
          <span className={`text-xs font-mono ${getMetricColor(metrics.themeSwitch, { good: 100, warning: 200 })}`}>
            {metrics.themeSwitch.toFixed(1)}ms
          </span>
        </div>
        
        {/* Memory Usage */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Memory:</span>
          <span className={`text-xs font-mono ${getMetricColor(metrics.memoryUsage, { good: 50, warning: 100 })}`}>
            {metrics.memoryUsage.toFixed(1)}MB
          </span>
        </div>
        
        {/* API Response Time */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">API Response:</span>
          <span className={`text-xs font-mono ${getMetricColor(metrics.apiResponseTime, { good: 200, warning: 500 })}`}>
            {metrics.apiResponseTime.toFixed(0)}ms
          </span>
        </div>
        
        {/* FPS */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">FPS:</span>
          <span className={`text-xs font-mono ${getMetricColor(60 - metrics.fps, { good: 10, warning: 20 })}`}>
            {metrics.fps.toFixed(0)}
          </span>
        </div>
      </div>
      
      {/* Performance Status */}
      <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            metrics.themeSwitch < 100 && metrics.memoryUsage < 50 && metrics.apiResponseTime < 300 
              ? 'bg-green-500' 
              : metrics.themeSwitch < 200 && metrics.memoryUsage < 100 && metrics.apiResponseTime < 500
              ? 'bg-yellow-500'
              : 'bg-red-500'
          }`} />
          <span className="text-xs text-gray-600 dark:text-gray-400">
            Performance: {
              metrics.themeSwitch < 100 && metrics.memoryUsage < 50 && metrics.apiResponseTime < 300 
                ? 'Excellent' 
                : metrics.themeSwitch < 200 && metrics.memoryUsage < 100 && metrics.apiResponseTime < 500
                ? 'Good'
                : 'Needs Optimization'
            }
          </span>
        </div>
      </div>
    </div>
  );
};

export default PerformanceMonitor;