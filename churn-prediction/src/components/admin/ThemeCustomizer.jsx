import React, { useState, useRef } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

const ThemeCustomizer = () => {
  const { theme, updateTheme, resetTheme, getThemePresets, customCSS } = useTheme();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('colors');
  const [saving, setSaving] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [previewChanges, setPreviewChanges] = useState({});
  const [customCSSInput, setCustomCSSInput] = useState(customCSS || '');
  const logoUploadRef = useRef();

  if (!user || user.role !== 'admin') {
    return (
      <div className="p-6 text-center">
        <div className="text-gray-500">
          <div className="text-4xl mb-2">🔒</div>
          <div>Access Denied</div>
          <div className="text-sm">Only administrators can customize themes</div>
        </div>
      </div>
    );
  }

  if (!theme) {
    return <div className="p-6">Loading theme...</div>;
  }

  const currentTheme = { ...theme, ...previewChanges };

  const handleColorChange = (colorKey, value) => {
    setPreviewChanges(prev => ({
      ...prev,
      colors: { ...(prev.colors || theme.colors), [colorKey]: value }
    }));
  };

  const handleFontChange = (fontKey, value) => {
    setPreviewChanges(prev => ({
      ...prev,
      fonts: { ...(prev.fonts || theme.fonts), [fontKey]: value }
    }));
  };

  const handleCompanyInfoChange = (field, value) => {
    setPreviewChanges(prev => ({ ...prev, [field]: value }));
  };

  const handlePresetSelect = (preset) => {
    setPreviewChanges(prev => ({
      ...prev,
      colors: { ...(prev.colors || theme.colors), ...preset.colors }
    }));
  };

  const handleSaveChanges = async () => {
    setSaving(true);
    try {
      const result = await updateTheme(previewChanges, customCSSInput);
      if (result.success) {
        setPreviewChanges({});
        alert('Theme updated successfully!');
      } else {
        alert('Failed to update theme: ' + result.error);
      }
    } catch (error) {
      alert('Error updating theme: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleResetTheme = async () => {
    if (confirm('Are you sure you want to reset to the default theme? This will remove all customizations.')) {
      setSaving(true);
      try {
        await resetTheme();
        setPreviewChanges({});
        setCustomCSSInput('');
        alert('Theme reset successfully!');
      } catch (error) {
        alert('Error resetting theme: ' + error.message);
      } finally {
        setSaving(false);
      }
    }
  };

  const handleLogoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingLogo(true);
    try {
      const formData = new FormData();
      formData.append('logo', file);
      
      const response = await fetch('/api/upload/logo', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        const { logoUrl } = await response.json();
        handleCompanyInfoChange('logo', logoUrl);
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      alert('Error uploading logo: ' + error.message);
    } finally {
      setUploadingLogo(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Theme Customization</h1>
        <p className="text-gray-600">Customize your organization's branding and appearance</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'colors', name: 'Colors', icon: '🎨' },
            { id: 'branding', name: 'Branding', icon: '🏢' },
            { id: 'typography', name: 'Typography', icon: '📝' },
            { id: 'advanced', name: 'Advanced CSS', icon: '⚙️' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings Panel */}
        <div className="lg:col-span-2">
          {/* Colors Tab */}
          {activeTab === 'colors' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Color Presets</h3>
                <div className="grid grid-cols-2 gap-3">
                  {getThemePresets().map(preset => (
                    <button
                      key={preset.id}
                      onClick={() => handlePresetSelect(preset)}
                      className="p-3 border border-gray-200 rounded-lg hover:shadow-sm transition-shadow text-left"
                    >
                      <div className="flex items-center space-x-3 mb-2">
                        <div
                          className="w-6 h-6 rounded-full"
                          style={{ backgroundColor: preset.colors.primary }}
                        />
                        <span className="font-medium">{preset.name}</span>
                      </div>
                      <div className="flex space-x-1">
                        {Object.values(preset.colors).slice(0, 3).map((color, idx) => (
                          <div
                            key={idx}
                            className="w-4 h-4 rounded"
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Custom Colors</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(currentTheme.colors).map(([key, value]) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-gray-700 mb-1 capitalize">
                        {key.replace(/([A-Z])/g, ' $1').toLowerCase()}
                      </label>
                      <div className="flex items-center space-x-3">
                        <input
                          type="color"
                          value={value}
                          onChange={(e) => handleColorChange(key, e.target.value)}
                          className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                        />
                        <input
                          type="text"
                          value={value}
                          onChange={(e) => handleColorChange(key, e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
                          placeholder="#000000"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Branding Tab */}
          {activeTab === 'branding' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Company Information</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company Name
                    </label>
                    <input
                      type="text"
                      value={currentTheme.companyName || ''}
                      onChange={(e) => handleCompanyInfoChange('companyName', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      placeholder="Your Company Name"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Logo
                    </label>
                    <div className="flex items-center space-x-4">
                      {currentTheme.logo && (
                        <img
                          src={currentTheme.logo}
                          alt="Company Logo"
                          className="h-12 w-auto object-contain border border-gray-200 rounded p-1"
                        />
                      )}
                      <div>
                        <input
                          ref={logoUploadRef}
                          type="file"
                          accept="image/*"
                          onChange={handleLogoUpload}
                          className="hidden"
                        />
                        <button
                          onClick={() => logoUploadRef.current?.click()}
                          disabled={uploadingLogo}
                          className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                        >
                          {uploadingLogo ? 'Uploading...' : 'Upload Logo'}
                        </button>
                        <p className="text-xs text-gray-500 mt-1">
                          Recommended: PNG or SVG, max 2MB
                        </p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Favicon URL
                    </label>
                    <input
                      type="url"
                      value={currentTheme.favicon || ''}
                      onChange={(e) => handleCompanyInfoChange('favicon', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      placeholder="/favicon.ico"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Typography Tab */}
          {activeTab === 'typography' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Font Settings</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Primary Font
                    </label>
                    <select
                      value={currentTheme.fonts.primary}
                      onChange={(e) => handleFontChange('primary', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    >
                      <option value="Inter, -apple-system, BlinkMacSystemFont, sans-serif">Inter</option>
                      <option value="'Helvetica Neue', Helvetica, Arial, sans-serif">Helvetica</option>
                      <option value="'Roboto', sans-serif">Roboto</option>
                      <option value="'Open Sans', sans-serif">Open Sans</option>
                      <option value="'Lato', sans-serif">Lato</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Heading Font
                    </label>
                    <select
                      value={currentTheme.fonts.heading}
                      onChange={(e) => handleFontChange('heading', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    >
                      <option value="Inter, -apple-system, BlinkMacSystemFont, sans-serif">Inter</option>
                      <option value="'Helvetica Neue', Helvetica, Arial, sans-serif">Helvetica</option>
                      <option value="'Roboto', sans-serif">Roboto</option>
                      <option value="'Playfair Display', serif">Playfair Display</option>
                      <option value="'Merriweather', serif">Merriweather</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Advanced CSS Tab */}
          {activeTab === 'advanced' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Custom CSS</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Add custom CSS to further customize your dashboard appearance. Use CSS custom properties 
                  like <code className="bg-gray-100 px-1 rounded">var(--color-primary)</code> to reference theme colors.
                </p>
                <textarea
                  value={customCSSInput}
                  onChange={(e) => setCustomCSSInput(e.target.value)}
                  className="w-full h-64 px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
                  placeholder="/* Custom CSS */
.dashboard-header {
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
}

.widget {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}"
                />
                <p className="text-xs text-gray-500 mt-2">
                  Changes will be applied after saving. Invalid CSS may break the interface.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Preview Panel */}
        <div className="lg:col-span-1">
          <div className="sticky top-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Preview</h3>
            <div 
              className="border border-gray-300 rounded-lg overflow-hidden"
              style={{
                backgroundColor: currentTheme.colors.background,
                color: currentTheme.colors.text,
                fontFamily: currentTheme.fonts.primary
              }}
            >
              {/* Mock header */}
              <div 
                className="p-4 flex items-center justify-between"
                style={{ backgroundColor: currentTheme.colors.surface, borderBottom: `1px solid ${currentTheme.colors.border}` }}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gray-300 rounded flex items-center justify-center text-xs">
                    {currentTheme.logo ? (
                      <img src={currentTheme.logo} alt="Logo" className="w-6 h-6 object-contain" />
                    ) : (
                      'Logo'
                    )}
                  </div>
                  <h2 className="font-bold" style={{ fontFamily: currentTheme.fonts.heading }}>
                    {currentTheme.companyName || 'Your Company'}
                  </h2>
                </div>
              </div>

              {/* Mock content */}
              <div className="p-4 space-y-4">
                <button 
                  className="w-full py-2 px-4 rounded text-white font-medium"
                  style={{ backgroundColor: currentTheme.colors.primary }}
                >
                  Primary Button
                </button>
                
                <div 
                  className="p-3 rounded"
                  style={{ backgroundColor: currentTheme.colors.surface, border: `1px solid ${currentTheme.colors.border}` }}
                >
                  <h4 className="font-medium mb-2" style={{ fontFamily: currentTheme.fonts.heading }}>
                    Widget Title
                  </h4>
                  <p className="text-sm" style={{ color: currentTheme.colors.textSecondary }}>
                    This is how your dashboard widgets will look with the current theme.
                  </p>
                </div>

                <div className="flex space-x-2">
                  <span 
                    className="px-2 py-1 rounded-full text-xs"
                    style={{ backgroundColor: currentTheme.colors.accent + '20', color: currentTheme.colors.accent }}
                  >
                    Accent Color
                  </span>
                  <span 
                    className="px-2 py-1 rounded-full text-xs"
                    style={{ backgroundColor: currentTheme.colors.warning + '20', color: currentTheme.colors.warning }}
                  >
                    Warning
                  </span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-4 space-y-2">
              <button
                onClick={handleSaveChanges}
                disabled={saving || Object.keys(previewChanges).length === 0}
                className="w-full py-2 px-4 bg-primary text-white rounded-md font-medium hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
              
              <button
                onClick={handleResetTheme}
                disabled={saving}
                className="w-full py-2 px-4 bg-gray-500 text-white rounded-md font-medium hover:bg-gray-600 disabled:opacity-50"
              >
                Reset to Default
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThemeCustomizer;