import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';

const ComplianceCenter = () => {
  const { user, organization } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [dataRequests, setDataRequests] = useState([]);
  const [retentionPolicies, setRetentionPolicies] = useState([]);
  const [complianceReport, setComplianceReport] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!user || user.role !== 'admin') {
    return (
      <div className="p-6 text-center">
        <div className="text-gray-500">
          <div className="text-4xl mb-2">🔒</div>
          <div>Access Denied</div>
          <div className="text-sm">Only administrators can access compliance tools</div>
        </div>
      </div>
    );
  }

  useEffect(() => {
    loadComplianceData();
  }, []);

  const loadComplianceData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadDataRequests(),
        loadRetentionPolicies(),
        loadComplianceReport()
      ]);
    } catch (error) {
      console.error('Error loading compliance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDataRequests = async () => {
    try {
      const response = await fetch(`/api/compliance/data-requests?org_id=${organization.id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setDataRequests(data.requests || []);
      }
    } catch (error) {
      console.error('Error loading data requests:', error);
    }
  };

  const loadRetentionPolicies = async () => {
    try {
      const response = await fetch(`/api/compliance/retention-policies?org_id=${organization.id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setRetentionPolicies(data.policies || []);
      }
    } catch (error) {
      console.error('Error loading retention policies:', error);
    }
  };

  const loadComplianceReport = async () => {
    try {
      const response = await fetch(`/api/compliance/privacy-report?org_id=${organization.id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setComplianceReport(data.report);
      }
    } catch (error) {
      console.error('Error loading compliance report:', error);
    }
  };

  const processDataRequest = async (requestId, action) => {
    try {
      const response = await fetch(`/api/compliance/data-requests/${requestId}/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ action })
      });

      if (response.ok) {
        alert(`Data request ${action}ed successfully`);
        loadDataRequests();
      } else {
        alert('Failed to process request');
      }
    } catch (error) {
      console.error('Error processing data request:', error);
      alert('Error processing request');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      case 'in_progress': return 'text-blue-600 bg-blue-100';
      case 'completed': return 'text-green-600 bg-green-100';
      case 'rejected': return 'text-red-600 bg-red-100';
      case 'expired': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRequestTypeLabel = (type) => {
    const labels = {
      access: 'Data Access',
      rectification: 'Data Correction',
      erasure: 'Data Erasure',
      portability: 'Data Export',
      restriction: 'Processing Restriction',
      objection: 'Processing Objection'
    };
    return labels[type] || type;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isOverdue = (expiryDate) => {
    return new Date(expiryDate) < new Date();
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">GDPR Compliance Center</h1>
        <p className="text-gray-600">Manage data protection and privacy compliance</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: '📊' },
            { id: 'requests', name: 'Data Requests', icon: '📋' },
            { id: 'retention', name: 'Data Retention', icon: '🗂️' },
            { id: 'reports', name: 'Privacy Reports', icon: '📈' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="text-gray-600 mt-2">Loading compliance data...</p>
        </div>
      )}

      {/* Overview Tab */}
      {activeTab === 'overview' && complianceReport && (
        <div className="space-y-6">
          {/* Compliance Score */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Compliance Score</h3>
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Overall Score</span>
                  <span>{complianceReport.compliance_status.overall_score}/100</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      complianceReport.compliance_status.overall_score >= 80 
                        ? 'bg-green-500' 
                        : complianceReport.compliance_status.overall_score >= 60
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${complianceReport.compliance_status.overall_score}%` }}
                  />
                </div>
              </div>
              <div className="text-2xl">
                {complianceReport.compliance_status.overall_score >= 80 ? '✅' : 
                 complianceReport.compliance_status.overall_score >= 60 ? '⚠️' : '❌'}
              </div>
            </div>

            {/* Issues and Recommendations */}
            {complianceReport.compliance_status.issues.length > 0 && (
              <div className="mt-4">
                <h4 className="font-medium text-red-800 mb-2">Issues Found</h4>
                <ul className="space-y-1">
                  {complianceReport.compliance_status.issues.map((issue, idx) => (
                    <li key={idx} className="text-sm text-red-600 flex items-center">
                      <span className="mr-2">•</span>
                      {issue}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {complianceReport.compliance_status.recommendations.length > 0 && (
              <div className="mt-4">
                <h4 className="font-medium text-blue-800 mb-2">Recommendations</h4>
                <ul className="space-y-1">
                  {complianceReport.compliance_status.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-sm text-blue-600 flex items-center">
                      <span className="mr-2">•</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">
                {complianceReport.data_processing_summary.total_customers}
              </div>
              <div className="text-sm text-gray-600">Total Customers</div>
            </div>
            
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">
                {Object.values(complianceReport.data_subject_requests).reduce((sum, statuses) => 
                  sum + Object.values(statuses).reduce((s, count) => s + count, 0), 0
                )}
              </div>
              <div className="text-sm text-gray-600">Data Requests</div>
            </div>
            
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">
                {complianceReport.retention_policies.length}
              </div>
              <div className="text-sm text-gray-600">Retention Policies</div>
            </div>
          </div>
        </div>
      )}

      {/* Data Requests Tab */}
      {activeTab === 'requests' && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Data Subject Requests</h3>
              <p className="text-sm text-gray-600">GDPR data subject access, erasure, and other requests</p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Request</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expiry</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {dataRequests.map((request) => (
                    <tr key={request.id} className={isOverdue(request.expiry_date) && request.status === 'pending' ? 'bg-red-50' : ''}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {request.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {request.customer_email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {getRequestTypeLabel(request.request_type)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(request.status)}`}>
                          {request.status}
                        </span>
                        {isOverdue(request.expiry_date) && request.status === 'pending' && (
                          <span className="ml-2 text-xs text-red-600">OVERDUE</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {formatDate(request.expiry_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        {request.status === 'pending' && (
                          <>
                            <button
                              onClick={() => processDataRequest(request.id, 'approve')}
                              className="text-green-600 hover:text-green-900"
                            >
                              Process
                            </button>
                            <button
                              onClick={() => processDataRequest(request.id, 'reject')}
                              className="text-red-600 hover:text-red-900"
                            >
                              Reject
                            </button>
                          </>
                        )}
                        {request.status === 'completed' && request.response_data && (
                          <button className="text-blue-600 hover:text-blue-900">
                            Download
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {dataRequests.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">📋</div>
                  <div>No data subject requests</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Data Retention Tab */}
      {activeTab === 'retention' && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Data Retention Policies</h3>
                <p className="text-sm text-gray-600">Configure automatic data deletion policies</p>
              </div>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700">
                Add Policy
              </button>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Data Category</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Retention Period</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Auto Delete</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Legal Basis</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {retentionPolicies.map((policy) => (
                    <tr key={policy.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 capitalize">
                        {policy.data_category.replace('_', ' ')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {policy.retention_period_days} days
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          policy.auto_delete ? 'text-green-600 bg-green-100' : 'text-gray-600 bg-gray-100'
                        }`}>
                          {policy.auto_delete ? 'Enabled' : 'Manual'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {policy.legal_basis || 'Not specified'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button className="text-blue-600 hover:text-blue-900">Edit</button>
                        <button className="text-red-600 hover:text-red-900">Delete</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {retentionPolicies.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">🗂️</div>
                  <div>No retention policies configured</div>
                  <div className="text-sm">Add policies to automatically manage data lifecycle</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Privacy Reports Tab */}
      {activeTab === 'reports' && complianceReport && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Privacy Impact Report</h3>
              <div className="text-sm text-gray-600">
                Generated: {formatDate(complianceReport.generated_at)}
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Data Processing Summary */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Data Processing</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Customers:</span>
                    <span className="text-sm font-medium">{complianceReport.data_processing_summary.total_customers}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Predictions:</span>
                    <span className="text-sm font-medium">{complianceReport.data_processing_summary.total_predictions}</span>
                  </div>
                </div>
              </div>
              
              {/* Request Types Summary */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Request Summary</h4>
                <div className="space-y-2">
                  {Object.entries(complianceReport.data_subject_requests).map(([type, statuses]) => (
                    <div key={type} className="flex justify-between">
                      <span className="text-sm text-gray-600 capitalize">{getRequestTypeLabel(type)}:</span>
                      <span className="text-sm font-medium">
                        {Object.values(statuses).reduce((sum, count) => sum + count, 0)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="mt-6 pt-4 border-t border-gray-200">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700">
                Download Full Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComplianceCenter;