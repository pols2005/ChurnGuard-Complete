import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const EnterpriseSettings = () => {
  const { 
    user, 
    organization, 
    updateOrganization, 
    apiRequest, 
    hasPermission, 
    hasFeature, 
    isAdmin,
    organizationTier 
  } = useAuth();

  const [activeTab, setActiveTab] = useState('organization');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  // Organization settings state
  const [orgSettings, setOrgSettings] = useState({
    name: '',
    logo_url: '',
    primary_color: '#DAA520',
    secondary_color: '#B8860B',
    billing_email: '',
    custom_css: '',
    custom_domain: ''
  });

  // SSO settings state
  const [ssoConfigs, setSsoConfigs] = useState([]);
  const [newSSO, setNewSSO] = useState({
    provider: 'saml',
    provider_name: '',
    config: {}
  });

  // Users state
  const [users, setUsers] = useState([]);
  const [newUser, setNewUser] = useState({
    email: '',
    first_name: '',
    last_name: '',
    role: 'user'
  });

  useEffect(() => {
    if (organization) {
      setOrgSettings({
        name: organization.name || '',
        logo_url: organization.logo_url || '',
        primary_color: organization.primary_color || '#DAA520',
        secondary_color: organization.secondary_color || '#B8860B',
        billing_email: organization.billing_email || '',
        custom_css: organization.custom_css || '',
        custom_domain: organization.custom_domain || ''
      });
    }
  }, [organization]);

  useEffect(() => {
    if (activeTab === 'sso' && hasFeature('sso')) {
      loadSSOConfigs();
    } else if (activeTab === 'users' && hasPermission('user.read')) {
      loadUsers();
    }
  }, [activeTab, hasFeature, hasPermission]);

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage({ type: '', text: '' }), 5000);
  };

  const loadSSOConfigs = async () => {
    try {
      const data = await apiRequest('/api/auth/sso/config');
      setSsoConfigs(data.configurations || []);
    } catch (error) {
      console.error('Failed to load SSO configs:', error);
    }
  };

  const loadUsers = async () => {
    try {
      const data = await apiRequest('/api/auth/users?per_page=50');
      setUsers(data.users || []);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const handleOrgUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await updateOrganization(orgSettings);
      if (result.success) {
        showMessage('success', 'Organization settings updated successfully');
      } else {
        showMessage('error', result.error || 'Update failed');
      }
    } catch (error) {
      showMessage('error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSSOCreate = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await apiRequest('/api/auth/sso/config', {
        method: 'POST',
        body: JSON.stringify(newSSO)
      });

      if (response.success) {
        showMessage('success', 'SSO configuration created successfully');
        setNewSSO({ provider: 'saml', provider_name: '', config: {} });
        loadSSOConfigs();
      } else {
        showMessage('error', response.error || 'Failed to create SSO config');
      }
    } catch (error) {
      showMessage('error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUserCreate = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await apiRequest('/api/auth/users', {
        method: 'POST',
        body: JSON.stringify(newUser)
      });

      if (response.success) {
        showMessage('success', 'User created successfully');
        setNewUser({ email: '', first_name: '', last_name: '', role: 'user' });
        loadUsers();
      } else {
        showMessage('error', response.error || 'Failed to create user');
      }
    } catch (error) {
      showMessage('error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'organization', name: 'Organization', permission: 'organization.read' },
    { id: 'users', name: 'Users', permission: 'user.read' },
    { id: 'sso', name: 'Single Sign-On', feature: 'sso' },
    { id: 'api', name: 'API Keys', feature: 'api_access' },
    { id: 'billing', name: 'Billing', permission: 'organization.read' }
  ];

  const visibleTabs = tabs.filter(tab => {
    if (tab.permission && !hasPermission(tab.permission)) return false;
    if (tab.feature && !hasFeature(tab.feature)) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage your organization, users, and integrations
          </p>
        </div>

        {/* Message */}
        {message.text && (
          <div className={`mb-6 p-4 rounded-md ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-800 border border-green-200' 
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}

        <div className="bg-white shadow rounded-lg">
          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              {visibleTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {/* Organization Settings */}
            {activeTab === 'organization' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Organization Settings
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Configure your organization's basic information and branding.
                  </p>
                </div>

                <form onSubmit={handleOrgUpdate} className="space-y-6">
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                    {/* Organization Name */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Organization Name
                      </label>
                      <input
                        type="text"
                        value={orgSettings.name}
                        onChange={(e) => setOrgSettings(prev => ({ ...prev, name: e.target.value }))}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary"
                      />
                    </div>

                    {/* Billing Email */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Billing Email
                      </label>
                      <input
                        type="email"
                        value={orgSettings.billing_email}
                        onChange={(e) => setOrgSettings(prev => ({ ...prev, billing_email: e.target.value }))}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary"
                      />
                    </div>
                  </div>

                  {/* Branding Section */}
                  {hasFeature('custom_colors') && (
                    <div className="space-y-4">
                      <h4 className="text-md font-medium text-gray-900">Branding</h4>
                      
                      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                        {/* Primary Color */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700">
                            Primary Color
                          </label>
                          <div className="mt-1 flex rounded-md shadow-sm">
                            <input
                              type="color"
                              value={orgSettings.primary_color}
                              onChange={(e) => setOrgSettings(prev => ({ ...prev, primary_color: e.target.value }))}
                              className="h-10 w-16 border border-gray-300 rounded-l-md"
                            />
                            <input
                              type="text"
                              value={orgSettings.primary_color}
                              onChange={(e) => setOrgSettings(prev => ({ ...prev, primary_color: e.target.value }))}
                              className="flex-1 border-gray-300 rounded-r-md shadow-sm focus:ring-primary focus:border-primary"
                            />
                          </div>
                        </div>

                        {/* Secondary Color */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700">
                            Secondary Color
                          </label>
                          <div className="mt-1 flex rounded-md shadow-sm">
                            <input
                              type="color"
                              value={orgSettings.secondary_color}
                              onChange={(e) => setOrgSettings(prev => ({ ...prev, secondary_color: e.target.value }))}
                              className="h-10 w-16 border border-gray-300 rounded-l-md"
                            />
                            <input
                              type="text"
                              value={orgSettings.secondary_color}
                              onChange={(e) => setOrgSettings(prev => ({ ...prev, secondary_color: e.target.value }))}
                              className="flex-1 border-gray-300 rounded-r-md shadow-sm focus:ring-primary focus:border-primary"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Logo URL */}
                      {hasFeature('logo_upload') && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700">
                            Logo URL
                          </label>
                          <input
                            type="url"
                            value={orgSettings.logo_url}
                            onChange={(e) => setOrgSettings(prev => ({ ...prev, logo_url: e.target.value }))}
                            placeholder="https://example.com/logo.png"
                            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary"
                          />
                        </div>
                      )}

                      {/* Custom CSS */}
                      {hasFeature('custom_css') && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700">
                            Custom CSS
                          </label>
                          <textarea
                            value={orgSettings.custom_css}
                            onChange={(e) => setOrgSettings(prev => ({ ...prev, custom_css: e.target.value }))}
                            rows={6}
                            placeholder="/* Custom CSS styles */"
                            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary font-mono text-sm"
                          />
                          <p className="mt-1 text-xs text-gray-500">
                            Enterprise feature: Add custom CSS to override default styles
                          </p>
                        </div>
                      )}

                      {/* Custom Domain */}
                      {hasFeature('custom_domain') && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700">
                            Custom Domain
                          </label>
                          <input
                            type="text"
                            value={orgSettings.custom_domain}
                            onChange={(e) => setOrgSettings(prev => ({ ...prev, custom_domain: e.target.value }))}
                            placeholder="churn.yourcompany.com"
                            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary"
                          />
                          <p className="mt-1 text-xs text-gray-500">
                            Contact support to configure DNS settings for your custom domain
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Subscription Info */}
                  <div className="bg-gray-50 px-4 py-3 rounded-md">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">
                          Current Plan: {organizationTier.charAt(0).toUpperCase() + organizationTier.slice(1)}
                        </h4>
                        <p className="text-xs text-gray-600">
                          {organizationTier === 'starter' && 'Basic features with 5 users'}
                          {organizationTier === 'professional' && 'Advanced features with 25 users'}
                          {organizationTier === 'enterprise' && 'Full feature set with unlimited users'}
                        </p>
                      </div>
                      {organizationTier !== 'enterprise' && (
                        <button
                          type="button"
                          className="text-sm text-primary hover:text-primary-dark"
                          onClick={() => alert('Upgrade functionality would be implemented here')}
                        >
                          Upgrade Plan
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-primary text-white px-4 py-2 rounded-md hover:bg-primary-dark disabled:opacity-50"
                    >
                      {loading ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Users Management */}
            {activeTab === 'users' && hasPermission('user.read') && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      User Management
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Manage users and their roles in your organization.
                    </p>
                  </div>
                </div>

                {/* Add User Form */}
                {hasPermission('user.create') && (
                  <div className="bg-gray-50 p-4 rounded-md">
                    <h4 className="text-md font-medium text-gray-900 mb-4">Add New User</h4>
                    <form onSubmit={handleUserCreate} className="grid grid-cols-1 gap-4 sm:grid-cols-4">
                      <input
                        type="email"
                        placeholder="Email address"
                        value={newUser.email}
                        onChange={(e) => setNewUser(prev => ({ ...prev, email: e.target.value }))}
                        required
                        className="border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary"
                      />
                      <input
                        type="text"
                        placeholder="First name"
                        value={newUser.first_name}
                        onChange={(e) => setNewUser(prev => ({ ...prev, first_name: e.target.value }))}
                        className="border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary"
                      />
                      <input
                        type="text"
                        placeholder="Last name"
                        value={newUser.last_name}
                        onChange={(e) => setNewUser(prev => ({ ...prev, last_name: e.target.value }))}
                        className="border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary"
                      />
                      <div className="flex space-x-2">
                        <select
                          value={newUser.role}
                          onChange={(e) => setNewUser(prev => ({ ...prev, role: e.target.value }))}
                          className="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary"
                        >
                          <option value="viewer">Viewer</option>
                          <option value="user">User</option>
                          <option value="manager">Manager</option>
                          {isAdmin && <option value="admin">Admin</option>}
                        </select>
                        <button
                          type="submit"
                          disabled={loading}
                          className="bg-primary text-white px-4 py-2 rounded-md hover:bg-primary-dark disabled:opacity-50"
                        >
                          Add
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Users List */}
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200">
                    {users.map((user) => (
                      <li key={user.id} className="px-6 py-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="flex-shrink-0">
                              <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                                <span className="text-sm font-medium text-gray-700">
                                  {user.first_name?.[0] || user.email[0].toUpperCase()}
                                </span>
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {user.first_name && user.last_name 
                                  ? `${user.first_name} ${user.last_name}`
                                  : user.email
                                }
                              </div>
                              <div className="text-sm text-gray-500">
                                {user.email}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              user.role === 'admin' ? 'bg-red-100 text-red-800' :
                              user.role === 'manager' ? 'bg-blue-100 text-blue-800' :
                              user.role === 'user' ? 'bg-green-100 text-green-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {user.role}
                            </span>
                            {!user.is_active && (
                              <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                                Inactive
                              </span>
                            )}
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* SSO Configuration */}
            {activeTab === 'sso' && hasFeature('sso') && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Single Sign-On Configuration
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Configure SSO providers for seamless user authentication.
                  </p>
                </div>

                {/* Existing SSO Configs */}
                {ssoConfigs.length > 0 && (
                  <div className="space-y-4">
                    <h4 className="text-md font-medium text-gray-900">Configured Providers</h4>
                    {ssoConfigs.map((config, index) => (
                      <div key={index} className="border border-gray-200 rounded-md p-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <h5 className="text-sm font-medium text-gray-900">
                              {config.provider_name}
                            </h5>
                            <p className="text-sm text-gray-500">
                              Provider: {config.provider.toUpperCase()}
                            </p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              config.is_active 
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {config.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add New SSO Config */}
                {isAdmin && (
                  <div className="bg-gray-50 p-4 rounded-md">
                    <h4 className="text-md font-medium text-gray-900 mb-4">Add SSO Provider</h4>
                    <form onSubmit={handleSSOCreate} className="space-y-4">
                      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Provider</label>
                          <select
                            value={newSSO.provider}
                            onChange={(e) => setNewSSO(prev => ({ ...prev, provider: e.target.value }))}
                            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary"
                          >
                            <option value="saml">SAML</option>
                            <option value="google">Google</option>
                            <option value="microsoft">Microsoft Azure AD</option>
                            <option value="okta">Okta</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Provider Name</label>
                          <input
                            type="text"
                            value={newSSO.provider_name}
                            onChange={(e) => setNewSSO(prev => ({ ...prev, provider_name: e.target.value }))}
                            placeholder="e.g., Company SAML"
                            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary"
                          />
                        </div>
                      </div>
                      <div className="flex justify-end">
                        <button
                          type="submit"
                          disabled={loading}
                          className="bg-primary text-white px-4 py-2 rounded-md hover:bg-primary-dark disabled:opacity-50"
                        >
                          {loading ? 'Adding...' : 'Add Provider'}
                        </button>
                      </div>
                    </form>
                    <p className="mt-2 text-xs text-gray-500">
                      After creating the provider, detailed configuration options will be available for setup.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* API Keys */}
            {activeTab === 'api' && hasFeature('api_access') && (
              <div className="text-center py-12">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900">API Key Management</h3>
                <p className="mt-2 text-sm text-gray-500">
                  API key management interface would be implemented here.
                </p>
              </div>
            )}

            {/* Billing */}
            {activeTab === 'billing' && (
              <div className="text-center py-12">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900">Billing Management</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Billing and subscription management interface would be implemented here.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnterpriseSettings;