import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, MemoryRouter, Route, Routes } from 'react-router-dom';
import { NotificationProvider } from '../contexts/NotificationContext';
import AppointmentDetail from './AppointmentDetail';

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Mock window.confirm
global.confirm = jest.fn(() => true);

// Helper to render component with providers and route params
const renderWithProviders = (component, { appointmentId = '1' } = {}) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }} initialEntries={[`/appointments/${appointmentId}`]}>
        <NotificationProvider>
          <Routes>
            <Route path="/appointments/:id" element={component} />
          </Routes>
        </NotificationProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

// Mock fetch
global.fetch = jest.fn();

describe('AppointmentDetail Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    global.fetch.mockRestore();
  });

  const mockAppointment = {
    id: 1,
    title: 'Wellness Exam - Fluffy',
    appointment_type_name: 'Wellness Exam',
    appointment_type_color: '#10b981',
    status: 'scheduled',
    start_time: '2025-11-15T10:00:00',
    end_time: '2025-11-15T10:30:00',
    patient_id: 2,
    patient_name: 'Fluffy',
    client_id: 1,
    client_name: 'Jane Doe',
    assigned_to_name: 'Dr. Smith',
    room: 'Room 1',
    description: 'Annual wellness checkup',
    duration_minutes: 30,
    created_at: '2025-11-01T09:00:00',
  };

  describe('Loading State', () => {
    test('shows loading spinner while fetching appointment', () => {
      global.fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

      renderWithProviders(<AppointmentDetail />);

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    test('shows error message when fetch fails', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Failed to fetch'));

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to load appointment/i)).toBeInTheDocument();
      });
    });

    test('shows error message when appointment not found', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to load appointment/i)).toBeInTheDocument();
      });
    });
  });

  describe('Appointment Display', () => {
    test('displays appointment details correctly', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAppointment,
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText('Wellness Exam - Fluffy')).toBeInTheDocument();
        expect(screen.getByText('Wellness Exam')).toBeInTheDocument();
        expect(screen.getByText(/Room 1/i)).toBeInTheDocument();
        expect(screen.getByText(/Annual wellness checkup/i)).toBeInTheDocument();
      });
    });

    test('displays status chip with correct color', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAppointment,
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/scheduled/i)).toBeInTheDocument();
      });
    });

    test('displays patient information', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAppointment,
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText('Fluffy')).toBeInTheDocument();
      });
    });

    test('displays client information', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAppointment,
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText('Jane Doe')).toBeInTheDocument();
      });
    });

    test('displays assigned staff', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAppointment,
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Dr. Smith/i)).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    test('shows back button', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAppointment,
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Back/i)).toBeInTheDocument();
      });
    });

    test('back button navigates to calendar', async () => {
      const user = userEvent.setup();
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAppointment,
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Back/i)).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText(/Back/i));

      expect(mockNavigate).toHaveBeenCalledWith('/calendar');
    });

    test('shows edit button', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAppointment,
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Edit/i)).toBeInTheDocument();
      });
    });
  });

  describe('Status Actions', () => {
    test('shows confirm button for scheduled appointments', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAppointment,
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Confirm/i)).toBeInTheDocument();
      });
    });

    test('shows check-in button for confirmed appointments', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockAppointment, status: 'confirmed' }),
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Check In/i)).toBeInTheDocument();
      });
    });

    test('shows start button for checked-in appointments', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockAppointment, status: 'checked_in' }),
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Start/i)).toBeInTheDocument();
      });
    });

    test('shows complete button for in-progress appointments', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockAppointment, status: 'in_progress' }),
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Complete/i)).toBeInTheDocument();
      });
    });

    test('updates status when confirm button is clicked', async () => {
      const user = userEvent.setup();
      global.fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockAppointment,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...mockAppointment, status: 'confirmed' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...mockAppointment, status: 'confirmed' }),
        });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Confirm/i)).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText(/Confirm/i));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/appointments/1',
          expect.objectContaining({
            method: 'PUT',
            body: expect.stringContaining('confirmed'),
          })
        );
      });
    });
  });

  describe('Cancel Functionality', () => {
    test('shows cancel button', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAppointment,
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Cancel Appointment/i)).toBeInTheDocument();
      });
    });

    test('prompts for cancellation reason', async () => {
      const user = userEvent.setup();
      const promptSpy = jest.spyOn(window, 'prompt').mockReturnValue('Patient is sick');

      global.fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockAppointment,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...mockAppointment, status: 'cancelled' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            ...mockAppointment,
            status: 'cancelled',
            cancellation_reason: 'Patient is sick',
          }),
        });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Cancel Appointment/i)).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText(/Cancel Appointment/i));

      expect(promptSpy).toHaveBeenCalled();
      promptSpy.mockRestore();
    });
  });

  describe('Completed Appointment', () => {
    test('hides action buttons for completed appointments', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockAppointment, status: 'completed' }),
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.queryByText(/Confirm/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/Check In/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/Start/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Cancelled Appointment', () => {
    test('displays cancellation reason when present', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...mockAppointment,
          status: 'cancelled',
          cancellation_reason: 'Patient emergency',
        }),
      });

      renderWithProviders(<AppointmentDetail />);

      await waitFor(() => {
        expect(screen.getByText(/Patient emergency/i)).toBeInTheDocument();
      });
    });
  });
});
