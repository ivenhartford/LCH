import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { NotificationProvider } from '../contexts/NotificationContext';
import Clients from './Clients';
import logger from '../utils/logger';

// Mock logger
jest.mock('../utils/logger', () => ({
  logLifecycle: jest.fn(),
  logAction: jest.fn(),
  logAPICall: jest.fn(),
  info: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
}));

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Helper to render component with providers
const renderWithProviders = (component) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <NotificationProvider>{component}</NotificationProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

// Mock fetch
global.fetch = jest.fn();

describe('Clients Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    global.fetch.mockRestore();
  });

  describe('Loading State', () => {
    test('shows loading spinner while fetching clients', () => {
      global.fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

      renderWithProviders(<Clients />);

      expect(screen.getByText('Loading clients...')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    test('shows empty state when no clients exist', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          clients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      renderWithProviders(<Clients />);

      await waitFor(() => {
        expect(screen.getByText(/No clients yet/)).toBeInTheDocument();
      });
    });
  });

  describe('Clients List', () => {
    const mockClients = [
      {
        id: 1,
        first_name: 'John',
        last_name: 'Doe',
        email: 'john@example.com',
        phone_primary: '555-0101',
        city: 'New York',
        is_active: true,
        account_balance: '150.50',
      },
      {
        id: 2,
        first_name: 'Jane',
        last_name: 'Smith',
        email: 'jane@example.com',
        phone_primary: '555-0102',
        city: 'Los Angeles',
        is_active: true,
        account_balance: '0.00',
      },
    ];

    test('renders client list with data', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          clients: mockClients,
          pagination: { page: 1, total: 2, pages: 1 },
        }),
      });

      renderWithProviders(<Clients />);

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      });

      // Check table headers
      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
      expect(screen.getByText('Phone')).toBeInTheDocument();

      // Check details
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
      expect(screen.getByText('555-0101')).toBeInTheDocument();
      expect(screen.getByText('New York')).toBeInTheDocument();
      expect(screen.getByText('$150.50')).toBeInTheDocument();
    });

    test('shows pagination info correctly', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          clients: mockClients,
          pagination: { page: 1, total: 2, pages: 1 },
        }),
      });

      renderWithProviders(<Clients />);

      await waitFor(() => {
        expect(screen.getByText(/Showing 2 of 2 clients/)).toBeInTheDocument();
      });
    });
  });

  describe('Search Functionality', () => {
    test('performs search when search button clicked', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          clients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      renderWithProviders(<Clients />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Search by name/)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/Search by name/);
      await userEvent.type(searchInput, 'John');

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          clients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      const searchButton = screen.getByRole('button', { name: /Search/i });
      await userEvent.click(searchButton);

      await waitFor(() => {
        expect(logger.logAction).toHaveBeenCalledWith('Search clients', {
          searchTerm: 'John',
        });
      });
    });

    test('clears search when clear button clicked', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          clients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      renderWithProviders(<Clients />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Search by name/)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/Search by name/);
      await userEvent.type(searchInput, 'John');

      // Find clear button (IconButton with ClearIcon)
      const buttons = screen.getAllByRole('button');
      const clearButton = buttons.find((btn) => btn.querySelector('svg')); // IconButton with icon

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          clients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      if (clearButton) {
        await userEvent.click(clearButton);

        await waitFor(() => {
          expect(searchInput).toHaveValue('');
        });
      }
    });
  });

  describe('Navigation', () => {
    test('navigates to client detail when row clicked', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          clients: [
            {
              id: 1,
              first_name: 'John',
              last_name: 'Doe',
              email: 'john@example.com',
              phone_primary: '555-0101',
              is_active: true,
              account_balance: '0.00',
            },
          ],
          pagination: { page: 1, total: 1, pages: 1 },
        }),
      });

      renderWithProviders(<Clients />);

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      const row = screen.getByText('John Doe').closest('tr');
      await userEvent.click(row);

      expect(mockNavigate).toHaveBeenCalledWith('/clients/1');
      expect(logger.logAction).toHaveBeenCalledWith('View client details', {
        clientId: 1,
      });
    });

    test('navigates to new client form when "New Client" clicked', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          clients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      renderWithProviders(<Clients />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /New Client/i })).toBeInTheDocument();
      });

      const newButton = screen.getByRole('button', { name: /New Client/i });
      await userEvent.click(newButton);

      expect(mockNavigate).toHaveBeenCalledWith('/clients/new');
      expect(logger.logAction).toHaveBeenCalledWith('Navigate to create client');
    });
  });

  describe('Component Lifecycle', () => {
    test('logs lifecycle events', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          clients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      const { unmount } = renderWithProviders(<Clients />);

      expect(logger.logLifecycle).toHaveBeenCalledWith('Clients', 'mounted', {
        initialPage: 0,
        rowsPerPage: 50,
        activeOnly: true,
      });

      unmount();

      expect(logger.logLifecycle).toHaveBeenCalledWith('Clients', 'unmounted');
    });
  });
});
