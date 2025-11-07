/**
 * Test Utilities
 *
 * Provides custom render functions and utilities for testing React components
 * with all necessary context providers.
 */

import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NotificationProvider } from './contexts/NotificationContext';

/**
 * Create a new QueryClient for each test to ensure isolation
 */
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Don't retry failed queries in tests
        cacheTime: 0, // Don't cache data in tests
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: console.log,
      warn: console.warn,
      error: () => {}, // Suppress error logging in tests
    },
  });
}

/**
 * Wrapper component that provides all necessary context providers for testing
 * Uses MemoryRouter instead of BrowserRouter for better test isolation
 */
function AllTheProviders({ children }) {
  const queryClient = createTestQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <NotificationProvider>{children}</NotificationProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

/**
 * Custom render function that wraps components with all providers
 *
 * Usage:
 * ```jsx
 * import { renderWithProviders } from './test-utils';
 *
 * test('renders component', () => {
 *   renderWithProviders(<MyComponent />);
 *   // assertions...
 * });
 * ```
 */
function renderWithProviders(ui, options) {
  return render(ui, { wrapper: AllTheProviders, ...options });
}

// Re-export everything from React Testing Library
export * from '@testing-library/react';

// Override the default render with our custom version
export { renderWithProviders as render };
