import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { NotificationProvider } from '../contexts/NotificationContext';
import ClientForm from './ClientForm';
import logger from '../utils/logger';

// Mock logger
jest.mock('../utils/logger', () => ({
  logLifecycle: jest.fn(),
  logAction: jest.fn(),
  logAPICall: jest.fn(),
  info: jest.fn(),
  error: jest.fn(),
}));

// Mock navigation hooks
const mockNavigate = jest.fn();
let mockParams = {};

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => mockParams,
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
          <ClientForm />
        </NotificationProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

// Mock fetch
global.fetch = jest.fn();

// Mock window.confirm
global.confirm = jest.fn();

const mockClient = {
  id: 1,
  first_name: 'John',
  last_name: 'Doe',
  email: 'john@example.com',
  phone_primary: '555-0101',
  is_active: true,
};

describe('ClientForm Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockParams = {};
    global.confirm.mockReturnValue(true);
  });

  afterEach(() => {
    global.fetch.mockRestore();
  });

  describe('Create Mode', () => {
    test('renders create form', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Client')).toBeInTheDocument();
      });

      expect(screen.getByLabelText(/First Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Last Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Primary Phone/i)).toBeInTheDocument();
    });

    test('shows validation errors for required fields', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Client')).toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /Save Client/i });
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/First name is required/i)).toBeInTheDocument();
      });
    });

    test('submits form with valid data', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Client')).toBeInTheDocument();
      });

      const firstNameInput = screen.getByLabelText(/First Name/i);
      const lastNameInput = screen.getByLabelText(/Last Name/i);
      const phoneInput = screen.getByLabelText(/Primary Phone/i);

      await userEvent.type(firstNameInput, 'John');
      await userEvent.type(lastNameInput, 'Doe');
      await userEvent.type(phoneInput, '555-0101');

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 10, first_name: 'John', last_name: 'Doe' }),
      });

      const saveButton = screen.getByRole('button', { name: /Save Client/i });
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/clients/10');
      });
    });
  });

  describe('Edit Mode', () => {
    beforeEach(() => {
      mockParams = { clientId: '1' };
    });

    test('renders edit form', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockClient,
      });

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Edit Client')).toBeInTheDocument();
      });
    });

    test('loads and populates existing client data', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockClient,
      });

      renderWithProviders();

      await waitFor(() => {
        const firstNameInput = screen.getByLabelText(/First Name/i);
        expect(firstNameInput).toHaveValue('John');
      });

      expect(screen.getByLabelText(/Last Name/i)).toHaveValue('Doe');
      expect(screen.getByLabelText(/Primary Phone/i)).toHaveValue('555-0101');
    });
  });

  describe('Component Lifecycle', () => {
    test('logs lifecycle events for create mode', async () => {
      const { unmount } = renderWithProviders();

      expect(logger.logLifecycle).toHaveBeenCalledWith('ClientForm', 'mounted', {
        mode: 'create',
        clientId: undefined,
      });

      await waitFor(() => {
        expect(screen.getByText('New Client')).toBeInTheDocument();
      });

      unmount();

      expect(logger.logLifecycle).toHaveBeenCalledWith('ClientForm', 'unmounted');
    });
  });
});
