import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

const AuthLayout = ({ children, title, subtitle, showLogo = true }) => {
  const { organization } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          {showLogo && (
            <div className="mx-auto h-12 w-12 bg-indigo-600 rounded-lg flex items-center justify-center mb-6">
              {organization?.logoUrl ? (
                <img 
                  src={organization.logoUrl} 
                  alt={organization.name}
                  className="h-8 w-8 object-contain"
                />
              ) : (
                <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              )}
            </div>
          )}
          
          <h2 className="text-3xl font-bold text-gray-900">
            {title}
          </h2>
          
          {subtitle && (
            <p className="mt-2 text-sm text-gray-600">
              {subtitle}
            </p>
          )}
        </div>

        {/* Content Card */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {children}
        </div>

        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            © 2024 {organization?.name || 'ChurnGuard'}. All rights reserved.
          </p>
          <div className="flex justify-center space-x-4 mt-2">
            <a href="#privacy" className="text-xs text-gray-500 hover:text-gray-700">
              Privacy Policy
            </a>
            <a href="#terms" className="text-xs text-gray-500 hover:text-gray-700">
              Terms of Service
            </a>
            <a href="#support" className="text-xs text-gray-500 hover:text-gray-700">
              Support
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;