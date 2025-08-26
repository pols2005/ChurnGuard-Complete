import React, { useState, useCallback, useMemo } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import { useDashboard } from '../contexts/DashboardContext';
import { useAuth } from '../contexts/AuthContext';
import DashboardWidget from './DashboardWidget';
import WidgetSelector from './WidgetSelector';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

const DashboardBuilder = () => {
  const {
    currentDashboard,
    isEditing,
    startEditing,
    stopEditing,
    updateLayout,
    addWidget,
    removeWidget,
    saveDashboard,
    availableWidgets,
    WIDGET_TYPES
  } = useDashboard();

  const { hasPermission } = useAuth();
  const [showWidgetSelector, setShowWidgetSelector] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const showMessage = useCallback((type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage({ type: '', text: '' }), 3000);
  }, []);

  // Handle layout changes from drag/resize
  const handleLayoutChange = useCallback((layout) => {
    if (isEditing) {
      updateLayout(layout);
    }
  }, [isEditing, updateLayout]);

  // Handle adding a widget
  const handleAddWidget = useCallback((widgetType) => {
    const nextPosition = getNextWidgetPosition();
    addWidget(widgetType, nextPosition);
    setShowWidgetSelector(false);
    showMessage('success', 'Widget added to dashboard');
  }, [addWidget, showMessage]);

  // Handle removing a widget
  const handleRemoveWidget = useCallback((widgetId) => {
    removeWidget(widgetId);
    showMessage('success', 'Widget removed from dashboard');
  }, [removeWidget, showMessage]);

  // Calculate next best position for new widget
  const getNextWidgetPosition = () => {
    if (!currentDashboard?.layout) return { x: 0, y: 0 };
    
    const layout = currentDashboard.layout;
    const maxY = Math.max(...layout.map(item => item.y + item.h), 0);
    
    return { x: 0, y: maxY };
  };

  // Save dashboard changes
  const handleSave = useCallback(async () => {
    if (!currentDashboard) return;
    
    setSaving(true);
    try {
      const result = await saveDashboard(currentDashboard);
      if (result.success) {
        showMessage('success', 'Dashboard saved successfully');
        stopEditing();
      } else {
        showMessage('error', result.error || 'Failed to save dashboard');
      }
    } catch (error) {
      showMessage('error', error.message);
    } finally {
      setSaving(false);
    }
  }, [currentDashboard, saveDashboard, stopEditing, showMessage]);

  // Cancel editing
  const handleCancel = useCallback(() => {
    stopEditing();
    showMessage('info', 'Changes cancelled');
  }, [stopEditing, showMessage]);

  // Grid breakpoints and column configuration
  const breakpoints = { lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 };
  const cols = { lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 };

  // Generate grid items from dashboard widgets
  const gridItems = useMemo(() => {
    if (!currentDashboard?.widgets) return [];

    return currentDashboard.widgets.map((widget) => {
      const widgetConfig = WIDGET_TYPES[widget.type];
      
      return (
        <div key={widget.id} className="dashboard-widget-container">
          {isEditing && (
            <div className="absolute top-2 right-2 z-10 flex space-x-1">
              <button
                onClick={() => setSelectedWidget(widget)}
                className="p-1 bg-blue-500 text-white rounded shadow-lg hover:bg-blue-600 transition-colors"
                title="Configure Widget"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
              <button
                onClick={() => handleRemoveWidget(widget.id)}
                className="p-1 bg-red-500 text-white rounded shadow-lg hover:bg-red-600 transition-colors"
                title="Remove Widget"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
          <DashboardWidget
            widget={widget}
            isEditing={isEditing}
            className="h-full"
          />
        </div>
      );
    });
  }, [currentDashboard?.widgets, isEditing, WIDGET_TYPES, handleRemoveWidget, setSelectedWidget]);

  if (!currentDashboard) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="dashboard-builder min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {currentDashboard.name || 'My Dashboard'}
            </h1>
            {currentDashboard.description && (
              <p className="text-sm text-gray-600 mt-1">
                {currentDashboard.description}
              </p>
            )}
          </div>
          
          <div className="flex items-center space-x-3">
            {!isEditing ? (
              <>
                {hasPermission('dashboard.edit') && (
                  <button
                    onClick={startEditing}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Edit Dashboard
                  </button>
                )}
              </>
            ) : (
              <>
                <button
                  onClick={() => setShowWidgetSelector(true)}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Add Widget
                </button>
                
                <button
                  onClick={handleCancel}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancel
                </button>
                
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                >
                  {saving ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Saving...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Save
                    </>
                  )}
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Status Messages */}
      {message.text && (
        <div className={`mx-6 mt-4 p-3 rounded-md ${
          message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' :
          message.type === 'error' ? 'bg-red-50 text-red-800 border border-red-200' :
          'bg-blue-50 text-blue-800 border border-blue-200'
        }`}>
          {message.text}
        </div>
      )}

      {/* Edit Mode Indicator */}
      {isEditing && (
        <div className="bg-blue-50 border-b border-blue-200 px-6 py-3">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-800">
                <strong>Edit Mode:</strong> Drag widgets to reposition, resize by dragging corners, or use the controls to add/remove widgets.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Grid */}
      <div className="dashboard-container p-6">
        <ResponsiveGridLayout
          className="layout"
          layouts={{ lg: currentDashboard.layout }}
          breakpoints={breakpoints}
          cols={cols}
          rowHeight={60}
          isDraggable={isEditing}
          isResizable={isEditing}
          onLayoutChange={handleLayoutChange}
          compactType="vertical"
          preventCollision={false}
          margin={[16, 16]}
          containerPadding={[0, 0]}
        >
          {gridItems}
        </ResponsiveGridLayout>
      </div>

      {/* Widget Selector Modal */}
      {showWidgetSelector && (
        <WidgetSelector
          availableWidgets={availableWidgets}
          onSelectWidget={handleAddWidget}
          onClose={() => setShowWidgetSelector(false)}
        />
      )}

      {/* Widget Configuration Modal */}
      {selectedWidget && (
        <WidgetConfigModal
          widget={selectedWidget}
          onClose={() => setSelectedWidget(null)}
          onSave={(config) => {
            // Update widget config would be handled here
            setSelectedWidget(null);
            showMessage('success', 'Widget configuration updated');
          }}
        />
      )}

      {/* Empty State */}
      {(!currentDashboard.widgets || currentDashboard.widgets.length === 0) && (
        <div className="text-center py-16">
          <div className="mx-auto max-w-md">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No widgets yet</h3>
            <p className="mt-2 text-sm text-gray-500">
              Get started by adding some widgets to your dashboard.
            </p>
            {hasPermission('dashboard.edit') && (
              <div className="mt-6">
                <button
                  onClick={() => {
                    if (!isEditing) startEditing();
                    setShowWidgetSelector(true);
                  }}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Add Your First Widget
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Widget Configuration Modal Component
const WidgetConfigModal = ({ widget, onClose, onSave }) => {
  const [config, setConfig] = useState(widget.config || {});
  const { WIDGET_TYPES } = useDashboard();
  
  const widgetType = WIDGET_TYPES[widget.type];
  
  const handleSave = () => {
    onSave(config);
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">
            Configure {widgetType?.name}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-4">
            {widgetType?.description}
          </p>
          
          {/* Generic configuration options */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Widget Title (Optional)
              </label>
              <input
                type="text"
                value={config.title || ''}
                onChange={(e) => setConfig(prev => ({ ...prev, title: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                placeholder={`Default: ${widgetType?.name}`}
              />
            </div>
            
            {widget.type === 'churn_trend' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Time Range
                </label>
                <select
                  value={config.timeRange || '6m'}
                  onChange={(e) => setConfig(prev => ({ ...prev, timeRange: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                >
                  <option value="1m">Last Month</option>
                  <option value="3m">Last 3 Months</option>
                  <option value="6m">Last 6 Months</option>
                  <option value="1y">Last Year</option>
                </select>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary-dark"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardBuilder;