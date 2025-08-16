import React, { createContext, useContext, useEffect, useState } from 'react';

const OrganizationContext = createContext();

export const useOrganization = () => {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error('useOrganization must be used within an OrganizationProvider');
  }
  return context;
};

export const OrganizationProvider = ({ children }) => {
  const [organization, setOrganization] = useState({
    name: 'ChurnGuard',
    logoUrl: '',
    primaryColor: '#DAA520',
    secondaryColor: '#B8860B',
    customCss: '',
    tier: 'starter', // starter, professional, enterprise
  });

  useEffect(() => {
    // Load organization data from localStorage or API
    const storedOrg = localStorage.getItem('churnguard-organization');
    if (storedOrg) {
      try {
        const parsedOrg = JSON.parse(storedOrg);
        setOrganization(prev => ({ ...prev, ...parsedOrg }));
      } catch (error) {
        console.error('Failed to parse organization data:', error);
      }
    }
  }, []);

  useEffect(() => {
    // Apply organization branding to CSS variables
    const root = document.documentElement;
    
    // Apply colors
    root.style.setProperty('--org-primary', organization.primaryColor);
    root.style.setProperty('--org-secondary', organization.secondaryColor);
    root.style.setProperty('--brand-primary', organization.primaryColor);
    root.style.setProperty('--brand-secondary', organization.secondaryColor);
    
    // Apply logo
    if (organization.logoUrl) {
      root.style.setProperty('--org-logo-url', `url(${organization.logoUrl})`);
    }
    
    // Apply organization name
    root.style.setProperty('--org-name', `'${organization.name}'`);
    
    // Apply custom CSS for enterprise tier
    if (organization.tier === 'enterprise' && organization.customCss) {
      let customStyleEl = document.getElementById('custom-org-styles');
      if (!customStyleEl) {
        customStyleEl = document.createElement('style');
        customStyleEl.id = 'custom-org-styles';
        document.head.appendChild(customStyleEl);
      }
      customStyleEl.textContent = organization.customCss;
    }
  }, [organization]);

  const updateOrganization = (updates) => {
    const newOrg = { ...organization, ...updates };
    setOrganization(newOrg);
    localStorage.setItem('churnguard-organization', JSON.stringify(newOrg));
  };

  const resetToDefault = () => {
    const defaultOrg = {
      name: 'ChurnGuard',
      logoUrl: '',
      primaryColor: '#DAA520',
      secondaryColor: '#B8860B',
      customCss: '',
      tier: 'starter',
    };
    setOrganization(defaultOrg);
    localStorage.removeItem('churnguard-organization');
  };

  return (
    <OrganizationContext.Provider value={{ 
      organization, 
      updateOrganization, 
      resetToDefault 
    }}>
      {children}
    </OrganizationContext.Provider>
  );
};