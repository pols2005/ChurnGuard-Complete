import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useForm } from 'react-hook-form';
import { toast } from 'react-toastify';

const UserProfile = ({ onClose = null }) => {
  const { user, updateProfile, changePassword, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);

  const {
    register: registerProfile,
    handleSubmit: handleSubmitProfile,
    formState: { errors: profileErrors }
  } = useForm({
    defaultValues: {
      firstName: user?.firstName || '',
      lastName: user?.lastName || '',
      email: user?.email || '',
      phone: user?.phone || '',
      timezone: user?.timezone || 'UTC',
      locale: user?.locale || 'en'
    }
  });

  const {
    register: registerPassword,
    handleSubmit: handleSubmitPassword,
    formState: { errors: passwordErrors },
    watch,
    reset: resetPassword
  } = useForm();

  const watchPassword = watch('newPassword');

  const onSubmitProfile = async (data) => {
    setLoading(true);
    try {
      const result = await updateProfile(data);
      if (result.success) {
        toast.success('Profile updated successfully');
      } else {
        toast.error(result.error || 'Failed to update profile');
      }
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const onSubmitPassword = async (data) => {
    setLoading(true);
    try {
      const result = await changePassword(data.currentPassword, data.newPassword);
      if (result.success) {
        toast.success('Password changed successfully');
        resetPassword();
      } else {
        toast.error(result.error || 'Failed to change password');
      }
    } catch (error) {
      toast.error('Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    if (window.confirm('Are you sure you want to sign out?')) {
      await logout();
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: 'user' },
    { id: 'security', label: 'Security', icon: 'shield' },
    { id: 'preferences', label: 'Preferences', icon: 'settings' }
  ];

  const getTabIcon = (icon) => {
    switch (icon) {
      case 'user':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        );
      case 'shield':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        );
      case 'settings':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={onClose}></div>

        <div className="inline-block w-full max-w-4xl px-4 pt-5 pb-4 overflow-hidden text-left align-bottom transition-all transform bg-white rounded-lg shadow-xl sm:my-8 sm:align-middle sm:p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-medium text-gray-900">User Profile</h3>
            {onClose && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* User Info Header */}
          <div className="flex items-center space-x-4 mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="h-16 w-16 bg-indigo-600 rounded-full flex items-center justify-center">
              <span className="text-xl font-bold text-white">
                {user?.firstName?.[0]}{user?.lastName?.[0]}
              </span>
            </div>
            <div>
              <h4 className="text-lg font-semibold text-gray-900">
                {user?.firstName} {user?.lastName}
              </h4>
              <p className="text-gray-600">{user?.email}</p>
              <p className="text-sm text-gray-500">
                {user?.role} • {user?.organization?.name}
              </p>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
                >
                  {getTabIcon(tab.icon)}
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="space-y-6">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <form onSubmit={handleSubmitProfile(onSubmitProfile)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">First Name</label>
                    <input
                      {...registerProfile('firstName', { required: 'First name is required' })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    {profileErrors.firstName && (
                      <p className="mt-1 text-sm text-red-600">{profileErrors.firstName.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Last Name</label>
                    <input
                      {...registerProfile('lastName', { required: 'Last name is required' })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    {profileErrors.lastName && (
                      <p className="mt-1 text-sm text-red-600">{profileErrors.lastName.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <input
                      {...registerProfile('email', { 
                        required: 'Email is required',
                        pattern: {
                          value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                          message: 'Invalid email address'
                        }
                      })}
                      type="email"
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    {profileErrors.email && (
                      <p className="mt-1 text-sm text-red-600">{profileErrors.email.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Phone</label>
                    <input
                      {...registerProfile('phone')}
                      type="tel"
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Timezone</label>
                    <select
                      {...registerProfile('timezone')}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="UTC">UTC</option>
                      <option value="America/New_York">Eastern Time</option>
                      <option value="America/Chicago">Central Time</option>
                      <option value="America/Denver">Mountain Time</option>
                      <option value="America/Los_Angeles">Pacific Time</option>
                      <option value="Europe/London">London</option>
                      <option value="Europe/Paris">Paris</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Language</label>
                    <select
                      {...registerProfile('locale')}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    {loading ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            )}

            {/* Security Tab */}
            {activeTab === 'security' && (
              <div className="space-y-6">
                <form onSubmit={handleSubmitPassword(onSubmitPassword)} className="space-y-6">
                  <h4 className="text-lg font-medium text-gray-900">Change Password</h4>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Current Password</label>
                    <input
                      {...registerPassword('currentPassword', { required: 'Current password is required' })}
                      type="password"
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    {passwordErrors.currentPassword && (
                      <p className="mt-1 text-sm text-red-600">{passwordErrors.currentPassword.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">New Password</label>
                    <input
                      {...registerPassword('newPassword', { 
                        required: 'New password is required',
                        minLength: {
                          value: 8,
                          message: 'Password must be at least 8 characters'
                        }
                      })}
                      type="password"
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    {passwordErrors.newPassword && (
                      <p className="mt-1 text-sm text-red-600">{passwordErrors.newPassword.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
                    <input
                      {...registerPassword('confirmPassword', { 
                        required: 'Please confirm your password',
                        validate: value => value === watchPassword || 'Passwords do not match'
                      })}
                      type="password"
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    {passwordErrors.confirmPassword && (
                      <p className="mt-1 text-sm text-red-600">{passwordErrors.confirmPassword.message}</p>
                    )}
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={loading}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                      {loading ? 'Changing...' : 'Change Password'}
                    </button>
                  </div>
                </form>

                <div className="pt-6 border-t border-gray-200">
                  <h4 className="text-lg font-medium text-gray-900 mb-4">Account Actions</h4>
                  <button
                    onClick={handleLogout}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                  >
                    Sign Out
                  </button>
                </div>
              </div>
            )}

            {/* Preferences Tab */}
            {activeTab === 'preferences' && (
              <div className="space-y-6">
                <h4 className="text-lg font-medium text-gray-900">Notification Preferences</h4>
                <div className="space-y-4">
                  <label className="flex items-center">
                    <input type="checkbox" className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" />
                    <span className="ml-2 text-sm text-gray-700">Email notifications for churn alerts</span>
                  </label>
                  <label className="flex items-center">
                    <input type="checkbox" className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" />
                    <span className="ml-2 text-sm text-gray-700">Weekly summary reports</span>
                  </label>
                  <label className="flex items-center">
                    <input type="checkbox" className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" />
                    <span className="ml-2 text-sm text-gray-700">Product updates and announcements</span>
                  </label>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;