import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Navigate, useLocation } from 'react-router-dom';

const ProtectedRoute = ({ 
  children, 
  requiredPermission = null, 
  requiredRole = null, 
  fallback = null,
  redirectTo = '/login' 
}) => {
  const { user, loading, isAuthenticated, hasPermission, hasRole } = useAuth();
  const location = useLocation();
  const [isAuthorized, setIsAuthorized] = useState(null);

  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated) {
        setIsAuthorized(false);
        return;
      }

      // Check permission if required
      if (requiredPermission && !hasPermission(requiredPermission)) {
        setIsAuthorized(false);
        return;
      }

      // Check role if required
      if (requiredRole && !hasRole(requiredRole)) {
        setIsAuthorized(false);
        return;
      }

      setIsAuthorized(true);
    }
  }, [user, loading, isAuthenticated, requiredPermission, requiredRole, hasPermission, hasRole]);

  // Show loading spinner while checking authentication
  if (loading || isAuthorized === null) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Not authenticated - redirect to login
  if (!isAuthenticated) {
    return (
      <Navigate 
        to={redirectTo} 
        state={{ from: location.pathname }} 
        replace 
      />
    );
  }

  // Not authorized - show fallback or access denied
  if (!isAuthorized) {
    if (fallback) {
      return fallback;
    }

    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="mx-auto h-16 w-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-4">
            {requiredPermission 
              ? `You don't have the required permission: ${requiredPermission}`
              : requiredRole
              ? `You don't have the required role: ${requiredRole}`
              : 'You are not authorized to access this page.'
            }
          </p>
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // Authorized - render children
  return children;
};

export default ProtectedRoute;