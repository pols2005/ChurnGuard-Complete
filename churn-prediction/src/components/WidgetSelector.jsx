import React, { useState, useMemo } from 'react';
import { useDashboard } from '../contexts/DashboardContext';

const WidgetSelector = ({ availableWidgets, onSelectWidget, onClose }) => {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set(availableWidgets.map(widget => widget.category));
    return ['all', ...Array.from(cats)];
  }, [availableWidgets]);

  // Filter widgets based on category and search
  const filteredWidgets = useMemo(() => {
    return availableWidgets.filter(widget => {
      const matchesCategory = selectedCategory === 'all' || widget.category === selectedCategory;
      const matchesSearch = searchTerm === '' || 
        widget.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        widget.description.toLowerCase().includes(searchTerm.toLowerCase());
      
      return matchesCategory && matchesSearch;
    });
  }, [availableWidgets, selectedCategory, searchTerm]);

  const getCategoryLabel = (category) => {
    const labels = {
      all: 'All Widgets',
      analytics: 'Analytics',
      customers: 'Customers',
      models: 'ML Models',
      predictions: 'Predictions',
      system: 'System',
      tools: 'Tools',
      users: 'Users'
    };
    return labels[category] || category.charAt(0).toUpperCase() + category.slice(1);
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-8 mx-auto p-0 border max-w-4xl shadow-lg rounded-lg bg-white">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Add Widget to Dashboard
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Choose from available widgets based on your permissions
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Filters */}
        <div className="p-6 border-b border-gray-200 bg-gray-50">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  placeholder="Search widgets..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary focus:border-primary"
                />
              </div>
            </div>

            {/* Category Filter */}
            <div className="sm:w-48">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
              >
                {categories.map(category => (
                  <option key={category} value={category}>
                    {getCategoryLabel(category)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Widget Grid */}
        <div className="p-6 max-h-96 overflow-y-auto">
          {filteredWidgets.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredWidgets.map((widget) => (
                <WidgetCard
                  key={widget.id}
                  widget={widget}
                  onClick={() => onSelectWidget(widget.id)}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 20.055a7.962 7.962 0 01-6-2.764M3 3l1.664 1.664L6 6l12 12 1.664 1.664L21 21" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No widgets found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Try adjusting your search or filter criteria.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500">
              {filteredWidgets.length} of {availableWidgets.length} widgets available
            </p>
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Individual Widget Card Component
const WidgetCard = ({ widget, onClick }) => {
  const getCategoryColor = (category) => {
    const colors = {
      analytics: 'bg-blue-100 text-blue-800',
      customers: 'bg-green-100 text-green-800',
      models: 'bg-purple-100 text-purple-800',
      predictions: 'bg-orange-100 text-orange-800',
      system: 'bg-gray-100 text-gray-800',
      tools: 'bg-yellow-100 text-yellow-800',
      users: 'bg-indigo-100 text-indigo-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div
      onClick={onClick}
      className="relative rounded-lg border border-gray-300 bg-white p-4 shadow-sm hover:border-primary hover:shadow-md transition-all cursor-pointer group"
    >
      {/* Widget Icon and Name */}
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-lg group-hover:bg-primary group-hover:text-white transition-colors">
            {widget.icon}
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-gray-900 group-hover:text-primary transition-colors">
            {widget.name}
          </h4>
          <p className="text-xs text-gray-500 mt-1">
            {widget.description}
          </p>
        </div>
      </div>

      {/* Widget Details */}
      <div className="mt-4 flex items-center justify-between">
        {/* Category Badge */}
        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(widget.category)}`}>
          {widget.category}
        </span>

        {/* Size Indicator */}
        <div className="text-xs text-gray-400">
          {widget.defaultSize.w}×{widget.defaultSize.h}
        </div>
      </div>

      {/* Permissions Required (if any) */}
      {widget.permissions && widget.permissions.length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-200">
          <div className="flex items-center text-xs text-gray-500">
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            Requires: {widget.permissions.slice(0, 2).join(', ')}
            {widget.permissions.length > 2 && ` +${widget.permissions.length - 2}`}
          </div>
        </div>
      )}

      {/* Add Button Overlay */}
      <div className="absolute inset-0 bg-primary bg-opacity-0 group-hover:bg-opacity-5 transition-all rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100">
        <div className="bg-white border border-primary rounded-full p-2 shadow-lg">
          <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        </div>
      </div>
    </div>
  );
};

export default WidgetSelector;