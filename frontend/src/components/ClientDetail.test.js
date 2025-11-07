import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { NotificationProvider } from '../contexts/NotificationContext';
import ClientDetail from './ClientDetail';
import logger from '../utils/logger';

// Mock logger
jest.mock('../utils/logger', () => ({
  logLifecycle: jest.fn(),
  logAction: jest.fn(),
  logAPICall: jest.fn(),
  info: jest.fn(),
  error: jest.fn(),
}));

// Mock useNavigate and useParams
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ clientId: '1' }),
}));

// Helper to render component with providers
const renderWithProviders = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <NotificationProvider>
          <ClientDetail />
        </NotificationProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

// Mock fetch
global.fetch = jest.fn();

const mockClient = {
  id: 1,
  first_name: 'John',
  last_name: 'Doe',
  email: 'john@example.com',
  phone_primary: '555-0101',
  phone_secondary: '555-0102',
  address_line1: '123 Main St',
  city: 'New York',
  state: 'NY',
  zip_code: '10001',
  account_balance: '150.50',
  is_active: true,
  preferred_contact: 'email',
  email_reminders: true,
  sms_reminders: false,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

describe('ClientDetail Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    global.fetch.mockRestore();
  });

  test('renders client details', async () => {
    // Mock both client and patients fetch
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockClient,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ patients: [] }),
      });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    expect(screen.getByText('john@example.com')).toBeInTheDocument();
    expect(screen.getByText('555-0101')).toBeInTheDocument();
    expect(screen.getByText('$150.50')).toBeInTheDocument();
  });

  test('navigates to edit when edit button clicked', async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockClient,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ patients: [] }),
      });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const editButton = screen.getByRole('button', { name: /Edit/i });
    await userEvent.click(editButton);

    expect(mockNavigate).toHaveBeenCalledWith('/clients/1/edit');
  });

  test('logs lifecycle events', async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockClient,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ patients: [] }),
      });

    const { unmount } = renderWithProviders();

    expect(logger.logLifecycle).toHaveBeenCalledWith('ClientDetail', 'mounted', {
      clientId: '1',
    });

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    unmount();

    expect(logger.logLifecycle).toHaveBeenCalledWith('ClientDetail', 'unmounted');
  });
});
