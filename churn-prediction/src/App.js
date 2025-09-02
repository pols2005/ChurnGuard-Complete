import React from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { OrganizationProvider } from './contexts/OrganizationContext';
import { SubscriptionProvider } from './contexts/SubscriptionContext';
import { AuthProvider } from './contexts/AuthContext';
import { DashboardProvider } from './contexts/DashboardContext';
import DashboardBuilder from './components/DashboardBuilder';
import ThemeToggle from './components/ThemeToggle';
import SettingsButton from './components/SettingsButton';
import PerformanceMonitor from './components/PerformanceMonitor';

const App = () => {
  return (
    <SubscriptionProvider>
      <OrganizationProvider>
        <ThemeProvider>
          <AuthProvider>
            <DashboardProvider>
              <div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 min-h-screen transition-colors duration-200">
                {/* Control Panel in top-right corner */}
                <div className="fixed top-4 right-4 z-50 flex space-x-2">
                  <SettingsButton />
                  <ThemeToggle />
                </div>
            
                {/* Main Dashboard Content */}
                <DashboardBuilder />
                
                {/* Performance Monitor */}
                <PerformanceMonitor />
              </div>
            </DashboardProvider>
          </AuthProvider>
        </ThemeProvider>
      </OrganizationProvider>
    </SubscriptionProvider>
  );
};

export default App;