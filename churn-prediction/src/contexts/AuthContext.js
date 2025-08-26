import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);

  // Check if user has specific permission
  const hasPermission = useCallback((permission) => {
    if (!user) return false;
    if (user.is_admin) return true;
    return permissions.includes(permission);
  }, [user, permissions]);

  // Check if user has any of the specified permissions
  const hasAnyPermission = useCallback((requiredPermissions) => {
    if (!user) return false;
    if (user.is_admin) return true;
    return requiredPermissions.some(permission => permissions.includes(permission));
  }, [user, permissions]);

  // Check if user has specific role
  const hasRole = useCallback((role) => {
    if (!user) return false;
    return user.role === role || user.is_admin;
  }, [user]);

  // Check if organization has feature
  const hasFeature = useCallback((feature) => {
    if (!organization) return false;
    
    const tierFeatures = {
      starter: ['basic_analytics', 'standard_support'],
      professional: [
        'basic_analytics', 'advanced_analytics', 'data_export',
        'custom_colors', 'logo_upload', 'priority_support'
      ],
      enterprise: [
        'basic_analytics', 'advanced_analytics', 'data_export',
        'custom_colors', 'logo_upload', 'custom_css', 'white_label',
        'sso', 'api_access', 'dedicated_support', 'custom_domain'
      ]
    };

    const availableFeatures = tierFeatures[organization.subscription_tier] || [];
    return availableFeatures.includes(feature) || (organization.features && organization.features[feature]);
  }, [organization]);

  // Make authenticated API request
  const apiRequest = useCallback(async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (response.status === 401) {
        // Token expired or invalid
        setUser(null);
        setOrganization(null);
        setPermissions([]);
        throw new Error('Authentication required');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }, []);

  // Login function
  const login = useCallback(async (credentials) => {
    try {
      setLoading(true);
      
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Login failed');
      }

      const data = await response.json();
      
      setUser(data.user);
      setOrganization(data.organization);
      setPermissions(data.permissions || []);
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    try {
      await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setOrganization(null);
      setPermissions([]);
    }
  }, []);

  // SSO login
  const loginWithSSO = useCallback((provider, organizationSlug) => {
    const params = new URLSearchParams({
      org: organizationSlug || ''
    });
    
    window.location.href = `${API_BASE_URL}/api/auth/sso/${provider}/login?${params}`;
  }, []);

  // Check current authentication status
  const checkAuth = useCallback(async () => {
    try {
      setLoading(true);
      
      const data = await apiRequest('/api/auth/me');
      
      setUser(data.user);
      setOrganization(data.organization);
      setPermissions(data.permissions || []);
      
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
      setOrganization(null);
      setPermissions([]);
    } finally {
      setLoading(false);
      setInitialized(true);
    }
  }, [apiRequest]);

  // Refresh token
  const refreshToken = useCallback(async () => {
    try {
      await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: 'POST',
        credentials: 'include'
      });
      
      // Re-check auth status to get updated user data
      await checkAuth();
      
    } catch (error) {
      console.error('Token refresh failed:', error);
      setUser(null);
      setOrganization(null);
      setPermissions([]);
    }
  }, [checkAuth]);

  // Update user profile
  const updateUser = useCallback(async (userData) => {
    try {
      const response = await apiRequest('/api/auth/users/me', {
        method: 'PUT',
        body: JSON.stringify(userData)
      });

      if (response.success) {
        setUser(prev => ({ ...prev, ...userData }));
        return { success: true };
      }
      
      throw new Error(response.error || 'Update failed');
    } catch (error) {
      console.error('User update error:', error);
      return { success: false, error: error.message };
    }
  }, [apiRequest]);

  // Update organization
  const updateOrganization = useCallback(async (orgData) => {
    try {
      const response = await apiRequest('/api/auth/organization', {
        method: 'PUT',
        body: JSON.stringify(orgData)
      });

      if (response.success) {
        setOrganization(prev => ({ ...prev, ...orgData }));
        return { success: true };
      }
      
      throw new Error(response.error || 'Update failed');
    } catch (error) {
      console.error('Organization update error:', error);
      return { success: false, error: error.message };
    }
  }, [apiRequest]);

  // Check specific permissions
  const checkPermissions = useCallback(async (permissionList) => {
    try {
      const response = await apiRequest('/api/auth/permissions/check', {
        method: 'POST',
        body: JSON.stringify({ permissions: permissionList })
      });

      return response.permissions;
    } catch (error) {
      console.error('Permission check error:', error);
      return {};
    }
  }, [apiRequest]);

  // Initialize auth on mount
  useEffect(() => {
    if (!initialized) {
      checkAuth();
    }
  }, [initialized, checkAuth]);

  // Auto-refresh token before expiration
  useEffect(() => {
    if (user) {
      // Refresh token every 30 minutes
      const interval = setInterval(refreshToken, 30 * 60 * 1000);
      return () => clearInterval(interval);
    }
  }, [user, refreshToken]);

  const value = {
    // State
    user,
    organization,
    permissions,
    loading,
    isAuthenticated: !!user,
    initialized,

    // Functions
    login,
    logout,
    loginWithSSO,
    checkAuth,
    refreshToken,
    updateUser,
    updateOrganization,
    checkPermissions,
    apiRequest,

    // Permission helpers
    hasPermission,
    hasAnyPermission,
    hasRole,
    hasFeature,

    // User info helpers
    isAdmin: user?.is_admin || false,
    userRole: user?.role || null,
    organizationTier: organization?.subscription_tier || 'starter'
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// HOC for protected routes
export const withAuth = (Component, requiredPermissions = []) => {
  return function AuthenticatedComponent(props) {
    const { isAuthenticated, hasAnyPermission, loading, initialized } = useAuth();

    if (!initialized || loading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      );
    }

    if (!isAuthenticated) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-4">Authentication Required</h2>
            <p>Please log in to access this page.</p>
          </div>
        </div>
      );
    }

    if (requiredPermissions.length > 0 && !hasAnyPermission(requiredPermissions)) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-4">Access Denied</h2>
            <p>You don't have permission to access this page.</p>
            <p className="text-sm text-gray-500 mt-2">
              Required permissions: {requiredPermissions.join(', ')}
            </p>
          </div>
        </div>
      );
    }

    return <Component {...props} />;
  };
};

// Hook for permission-based rendering
export const usePermission = (permission) => {
  const { hasPermission } = useAuth();
  return hasPermission(permission);
};

// Hook for feature-based rendering
export const useFeature = (feature) => {
  const { hasFeature } = useAuth();
  return hasFeature(feature);
};