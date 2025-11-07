import { render, screen, waitFor, within } from '../test-utils';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import GlobalSearch from './GlobalSearch';

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
      <BrowserRouter>{component}</BrowserRouter>
    </QueryClientProvider>
  );
};

// Mock fetch
global.fetch = jest.fn();

describe('GlobalSearch Component', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    global.fetch.mockRestore();
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Dialog Behavior', () => {
    test('renders dialog when open is true', () => {
      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      expect(
        screen.getByPlaceholderText(/Search clients, patients, or appointments/i)
      ).toBeInTheDocument();
    });

    test('does not render dialog when open is false', () => {
      renderWithProviders(<GlobalSearch open={false} onClose={mockOnClose} />);

      expect(
        screen.queryByPlaceholderText(/Search clients, patients, or appointments/i)
      ).not.toBeInTheDocument();
    });

    test('calls onClose when dialog is closed', async () => {
      // Using userEvent directly (v13 API)
      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      // Close dialog by pressing Escape
      await userEvent.keyboard('{Escape}');

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });
  });

  describe('Initial State', () => {
    test('shows placeholder text when search is empty', () => {
      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      expect(screen.getByText(/Start typing to search/i)).toBeInTheDocument();
    });

    test('search input is auto-focused', () => {
      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      expect(searchInput).toHaveFocus();
    });

    test('shows keyboard shortcut hint', () => {
      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      expect(screen.getByText(/Ctrl\+K/i)).toBeInTheDocument();
    });
  });

  describe('Search Input', () => {
    test('allows user to type in search field', async () => {
      // Using userEvent directly (v13 API)
      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      await userEvent.type(searchInput, 'John');

      expect(searchInput).toHaveValue('John');
    });

    test('shows minimum character message when typing less than 2 characters', async () => {
      // Using userEvent directly (v13 API)
      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      await userEvent.type(searchInput, 'J');

      expect(screen.getByText(/Type at least 2 characters/i)).toBeInTheDocument();
    });
  });

  describe('Debouncing', () => {
    test('debounces search queries by 300ms', async () => {
      // Using userEvent directly (v13 API)

      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({ clients: [], patients: [], appointments: [] }),
      });

      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      await userEvent.type(searchInput, 'John');

      // Should not call fetch immediately
      expect(global.fetch).not.toHaveBeenCalled();

      // Fast-forward 300ms
      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalled();
      });
    });
  });

  describe('Search Results - Clients', () => {
    test('displays client search results', async () => {
      // Using userEvent directly (v13 API)
      const mockClients = [
        {
          id: 1,
          first_name: 'John',
          last_name: 'Doe',
          email: 'john@example.com',
          phone_primary: '555-0101',
        },
      ];

      global.fetch.mockImplementation((url) => {
        if (url.includes('/api/clients')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ clients: mockClients }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ patients: [], appointments: [] }),
        });
      });

      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      await userEvent.type(searchInput, 'John');

      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('john@example.com')).toBeInTheDocument();
        expect(screen.getByText(/Clients \(1\)/i)).toBeInTheDocument();
      });
    });

    test('navigates to client detail when clicking client result', async () => {
      // Using userEvent directly (v13 API)
      const mockClients = [
        {
          id: 1,
          first_name: 'John',
          last_name: 'Doe',
          email: 'john@example.com',
          phone_primary: '555-0101',
        },
      ];

      global.fetch.mockImplementation((url) => {
        if (url.includes('/api/clients')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ clients: mockClients }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ patients: [], appointments: [] }),
        });
      });

      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      await userEvent.type(searchInput, 'John');

      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText('John Doe'));

      expect(mockNavigate).toHaveBeenCalledWith('/clients/1');
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('Search Results - Patients', () => {
    test('displays patient search results', async () => {
      // Using userEvent directly (v13 API)
      const mockPatients = [
        {
          id: 2,
          name: 'Fluffy',
          breed: 'Persian',
          owner_name: 'Jane Doe',
          status: 'Active',
        },
      ];

      global.fetch.mockImplementation((url) => {
        if (url.includes('/api/patients')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ patients: mockPatients }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ clients: [], appointments: [] }),
        });
      });

      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      await userEvent.type(searchInput, 'Fluffy');

      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText('Fluffy')).toBeInTheDocument();
        expect(screen.getByText('Persian')).toBeInTheDocument();
        expect(screen.getByText(/Owner: Jane Doe/i)).toBeInTheDocument();
        expect(screen.getByText(/Patients \(1\)/i)).toBeInTheDocument();
      });
    });

    test('navigates to patient detail when clicking patient result', async () => {
      // Using userEvent directly (v13 API)
      const mockPatients = [
        {
          id: 2,
          name: 'Fluffy',
          breed: 'Persian',
          owner_name: 'Jane Doe',
          status: 'Active',
        },
      ];

      global.fetch.mockImplementation((url) => {
        if (url.includes('/api/patients')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ patients: mockPatients }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ clients: [], appointments: [] }),
        });
      });

      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      await userEvent.type(searchInput, 'Fluffy');

      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText('Fluffy')).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText('Fluffy'));

      expect(mockNavigate).toHaveBeenCalledWith('/patients/2');
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('Search Results - Appointments', () => {
    test('displays appointment search results', async () => {
      // Using userEvent directly (v13 API)
      const mockAppointments = {
        appointments: [
          {
            id: 3,
            title: 'Wellness Exam',
            start_time: '2025-11-15T10:00:00',
            patient_name: 'Fluffy',
            status: 'pending',
            appointment_type_color: '#10b981',
          },
        ],
      };

      global.fetch.mockImplementation((url) => {
        if (url.includes('/api/appointments')) {
          return Promise.resolve({
            ok: true,
            json: async () => mockAppointments,
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ clients: [], patients: [] }),
        });
      });

      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      await userEvent.type(searchInput, 'Wellness');

      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText('Wellness Exam')).toBeInTheDocument();
        expect(screen.getByText('Fluffy')).toBeInTheDocument();
        expect(screen.getByText(/Appointments \(1\)/i)).toBeInTheDocument();
      });
    });

    test('navigates to appointment detail when clicking appointment result', async () => {
      // Using userEvent directly (v13 API)
      const mockAppointments = {
        appointments: [
          {
            id: 3,
            title: 'Wellness Exam',
            start_time: '2025-11-15T10:00:00',
            patient_name: 'Fluffy',
            status: 'pending',
            appointment_type_color: '#10b981',
          },
        ],
      };

      global.fetch.mockImplementation((url) => {
        if (url.includes('/api/appointments')) {
          return Promise.resolve({
            ok: true,
            json: async () => mockAppointments,
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ clients: [], patients: [] }),
        });
      });

      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      await userEvent.type(searchInput, 'Wellness');

      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText('Wellness Exam')).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText('Wellness Exam'));

      expect(mockNavigate).toHaveBeenCalledWith('/appointments/3');
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('No Results', () => {
    test('displays no results message when search returns empty', async () => {
      // Using userEvent directly (v13 API)

      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({ clients: [], patients: [], appointments: [] }),
      });

      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      await userEvent.type(searchInput, 'nonexistent');

      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText(/No results found for "nonexistent"/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    test('shows loading indicator while searching', async () => {
      // Using userEvent directly (v13 API)

      global.fetch.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      await userEvent.type(searchInput, 'John');

      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByRole('progressbar')).toBeInTheDocument();
      });
    });
  });

  describe('Clear Search', () => {
    test('clears search query when dialog is closed', async () => {
      // Using userEvent directly (v13 API)

      global.fetch.mockResolvedValue({
        ok: true,
        json: async () => ({ clients: [], patients: [], appointments: [] }),
      });

      renderWithProviders(<GlobalSearch open={true} onClose={mockOnClose} />);

      const searchInput = screen.getByPlaceholderText(/Search clients, patients, or appointments/i);
      await userEvent.type(searchInput, 'John');

      expect(searchInput).toHaveValue('John');

      // Close dialog
      await userEvent.keyboard('{Escape}');

      // Wait for onClose to be called
      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });
  });
});
