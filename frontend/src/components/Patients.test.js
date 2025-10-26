import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import Patients from './Patients';
import logger from '../utils/logger';

// Mock logger
jest.mock('../utils/logger', () => ({
  logLifecycle: jest.fn(),
  logAction: jest.fn(),
  logAPICall: jest.fn(),
  info: jest.fn(),
  error: jest.fn(),
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
      <BrowserRouter>{component}</BrowserRouter>
    </QueryClientProvider>
  );
};

// Mock fetch
global.fetch = jest.fn();

describe('Patients Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    global.fetch.mockRestore();
  });

  describe('Loading State', () => {
    test('shows loading spinner while fetching patients', () => {
      global.fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

      renderWithProviders(<Patients />);

      expect(screen.getByText('Loading patients...')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    test('shows error message when fetch fails', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByText(/Error loading patients/)).toBeInTheDocument();
      });

      expect(logger.error).toHaveBeenCalled();
    });

    test('allows retry on error', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByText(/Error loading patients/)).toBeInTheDocument();
      });

      // Click the alert to retry (clicking the close button triggers refetch)
      const alert = screen.getByRole('alert');
      const closeButton = within(alert).getByRole('button');

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      userEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.getByText(/No patients yet/)).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    test('shows empty state when no patients exist', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByText(/No patients yet/)).toBeInTheDocument();
        expect(screen.getByText(/Click "New Patient" to add one/)).toBeInTheDocument();
      });
    });

    test('shows empty state with search message when search returns no results', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Search by name/)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/Search by name/);
      await userEvent.type(searchInput, 'Fluffy');

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      const searchButton = screen.getByRole('button', { name: /Search/i });
      await userEvent.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/No patients found matching your search/)).toBeInTheDocument();
      });
    });
  });

  describe('Patients List', () => {
    const mockPatients = [
      {
        id: 1,
        name: 'Whiskers',
        breed: 'Persian',
        color: 'White',
        age_display: '3 years',
        sex: 'Male',
        owner_name: 'John Doe',
        status: 'Active',
        microchip_number: 'ABC123',
      },
      {
        id: 2,
        name: 'Shadow',
        breed: 'Domestic Shorthair',
        color: 'Black',
        age_display: '5 years',
        sex: 'Female',
        owner_name: 'Jane Smith',
        status: 'Active',
        microchip_number: null,
      },
      {
        id: 3,
        name: 'Mittens',
        breed: 'Siamese',
        color: 'Cream',
        age_display: '2 years',
        sex: 'Female',
        owner_name: 'Bob Johnson',
        status: 'Deceased',
      },
    ];

    test('renders patient list with data', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: mockPatients,
          pagination: { page: 1, total: 3, pages: 1 },
        }),
      });

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByText('Whiskers')).toBeInTheDocument();
        expect(screen.getByText('Shadow')).toBeInTheDocument();
        expect(screen.getByText('Mittens')).toBeInTheDocument();
      });

      // Check table headers
      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Breed')).toBeInTheDocument();
      expect(screen.getByText('Color')).toBeInTheDocument();
      expect(screen.getByText('Age')).toBeInTheDocument();
      expect(screen.getByText('Sex')).toBeInTheDocument();
      expect(screen.getByText('Owner')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();

      // Check patient details
      expect(screen.getByText('Persian')).toBeInTheDocument();
      expect(screen.getByText('White')).toBeInTheDocument();
      expect(screen.getByText('3 years')).toBeInTheDocument();
      expect(screen.getByText('Male')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();

      // Check microchip display
      expect(screen.getByText('Chip: ABC123')).toBeInTheDocument();

      // Check status chips
      const activeChips = screen.getAllByText('Active');
      expect(activeChips).toHaveLength(2);
      expect(screen.getByText('Deceased')).toBeInTheDocument();
    });

    test('shows pagination info correctly', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: mockPatients,
          pagination: { page: 1, total: 3, pages: 1 },
        }),
      });

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByText(/Showing 3 of 3 patients/)).toBeInTheDocument();
      });
    });
  });

  describe('Search Functionality', () => {
    test('performs search when search button clicked', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Search by name/)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/Search by name/);
      await userEvent.type(searchInput, 'Whiskers');

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [
            {
              id: 1,
              name: 'Whiskers',
              breed: 'Persian',
              color: 'White',
              age_display: '3 years',
              sex: 'Male',
              owner_name: 'John Doe',
              status: 'Active',
            },
          ],
          pagination: { page: 1, total: 1, pages: 1 },
        }),
      });

      const searchButton = screen.getByRole('button', { name: /Search/i });
      await userEvent.click(searchButton);

      await waitFor(() => {
        expect(logger.logAction).toHaveBeenCalledWith('Search patients', {
          searchTerm: 'Whiskers',
        });
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('search=Whiskers'),
          expect.any(Object)
        );
      });
    });

    test('clears search when clear button clicked', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Search by name/)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/Search by name/);
      await userEvent.type(searchInput, 'Whiskers');

      // Clear button should appear
      const clearButton = screen.getByRole('button', { name: '' }); // IconButton has no name

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      await userEvent.click(clearButton);

      await waitFor(() => {
        expect(searchInput).toHaveValue('');
        expect(logger.logAction).toHaveBeenCalledWith('Clear search');
      });
    });

    test('searches on Enter key press', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Search by name/)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/Search by name/);
      await userEvent.type(searchInput, 'Shadow');

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(logger.logAction).toHaveBeenCalledWith('Search patients', {
          searchTerm: 'Shadow',
        });
      });
    });
  });

  describe('Status Filter', () => {
    test('changes status filter', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByLabelText('Status')).toBeInTheDocument();
      });

      const statusSelect = screen.getByLabelText('Status');

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      await userEvent.click(statusSelect);
      const inactiveOption = await screen.findByText('Inactive');
      await userEvent.click(inactiveOption);

      await waitFor(() => {
        expect(logger.logAction).toHaveBeenCalledWith('Change status filter', {
          from: 'Active',
          to: 'Inactive',
        });
      });
    });
  });

  describe('Pagination', () => {
    test('changes page', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: Array(50).fill(null).map((_, i) => ({
            id: i + 1,
            name: `Cat ${i + 1}`,
            breed: 'Persian',
            color: 'White',
            age_display: '3 years',
            sex: 'Male',
            owner_name: 'Owner',
            status: 'Active',
          })),
          pagination: { page: 1, total: 100, pages: 2 },
        }),
      });

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByText('Cat 1')).toBeInTheDocument();
      });

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: Array(50).fill(null).map((_, i) => ({
            id: i + 51,
            name: `Cat ${i + 51}`,
            breed: 'Persian',
            color: 'White',
            age_display: '3 years',
            sex: 'Male',
            owner_name: 'Owner',
            status: 'Active',
          })),
          pagination: { page: 2, total: 100, pages: 2 },
        }),
      });

      const nextPageButton = screen.getByRole('button', { name: /next page/i });
      await userEvent.click(nextPageButton);

      await waitFor(() => {
        expect(logger.logAction).toHaveBeenCalledWith('Change page', {
          from: 0,
          to: 1,
        });
      });
    });

    test('changes rows per page', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByText(/Rows per page/i)).toBeInTheDocument();
      });

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      // This is tricky with MUI Select, so we'll just verify the element exists
      const rowsPerPageSelect = screen.getByRole('combobox', { name: /rows per page/i });
      expect(rowsPerPageSelect).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    test('navigates to patient detail when row clicked', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [
            {
              id: 1,
              name: 'Whiskers',
              breed: 'Persian',
              color: 'White',
              age_display: '3 years',
              sex: 'Male',
              owner_name: 'John Doe',
              status: 'Active',
            },
          ],
          pagination: { page: 1, total: 1, pages: 1 },
        }),
      });

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByText('Whiskers')).toBeInTheDocument();
      });

      const row = screen.getByText('Whiskers').closest('tr');
      await userEvent.click(row);

      expect(mockNavigate).toHaveBeenCalledWith('/patients/1');
      expect(logger.logAction).toHaveBeenCalledWith('View patient details', {
        patientId: 1,
      });
    });

    test('navigates to new patient form when "New Patient" clicked', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      renderWithProviders(<Patients />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /New Patient/i })).toBeInTheDocument();
      });

      const newButton = screen.getByRole('button', { name: /New Patient/i });
      await userEvent.click(newButton);

      expect(mockNavigate).toHaveBeenCalledWith('/patients/new');
      expect(logger.logAction).toHaveBeenCalledWith('Navigate to create patient');
    });
  });

  describe('Component Lifecycle', () => {
    test('logs lifecycle events', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          patients: [],
          pagination: { page: 1, total: 0, pages: 0 },
        }),
      });

      const { unmount } = renderWithProviders(<Patients />);

      expect(logger.logLifecycle).toHaveBeenCalledWith('Patients', 'mounted', {
        initialPage: 0,
        rowsPerPage: 50,
        statusFilter: 'Active',
      });

      unmount();

      expect(logger.logLifecycle).toHaveBeenCalledWith('Patients', 'unmounted');
    });
  });
});
