import React, { useState } from 'react';

const CustomerListWidget = ({ data, config, onRefresh, refreshing }) => {
  const [sortBy, setSortBy] = useState(config?.sortBy || 'churn_probability');
  const [sortOrder, setSortOrder] = useState(config?.sortOrder || 'desc');
  const [filterRisk, setFilterRisk] = useState('all');

  // Mock data - in production this would come from the API
  const defaultData = {
    customers: [
      {
        id: 'cust_001',
        name: 'John Smith',
        email: 'john.smith@email.com',
        company: 'Acme Corp',
        churn_probability: 0.89,
        churn_risk_level: 'high',
        predicted_at: '2024-01-15T10:30:00Z',
        value: 5200,
        tenure_months: 18,
        last_activity: '2024-01-10T15:45:00Z'
      },
      {
        id: 'cust_002',
        name: 'Sarah Johnson',
        email: 'sarah.j@company.com',
        company: 'Tech Solutions',
        churn_probability: 0.72,
        churn_risk_level: 'high',
        predicted_at: '2024-01-15T09:15:00Z',
        value: 3800,
        tenure_months: 12,
        last_activity: '2024-01-12T11:20:00Z'
      },
      {
        id: 'cust_003',
        name: 'Mike Davis',
        email: 'mike.davis@example.org',
        company: 'Global Inc',
        churn_probability: 0.45,
        churn_risk_level: 'medium',
        predicted_at: '2024-01-15T08:45:00Z',
        value: 7500,
        tenure_months: 24,
        last_activity: '2024-01-14T16:30:00Z'
      },
      {
        id: 'cust_004',
        name: 'Lisa Wilson',
        email: 'lisa.wilson@startup.io',
        company: 'StartupCo',
        churn_probability: 0.23,
        churn_risk_level: 'low',
        predicted_at: '2024-01-15T07:20:00Z',
        value: 2100,
        tenure_months: 6,
        last_activity: '2024-01-15T09:10:00Z'
      },
      {
        id: 'cust_005',
        name: 'David Brown',
        email: 'david.brown@enterprise.com',
        company: 'Enterprise Ltd',
        churn_probability: 0.78,
        churn_risk_level: 'high',
        predicted_at: '2024-01-15T06:30:00Z',
        value: 12000,
        tenure_months: 36,
        last_activity: '2024-01-08T14:15:00Z'
      }
    ],
    total: 1250,
    showing: 5
  };

  const customerData = data || defaultData;
  const pageSize = config?.pageSize || 10;

  // Filter customers by risk level
  const filteredCustomers = filterRisk === 'all' 
    ? customerData.customers 
    : customerData.customers.filter(customer => customer.churn_risk_level === filterRisk);

  // Sort customers
  const sortedCustomers = [...filteredCustomers].sort((a, b) => {
    let aValue = a[sortBy];
    let bValue = b[sortBy];
    
    if (typeof aValue === 'string') {
      aValue = aValue.toLowerCase();
      bValue = bValue.toLowerCase();
    }
    
    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const getRiskBadgeColor = (riskLevel) => {
    switch (riskLevel) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getTimeAgo = (dateString) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffInDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Yesterday';
    return `${diffInDays} days ago`;
  };

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          {/* Risk Filter */}
          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
          >
            <option value="all">All Risk Levels</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>

          {/* Sort */}
          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('-');
              setSortBy(field);
              setSortOrder(order);
            }}
            className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
          >
            <option value="churn_probability-desc">Highest Risk First</option>
            <option value="churn_probability-asc">Lowest Risk First</option>
            <option value="value-desc">Highest Value First</option>
            <option value="name-asc">Name A-Z</option>
            <option value="last_activity-desc">Recent Activity</option>
          </select>
        </div>

        {/* Stats */}
        <div className="text-xs text-gray-500">
          Showing {sortedCustomers.length} of {customerData.total} customers
        </div>
      </div>

      {/* Customer List */}
      <div className="flex-1 overflow-auto">
        <div className="space-y-2">
          {sortedCustomers.slice(0, pageSize).map((customer) => (
            <div
              key={customer.id}
              className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow"
            >
              {/* Customer Info */}
              <div className="flex items-center space-x-3 min-w-0 flex-1">
                {/* Avatar */}
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-gray-600">
                      {customer.name.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                </div>

                {/* Details */}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {customer.name}
                    </p>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getRiskBadgeColor(customer.churn_risk_level)}`}>
                      {customer.churn_risk_level}
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-4 mt-1">
                    <p className="text-xs text-gray-500 truncate">
                      {customer.email}
                    </p>
                    {customer.company && (
                      <p className="text-xs text-gray-500">
                        {customer.company}
                      </p>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-4 mt-1 text-xs text-gray-400">
                    <span>Value: {formatCurrency(customer.value)}</span>
                    <span>Tenure: {customer.tenure_months}mo</span>
                    <span>Last seen: {getTimeAgo(customer.last_activity)}</span>
                  </div>
                </div>
              </div>

              {/* Churn Risk */}
              <div className="flex-shrink-0 text-right">
                <div className="text-lg font-bold text-gray-900">
                  {formatPercentage(customer.churn_probability)}
                </div>
                <div className="text-xs text-gray-500">
                  churn risk
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {formatDate(customer.predicted_at)}
                </div>
              </div>

              {/* Actions */}
              <div className="flex-shrink-0 ml-4">
                <div className="flex space-x-1">
                  <button
                    className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                    title="View Details"
                    onClick={() => alert(`View details for ${customer.name}`)}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button
                    className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                    title="Create Campaign"
                    onClick={() => alert(`Create retention campaign for ${customer.name}`)}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {sortedCustomers.length === 0 && (
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No customers found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your filter criteria.
            </p>
          </div>
        )}
      </div>

      {/* Pagination/Load More */}
      {sortedCustomers.length > pageSize && (
        <div className="mt-4 pt-3 border-t border-gray-200">
          <button
            className="w-full text-sm text-primary hover:text-primary-dark font-medium"
            onClick={() => alert('Load more functionality would be implemented here')}
          >
            Load More Customers ({sortedCustomers.length - pageSize} remaining)
          </button>
        </div>
      )}
    </div>
  );
};

export default CustomerListWidget;