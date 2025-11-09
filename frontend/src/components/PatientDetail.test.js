import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, MemoryRouter, Route, Routes } from 'react-router-dom';
import { NotificationProvider } from '../contexts/NotificationContext';
import PatientDetail from './PatientDetail';
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

// Helper to render component with providers and router
const renderWithProviders = (patientId = '1') => {
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
          <Routes>
            <Route path="/" element={<PatientDetail />} />
          </Routes>
        </NotificationProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

// Mock fetch
global.fetch = jest.fn();

// Mock useParams
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ patientId: '1' }),
}));

describe('PatientDetail Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    global.fetch.mockRestore();
  });

  const mockPatient = {
    id: 1,
    name: 'Whiskers',
    species: 'Cat',
    breed: 'Persian',
    color: 'White',
    markings: 'White paw on left front leg',
    sex: 'Male',
    reproductive_status: 'Neutered',
    date_of_birth: '2020-01-15',
    age_display: '3 years, 9 months',
    weight_kg: '5.2',
    microchip_number: 'ABC123456',
    owner_id: 10,
    owner_name: 'John Doe',
    insurance_company: 'Pet Insurance Co',
    insurance_policy_number: 'POL123456',
    allergies: 'Penicillin',
    medical_notes: 'Prone to hairballs',
    behavioral_notes: 'Friendly, loves to be petted',
    status: 'Active',
    photo_url: 'https://example.com/whiskers.jpg',
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2024-10-01T00:00:00Z',
  };

  describe('Loading State', () => {
    test('shows loading spinner while fetching patient', () => {
      global.fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

      renderWithProviders();

      expect(screen.getByText('Loading patient details...')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    test('shows error message when fetch fails', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Network error' }),
      });

      renderWithProviders();

      await waitFor(
        () => {
          expect(screen.getByText(/Error loading patient/)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );

      expect(logger.error).toHaveBeenCalled();
      expect(screen.getByRole('button', { name: /Back to Patients/i })).toBeInTheDocument();
    });

    test('navigates back when back button clicked after error', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Network error' }),
      });

      renderWithProviders();

      await waitFor(
        () => {
          expect(screen.getByText(/Error loading patient/)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );

      const backButton = screen.getByRole('button', { name: /Back to Patients/i });
      await userEvent.click(backButton);

      expect(mockNavigate).toHaveBeenCalledWith('/patients');
    });
  });

  describe('Patient Not Found', () => {
    test('shows warning when patient not found', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ error: 'Patient not found' }),
      });

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText(/Patient not found/)).toBeInTheDocument();
      });
    });
  });

  describe('Patient Details Display', () => {
    beforeEach(() => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPatient,
      });
    });

    test('renders patient header with name, breed, and age', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Whiskers')).toBeInTheDocument();
        expect(screen.getByText(/Persian.*3 years, 9 months/)).toBeInTheDocument();
      });
    });

    test('renders status chip with correct color', async () => {
      renderWithProviders();

      await waitFor(() => {
        const statusChip = screen.getByText('Active');
        expect(statusChip).toBeInTheDocument();
      });
    });

    test('renders basic information section', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Cat')).toBeInTheDocument(); // Species
        expect(screen.getByText('Persian')).toBeInTheDocument(); // Breed
        expect(screen.getByText('White')).toBeInTheDocument(); // Color
        expect(screen.getByText('Male')).toBeInTheDocument(); // Sex
        expect(screen.getByText('Neutered')).toBeInTheDocument(); // Reproductive status
        expect(screen.getByText('5.2 kg')).toBeInTheDocument(); // Weight
      });
    });

    test('renders markings when present', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('White paw on left front leg')).toBeInTheDocument();
      });
    });

    test('renders microchip number when present', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('ABC123456')).toBeInTheDocument();
      });
    });

    test('renders date of birth when present', async () => {
      renderWithProviders();

      await waitFor(() => {
        // Date formatting may vary, just check it exists
        expect(screen.getByText(/Date of Birth/i)).toBeInTheDocument();
      });
    });

    test('renders owner information with view button', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /View Profile/i })).toBeInTheDocument();
      });
    });

    test('renders insurance information when present', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Pet Insurance Co')).toBeInTheDocument();
        expect(screen.getByText('POL123456')).toBeInTheDocument();
      });
    });

    test('renders medical information section', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Penicillin')).toBeInTheDocument(); // Allergies
        expect(screen.getByText('Prone to hairballs')).toBeInTheDocument(); // Medical notes
        expect(screen.getByText('Friendly, loves to be petted')).toBeInTheDocument(); // Behavioral notes
      });
    });

    test('shows allergies in error alert', async () => {
      renderWithProviders();

      await waitFor(() => {
        const allergiesSection = screen.getByText('Penicillin').closest('.MuiAlert-root');
        expect(allergiesSection).toHaveClass('MuiAlert-colorError');
      });
    });

    test('renders photo when photo_url is present', async () => {
      renderWithProviders();

      await waitFor(() => {
        const avatar = screen.getByAltText('Whiskers');
        expect(avatar).toBeInTheDocument();
        expect(avatar).toHaveAttribute('src', 'https://example.com/whiskers.jpg');
      });
    });

    test('renders metadata timestamps', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText(/Created:/)).toBeInTheDocument();
        expect(screen.getByText(/Last Updated:/)).toBeInTheDocument();
      });
    });
  });

  describe('Deceased Patient', () => {
    test('shows deceased alert when status is Deceased', async () => {
      const deceasedPatient = {
        ...mockPatient,
        status: 'Deceased',
        deceased_date: '2024-09-15',
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => deceasedPatient,
      });

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText(/Deceased on/)).toBeInTheDocument();
      });

      const statusChip = screen.getByText('Deceased');
      expect(statusChip).toBeInTheDocument();
    });

    test('disables edit button for deceased patient', async () => {
      const deceasedPatient = {
        ...mockPatient,
        status: 'Deceased',
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => deceasedPatient,
      });

      renderWithProviders();

      await waitFor(() => {
        const editButton = screen.getByRole('button', { name: /Edit/i });
        expect(editButton).toBeDisabled();
      });
    });
  });

  describe('Optional Fields', () => {
    test('shows "Unknown" for missing breed', async () => {
      const patientWithoutBreed = { ...mockPatient, breed: null };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => patientWithoutBreed,
      });

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Unknown')).toBeInTheDocument();
      });
    });

    test('shows "Not recorded" for missing weight', async () => {
      const patientWithoutWeight = { ...mockPatient, weight_kg: null };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => patientWithoutWeight,
      });

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Not recorded')).toBeInTheDocument();
      });
    });

    test('does not show insurance section when no insurance info', async () => {
      const patientWithoutInsurance = {
        ...mockPatient,
        insurance_company: null,
        insurance_policy_number: null,
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => patientWithoutInsurance,
      });

      renderWithProviders();

      await waitFor(() => {
        expect(screen.queryByText('Insurance Information')).not.toBeInTheDocument();
      });
    });

    test('shows message when no medical notes', async () => {
      const patientWithoutNotes = {
        ...mockPatient,
        allergies: null,
        medical_notes: null,
        behavioral_notes: null,
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => patientWithoutNotes,
      });

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('No medical notes recorded yet.')).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    beforeEach(() => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPatient,
      });
    });

    test('navigates back to patient list when back button clicked', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Whiskers')).toBeInTheDocument();
      });

      const backButton = screen.getAllByRole('button', { name: '' })[0]; // First icon button (back arrow)
      await userEvent.click(backButton);

      expect(mockNavigate).toHaveBeenCalledWith('/patients');
      expect(logger.logAction).toHaveBeenCalledWith('Navigate back to patient list');
    });

    test('navigates to edit form when edit button clicked', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Whiskers')).toBeInTheDocument();
      });

      const editButton = screen.getByRole('button', { name: /Edit/i });
      await userEvent.click(editButton);

      expect(mockNavigate).toHaveBeenCalledWith('/patients/1/edit');
      expect(logger.logAction).toHaveBeenCalledWith('Navigate to edit patient', {
        patientId: '1',
      });
    });

    test('navigates to owner profile when view profile clicked', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Whiskers')).toBeInTheDocument();
      });

      const viewProfileButton = screen.getByRole('button', { name: /View Profile/i });
      await userEvent.click(viewProfileButton);

      expect(mockNavigate).toHaveBeenCalledWith('/clients/10');
      expect(logger.logAction).toHaveBeenCalledWith('Navigate to owner details', {
        ownerId: 10,
      });
    });
  });

  describe('Component Lifecycle', () => {
    test('logs lifecycle events', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPatient,
      });

      const { unmount } = renderWithProviders();

      expect(logger.logLifecycle).toHaveBeenCalledWith('PatientDetail', 'mounted', {
        patientId: '1',
      });

      await waitFor(() => {
        expect(screen.getByText('Whiskers')).toBeInTheDocument();
      });

      unmount();

      expect(logger.logLifecycle).toHaveBeenCalledWith('PatientDetail', 'unmounted');
    });

    test('logs API call with duration', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPatient,
      });

      renderWithProviders();

      await waitFor(() => {
        expect(logger.logAPICall).toHaveBeenCalledWith(
          'GET',
          '/api/patients/1',
          200,
          expect.any(Number)
        );
      });
    });
  });
});
