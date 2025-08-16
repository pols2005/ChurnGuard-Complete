import React from 'react';
import { useOrganization } from './contexts/OrganizationContext';

const Heading = () => {
  const { organization } = useOrganization();

  return (
    <header className="mb-8 text-center">
      <div className="flex items-center justify-center space-x-4 mb-4">
        {organization.logoUrl && (
          <img 
            src={organization.logoUrl} 
            alt={`${organization.name} logo`}
            className="w-16 h-16 object-contain"
          />
        )}
        <h1 className="text-5xl font-bold text-primary bg-gradient-to-r from-primary via-secondary to-primary bg-clip-text text-transparent">
          {organization.name}
        </h1>
      </div>
      <p className="text-gray-600 dark:text-gray-400 mt-3 text-lg max-w-2xl mx-auto">
        An effective solution for customer churn prediction and mitigation
      </p>
      <div className="mt-4 h-1 w-24 bg-gradient-to-r from-primary to-secondary mx-auto rounded-full"></div>
    </header>
  );
};

export default Heading;

