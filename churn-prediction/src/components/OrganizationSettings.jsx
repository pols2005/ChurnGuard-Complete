import React, { useState } from 'react';
import { useOrganization } from '../contexts/OrganizationContext';
import { useSubscription } from '../contexts/SubscriptionContext';
import FeatureGate from './FeatureGate';
import UsageDashboard from './UsageDashboard';
import ExportFeature from './ExportFeature';

const OrganizationSettings = ({ isOpen, onClose }) => {
  const { organization, updateOrganization } = useOrganization();
  const { hasFeature, currentTier } = useSubscription();
  
  const [formData, setFormData] = useState({
    name: organization.name,
    logoUrl: organization.logoUrl,
    primaryColor: organization.primaryColor,
    secondaryColor: organization.secondaryColor,
    customCss: organization.customCss || ''
  });

  const [logoFile, setLogoFile] = useState(null);
  const [previewLogo, setPreviewLogo] = useState(organization.logoUrl);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleLogoUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setLogoFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviewLogo(e.target.result);
        setFormData(prev => ({ ...prev, logoUrl: e.target.result }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSave = () => {
    updateOrganization(formData);
    onClose();
  };

  const handleReset = () => {
    setFormData({
      name: 'ChurnGuard',
      logoUrl: '',
      primaryColor: '#DAA520',
      secondaryColor: '#B8860B',
      customCss: ''
    });
    setPreviewLogo('');
    setLogoFile(null);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                Organization Settings
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Current plan: <span className="font-semibold capitalize">{currentTier}</span>
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Usage Dashboard */}
          <UsageDashboard />

          {/* Organization Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Organization Name
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary focus:border-primary"
              placeholder="Enter organization name"
            />
          </div>

          {/* Logo Upload */}
          <FeatureGate 
            feature="logoUpload" 
            requiredTier="professional"
            fallback={
              <div className="opacity-50">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Organization Logo (Professional+ Feature)
                </label>
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
                  <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <p className="text-gray-500">Logo upload requires Professional plan</p>
                </div>
              </div>
            }
          >
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Organization Logo
              </label>
              <div className="flex items-center space-x-4">
                {previewLogo && (
                  <img 
                    src={previewLogo} 
                    alt="Logo preview" 
                    className="w-16 h-16 object-contain rounded-lg border border-gray-200 dark:border-gray-600"
                  />
                )}
                <div>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleLogoUpload}
                    className="hidden"
                    id="logo-upload"
                  />
                  <label
                    htmlFor="logo-upload"
                    className="cursor-pointer inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    Upload Logo
                  </label>
                  <p className="text-xs text-gray-500 mt-1">PNG, JPG up to 2MB</p>
                </div>
              </div>
            </div>
          </FeatureGate>

          {/* Color Customization */}
          <FeatureGate 
            feature="customColors" 
            requiredTier="professional"
            fallback={
              <div className="opacity-50 space-y-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Brand Colors (Professional+ Feature)
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Primary Color</label>
                    <div className="w-full h-10 bg-gray-300 rounded-lg"></div>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Secondary Color</label>
                    <div className="w-full h-10 bg-gray-300 rounded-lg"></div>
                  </div>
                </div>
              </div>
            }
          >
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Primary Color
                </label>
                <div className="flex items-center space-x-3">
                  <input
                    type="color"
                    name="primaryColor"
                    value={formData.primaryColor}
                    onChange={handleInputChange}
                    className="w-12 h-10 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer"
                  />
                  <input
                    type="text"
                    name="primaryColor"
                    value={formData.primaryColor}
                    onChange={handleInputChange}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary focus:border-primary"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Secondary Color
                </label>
                <div className="flex items-center space-x-3">
                  <input
                    type="color"
                    name="secondaryColor"
                    value={formData.secondaryColor}
                    onChange={handleInputChange}
                    className="w-12 h-10 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer"
                  />
                  <input
                    type="text"
                    name="secondaryColor"
                    value={formData.secondaryColor}
                    onChange={handleInputChange}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary focus:border-primary"
                  />
                </div>
              </div>
            </div>
          </FeatureGate>

          {/* Custom CSS */}
          <FeatureGate 
            feature="customCss" 
            requiredTier="enterprise"
            fallback={
              <div className="opacity-50">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Custom CSS (Enterprise Feature)
                </label>
                <textarea
                  disabled
                  rows="6"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-500"
                  placeholder="Custom CSS injection available with Enterprise plan..."
                />
              </div>
            }
          >
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Custom CSS
              </label>
              <textarea
                name="customCss"
                value={formData.customCss}
                onChange={handleInputChange}
                rows="6"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary focus:border-primary font-mono text-sm"
                placeholder="/* Enter custom CSS here */&#10;.custom-header {&#10;  background: linear-gradient(45deg, #f00, #00f);&#10;}"
              />
              <p className="text-xs text-gray-500 mt-1">
                Add custom CSS to further customize the appearance of your ChurnGuard instance.
              </p>
            </div>
          </FeatureGate>

          {/* Export Feature */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Data Export</h3>
            <ExportFeature />
          </div>

          {/* Preview Section */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Preview</h3>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center space-x-3 mb-3">
                {previewLogo && (
                  <img src={previewLogo} alt="Logo" className="w-8 h-8 object-contain" />
                )}
                <span className="text-xl font-bold" style={{ color: formData.primaryColor }}>
                  {formData.name}
                </span>
              </div>
              <div className="flex space-x-2">
                <div 
                  className="w-16 h-8 rounded" 
                  style={{ backgroundColor: formData.primaryColor }}
                  title={`Primary: ${formData.primaryColor}`}
                />
                <div 
                  className="w-16 h-8 rounded" 
                  style={{ backgroundColor: formData.secondaryColor }}
                  title={`Secondary: ${formData.secondaryColor}`}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-6 flex justify-between">
          <button
            onClick={handleReset}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200"
          >
            Reset to Default
          </button>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-6 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg font-medium transition-colors duration-200"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrganizationSettings;