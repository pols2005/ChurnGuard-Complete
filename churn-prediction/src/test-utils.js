import React from 'react';
import { render } from '@testing-library/react';
import { ThemeProvider } from './contexts/ThemeContext';
import { OrganizationProvider } from './contexts/OrganizationContext';
import { SubscriptionProvider } from './contexts/SubscriptionContext';

// Mock localStorage for tests
export const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

// Mock matchMedia for theme tests
export const mockMatchMedia = (matches = false) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
};

// Custom render with all providers
export const renderWithProviders = (ui, options = {}) => {
  const {
    theme = 'light',
    subscription = 'starter',
    organization = { name: 'ChurnGuard', primaryColor: '#DAA520' },
    ...renderOptions
  } = options;

  // Setup localStorage mocks
  global.localStorage = mockLocalStorage;
  
  mockLocalStorage.getItem.mockImplementation((key) => {
    switch (key) {
      case 'churnguard-theme':
        return theme;
      case 'churnguard-subscription-tier':
        return subscription;
      case 'churnguard-organization':
        return JSON.stringify(organization);
      default:
        return null;
    }
  });

  mockMatchMedia();

  const AllProviders = ({ children }) => {
    return (
      <SubscriptionProvider>
        <OrganizationProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </OrganizationProvider>
      </SubscriptionProvider>
    );
  };

  return render(ui, { wrapper: AllProviders, ...renderOptions });
};

// Test data factories
export const createMockCustomer = (overrides = {}) => ({
  CustomerId: 'CUST001',
  Surname: 'TestSurname',
  CreditScore: 650,
  Geography: 'TestCity',
  Gender: 'Male',
  Age: 35,
  Tenure: 5,
  Balance: 50000,
  NumOfProducts: 2,
  HasCrCard: 1,
  IsActiveMember: 1,
  EstimatedSalary: 75000,
  ...overrides,
});

export const createMockChurnData = (overrides = {}) => ({
  average_probability: 0.25,
  model_probabilities: {
    'Random Forest': 0.23,
    'Gradient Boosting': 0.27,
    'Logistic Regression': 0.25,
  },
  percentiles: {
    'Credit Score': 75,
    'Age': 45,
    'Balance': 60,
    'Estimated Salary': 70,
  },
  explanation: 'The customer shows moderate churn risk based on...',
  email_content: 'Dear Customer, we noticed...',
  ...overrides,
});

// Mock API responses
export const mockApiResponses = {
  customers: [
    { CustomerId: 'CUST001', Surname: 'Smith' },
    { CustomerId: 'CUST002', Surname: 'Johnson' },
  ],
  customer: createMockCustomer(),
  churnProbability: { average_probability: 0.25 },
  modelProbabilities: {
    model_probabilities: {
      'Random Forest': 0.23,
      'Gradient Boosting': 0.27,
      'Logistic Regression': 0.25,
    },
  },
  percentiles: {
    percentiles: {
      'Credit Score': 75,
      'Age': 45,
      'Balance': 60,
      'Estimated Salary': 70,
    },
  },
  explanationWithEmail: {
    explanation: 'The customer shows moderate churn risk...',
    email_content: 'Dear Customer, we noticed...',
  },
};

// Setup fetch mock
export const setupFetchMock = (responses = mockApiResponses) => {
  global.fetch = jest.fn((url) => {
    if (url.includes('/customers')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(responses.customers),
      });
    }
    if (url.includes('/customer/') && url.includes('/churn-probability')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(responses.churnProbability),
      });
    }
    if (url.includes('/customer/') && url.includes('/churn-model-probabilities')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(responses.modelProbabilities),
      });
    }
    if (url.includes('/customer/') && url.includes('/feature-percentiles')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(responses.percentiles),
      });
    }
    if (url.includes('/explanationwithemail/')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(responses.explanationWithEmail),
      });
    }
    if (url.includes('/customer/')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ customer: responses.customer }),
      });
    }
    
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({}),
    });
  });
};

// Performance mocks
export const setupPerformanceMocks = () => {
  global.PerformanceObserver = jest.fn().mockImplementation((callback) => ({
    observe: jest.fn(),
    disconnect: jest.fn(),
  }));

  global.performance = {
    ...global.performance,
    now: jest.fn(() => 123.45),
    memory: {
      usedJSHeapSize: 12345678,
    },
  };
};

// Cleanup function for tests
export const cleanup = () => {
  mockLocalStorage.getItem.mockClear();
  mockLocalStorage.setItem.mockClear();
  mockLocalStorage.removeItem.mockClear();
  mockLocalStorage.clear.mockClear();
  
  if (global.fetch) {
    global.fetch.mockClear();
  }
  
  document.documentElement.className = '';
};