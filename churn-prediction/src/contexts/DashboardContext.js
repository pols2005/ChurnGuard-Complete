import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useAuth } from './AuthContext';

const DashboardContext = createContext();

export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within a DashboardProvider');
  }
  return context;
};

// Default widget configurations
export const WIDGET_TYPES = {
  CHURN_SUMMARY: {
    id: 'churn_summary',
    name: 'Churn Summary',
    description: 'Overview of churn statistics',
    icon: '📊',
    defaultSize: { w: 6, h: 4 },
    category: 'analytics',
    permissions: ['analytics.read']
  },
  CUSTOMER_LIST: {
    id: 'customer_list',
    name: 'Customer List',
    description: 'Recent customers and their churn risk',
    icon: '👥',
    defaultSize: { w: 12, h: 6 },
    category: 'customers',
    permissions: ['customer.read']
  },
  CHURN_TREND: {
    id: 'churn_trend',
    name: 'Churn Trend Chart',
    description: 'Churn rate over time',
    icon: '📈',
    defaultSize: { w: 8, h: 5 },
    category: 'analytics',
    permissions: ['analytics.read']
  },
  RISK_DISTRIBUTION: {
    id: 'risk_distribution',
    name: 'Risk Distribution',
    description: 'Distribution of customer risk levels',
    icon: '🎯',
    defaultSize: { w: 6, h: 5 },
    category: 'analytics',
    permissions: ['analytics.read']
  },
  MODEL_PERFORMANCE: {
    id: 'model_performance',
    name: 'Model Performance',
    description: 'ML model accuracy and metrics',
    icon: '🤖',
    defaultSize: { w: 8, h: 4 },
    category: 'models',
    permissions: ['analytics.read']
  },
  RECENT_PREDICTIONS: {
    id: 'recent_predictions',
    name: 'Recent Predictions',
    description: 'Latest prediction results',
    icon: '🔮',
    defaultSize: { w: 6, h: 6 },
    category: 'predictions',
    permissions: ['prediction.read']
  },
  KPI_CARDS: {
    id: 'kpi_cards',
    name: 'KPI Cards',
    description: 'Key performance indicators',
    icon: '📋',
    defaultSize: { w: 12, h: 3 },
    category: 'analytics',
    permissions: ['analytics.read']
  },
  ACTIVITY_FEED: {
    id: 'activity_feed',
    name: 'Activity Feed',
    description: 'Recent system activity',
    icon: '📡',
    defaultSize: { w: 4, h: 8 },
    category: 'system',
    permissions: ['audit.read']
  },
  EXPORT_TOOLS: {
    id: 'export_tools',
    name: 'Export Tools',
    description: 'Data export and download options',
    icon: '📤',
    defaultSize: { w: 4, h: 3 },
    category: 'tools',
    permissions: ['export.create']
  },
  USER_ANALYTICS: {
    id: 'user_analytics',
    name: 'User Analytics',
    description: 'User engagement and usage stats',
    icon: '👤',
    defaultSize: { w: 6, h: 4 },
    category: 'users',
    permissions: ['user.read', 'analytics.read']
  }
};

// Default dashboard layouts for different roles
const DEFAULT_LAYOUTS = {
  admin: [
    { i: 'kpi_cards', x: 0, y: 0, w: 12, h: 3 },
    { i: 'churn_summary', x: 0, y: 3, w: 6, h: 4 },
    { i: 'churn_trend', x: 6, y: 3, w: 6, h: 4 },
    { i: 'customer_list', x: 0, y: 7, w: 8, h: 6 },
    { i: 'activity_feed', x: 8, y: 7, w: 4, h: 6 }
  ],
  manager: [
    { i: 'kpi_cards', x: 0, y: 0, w: 12, h: 3 },
    { i: 'churn_summary', x: 0, y: 3, w: 6, h: 4 },
    { i: 'risk_distribution', x: 6, y: 3, w: 6, h: 4 },
    { i: 'customer_list', x: 0, y: 7, w: 12, h: 6 }
  ],
  user: [
    { i: 'churn_summary', x: 0, y: 0, w: 6, h: 4 },
    { i: 'recent_predictions', x: 6, y: 0, w: 6, h: 4 },
    { i: 'customer_list', x: 0, y: 4, w: 12, h: 6 }
  ],
  viewer: [
    { i: 'churn_summary', x: 0, y: 0, w: 12, h: 4 },
    { i: 'churn_trend', x: 0, y: 4, w: 12, h: 5 }
  ]
};

export const DashboardProvider = ({ children }) => {
  const { user, organization, hasPermission, apiRequest } = useAuth();
  const [dashboards, setDashboards] = useState([]);
  const [currentDashboard, setCurrentDashboard] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [widgetData, setWidgetData] = useState({});
  const [loading, setLoading] = useState(false);

  // Get available widgets based on user permissions
  const getAvailableWidgets = useCallback(() => {
    return Object.values(WIDGET_TYPES).filter(widget => {
      if (!widget.permissions || widget.permissions.length === 0) return true;
      return widget.permissions.some(permission => hasPermission(permission));
    });
  }, [hasPermission]);

  // Load dashboards for current user/organization
  const loadDashboards = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiRequest('/api/v2/dashboards');
      setDashboards(response.dashboards || []);
      
      // Set default dashboard if none exists
      if (response.dashboards.length === 0) {
        const defaultDashboard = createDefaultDashboard();
        setCurrentDashboard(defaultDashboard);
      } else {
        setCurrentDashboard(response.dashboards[0]);
      }
    } catch (error) {
      console.error('Failed to load dashboards:', error);
      // Fallback to default dashboard
      const defaultDashboard = createDefaultDashboard();
      setCurrentDashboard(defaultDashboard);
      setDashboards([defaultDashboard]);
    } finally {
      setLoading(false);
    }
  }, [apiRequest, user]);

  // Create default dashboard based on user role
  const createDefaultDashboard = useCallback(() => {
    const userRole = user?.role || 'viewer';
    const availableWidgets = getAvailableWidgets();
    const defaultLayout = DEFAULT_LAYOUTS[userRole] || DEFAULT_LAYOUTS.viewer;
    
    // Filter layout to only include widgets user has permission for
    const filteredLayout = defaultLayout.filter(item => 
      availableWidgets.some(widget => widget.id === item.i)
    );

    return {
      id: 'default',
      name: 'My Dashboard',
      description: 'Default dashboard',
      layout: filteredLayout,
      widgets: filteredLayout.map(item => ({
        id: item.i,
        type: item.i,
        config: getDefaultWidgetConfig(item.i)
      })),
      isDefault: true,
      created_at: new Date().toISOString()
    };
  }, [user, getAvailableWidgets]);

  // Get default configuration for a widget type
  const getDefaultWidgetConfig = (widgetType) => {
    const configs = {
      churn_summary: {
        showTrends: true,
        timeRange: '30d',
        includeComparison: true
      },
      customer_list: {
        pageSize: 10,
        sortBy: 'churn_probability',
        sortOrder: 'desc',
        showRiskLevel: true
      },
      churn_trend: {
        timeRange: '6m',
        chartType: 'line',
        showPredictions: true
      },
      risk_distribution: {
        chartType: 'pie',
        showPercentages: true
      },
      model_performance: {
        metrics: ['accuracy', 'precision', 'recall'],
        timeRange: '30d'
      },
      recent_predictions: {
        limit: 20,
        showConfidence: true
      },
      kpi_cards: {
        cards: ['total_customers', 'churn_rate', 'high_risk', 'model_accuracy']
      },
      activity_feed: {
        limit: 50,
        showUserActions: true
      },
      export_tools: {
        formats: ['csv', 'xlsx', 'pdf']
      },
      user_analytics: {
        timeRange: '7d',
        metrics: ['active_users', 'predictions_made', 'dashboards_viewed']
      }
    };
    
    return configs[widgetType] || {};
  };

  // Save dashboard
  const saveDashboard = useCallback(async (dashboard) => {
    try {
      const response = await apiRequest('/api/v2/dashboards', {
        method: dashboard.id && dashboard.id !== 'default' ? 'PUT' : 'POST',
        body: JSON.stringify({
          ...dashboard,
          id: dashboard.id === 'default' ? undefined : dashboard.id
        })
      });

      if (response.success) {
        const savedDashboard = response.dashboard;
        setDashboards(prev => {
          const existing = prev.find(d => d.id === savedDashboard.id);
          if (existing) {
            return prev.map(d => d.id === savedDashboard.id ? savedDashboard : d);
          }
          return [...prev, savedDashboard];
        });
        
        setCurrentDashboard(savedDashboard);
        return { success: true, dashboard: savedDashboard };
      }
      
      throw new Error(response.error || 'Failed to save dashboard');
    } catch (error) {
      console.error('Save dashboard error:', error);
      return { success: false, error: error.message };
    }
  }, [apiRequest]);

  // Delete dashboard
  const deleteDashboard = useCallback(async (dashboardId) => {
    try {
      const response = await apiRequest(`/api/v2/dashboards/${dashboardId}`, {
        method: 'DELETE'
      });

      if (response.success) {
        setDashboards(prev => prev.filter(d => d.id !== dashboardId));
        
        // Switch to default dashboard if current was deleted
        if (currentDashboard?.id === dashboardId) {
          const remaining = dashboards.filter(d => d.id !== dashboardId);
          if (remaining.length > 0) {
            setCurrentDashboard(remaining[0]);
          } else {
            const defaultDashboard = createDefaultDashboard();
            setCurrentDashboard(defaultDashboard);
          }
        }
        
        return { success: true };
      }
      
      throw new Error(response.error || 'Failed to delete dashboard');
    } catch (error) {
      console.error('Delete dashboard error:', error);
      return { success: false, error: error.message };
    }
  }, [apiRequest, currentDashboard, dashboards, createDefaultDashboard]);

  // Update dashboard layout
  const updateLayout = useCallback((newLayout) => {
    if (!currentDashboard) return;
    
    const updatedDashboard = {
      ...currentDashboard,
      layout: newLayout
    };
    
    setCurrentDashboard(updatedDashboard);
  }, [currentDashboard]);

  // Add widget to dashboard
  const addWidget = useCallback((widgetType, position) => {
    if (!currentDashboard) return;
    
    const widgetConfig = WIDGET_TYPES[widgetType];
    if (!widgetConfig) return;
    
    const newWidget = {
      id: `${widgetType}_${Date.now()}`,
      type: widgetType,
      config: getDefaultWidgetConfig(widgetType)
    };
    
    const newLayoutItem = {
      i: newWidget.id,
      x: position?.x || 0,
      y: position?.y || 0,
      w: widgetConfig.defaultSize.w,
      h: widgetConfig.defaultSize.h
    };
    
    const updatedDashboard = {
      ...currentDashboard,
      widgets: [...currentDashboard.widgets, newWidget],
      layout: [...currentDashboard.layout, newLayoutItem]
    };
    
    setCurrentDashboard(updatedDashboard);
  }, [currentDashboard]);

  // Remove widget from dashboard
  const removeWidget = useCallback((widgetId) => {
    if (!currentDashboard) return;
    
    const updatedDashboard = {
      ...currentDashboard,
      widgets: currentDashboard.widgets.filter(w => w.id !== widgetId),
      layout: currentDashboard.layout.filter(l => l.i !== widgetId)
    };
    
    setCurrentDashboard(updatedDashboard);
  }, [currentDashboard]);

  // Update widget configuration
  const updateWidgetConfig = useCallback((widgetId, config) => {
    if (!currentDashboard) return;
    
    const updatedDashboard = {
      ...currentDashboard,
      widgets: currentDashboard.widgets.map(w =>
        w.id === widgetId ? { ...w, config: { ...w.config, ...config } } : w
      )
    };
    
    setCurrentDashboard(updatedDashboard);
  }, [currentDashboard]);

  // Load widget data
  const loadWidgetData = useCallback(async (widgetId, widgetType, config) => {
    try {
      const endpoint = getWidgetDataEndpoint(widgetType, config);
      const data = await apiRequest(endpoint);
      
      setWidgetData(prev => ({
        ...prev,
        [widgetId]: {
          data,
          lastUpdated: new Date().toISOString(),
          loading: false,
          error: null
        }
      }));
    } catch (error) {
      console.error(`Failed to load data for widget ${widgetId}:`, error);
      setWidgetData(prev => ({
        ...prev,
        [widgetId]: {
          data: null,
          lastUpdated: new Date().toISOString(),
          loading: false,
          error: error.message
        }
      }));
    }
  }, [apiRequest]);

  // Get API endpoint for widget data
  const getWidgetDataEndpoint = (widgetType, config) => {
    const endpoints = {
      churn_summary: `/api/v2/analytics/churn-summary?range=${config.timeRange || '30d'}`,
      customer_list: `/api/v2/customers?per_page=${config.pageSize || 10}&sort=${config.sortBy || 'churn_probability'}`,
      churn_trend: `/api/v2/analytics/churn-trend?range=${config.timeRange || '6m'}`,
      risk_distribution: '/api/v2/analytics/risk-distribution',
      model_performance: `/api/v2/models/performance?range=${config.timeRange || '30d'}`,
      recent_predictions: `/api/v2/predictions?limit=${config.limit || 20}`,
      kpi_cards: '/api/v2/analytics/kpis',
      activity_feed: `/api/v2/audit/activity?limit=${config.limit || 50}`,
      user_analytics: `/api/v2/analytics/users?range=${config.timeRange || '7d'}`
    };
    
    return endpoints[widgetType] || '/api/v2/analytics/default';
  };

  // Refresh all widget data
  const refreshAllWidgets = useCallback(async () => {
    if (!currentDashboard) return;
    
    setLoading(true);
    
    const refreshPromises = currentDashboard.widgets.map(widget =>
      loadWidgetData(widget.id, widget.type, widget.config)
    );
    
    await Promise.allSettled(refreshPromises);
    setLoading(false);
  }, [currentDashboard, loadWidgetData]);

  // Initialize dashboard data
  useEffect(() => {
    if (user) {
      loadDashboards();
    }
  }, [user, loadDashboards]);

  // Refresh widget data when dashboard changes
  useEffect(() => {
    if (currentDashboard && !isEditing) {
      refreshAllWidgets();
    }
  }, [currentDashboard, isEditing, refreshAllWidgets]);

  const value = {
    // State
    dashboards,
    currentDashboard,
    isEditing,
    loading,
    widgetData,

    // Widget types and configuration
    availableWidgets: getAvailableWidgets(),
    WIDGET_TYPES,

    // Dashboard operations
    loadDashboards,
    saveDashboard,
    deleteDashboard,
    setCurrentDashboard,
    createDefaultDashboard,

    // Layout operations
    updateLayout,
    addWidget,
    removeWidget,
    updateWidgetConfig,

    // Data operations
    loadWidgetData,
    refreshAllWidgets,

    // Edit mode
    setIsEditing,
    startEditing: () => setIsEditing(true),
    stopEditing: () => setIsEditing(false),

    // Utilities
    getWidgetById: (widgetId) => currentDashboard?.widgets.find(w => w.id === widgetId),
    getWidgetConfig: (widgetId) => currentDashboard?.widgets.find(w => w.id === widgetId)?.config || {},
    getWidgetData: (widgetId) => widgetData[widgetId] || { data: null, loading: true, error: null }
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
};