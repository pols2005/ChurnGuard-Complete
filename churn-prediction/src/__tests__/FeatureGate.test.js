import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import FeatureGate from '../components/FeatureGate';
import { SubscriptionProvider } from '../contexts/SubscriptionContext';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

const MockSubscriptionProvider = ({ tier, children }) => {
  // Mock the subscription context with specific tier
  React.useEffect(() => {
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === 'churnguard-subscription-tier') return tier;
      return null;
    });
  }, [tier]);
  
  return <SubscriptionProvider>{children}</SubscriptionProvider>;
};

describe('FeatureGate', () => {
  beforeEach(() => {
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
  });

  it('renders children when user has access to feature', () => {
    render(
      <MockSubscriptionProvider tier="professional">
        <FeatureGate feature="customColors">
          <div data-testid="premium-content">Premium Content</div>
        </FeatureGate>
      </MockSubscriptionProvider>
    );

    expect(screen.getByTestId('premium-content')).toBeInTheDocument();
  });

  it('renders upgrade prompt when user lacks access', () => {
    render(
      <MockSubscriptionProvider tier="starter">
        <FeatureGate feature="customColors">
          <div data-testid="premium-content">Premium Content</div>
        </FeatureGate>
      </MockSubscriptionProvider>
    );

    expect(screen.getByText('Premium Feature')).toBeInTheDocument();
    expect(screen.getByText(/Upgrade to/)).toBeInTheDocument();
    expect(screen.queryByTestId('premium-content')).toBeInTheDocument(); // Should be present but with opacity
  });

  it('renders fallback when provided and showUpgradePrompt is false', () => {
    render(
      <MockSubscriptionProvider tier="starter">
        <FeatureGate 
          feature="customColors" 
          showUpgradePrompt={false}
          fallback={<div data-testid="fallback-content">Basic Content</div>}
        >
          <div data-testid="premium-content">Premium Content</div>
        </FeatureGate>
      </MockSubscriptionProvider>
    );

    expect(screen.getByTestId('fallback-content')).toBeInTheDocument();
    expect(screen.queryByTestId('premium-content')).not.toBeInTheDocument();
  });

  it('shows upgrade modal when upgrade button is clicked', () => {
    render(
      <MockSubscriptionProvider tier="starter">
        <FeatureGate feature="customColors">
          <div data-testid="premium-content">Premium Content</div>
        </FeatureGate>
      </MockSubscriptionProvider>
    );

    fireEvent.click(screen.getByText('Upgrade Now'));
    
    expect(screen.getByText('Upgrade Your Plan')).toBeInTheDocument();
  });

  it('respects requiredTier prop in upgrade message', () => {
    render(
      <MockSubscriptionProvider tier="starter">
        <FeatureGate feature="customCss" requiredTier="enterprise">
          <div data-testid="premium-content">Premium Content</div>
        </FeatureGate>
      </MockSubscriptionProvider>
    );

    expect(screen.getByText(/Upgrade to enterprise/)).toBeInTheDocument();
  });

  it('handles upgrade modal close', () => {
    render(
      <MockSubscriptionProvider tier="starter">
        <FeatureGate feature="customColors">
          <div data-testid="premium-content">Premium Content</div>
        </FeatureGate>
      </MockSubscriptionProvider>
    );

    // Open modal
    fireEvent.click(screen.getByText('Upgrade Now'));
    expect(screen.getByText('Upgrade Your Plan')).toBeInTheDocument();

    // Close modal
    fireEvent.click(screen.getByRole('button', { name: /close|×/i }));
    expect(screen.queryByText('Upgrade Your Plan')).not.toBeInTheDocument();
  });
});