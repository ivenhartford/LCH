import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { NotificationProvider } from '../contexts/NotificationContext';
import PatientForm from './PatientForm';
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
let mockSearchParams = new URLSearchParams();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => mockParams,
  useSearchParams: () => [mockSearchParams, jest.fn()],
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
      <BrowserRouter>
        <NotificationProvider>
          <PatientForm />
        </NotificationProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

// Mock fetch
global.fetch = jest.fn();

// Mock window.confirm
global.confirm = jest.fn();

describe('PatientForm Component', () => {
  const mockOwners = [
    { id: 1, first_name: 'John', last_name: 'Doe' },
    { id: 2, first_name: 'Jane', last_name: 'Smith' },
  ];

  const mockPatient = {
    id: 1,
    name: 'Whiskers',
    species: 'Cat',
    breed: 'Persian',
    color: 'White',
    markings: 'White paw',
    sex: 'Male',
    reproductive_status: 'Neutered',
    date_of_birth: '2020-01-15',
    weight_kg: '5.2',
    microchip_number: 'ABC123',
    owner_id: 1,
    insurance_company: 'Pet Insurance',
    insurance_policy_number: 'POL123',
    allergies: 'Penicillin',
    medical_notes: 'Hairballs',
    behavioral_notes: 'Friendly',
    status: 'Active',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockParams = {};
    mockSearchParams = new URLSearchParams();
    global.confirm.mockReturnValue(true);

    // Mock owners fetch by default
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ clients: mockOwners }),
    });
  });

  afterEach(() => {
    global.fetch.mockRestore();
  });

  describe('Create Mode', () => {
    test('renders create form with all fields', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Patient')).toBeInTheDocument();
      });

      // Check required fields
      expect(screen.getByLabelText(/Cat's Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Species/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Owner/i)).toBeInTheDocument();

      // Check optional fields
      expect(screen.getByLabelText(/Breed/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Color/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Sex/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Weight/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Microchip Number/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Allergies/i)).toBeInTheDocument();

      // Check buttons
      expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Save Patient/i })).toBeInTheDocument();
    });

    test('species field is disabled and set to "Cat"', async () => {
      renderWithProviders();

      await waitFor(() => {
        const speciesField = screen.getByLabelText(/Species/i);
        expect(speciesField).toBeDisabled();
        expect(speciesField).toHaveValue('Cat');
      });
    });

    test('shows validation error for missing required fields', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Patient')).toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /Save Patient/i });
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/Name is required/i)).toBeInTheDocument();
        expect(screen.getByText(/Owner is required/i)).toBeInTheDocument();
      });
    });

    test('submits form with valid data', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ clients: mockOwners }),
      });

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Patient')).toBeInTheDocument();
      });

      // Fill in required fields
      const nameInput = screen.getByLabelText(/Cat's Name/i);
      await userEvent.type(nameInput, 'Fluffy');

      // Select owner (using autocomplete)
      const ownerInput = screen.getByLabelText(/Owner/i);
      await userEvent.click(ownerInput);
      await userEvent.type(ownerInput, 'John');

      await waitFor(() => {
        const option = screen.getByText('John Doe');
        expect(option).toBeInTheDocument();
      });

      const option = screen.getByText('John Doe');
      await userEvent.click(option);

      // Fill in optional fields
      const breedInput = screen.getByLabelText(/Breed/i);
      await userEvent.type(breedInput, 'Persian');

      // Mock successful create
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 10, name: 'Fluffy', owner_id: 1 }),
      });

      const saveButton = screen.getByRole('button', { name: /Save Patient/i });
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/patients/10');
        expect(logger.info).toHaveBeenCalledWith('Patient created', {
          patientId: 10,
          name: 'Fluffy',
        });
      });
    });

    test('shows error message on create failure', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Patient')).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/Cat's Name/i);
      await userEvent.type(nameInput, 'Fluffy');

      const ownerInput = screen.getByLabelText(/Owner/i);
      await userEvent.click(ownerInput);
      await userEvent.type(ownerInput, 'John');

      await waitFor(() => {
        const option = screen.getByText('John Doe');
        expect(option).toBeInTheDocument();
      });

      const option = screen.getByText('John Doe');
      await userEvent.click(option);

      // Mock failed create
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: async () => ({ error: 'Microchip already exists' }),
      });

      const saveButton = screen.getByRole('button', { name: /Save Patient/i });
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText('Microchip already exists')).toBeInTheDocument();
        expect(logger.error).toHaveBeenCalled();
      });
    });

    test('pre-populates owner from URL parameter', async () => {
      mockSearchParams = new URLSearchParams('owner_id=1');

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ clients: mockOwners }),
      });

      renderWithProviders();

      await waitFor(() => {
        expect(logger.info).toHaveBeenCalledWith('Pre-populated owner from URL', {
          ownerId: 1,
          ownerName: 'John Doe',
        });
      });

      // Owner should be pre-selected
      const ownerInput = screen.getByLabelText(/Owner/i);
      expect(ownerInput).toHaveValue('John Doe');
    });
  });

  describe('Edit Mode', () => {
    beforeEach(() => {
      mockParams = { patientId: '1' };
    });

    test('renders edit form with title', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ clients: mockOwners }),
      });

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPatient,
      });

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Edit Patient')).toBeInTheDocument();
      });
    });

    test('loads and populates existing patient data', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ clients: mockOwners }),
      });

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPatient,
      });

      renderWithProviders();

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/Cat's Name/i);
        expect(nameInput).toHaveValue('Whiskers');
      });

      expect(screen.getByLabelText(/Breed/i)).toHaveValue('Persian');
      expect(screen.getByLabelText(/Color/i)).toHaveValue('White');
      expect(screen.getByLabelText(/Weight/i)).toHaveValue(5.2); // number input
      expect(screen.getByLabelText(/Microchip Number/i)).toHaveValue('ABC123');
    });

    test('submits form with updated data', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ clients: mockOwners }),
      });

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPatient,
      });

      renderWithProviders();

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/Cat's Name/i);
        expect(nameInput).toHaveValue('Whiskers');
      });

      // Update name
      const nameInput = screen.getByLabelText(/Cat's Name/i);
      await userEvent.clear(nameInput);
      await userEvent.type(nameInput, 'Whiskers Jr');

      // Mock successful update
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockPatient, name: 'Whiskers Jr' }),
      });

      const saveButton = screen.getByRole('button', { name: /Save Patient/i });
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/patients/1');
        expect(logger.info).toHaveBeenCalledWith('Patient updated', {
          patientId: 1,
          name: 'Whiskers Jr',
        });
      });
    });

    test('shows error message on update failure', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ clients: mockOwners }),
      });

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPatient,
      });

      renderWithProviders();

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/Cat's Name/i);
        expect(nameInput).toHaveValue('Whiskers');
      });

      const nameInput = screen.getByLabelText(/Cat's Name/i);
      await userEvent.clear(nameInput);
      await userEvent.type(nameInput, 'Updated Name');

      // Mock failed update
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Server error' }),
      });

      const saveButton = screen.getByRole('button', { name: /Save Patient/i });
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText('Server error')).toBeInTheDocument();
      });
    });
  });

  describe('Status Field', () => {
    test('shows deceased_date field when status is Deceased', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Patient')).toBeInTheDocument();
      });

      // Initially, deceased_date should not be visible
      expect(screen.queryByLabelText(/Deceased Date/i)).not.toBeInTheDocument();

      // Change status to Deceased - MUI Select requires special handling
      // Use getAllByLabelText since there might be multiple "Status" labels (Sex, Reproductive Status)
      const statusFields = screen.getAllByLabelText(/^Status$/i);
      const statusField = statusFields[statusFields.length - 1]; // Get the last one (the actual Status field)
      fireEvent.mouseDown(statusField);

      // Wait for dropdown and click Deceased option
      await waitFor(() => {
        const deceasedOption = screen.getByRole('option', { name: 'Deceased' });
        expect(deceasedOption).toBeInTheDocument();
      });

      const deceasedOption = screen.getByRole('option', { name: 'Deceased' });
      fireEvent.click(deceasedOption);

      // Now deceased_date should be visible
      await waitFor(() => {
        expect(screen.getByLabelText(/Deceased Date/i)).toBeInTheDocument();
      });
    });

    test('hides deceased_date field when status is not Deceased', async () => {
      mockParams = { patientId: '1' };
      const deceasedPatient = { ...mockPatient, status: 'Deceased', deceased_date: '2024-09-15' };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ clients: mockOwners }),
      });

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => deceasedPatient,
      });

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByLabelText(/Deceased Date/i)).toBeInTheDocument();
      });

      // Change status to Active - MUI Select requires special handling
      // Use getAllByLabelText since there might be multiple "Status" labels (Sex, Reproductive Status)
      const statusFields = screen.getAllByLabelText(/^Status$/i);
      const statusField = statusFields[statusFields.length - 1]; // Get the last one (the actual Status field)
      fireEvent.mouseDown(statusField);

      // Wait for dropdown and click Active option
      await waitFor(() => {
        const activeOption = screen.getByRole('option', { name: 'Active' });
        expect(activeOption).toBeInTheDocument();
      });

      const activeOption = screen.getByRole('option', { name: 'Active' });
      fireEvent.click(activeOption);

      // deceased_date should be hidden
      await waitFor(() => {
        expect(screen.queryByLabelText(/Deceased Date/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Navigation and Cancellation', () => {
    test('navigates back when cancel button clicked without changes', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Patient')).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await userEvent.click(cancelButton);

      expect(mockNavigate).toHaveBeenCalledWith('/patients');
      expect(logger.logAction).toHaveBeenCalledWith('Navigate back from patient form');
    });

    test('shows confirmation dialog when cancelling with unsaved changes', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Patient')).toBeInTheDocument();
      });

      // Make a change
      const nameInput = screen.getByLabelText(/Cat's Name/i);
      await userEvent.type(nameInput, 'Fluffy');

      global.confirm.mockReturnValue(true);

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await userEvent.click(cancelButton);

      expect(global.confirm).toHaveBeenCalledWith(
        'You have unsaved changes. Are you sure you want to leave?'
      );
      expect(mockNavigate).toHaveBeenCalledWith('/patients');
    });

    test('does not navigate when user cancels confirmation', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Patient')).toBeInTheDocument();
      });

      // Make a change
      const nameInput = screen.getByLabelText(/Cat's Name/i);
      await userEvent.type(nameInput, 'Fluffy');

      global.confirm.mockReturnValue(false);

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await userEvent.click(cancelButton);

      expect(global.confirm).toHaveBeenCalled();
      expect(mockNavigate).not.toHaveBeenCalled();
      expect(logger.logAction).toHaveBeenCalledWith('Cancelled navigation with unsaved changes');
    });

    test('navigates to patient detail after edit', async () => {
      mockParams = { patientId: '1' };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ clients: mockOwners }),
      });

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPatient,
      });

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Edit Patient')).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await userEvent.click(cancelButton);

      expect(mockNavigate).toHaveBeenCalledWith('/patients/1');
    });
  });

  describe('Loading and Error States', () => {
    test('shows loading spinner while fetching owners', () => {
      global.fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

      renderWithProviders();

      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    test('shows loading spinner while fetching patient data in edit mode', async () => {
      mockParams = { patientId: '1' };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ clients: mockOwners }),
      });

      global.fetch.mockImplementation(() => new Promise(() => {})); // Patient fetch never resolves

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Loading...')).toBeInTheDocument();
      });
    });

    test('shows error state when patient fetch fails in edit mode', async () => {
      mockParams = { patientId: '1' };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ clients: mockOwners }),
      });

      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText(/Error loading patient/)).toBeInTheDocument();
      });

      expect(logger.error).toHaveBeenCalled();
    });
  });

  describe('Component Lifecycle', () => {
    test('logs lifecycle events for create mode', async () => {
      const { unmount } = renderWithProviders();

      expect(logger.logLifecycle).toHaveBeenCalledWith('PatientForm', 'mounted', {
        mode: 'create',
        patientId: undefined,
        preselectedOwnerId: null,
      });

      await waitFor(() => {
        expect(screen.getByText('New Patient')).toBeInTheDocument();
      });

      unmount();

      expect(logger.logLifecycle).toHaveBeenCalledWith('PatientForm', 'unmounted');
    });

    test('logs lifecycle events for edit mode', async () => {
      mockParams = { patientId: '1' };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ clients: mockOwners }),
      });

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPatient,
      });

      renderWithProviders();

      expect(logger.logLifecycle).toHaveBeenCalledWith('PatientForm', 'mounted', {
        mode: 'edit',
        patientId: '1',
        preselectedOwnerId: null,
      });
    });
  });

  describe('Save Button State', () => {
    test('save button is disabled when form is pristine', async () => {
      mockParams = { patientId: '1' };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ clients: mockOwners }),
      });

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPatient,
      });

      renderWithProviders();

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: /Save Patient/i });
        expect(saveButton).toBeDisabled();
      });
    });

    test('save button is enabled when form is dirty', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Patient')).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/Cat's Name/i);
      await userEvent.type(nameInput, 'Fluffy');

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: /Save Patient/i });
        expect(saveButton).not.toBeDisabled();
      });
    });

    test('save button shows loading state during submission', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('New Patient')).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/Cat's Name/i);
      await userEvent.type(nameInput, 'Fluffy');

      const ownerInput = screen.getByLabelText(/Owner/i);
      await userEvent.click(ownerInput);
      await userEvent.type(ownerInput, 'John');

      await waitFor(() => {
        const option = screen.getByText('John Doe');
        expect(option).toBeInTheDocument();
      });

      const option = screen.getByText('John Doe');
      await userEvent.click(option);

      // Mock slow create
      global.fetch.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => ({ id: 10, name: 'Fluffy' }),
                }),
              100
            )
          )
      );

      const saveButton = screen.getByRole('button', { name: /Save Patient/i });
      await userEvent.click(saveButton);

      // Should show "Saving..." immediately
      await waitFor(() => {
        expect(screen.getByText('Saving...')).toBeInTheDocument();
      });
    });
  });
});
