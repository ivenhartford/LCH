import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MyCalendar from './Calendar';

jest.mock('react-big-calendar', () => ({
  Calendar: ({ events, onSelectSlot }) => (
    <div>
      <button onClick={() => onSelectSlot({ start: new Date(), end: new Date() })}>
        Select Slot
      </button>
      {events.map(event => (
        <div key={event.id}>{event.title}</div>
      ))}
    </div>
  ),
  momentLocalizer: () => {},
}));

beforeEach(() => {
  jest.spyOn(window, 'fetch').mockImplementation(url => {
    if (url === '/api/appointments') {
      return Promise.resolve({
        ok: true,
        json: async () => [
          {
            id: 1,
            title: 'Test Appointment',
            start: '2025-01-01T10:00:00',
            end: '2025-01-01T11:00:00',
            description: 'A test appointment',
          },
        ],
      });
    }
    return Promise.resolve({
      ok: true,
      json: async () => ({}),
    });
  });
});

afterEach(() => {
  jest.restoreAllMocks();
});

test('renders calendar and fetches appointments', async () => {
  render(<MyCalendar />);

  await waitFor(() => {
    expect(screen.getByText('Test Appointment')).toBeInTheDocument();
  });
});

test('opens modal on slot select and creates appointment', async () => {
  render(<MyCalendar />);

  fireEvent.click(screen.getByText('Select Slot'));

  await waitFor(() => {
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  fireEvent.change(screen.getByLabelText('Title:'), { target: { value: 'New Appointment' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save' }));

  await waitFor(() => {
    expect(window.fetch).toHaveBeenCalledWith('/api/appointments', expect.any(Object));
  });
});
