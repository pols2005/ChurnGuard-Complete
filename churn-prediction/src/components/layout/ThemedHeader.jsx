import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

const ThemedHeader = ({ onMenuToggle, showMenuToggle = true, title = null }) => {
  const { theme } = useTheme();
  const { user, organization, logout } = useAuth();

  if (!theme) return null;

  const companyName = theme.companyName || organization?.name || 'ChurnGuard';
  const logoUrl = theme.logo || '/logo.png';

  return (
    <header 
      className="sticky top-0 z-50 border-b shadow-sm"
      style={{
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        fontFamily: theme.fonts.primary
      }}
    >
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left side - Logo and Menu */}
          <div className="flex items-center space-x-4">
            {showMenuToggle && (
              <button
                onClick={onMenuToggle}
                className="p-2 rounded-md lg:hidden hover:bg-gray-100 transition-colors"
                style={{ color: theme.colors.text }}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            )}

            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <img
                  src={logoUrl}
                  alt={`${companyName} Logo`}
                  className="h-8 w-auto object-contain"
                  onError={(e) => {
                    // Fallback to default logo if custom logo fails to load
                    e.target.src = '/logo.png';
                  }}
                />
              </div>
              
              <div className="hidden sm:block">
                <h1 
                  className="text-xl font-bold"
                  style={{ 
                    color: theme.colors.text,
                    fontFamily: theme.fonts.heading 
                  }}
                >
                  {title || companyName}
                </h1>
                {organization && organization.name !== companyName && (
                  <p 
                    className="text-sm"
                    style={{ color: theme.colors.textSecondary }}
                  >
                    {organization.name}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Center - Navigation or page title */}
          <div className="hidden md:flex items-center space-x-6">
            <nav className="flex space-x-6">
              <a
                href="/dashboard"
                className="text-sm font-medium hover:opacity-80 transition-opacity"
                style={{ color: theme.colors.text }}
              >
                Dashboard
              </a>
              <a
                href="/customers"
                className="text-sm font-medium hover:opacity-80 transition-opacity"
                style={{ color: theme.colors.textSecondary }}
              >
                Customers
              </a>
              <a
                href="/predictions"
                className="text-sm font-medium hover:opacity-80 transition-opacity"
                style={{ color: theme.colors.textSecondary }}
              >
                Predictions
              </a>
              <a
                href="/analytics"
                className="text-sm font-medium hover:opacity-80 transition-opacity"
                style={{ color: theme.colors.textSecondary }}
              >
                Analytics
              </a>
            </nav>
          </div>

          {/* Right side - User menu */}
          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <button
              className="p-2 rounded-md hover:bg-gray-100 transition-colors relative"
              style={{ color: theme.colors.textSecondary }}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM10.5 3.5L6.5 7.5h3v6h2v-6h3l-4-4z" />
              </svg>
              <span 
                className="absolute -top-1 -right-1 w-3 h-3 rounded-full text-xs flex items-center justify-center"
                style={{ backgroundColor: theme.colors.danger, color: 'white' }}
              >
                3
              </span>
            </button>

            {/* Theme indicator (subtle) */}
            {theme.id !== 'default' && (
              <div className="hidden lg:block">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: theme.colors.primary }}
                  title="Custom theme active"
                />
              </div>
            )}

            {/* User dropdown */}
            <div className="relative">
              <div className="flex items-center space-x-3">
                <div className="hidden sm:block text-right">
                  <p 
                    className="text-sm font-medium"
                    style={{ color: theme.colors.text }}
                  >
                    {user?.name || user?.email || 'User'}
                  </p>
                  <p 
                    className="text-xs capitalize"
                    style={{ color: theme.colors.textSecondary }}
                  >
                    {user?.role || 'user'}
                  </p>
                </div>
                
                <div 
                  className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium"
                  style={{ backgroundColor: theme.colors.primary }}
                >
                  {(user?.name || user?.email || 'U')[0].toUpperCase()}
                </div>
              </div>
            </div>

            {/* Settings */}
            {user?.role === 'admin' && (
              <a
                href="/admin/theme"
                className="p-2 rounded-md hover:bg-gray-100 transition-colors"
                style={{ color: theme.colors.textSecondary }}
                title="Theme Customization"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v14a4 4 0 01-4 4zM21 5a2 2 0 00-2-2h-4a2 2 0 00-2 2v14a4 4 0 004 4h4a2 2 0 002-2V5z" />
                </svg>
              </a>
            )}

            {/* Logout */}
            <button
              onClick={logout}
              className="p-2 rounded-md hover:bg-gray-100 transition-colors"
              style={{ color: theme.colors.textSecondary }}
              title="Logout"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default ThemedHeader;