import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock fetch for API calls
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve([]),
  })
);

// Mock performance API for PerformanceMonitor
global.PerformanceObserver = jest.fn().mockImplementation(() => ({
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

describe('Theme Integration', () => {
  beforeEach(() => {
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    document.documentElement.className = '';
    fetch.mockClear();
  });

  it('renders app with theme toggle', async () => {
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByTitle(/Current theme/)).toBeInTheDocument();
    });
  });

  it('switches themes when toggle is clicked', async () => {
    render(<App />);
    
    const themeToggle = await screen.findByTitle(/Current theme/);
    
    // Initial theme should be system (light)
    expect(document.documentElement.classList.contains('light')).toBe(true);
    
    // Click to switch to dark
    fireEvent.click(themeToggle);
    
    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });
    
    // Click to switch to system
    fireEvent.click(themeToggle);
    
    await waitFor(() => {
      expect(document.documentElement.classList.contains('light')).toBe(true);
    });
  });

  it('persists theme preference to localStorage', async () => {
    render(<App />);
    
    const themeToggle = await screen.findByTitle(/Current theme/);
    fireEvent.click(themeToggle);
    
    await waitFor(() => {
      expect(localStorageMock.setItem).toHaveBeenCalledWith('churnguard-theme', 'dark');
    });
  });

  it('applies theme to main app container', async () => {
    render(<App />);
    
    await waitFor(() => {
      const appContainer = document.querySelector('.bg-white.dark\\:bg-gray-900');
      expect(appContainer).toBeInTheDocument();
    });
  });

  it('settings button opens organization settings', async () => {
    render(<App />);
    
    const settingsButton = await screen.findByTitle('Organization Settings');
    fireEvent.click(settingsButton);
    
    await waitFor(() => {
      expect(screen.getByText('Organization Settings')).toBeInTheDocument();
    });
  });

  it('shows performance monitor', async () => {
    render(<App />);
    
    // Performance monitor should be hidden initially, but trigger button should exist
    await waitFor(() => {
      const perfButton = screen.getByTitle('Show Performance Monitor');
      expect(perfButton).toBeInTheDocument();
    });
  });

  it('organization name displays correctly in header', async () => {
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === 'churnguard-organization') {
        return JSON.stringify({ name: 'Test Organization' });
      }
      return null;
    });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Organization')).toBeInTheDocument();
    });
  });
});