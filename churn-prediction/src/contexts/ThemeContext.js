import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children, organization }) => {
  const [currentTheme, setCurrentTheme] = useState(null);
  const [customCSS, setCustomCSS] = useState('');
  
  // Default ChurnGuard theme
  const defaultTheme = {
    id: 'default',
    name: 'ChurnGuard Default',
    colors: {
      primary: '#3B82F6',
      primaryHover: '#2563EB',
      secondary: '#6B7280',
      accent: '#10B981',
      danger: '#EF4444',
      warning: '#F59E0B',
      background: '#F9FAFB',
      surface: '#FFFFFF',
      text: '#111827',
      textSecondary: '#6B7280',
      border: '#E5E7EB'
    },
    fonts: {
      primary: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
      heading: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif'
    },
    logo: '/logo.png',
    favicon: '/favicon.ico',
    borderRadius: '0.375rem',
    spacing: {
      xs: '0.25rem',
      sm: '0.5rem',
      md: '1rem',
      lg: '1.5rem',
      xl: '3rem'
    }
  };

  useEffect(() => {
    loadOrganizationTheme();
  }, [organization?.id]);

  useEffect(() => {
    if (currentTheme) {
      applyTheme(currentTheme);
    }
  }, [currentTheme]);

  const loadOrganizationTheme = async () => {
    try {
      if (!organization?.id) {
        setCurrentTheme(defaultTheme);
        return;
      }

      // Fetch organization's custom theme
      const response = await fetch(`/api/organizations/${organization.id}/theme`);
      if (response.ok) {
        const themeData = await response.json();
        const orgTheme = {
          ...defaultTheme,
          ...themeData.theme,
          colors: { ...defaultTheme.colors, ...themeData.theme?.colors },
          fonts: { ...defaultTheme.fonts, ...themeData.theme?.fonts },
          spacing: { ...defaultTheme.spacing, ...themeData.theme?.spacing }
        };
        
        setCurrentTheme(orgTheme);
        setCustomCSS(themeData.customCSS || '');
      } else {
        setCurrentTheme(defaultTheme);
      }
    } catch (error) {
      console.error('Failed to load organization theme:', error);
      setCurrentTheme(defaultTheme);
    }
  };

  const applyTheme = (theme) => {
    const root = document.documentElement;
    
    // Apply CSS custom properties
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });

    Object.entries(theme.fonts).forEach(([key, value]) => {
      root.style.setProperty(`--font-${key}`, value);
    });

    root.style.setProperty('--border-radius', theme.borderRadius);

    Object.entries(theme.spacing).forEach(([key, value]) => {
      root.style.setProperty(`--spacing-${key}`, value);
    });

    // Update document title and favicon if customized
    if (theme.companyName && theme.companyName !== 'ChurnGuard') {
      document.title = `${theme.companyName} - Dashboard`;
    }

    if (theme.favicon && theme.favicon !== defaultTheme.favicon) {
      const favicon = document.querySelector('link[rel="icon"]');
      if (favicon) {
        favicon.href = theme.favicon;
      }
    }

    // Apply custom CSS
    let customStyleElement = document.getElementById('custom-theme-styles');
    if (customStyleElement) {
      customStyleElement.remove();
    }

    if (customCSS.trim()) {
      customStyleElement = document.createElement('style');
      customStyleElement.id = 'custom-theme-styles';
      customStyleElement.textContent = customCSS;
      document.head.appendChild(customStyleElement);
    }
  };

  const updateTheme = async (themeUpdates, newCustomCSS = null) => {
    try {
      const updatedTheme = {
        ...currentTheme,
        ...themeUpdates,
        colors: { ...currentTheme.colors, ...themeUpdates.colors },
        fonts: { ...currentTheme.fonts, ...themeUpdates.fonts },
        spacing: { ...currentTheme.spacing, ...themeUpdates.spacing }
      };

      const payload = {
        theme: updatedTheme,
        customCSS: newCustomCSS !== null ? newCustomCSS : customCSS
      };

      const response = await fetch(`/api/organizations/${organization.id}/theme`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setCurrentTheme(updatedTheme);
        if (newCustomCSS !== null) {
          setCustomCSS(newCustomCSS);
        }
        return { success: true };
      } else {
        throw new Error('Failed to update theme');
      }
    } catch (error) {
      console.error('Error updating theme:', error);
      return { success: false, error: error.message };
    }
  };

  const resetTheme = async () => {
    return updateTheme(defaultTheme, '');
  };

  const getThemePresets = () => [
    {
      id: 'default',
      name: 'ChurnGuard Blue',
      colors: {
        primary: '#3B82F6',
        primaryHover: '#2563EB',
        accent: '#10B981'
      }
    },
    {
      id: 'corporate-red',
      name: 'Corporate Red',
      colors: {
        primary: '#DC2626',
        primaryHover: '#B91C1C',
        accent: '#059669'
      }
    },
    {
      id: 'modern-purple',
      name: 'Modern Purple',
      colors: {
        primary: '#7C3AED',
        primaryHover: '#6D28D9',
        accent: '#F59E0B'
      }
    },
    {
      id: 'professional-gray',
      name: 'Professional Gray',
      colors: {
        primary: '#374151',
        primaryHover: '#1F2937',
        accent: '#059669'
      }
    },
    {
      id: 'vibrant-green',
      name: 'Vibrant Green',
      colors: {
        primary: '#059669',
        primaryHover: '#047857',
        accent: '#F59E0B'
      }
    }
  ];

  const value = {
    theme: currentTheme,
    customCSS,
    updateTheme,
    resetTheme,
    loadOrganizationTheme,
    getThemePresets,
    isLoading: !currentTheme
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export default ThemeProvider;